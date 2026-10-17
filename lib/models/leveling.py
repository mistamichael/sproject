"""
Resource leveling
=================

Plant Tasks unter Berücksichtigung von Ressourcen ein (serielles
Planungsverfahren / Serial Schedule Generation Scheme):

- Kapazität: Eine Ressource bearbeitet höchstens Resource.slots Tasks
  gleichzeitig (Personen, LKW, Bagger: 1 – siehe Resource.slots).
- Verfügbarkeit: Urlaub (Person.vacation) unterbricht einen Task, Teilzeit
  (Person.workinghours_override) verlangsamt ihn. Ein Task mit mehreren
  Personen schreitet im Tempo der am wenigsten verfügbaren voran.
- Reihenfolge: Schrittweise wird der Task eingeplant, der am frühesten starten
  kann; bei Gleichstand entscheidet eine Prioritätsregel. Mehrere Standardregeln
  (PRIORITY_RULES) werden durchgerechnet, der kürzeste Plan gewinnt.

Wartet ein Task auf eine Ressource, entsteht eine Ressourcen-Abhängigkeit
(Vorgänger, der die Ressource freigibt). Die Rückwärtsrechnung berücksichtigt
sie, damit Puffer und kritischer Pfad zum eingeplanten Ablauf passen.

Alle Zeiten in CPM-Arbeitstagen seit Projektstart.
"""

import math
from datetime import date, datetime
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Tuple

from ..durations import hours_per_day
from ..work_calendar import WorkCalendar
from .dependencies import DepType, TaskId
from .resources import Person

if TYPE_CHECKING:
    from .cpm import CPMTaskResult

_EPS = 1e-9
_MAX_DAYS = 20000          # Abbruch, falls eine Person praktisch nie verfügbar ist
_WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class Availability:
    """Arbeitstempo je Ressource und Arbeitstag: 1 = voll, 0.5 = halbtags, 0 = abwesend."""

    def __init__(self, calendar: WorkCalendar, project_start: datetime, project):
        self.calendar = calendar
        self.start = project_start
        self._dates: List[date] = []
        persons = {p.id: p for p in (project.persons or [])}
        self._person_of: Dict[str, Person] = {
            r.id: persons[r.person_id] for r in (project.resources or [])
            if r.person_id in persons and _has_restrictions(persons[r.person_id])
        }
        self._vacation: Dict[str, Set[date]] = {pid: _vacation_days(p.vacation) for pid, p in persons.items()}
        self._outage: Dict[str, Set[date]] = {
            r.id: _vacation_days(r.unavailable) for r in (project.resources or []) if r.unavailable
        }

    @property
    def has_restrictions(self) -> bool:
        return bool(self._person_of or self._outage)

    def _date(self, day_index: int) -> date:
        while len(self._dates) <= day_index:
            self._dates.append(self.calendar.add_workdays(self.start, len(self._dates)).date())
        return self._dates[day_index]

    def rate(self, resource_id: str, day_index: int) -> float:
        if day_index < 0:
            return 1.0
        outage = self._outage.get(resource_id)
        if outage and self._date(day_index) in outage:
            return 0.0
        person = self._person_of.get(resource_id)
        if person is None:
            return 1.0
        day = self._date(day_index)
        if day in self._vacation[person.id]:
            return 0.0
        override = person.workinghours_override
        if override is None:
            return 1.0
        if _WEEKDAY_KEYS[day.weekday()] not in {d.strip().lower()[:3] for d in override.days}:
            return 0.0
        hours = sum(_hours(r.from_, r.to) for r in override.hours)
        return min(hours / hours_per_day(), 1.0)

    def task_rate(self, resources: List[str], day_index: int) -> float:
        return min((self.rate(r, day_index) for r in resources), default=1.0)

    def first_start(self, resources: List[str], t: float) -> float:
        """Frühester Zeitpunkt ≥ t, an dem alle Personen des Tasks arbeiten."""
        while self.task_rate(resources, math.floor(t + _EPS)) <= 0:
            t = math.floor(t + _EPS) + 1.0
            if t > _MAX_DAYS:
                raise ValueError(f"Ressourcen {resources} sind in den nächsten {_MAX_DAYS} Arbeitstagen nie verfügbar")
        return t

    def finish(self, resources: List[str], start: float, work: float) -> float:
        """Ende eines Tasks mit work Arbeitstagen Aufwand, der bei start beginnt."""
        t, remaining = start, work
        while remaining > _EPS:
            day = math.floor(t + _EPS)
            rate = self.task_rate(resources, day)
            if rate > 0:
                possible = (day + 1 - t) * rate
                if possible >= remaining - _EPS:
                    return t + remaining / rate
                remaining -= possible
            t = day + 1.0
            if t > _MAX_DAYS:
                raise ValueError(f"Ressourcen {resources} sind in den nächsten {_MAX_DAYS} Arbeitstagen nie verfügbar")
        return t


