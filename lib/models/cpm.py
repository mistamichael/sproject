"""
CPM (Critical Path Method) calculation
======================================

Netzplanberechnung in reinen Arbeitstagen (Phase 1). Kalenderdaten mit
Wochenenden und Feiertagen entstehen über CPMResult.calendar bzw. den
GanttCalculator (Phase 2).
"""

import math
from datetime import datetime
from functools import cached_property
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from ..durations import TimeUnit, format_time_value, hours_per_day, parse_duration_to_days
from ..work_calendar import WorkCalendar, load_calendar
from .leveling import Availability, ResourceScheduler, priority_rules
from .dependencies import DepType, Dependency, TaskId

# Toleranz, unter der ein Gesamtpuffer als 0 (kritisch) gilt
CRITICAL_EPS = 0.001

# Präfix, an dem ältere Projektdateien Kalender-Blocker erkennen
_LEGACY_BLOCKER_PREFIX = 'WE-'


class CPMTaskResult(BaseModel):
    """
    CPM-Ergebnis für einen Task (alle Zeiten in Arbeitstagen seit Projektstart).

    faz/fez = frühester Anfang/Ende, saz/sez = spätester Anfang/Ende,
    puffer = Gesamtpuffer (GP), free_puffer = freier Puffer (FP).
    """
    id: TaskId
    name: str
    duration: float
    faz: float = 0.0
    fez: float = 0.0
    saz: float = 0.0
    sez: float = 0.0
    puffer: float = 0.0
    free_puffer: float = 0.0
    is_critical: bool = False
    is_break: bool = False      # Ruhepause
    is_blocker: bool = False    # Kalender-Blocker (Wochenende/Feiertag)
    successor_deps: List[Dependency] = Field(default_factory=list)
    predecessor_deps: List[Dependency] = Field(default_factory=list)
    # Termine (in Arbeitstagen) und Ergebnis der Ressourcenplanung
    not_before: Optional[float] = None
    deadline: Optional[float] = None
    leveling_delay: float = 0.0                      # Verschiebung durch Ressourcen/Urlaub/Teilzeit
    resource_predecessors: List[TaskId] = Field(default_factory=list)  # auf deren Ressource gewartet wurde

    @property
    def span(self) -> float:
        """Belegte Zeit (FEZ − FAZ); größer als duration, wenn Urlaub/Teilzeit den Task streckt."""
        span = self.fez - self.faz
        return self.duration if abs(span - self.duration) < 1e-9 else span

    @property
    def deadline_missed(self) -> bool:
        return self.deadline is not None and self.fez > self.deadline + CRITICAL_EPS

    @property
    def is_system(self) -> bool:
        """Pausen und Blocker – keine echte Arbeit, in Task-Listen meist ausgeblendet."""
        return self.is_break or self.is_blocker

    @property
    def successors(self) -> List[TaskId]:
        """Alle Nachfolger-IDs (alle Abhängigkeitstypen, ohne Duplikate)."""
        return list(dict.fromkeys(d.target for d in self.successor_deps))

    @property
    def predecessors(self) -> List[TaskId]:
        """Alle Vorgänger-IDs (alle Abhängigkeitstypen, ohne Duplikate)."""
        return list(dict.fromkeys(d.target for d in self.predecessor_deps))

    def successors_of(self, dep_type: DepType) -> List[TaskId]:
        return [d.target for d in self.successor_deps if d.type == dep_type]

    def predecessors_of(self, dep_type: DepType) -> List[TaskId]:
        return [d.target for d in self.predecessor_deps if d.type == dep_type]

    @property
    def successors_ea(self) -> List[TaskId]:
        return self.successors_of(DepType.EA)

    @property
    def successors_aa(self) -> List[TaskId]:
        return self.successors_of(DepType.AA)

    @property
    def successors_ee(self) -> List[TaskId]:
        return self.successors_of(DepType.EE)

    @property
    def successors_ae(self) -> List[TaskId]:
        return self.successors_of(DepType.AE)


