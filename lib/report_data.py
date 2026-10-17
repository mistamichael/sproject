"""
Report data
===========

Aufbereitung von Projekt- und CPM-Daten, die mehrere Exporte gemeinsam nutzen
(Personen mit Abwesenheiten, Ressourcen-Zuordnung, Feldformatierung).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .durations import TimeUnit, format_time_value


def format_task_field(field: str, task, time_unit: TimeUnit, task_id=None) -> str:
    """
    Formatiert ein CPM-Task-Feld für Diagramme und Tabellen.

    Args:
        field:     id, name, duration/d/dauer, faz, fez, saz, sez, gp, fp
        task:      CPMTaskResult
        time_unit: Zeiteinheit für Zeitwerte
        task_id:   überschreibt task.id für das Feld 'id'

    Returns:
        Formatierter String oder '' für unbekannte Felder
    """
    f = field.lower()
    if f == 'id':
        return f"[{task_id if task_id is not None else task.id}]"
    if f == 'name':
        return task.name
    time_fields = {
        'd': ('D', 'duration'), 'duration': ('D', 'duration'), 'dauer': ('D', 'duration'),
        'faz': ('FAZ', 'faz'), 'fez': ('FEZ', 'fez'), 'saz': ('SAZ', 'saz'), 'sez': ('SEZ', 'sez'),
        'gp': ('GP', 'puffer'), 'fp': ('FP', 'free_puffer'),
    }
    if f in time_fields:
        label, attr = time_fields[f]
        return f"{label}:{format_time_value(getattr(task, attr), time_unit)}"
    return ''


# =============================================================================
# Personen
# =============================================================================

@dataclass
class PersonEntry:
    """Aufbereitete Personen-Daten für den Export."""
    name:            str
    hourly_rate:     Optional[float]
    absences:        List[str]   # Abwesenheiten im Projektzeitraum [proj_start, proj_end]
    absences_buffer: List[str]   # Abwesenheiten im Verzögerungspuffer (proj_end, proj_end_buffer]


def _collect_absences_in_window(
    person: Any,
    holidays: Optional[Dict[str, str]],
    win_start: Optional[datetime],
    win_end: Optional[datetime],
    exclusive_start: bool = False,
) -> List[str]:
    """Abwesenheits-Labels (Urlaub + Feiertage) einer Person im Zeitfenster."""
    absences: List[str] = []

    def _in_window(d: datetime) -> bool:
        if win_start is not None and not ((d > win_start) if exclusive_start else (d >= win_start)):
            return False
        return win_end is None or d <= win_end

    def _label(text: str, description: Optional[str]) -> str:
        return f"{text} ({description})" if description else text

    for vac in (person.vacation or []):
        try:
            if vac.date:
                if _in_window(datetime.strptime(vac.date, '%Y-%m-%d')):
                    absences.append(_label(vac.date, vac.description))
            elif vac.from_ and vac.to:
                d_from = datetime.strptime(vac.from_, '%Y-%m-%d')
                d_to = datetime.strptime(vac.to, '%Y-%m-%d')
                if (win_start is None or d_to >= win_start) and (win_end is None or d_from <= win_end):
                    absences.append(_label(f"{vac.from_} – {vac.to}", vac.description))
        except ValueError:
            pass

    if holidays and win_start and win_end:
        for h_date in sorted(holidays):
            try:
                if _in_window(datetime.strptime(h_date, '%Y-%m-%d')):
                    absences.append(f"{h_date} ({holidays[h_date]})")
            except ValueError:
                pass

    return absences


def collect_person_entries(persons: List[Any], result: Any) -> List[PersonEntry]:
    """
    Personen mit Stundensatz und Abwesenheiten für den Export.

    Zwei Zeitfenster:
    - absences:        [proj_start, proj_end]         — exakter Projektzeitraum
    - absences_buffer: (proj_end, proj_end_buffer]    — Verzögerungsrisiko

    Puffergröße: min(N_personen × 3, 30) Arbeitstage.
    """
    proj_start = result.project_start
    proj_end = proj_end_buffer = None
    if proj_start and result.tasks:
        proj_end = result.date_at(max(t.fez for t in result.tasks.values()))
        proj_end_buffer = result.calendar.add_workdays(proj_end, min(len(persons) * 3, 30))

    entries: List[PersonEntry] = []
    for person in persons:
        absences_buffer = _collect_absences_in_window(
            person, result.holidays, proj_end, proj_end_buffer, exclusive_start=True
        ) if proj_end else []
        entries.append(PersonEntry(
            name=person.name,
            hourly_rate=person.hourly_rate,
            absences=_collect_absences_in_window(person, result.holidays, proj_start, proj_end),
            absences_buffer=absences_buffer,
        ))
    return entries


# =============================================================================
# Ressourcen
# =============================================================================

@dataclass
class ResourceDetailEntry:
    """Ressourcen-Detail-Zeile für den Export (Ressource ↔ Person ↔ Typ)."""
    resource_id:   str
    resource_name: str
    person_name:   str   # Leer wenn keine Person verknüpft
    resource_type: str


def collect_resource_details(resources: List[Any], persons: List[Any]) -> List[ResourceDetailEntry]:
    """Flache Liste (Ressource, Person, Typ), sortiert nach Ressourcen-ID."""
    person_lookup = {p.id: p.name for p in persons}
    return [
        ResourceDetailEntry(
            resource_id=res.id,
            resource_name=res.name or res.id,
            person_name=person_lookup.get(res.person_id, res.person_id) if res.person_id else '',
            resource_type=res.type,
        )
        for res in sorted(resources, key=lambda r: r.id)
    ]


@dataclass
class ResourceData:
    """Gesammelte Ressourcen-Daten aus einem Projekt."""
    resource_usage:  Dict[str, List[str]]  # res_id → [task_id strings]
    resource_names:  Dict[str, str]        # res_id → Anzeigename
    resources:       List[Any]
    persons:         List[Any]


def collect_resource_data(project: Any) -> Optional[ResourceData]:
    """Ressourcen-Nutzung je Task; None wenn kein Task Ressourcen hat."""
    if not project:
        return None

    resource_usage: Dict[str, List[str]] = {}
    for task in project.tasks:
        for res_id in (task.resources or []):
            resource_usage.setdefault(res_id, []).append(str(task.id))
    if not resource_usage:
        return None

    resources = list(project.resources or [])
    return ResourceData(
        resource_usage=resource_usage,
        resource_names={res.id: res.name or res.id for res in resources},
        resources=resources,
        persons=list(project.persons or []),
    )


# =============================================================================
# Termine
# =============================================================================

@dataclass
class DeadlineViolation:
    task_id:  str
    name:     str
    deadline: str    # formatiertes Datum
    end:      str    # geplantes Ende
    late:     str    # Verspätung in Projekteinheit


def collect_deadline_violations(result: Any) -> List[DeadlineViolation]:
    """Tasks, die ihre Deadline verfehlen – für Warnungen in allen Exporten."""
    from .time_axis import point_in_time

    fmt = '%Y-%m-%d %H:%M' if result.time_unit != 'days' else '%Y-%m-%d'

    def moment(workdays: float) -> str:
        if result.project_start is None:
            return format_time_value(workdays, result.time_unit)
        return point_in_time(result, workdays, is_end=True).strftime(fmt)   # Ende des Arbeitstags

    return [
        DeadlineViolation(task_id=str(task.id), name=task.name, deadline=moment(task.deadline),
                          end=moment(task.fez), late=format_time_value(task.fez - task.deadline, result.time_unit))
        for task in result.deadline_violations
    ]


def deadline_warning_lines(result: Any) -> List[str]:
    """'Task 5 (Abnahme): Deadline 2026-05-01, geplantes Ende 2026-05-06 (+3.0d)'."""
    return [f"Task {v.task_id} ({v.name}): Deadline {v.deadline}, geplantes Ende {v.end} (+{v.late})"
            for v in collect_deadline_violations(result)]


# =============================================================================
# Plan gegen Ist
# =============================================================================

def tracking_summary(result: Any) -> List[Tuple[str, str]]:
    """(Label, Wert) für Stichtag, Baseline-Ende, Prognose-Ende und Verzug – leer ohne Tracking."""
    from .time_axis import point_in_time

    if result.project_start is None or (result.status_date is None and result.baseline_end is None):
        return []
    fmt = '%Y-%m-%d %H:%M' if result.time_unit != 'days' else '%Y-%m-%d'
    rows: List[Tuple[str, str]] = []
    if result.status_date is not None:
        rows.append(("Stichtag", point_in_time(result, result.status_date, is_end=True).strftime(fmt)))
        done = sum(1 for t in result.tasks.values() if t.status == 'done')
        running = sum(1 for t in result.tasks.values() if t.status == 'in_progress')
        rows.append(("Erledigt / laufend", f"{done} / {running}"))
    rows.append(("Prognose-Ende", point_in_time(result, result.project_end_days, is_end=True).strftime(fmt)))
    if result.baseline_end is not None:
        rows.append(("Baseline-Ende", point_in_time(result, result.baseline_end, is_end=True).strftime(fmt)))
        slip = result.slip
        rows.append(("Verzug", ("+" if slip > 1e-9 else "") + format_time_value(slip, result.time_unit)))
    return rows
