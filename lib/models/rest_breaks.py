"""
Rest Break Management for Person Resources
===========================================

Verwaltet Ruhepausen für Personen basierend auf Arbeitszeit-Regeln.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from ..durations import parse_duration_to_minutes
from .resources import Person, RestInterval
from .tasks import SimpleTask

if TYPE_CHECKING:
    from .project import Project


def resolve_rest_intervals(person: Person, project_resting_times: Optional[List[RestInterval]] = None) -> List[RestInterval]:
    """
    Löst rest_intervals Verweise auf und gibt die tatsächlichen RestInterval-Objekte zurück.

    Args:
        person: Person mit rest_intervals (kann Verweis oder direkte Liste sein)
        project_resting_times: Globale resting_times aus dem Projekt

    Returns:
        Liste von RestInterval-Objekten
    """
    if not person.rest_intervals:
        return []

    # Fall 1: Direkter Verweis auf project resting_times
    if isinstance(person.rest_intervals, str):
        if person.rest_intervals == "resting_times" and project_resting_times:
            return project_resting_times
        # Unbekannter Verweis
        return []

    # Fall 2: Direkte Liste von RestInterval
    return person.rest_intervals



class PersonWorkTracker:
    """
    Verfolgt Arbeitszeiten und Pausen für eine Person.
    """

    def __init__(self, person_id: str, rest_intervals: List[RestInterval]):
        self.person_id = person_id
        self.rest_intervals = sorted(rest_intervals, key=lambda x: x.after_hours)
        self.worked_hours = 0.0
        self.taken_breaks: List[float] = []  # Schwellenwerte der genommenen Pausen
        self.last_break_at = 0.0  # Arbeitszeit bei letzter Pause

    def add_work_time(self, hours: float) -> Optional[RestInterval]:
        """
        Fügt Arbeitszeit hinzu und prüft ob eine Pause erforderlich ist.

        Args:
            hours: Hinzuzufügende Arbeitsstunden

        Returns:
            RestInterval falls Pause erforderlich, sonst None
        """
        self.worked_hours += hours

        # Prüfe alle Pausenregeln
        for interval in self.rest_intervals:
            threshold = interval.after_hours
            if threshold in self.taken_breaks:
                continue  # Diese Pause wurde bereits genommen

            if self.worked_hours >= threshold:
                # Pause ist erforderlich
                return interval

        return None

    def take_break(self, interval: RestInterval):
        """
        Markiert eine Pause als genommen.

        Args:
            interval: Die genommene Pause
        """
        if interval.after_hours not in self.taken_breaks:
            self.taken_breaks.append(interval.after_hours)
            self.last_break_at = self.worked_hours



def insert_rest_breaks(tasks: List[SimpleTask], project: "Project") -> List[SimpleTask]:
    """
    Fügt nach Tasks Pausen-Tasks ein, sobald eine Person die Arbeitszeit-Schwelle
    einer Ruhepausen-Regel erreicht.

    Die Pause wird als Nachfolger des auslösenden Tasks eingehängt.
    """
    persons = {p.id: p for p in (project.persons or [])}
    trackers: Dict[str, PersonWorkTracker] = {}
    for person in persons.values():
        intervals = resolve_rest_intervals(person, project.resting_times)
        if intervals:
            trackers[person.id] = PersonWorkTracker(person.id, intervals)
    if not trackers:
        return tasks

    res_to_person = {r.id: r.person_id for r in (project.resources or []) if r.person_id}

    result: List[SimpleTask] = []
    for task in tasks:
        result.append(task)
        if not task.resources or task.is_break:
            continue

        task_hours = parse_duration_to_minutes(task.duration or 0) / 60.0
        working = dict.fromkeys(
            res_to_person[r] for r in task.resources
            if res_to_person.get(r) in trackers
        )
        required = {}
        for person_id in working:
            rest_interval = trackers[person_id].add_work_time(task_hours)
            if rest_interval:
                required[person_id] = rest_interval

        for person_id, rest_interval in required.items():
            person = persons[person_id]
            break_id = f"{task.id}-BRK-{person_id.replace('PERS', 'P')}"
            result.append(SimpleTask(
                id=break_id,
                name=f"Pause: {person.name} ({rest_interval.note or rest_interval.duration})",
                duration=rest_interval.duration,
                cost=0.0,
                is_break=True,
            ))
            task.successors.append(break_id)
            trackers[person_id].take_break(rest_interval)

    return result