class CPMResult(BaseModel):
    """
    Gesamtergebnis der CPM-Berechnung.

    Attributes:
        project_name:     Name des Projekts
        project_duration: Projektdauer (formatiert)
        critical_path:    Task-IDs auf dem kritischen Pfad (nach FAZ sortiert)
        tasks:            CPM-Ergebnis je Task
        time_unit:        dominante Zeiteinheit der Eingabe
        project_start:    Projektstart
        calculation_date: Zeitpunkt der Berechnung
        holidays:         Feiertage {YYYY-MM-DD: Name} (nur wenn skip_holidays)
        skip_weekends / skip_holidays: Kalender-Einstellungen
    """
    project_name: str
    project_duration: str
    critical_path: List[TaskId]
    tasks: Dict[TaskId, CPMTaskResult]
    time_unit: Literal['minutes', 'hours', 'days'] = 'days'
    project_start: Optional[datetime] = None
    calculation_date: Optional[datetime] = None
    holidays: Optional[Dict[str, str]] = None
    skip_weekends: bool = True
    skip_holidays: bool = False

    @cached_property
    def calendar(self) -> WorkCalendar:
        """Arbeitskalender dieses Ergebnisses (Wochenenden/Feiertage)."""
        holidays = frozenset(self.holidays or {}) if self.skip_holidays else frozenset()
        return WorkCalendar(skip_weekends=self.skip_weekends, holidays=holidays)

    def date_at(self, workdays: float) -> datetime:
        """Kalenderdatum nach workdays Arbeitstagen ab Projektstart."""
        if self.project_start is None:
            raise ValueError("Projekt hat kein Startdatum")
        return self.calendar.add_workdays(self.project_start, workdays)

    @property
    def project_end_days(self) -> float:
        """Projektdauer in Arbeitstagen (max. FEZ)."""
        return max((t.fez for t in self.tasks.values()), default=0.0)

    @property
    def deadline_violations(self) -> List[CPMTaskResult]:
        """Tasks, die ihre Deadline nicht halten (Verspätung = fez − deadline)."""
        return [t for t in self.tasks.values() if t.deadline_missed]

    def is_blocker(self, task_id: TaskId) -> bool:
        task = self.tasks.get(task_id)
        return task is not None and task.is_blocker

    # ------------------------------------------------------------------
    # Export-Hilfen
    # ------------------------------------------------------------------

    def _format_point(self, days: float) -> str:
        """Zeitpunkt als Dauer (unter 24 h) oder Datum/Uhrzeit."""
        if math.isinf(days):
            return "inf"
        if self.project_start is None:
            return format_time_value(days, self.time_unit)
        if self.time_unit != 'days':
            hours = days * hours_per_day()
            if hours < 24:
                return f"{hours:.2f}h"
            return self.date_at(days).strftime('%Y-%m-%d %H:%M')
        return self.date_at(days).strftime('%Y-%m-%d')

    def export_to_dict(self, include_dates: bool = True) -> dict:
        """Ergebnis als Dictionary (für JSON-Export)."""
        output: dict = {
            'project': self.project_name,
            'project_duration': self.project_duration,
            'critical_path': self.critical_path,
            'tasks': [],
            'settings': {
                'skip_weekends': self.skip_weekends,
                'skip_holidays': self.skip_holidays,
            },
        }
        if self.calculation_date:
            output['calculation_date'] = self.calculation_date.strftime('%Y-%m-%d %H:%M:%S')
        if self.project_start:
            output['project_start'] = self.project_start.strftime('%Y-%m-%d')
        if self.skip_holidays and self.holidays:
            output['holidays'] = sorted(self.holidays)

        fmt = lambda v: format_time_value(v, self.time_unit)  # noqa: E731
        for task_id, task in self.tasks.items():
            cpm = {
                'D': fmt(task.duration),
                'FB': self._format_point(task.faz),
                'FE': self._format_point(task.fez),
                'SB': self._format_point(task.saz),
                'SE': self._format_point(task.sez),
                'GP': fmt(task.puffer),
                'FP': fmt(task.free_puffer),
                'is_critical': task.is_critical,
            }
            if include_dates and self.project_start:
                faz_date, fez_date = self.date_at(task.faz), self.date_at(task.fez)
                dates: dict = {
                    'fb_date': faz_date.strftime('%Y-%m-%d'),
                    'fe_date': fez_date.strftime('%Y-%m-%d'),
                    'sb_date': self.date_at(task.saz).strftime('%Y-%m-%d'),
                    'se_date': self.date_at(task.sez).strftime('%Y-%m-%d'),
                }
                weekend_days = self.calendar.count_weekend_days(faz_date, fez_date)
                if weekend_days:
                    dates['num_weekend_days'] = weekend_days
                holidays = self.calendar.count_holidays(faz_date, fez_date)
                if holidays:
                    dates['num_holidays'] = holidays
                cpm['dates'] = dates
            output['tasks'].append({
                'id': task_id, 'name': task.name, 'duration': fmt(task.duration), 'cpm': cpm,
            })
        return output

    def to_network_csv(self) -> str:
        """Netzplan-Daten als CSV (ohne Kalender-Blocker)."""
        lines = ["TaskID,Task Name,Duration,FAZ,FEZ,SAZ,SEZ,GP,FP,Successors,IsCritical"]
        for task_id, task in sorted(self.tasks.items(), key=lambda x: x[1].faz):
            if task.is_blocker:
                continue
            successors = ";".join(str(s) for s in task.successors if not self.is_blocker(s))
            is_critical = "JA" if task.is_critical else "NEIN"
            lines.append(
                f'"{task_id}","{task.name}",{task.duration:.1f},{task.faz:.1f},{task.fez:.1f},'
                f'{task.saz:.1f},{task.sez:.1f},{task.puffer:.1f},{task.free_puffer:.1f},'
                f'"{successors}",{is_critical}'
            )
        return "\n".join(lines)