def _has_restrictions(person: Person) -> bool:
    return bool(person.vacation or person.workinghours_override)


def _vacation_days(entries) -> Set[date]:
    from .project import parse_start_date
    days: Set[date] = set()
    for entry in entries or []:
        if entry.date:
            days.add(parse_start_date(entry.date).date())       # type: ignore[union-attr]
        elif entry.from_ and entry.to:
            day = parse_start_date(entry.from_).date()          # type: ignore[union-attr]
            last = parse_start_date(entry.to).date()            # type: ignore[union-attr]
            while day <= last:
                days.add(day)
                day = date.fromordinal(day.toordinal() + 1)
    return days


def _hours(start: str, end: str) -> float:
    h1, m1 = map(int, start.split(":"))
    h2, m2 = map(int, end.split(":"))
    return max((h2 * 60 + m2 - h1 * 60 - m1) / 60, 0.0)


# ---------------------------------------------------------------------------
# Serielles Planungsverfahren
# ---------------------------------------------------------------------------

Interval = Tuple[float, float, TaskId]
Priority = Callable[["CPMTaskResult"], float]


def priority_rules(tasks: Dict[TaskId, "CPMTaskResult"]) -> Dict[str, Priority]:
    """Gängige Prioritätsregeln (kleiner Wert = zuerst)."""
    weight: Dict[TaskId, float] = {}

    def chain_weight(tid: TaskId) -> float:       # Dauer des Tasks + aller Nachfolger
        if tid not in weight:
            succ = {s for s in tasks[tid].successors if s in tasks}
            weight[tid] = tasks[tid].duration + sum(chain_weight(s) for s in succ)
        return weight[tid]

    return {
        "min_latest_start":  lambda t: t.saz,
        "min_latest_finish": lambda t: t.sez,
        "shortest_first":    lambda t: t.duration,
        "max_chain_weight":  lambda t: -chain_weight(t.id),
    }



def _max_overlap(intervals: List[Interval], start: float, end: float) -> int:
    """Größte Zahl gleichzeitig laufender Intervalle innerhalb von [start, end)."""
    events = []
    for s, e, _ in intervals:
        lo, hi = max(s, start), min(e, end)
        if lo < hi - _EPS:
            events += [(lo, 1), (hi, -1)]
    current = best = 0
    for _, delta in sorted(events, key=lambda ev: (ev[0], ev[1])):
        current += delta
        best = max(best, current)
    return best