# =============================================================================
# Berechnung
# =============================================================================

Times = CPMTaskResult

# Frühester Anfang des Nachfolgers s, den ein Vorgänger p erzwingt (Vorwärtsrechnung).
# EE wird gesondert behandelt, weil es am Ende ansetzt (siehe _forward_pass).
_FORWARD: Dict[DepType, Callable[[Times, Times], float]] = {
    DepType.EA: lambda p, s: p.fez,
    DepType.AA: lambda p, s: p.faz,
    DepType.AE: lambda p, s: p.faz - s.duration,
}

# Spätestes Ende des Vorgängers p, das ein Nachfolger s erzwingt (Rückwärtsrechnung).
_BACKWARD: Dict[DepType, Callable[[Times, Times], float]] = {
    DepType.EA: lambda p, s: s.saz,
    DepType.AA: lambda p, s: s.saz + p.span,
    DepType.EE: lambda p, s: s.sez,
    DepType.AE: lambda p, s: s.sez + p.span,
}


class CPMCalculator:
    """
    Berechnet den Netzplan eines (bereits expandierten) Projekts.

    Phasen: Graph aufbauen → Zyklen prüfen/topologisch sortieren → Vorwärts-
    und Rückwärtsrechnung → Ressourcenplanung (Kapazität, Urlaub, Teilzeit;
    siehe leveling.py) → Rückwärtsrechnung mit Ressourcen-Abhängigkeiten → Puffer.
    """

    def __init__(self, project, start_date: Optional[datetime] = None,
                 cfg_dir: Optional[Path] = None,
                 calendar: Optional[WorkCalendar] = None,
                 holidays: Optional[Dict[str, str]] = None):
        """
        Args:
            project:    Projekt (Pydantic-Modell)
            start_date: Projektstart; Default: project_start oder jetzt
            cfg_dir:    Konfigurationsverzeichnis, aus dem der Kalender geladen wird
            calendar, holidays: Kalender direkt vorgeben (überspringt das Laden)
        """
        from .project import parse_start_date

        self.project = project
        explicit_start = start_date or parse_start_date(project.project_start)
        self.time_unit: TimeUnit = project.get_time_unit()

        if calendar is None:
            year = (explicit_start or datetime.now()).year
            calendar, holidays = load_calendar(cfg_dir, year=year)
        elif holidays is None and calendar.holidays:
            holidays = {d: '' for d in calendar.holidays}
        self.calendar = calendar
        # Ohne Startdatum: heute bzw. nächster Arbeitstag zum Arbeitsbeginn (nicht "jetzt")
        self.start_date = explicit_start or calendar.next_work_start(datetime.now())
        # None = Feiertage deaktiviert, {} = aktiviert, aber keine gefunden
        self.holidays = holidays

        self.cpm_tasks: Dict[TaskId, CPMTaskResult] = {}

    def calculate(self) -> CPMResult:
        """
        Führt die vollständige CPM-Berechnung durch.

        Raises:
            ValueError: bei Selbstreferenz oder zyklischer Abhängigkeit
        """
        self._initialize_cpm_data()
        order = self._topological_order()
        self._forward_pass(order)
        self._backward_pass(order)
        self._resource_leveling(order)
        self._calculate_slack()

        project_duration = max((t.fez for t in self.cpm_tasks.values()), default=0.0)
        return CPMResult(
            project_name=self.project.project,
            project_duration=format_time_value(project_duration, self.time_unit),
            critical_path=self._get_critical_path(),
            tasks=self.cpm_tasks,
            time_unit=self.time_unit,
            project_start=self.start_date,
            calculation_date=datetime.now(),
            holidays=self.holidays,
            skip_weekends=self.calendar.skip_weekends,
            skip_holidays=self.holidays is not None,
        )

    def _initialize_cpm_data(self) -> None:
        """Legt je Task ein Ergebnis an und leitet die Vorgänger aus den Nachfolgern ab."""
        for task in self.project.tasks:
            is_blocker = getattr(task, 'is_blocker', False) or (
                isinstance(task.id, str) and task.id.startswith(_LEGACY_BLOCKER_PREFIX))
            self.cpm_tasks[task.id] = CPMTaskResult(
                id=task.id,
                name=task.name,
                duration=parse_duration_to_days(task.duration) if task.duration else 0.0,
                successor_deps=task.dependencies,
                is_break=getattr(task, 'is_break', False),
                is_blocker=is_blocker,
                not_before=self._offset(task.not_before),
                deadline=self._offset(task.deadline, end_of_day=True),
            )

        for task_id, task in self.cpm_tasks.items():
            for dep in task.successor_deps:
                if dep.target in self.cpm_tasks:
                    self.cpm_tasks[dep.target].predecessor_deps.append(Dependency(task_id, dep.type))

    def _offset(self, value: Optional[str], end_of_day: bool = False) -> Optional[float]:
        """Datum/Uhrzeit → Arbeitstage ab Projektstart."""
        from .project import parse_start_date
        moment = parse_start_date(value)
        if moment is None:
            return None
        return self.calendar.workday_offset(self.start_date, moment, hours_per_day(), end_of_day)

    def _earliest_start(self, task: CPMTaskResult) -> float:
        """Frühester Start aus Abhängigkeiten (EA/AA/AE) und not_before."""
        preds = [(self.cpm_tasks[d.target], d.type) for d in task.predecessor_deps]
        return max([0.0, task.not_before or 0.0] + [_FORWARD[t](p, task) for p, t in preds if t in _FORWARD])

    def _topological_order(self) -> List[TaskId]:
        """Topologische Reihenfolge; ValueError bei Selbstreferenz oder Zyklus."""
        graph: Dict[TaskId, List[TaskId]] = {}
        for task_id, task in self.cpm_tasks.items():
            if task_id in task.successors:
                raise ValueError(
                    f"Fehler in Eingabedaten: Task {task_id} ('{task.name}') "
                    f"referenziert sich selbst als Abhängigkeit (Selbstreferenz)."
                )
            graph[task_id] = [p for p in task.predecessors if p in self.cpm_tasks]

        try:
            return list(TopologicalSorter(graph).static_order())
        except CycleError as e:
            cycle = e.args[1]
            cycle_str = " -> ".join(f"{tid} ('{self.cpm_tasks[tid].name}')" for tid in cycle)
            raise ValueError(
                f"Fehler in Eingabedaten: Zyklische Abhängigkeit gefunden:\n  {cycle_str}"
            ) from None

    def _forward_pass(self, order: List[TaskId]) -> None:
        """Vorwärtsrechnung: FAZ/FEZ in reinen Arbeitstagen."""
        for task_id in order:
            task = self.cpm_tasks[task_id]
            preds = [(self.cpm_tasks[d.target], d.type) for d in task.predecessor_deps]

            task.faz = self._earliest_start(task)
            task.fez = task.faz + task.duration

            # EE: Nachfolger darf nicht vor dem Vorgänger enden → ggf. nach hinten schieben
            for pred, dep_type in preds:
                if dep_type == DepType.EE and task.fez < pred.fez:
                    task.faz = pred.fez - task.duration
                    task.fez = pred.fez

    def _backward_pass(self, order: List[TaskId],
                       resource_successors: Optional[Dict[TaskId, List[TaskId]]] = None) -> None:
        """
        Rückwärtsrechnung: SAZ/SEZ. Endknoten (ohne Nachfolger) erhalten SEZ = Projektende,
        eine Deadline begrenzt SEZ zusätzlich. Ressourcen-Abhängigkeiten wirken wie EA.
        """
        project_end = max((t.fez for t in self.cpm_tasks.values()), default=0.0)
        resource_successors = resource_successors or {}
        for task_id in reversed(order):
            task = self.cpm_tasks[task_id]
            constraints = [
                _BACKWARD[d.type](task, self.cpm_tasks[d.target])
                for d in task.successor_deps if d.target in self.cpm_tasks
            ] + [self.cpm_tasks[s].saz for s in resource_successors.get(task_id, [])]
            task.sez = min(constraints) if constraints else project_end
            if task.deadline is not None:
                task.sez = min(task.sez, task.deadline)
            task.saz = task.sez - task.span

    def _calculate_slack(self) -> None:
        """Gesamt-/freier Puffer; Pausen und Blocker sind fix (GP = 0, kritisch)."""
        for task in self.cpm_tasks.values():
            if task.is_system:
                task.saz, task.sez = task.faz, task.fez
                task.puffer = task.free_puffer = 0.0
                task.is_critical = True
                continue

            task.puffer = task.saz - task.faz
            successor_starts = [self.cpm_tasks[s].faz for s in task.successors if s in self.cpm_tasks]
            if successor_starts:
                task.free_puffer = min(successor_starts) - task.fez
            elif task.successors:
                task.free_puffer = math.inf
            else:
                task.free_puffer = task.puffer
            task.is_critical = task.puffer < CRITICAL_EPS      # negativ = Deadline verfehlt

    def _resource_leveling(self, order: List[TaskId]) -> None:
        """
        Plant mit Ressourcen-Kapazitäten, Urlaub und Teilzeit (leveling.py) und rechnet
        danach rückwärts mit den entstandenen Ressourcen-Abhängigkeiten.
        """
        availability = Availability(self.calendar, self.start_date, self.project)
        if not ResourceScheduler(self.project, self.cpm_tasks, availability, self._earliest_start).needed():
            return

        # Jede Prioritätsregel auf denselben Ausgangswerten rechnen, den kürzesten Plan behalten
        initial = {tid: (t.faz, t.fez) for tid, t in self.cpm_tasks.items()}
        best = None
        for priority in priority_rules(self.cpm_tasks).values():
            for tid, (faz, fez) in initial.items():
                self.cpm_tasks[tid].faz, self.cpm_tasks[tid].fez = faz, fez
            links = ResourceScheduler(self.project, self.cpm_tasks, availability,
                                      self._earliest_start).schedule(priority)
            makespan = max((t.fez for t in self.cpm_tasks.values()), default=0.0)
            if best is None or makespan < best[0] - 1e-9:
                plan = {tid: (t.faz, t.fez, t.leveling_delay) for tid, t in self.cpm_tasks.items()}
                best = (makespan, plan, links)
        assert best is not None
        _, plan, waits_for = best
        for tid, (faz, fez, delay) in plan.items():
            task = self.cpm_tasks[tid]
            task.faz, task.fez, task.leveling_delay = faz, fez, delay

        resource_successors: Dict[TaskId, List[TaskId]] = {}
        for task_id, blockers in waits_for.items():
            self.cpm_tasks[task_id].resource_predecessors = blockers
            for blocker in blockers:
                resource_successors.setdefault(blocker, []).append(task_id)
        self._backward_pass(order, resource_successors)

    def _get_critical_path(self) -> List[TaskId]:
        """Kritische Task-IDs, chronologisch nach FAZ."""
        critical = [tid for tid, t in self.cpm_tasks.items() if t.is_critical]
        return sorted(critical, key=lambda tid: self.cpm_tasks[tid].faz)