class ResourceScheduler:
    """
    Plant alle Tasks nach dem seriellen Verfahren ein und gibt die
    Ressourcen-Abhängigkeiten zurück (Task → Tasks, auf deren Ressource er gewartet hat).
    """

    def __init__(self, project, tasks: Dict[TaskId, "CPMTaskResult"], availability: Availability,
                 earliest_start: Callable[["CPMTaskResult"], float], status: Optional[float] = None):
        self.status = status          # Stichtag: laufende Tasks arbeiten ab hier weiter
        self.tasks = tasks
        self.availability = availability
        self.earliest_start = earliest_start
        slots = {r.id: r.slots for r in (project.resources or [])}
        self.resources: Dict[TaskId, List[str]] = {}
        for t in project.tasks:
            if t.id in tasks:
                self.resources[t.id] = list(dict.fromkeys(t.resources or []))
        self.limits = {res: n for res, n in slots.items() if n is not None}
        self.busy: Dict[str, List[Interval]] = {res: [] for res in self.limits}

    def needed(self) -> bool:
        """Leveling nur, wenn sich Tasks eine begrenzte Ressource teilen oder Personen eingeschränkt sind."""
        usage: Dict[str, int] = {}
        for res_list in self.resources.values():
            for res in res_list:
                usage[res] = usage.get(res, 0) + 1
        shared = any(usage.get(res, 0) > n for res, n in self.limits.items())
        return shared or self.availability.has_restrictions

    def schedule(self, priority: Priority) -> Dict[TaskId, List[TaskId]]:
        """
        Plant schrittweise den Task ein, der am frühesten starten kann
        (Gleichstand: priority, dann Reihenfolge im Projekt).
        """
        links: Dict[TaskId, List[TaskId]] = {}
        done: Set[TaskId] = set()
        pending = dict(self.tasks)
        position = {tid: i for i, tid in enumerate(self.tasks)}
        while pending:
            eligible = [t for t in pending.values()
                        if all(p in done for p in t.predecessors if p in self.tasks)]
            slots = {t.id: self._find_slot(t) for t in eligible}
            task = min(eligible, key=lambda t: (round(slots[t.id][0], 9), priority(t), position[t.id]))
            links[task.id] = self._commit(task, *slots[task.id])
            done.add(task.id)
            del pending[task.id]
        return {tid: preds for tid, preds in links.items() if preds}

    def _find_slot(self, task: "CPMTaskResult") -> Tuple[float, float]:
        """Frühester (Start, Ende), an dem Abhängigkeiten, Verfügbarkeit und Kapazität passen."""
        resources = self.resources.get(task.id, [])
        if task.status == 'done' and task.actual_start is not None and task.actual_finish is not None:
            return task.actual_start, task.actual_finish             # Ist-Daten liegen fest
        if task.status == 'in_progress' and task.actual_start is not None:
            resume = self.availability.first_start(resources, max(self.status or 0.0, task.actual_start))
            return task.actual_start, self.availability.finish(resources, resume, task.remaining or 0.0)
        limited = [r for r in resources if r in self.limits]
        min_finish = max([self.tasks[d.target].fez for d in task.predecessor_deps
                          if d.type == DepType.EE], default=0.0)
        t = self.earliest_start(task)
        for _ in range(100000):
            t = self.availability.first_start(resources, t)
            end = self.availability.finish(resources, t, task.duration)
            if end < min_finish - _EPS:                     # EE: nicht vor dem Vorgänger enden
                t += min_finish - end
                continue
            window_end = max(end, t + _EPS)
            blockers = [iv for r in limited
                        if _max_overlap(self.busy[r], t, window_end) >= self.limits[r]
                        for iv in self.busy[r] if iv[0] < window_end - _EPS and iv[1] > t + _EPS]
            if not blockers:
                return t, end
            t = min(iv[1] for iv in blockers)
        raise ValueError(f"Task {task.id} konnte nicht eingeplant werden")

    def _commit(self, task: "CPMTaskResult", start: float, end: float) -> List[TaskId]:
        """Belegt die Ressourcen; gibt die Tasks zurück, auf deren Ressource gewartet wurde."""
        limited = [r for r in self.resources.get(task.id, []) if r in self.limits]
        task.leveling_delay = max(start - task.faz, 0.0)
        waited = task.leveling_delay > _EPS and start > self.earliest_start(task) + _EPS
        task.faz, task.fez = start, end
        blockers = [iv[2] for r in limited for iv in self.busy[r] if abs(iv[1] - start) < 1e-6] if waited else []
        for r in limited:
            self.busy[r].append((start, end, task.id))
        return list(dict.fromkeys(blockers))
