"""
Rest Break Management for Person Resources
===========================================

Verwaltet Ruhepausen für Personen basierend auf Arbeitszeit-Regeln.
"""

import math
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from ..durations import parse_duration_to_minutes
from .resources import Person, RestInterval
from .dependencies import TaskId
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
    Arbeitsstunden einer Person an einem Arbeitstag und die bereits genommenen Pausen.

    Ruhepausen-Regeln gelten je Arbeitstag: reset() beim Tageswechsel.
    """

    def __init__(self, person_id: str, rest_intervals: List[RestInterval]):
        self.person_id = person_id
        self.rest_intervals = sorted(rest_intervals, key=lambda x: x.after_hours)
        self.reset()

    def reset(self) -> None:
        self.worked_hours = 0.0
        self.taken: Set[float] = set()   # Schwellenwerte der heute genommenen Pausen

    def add_work_time(self, hours: float) -> List[RestInterval]:
        """Bucht Arbeitszeit und gibt alle dadurch fälligen Pausen zurück (als genommen markiert)."""
        self.worked_hours += hours
        due = [i for i in self.rest_intervals
               if i.after_hours not in self.taken and self.worked_hours >= i.after_hours]
        self.taken.update(i.after_hours for i in due)
        return due


def insert_rest_breaks(tasks: List[SimpleTask], project: "Project",
                       start_days: Optional[Dict[TaskId, float]] = None) -> List[SimpleTask]:
    """
    Fügt Pausen-Tasks ein, sobald eine Person an einem Arbeitstag die Stunden-Schwelle
    einer Ruhepausen-Regel erreicht.

    Args:
        tasks:      expandierte Tasks (ohne Pausen)
        project:    Projekt mit persons, resources und resting_times
        start_days: Task-ID → frühester Start in Arbeitstagen (FAZ aus einer CPM-Rechnung).
                    Bestimmt Reihenfolge und Arbeitstag der Buchung. Ohne Angabe gilt die
                    Listenreihenfolge und alles zählt als ein Arbeitstag.

    Die Pause wird als Nachfolger des auslösenden Tasks eingehängt (Seitenzweig, verschiebt
    keine anderen Tasks). Ein Task bucht seine Stunden auf seinen Starttag.
    """
    persons = {p.id: p for p in (project.persons or [])}
    trackers: Dict[str, PersonWorkTracker] = {}
    for person in persons.values():
        intervals = resolve_rest_intervals(person, project.resting_times)
        if intervals:
            trackers[person.id] = PersonWorkTracker(person.id, intervals)
    if not trackers:
        return tasks

    tasks = [t.model_copy(deep=True) for t in tasks]   # Eingabe-Projekt nicht verändern
    res_to_person = {r.id: r.person_id for r in (project.resources or []) if r.person_id}
    days = start_days or {}
    order = sorted(range(len(tasks)), key=lambda i: (days.get(tasks[i].id, 0.0), i))

    breaks_after: Dict[int, List[SimpleTask]] = {}
    current_day: Dict[str, int] = {}
    for idx in order:
        task = tasks[idx]
        if not task.resources or task.is_break:
            continue
        day = int(math.floor(days.get(task.id, 0.0) + 1e-9))
        task_hours = parse_duration_to_minutes(task.duration or 0) / 60.0
        working = dict.fromkeys(res_to_person[r] for r in task.resources if res_to_person.get(r) in trackers)
        for person_id in working:
            tracker = trackers[person_id]
            if current_day.get(person_id) != day:
                tracker.reset()
                current_day[person_id] = day
            for n, interval in enumerate(tracker.add_work_time(task_hours), start=1):
                suffix = "" if n == 1 else f"-{n}"
                break_id = f"{task.id}-BRK-{person_id.replace('PERS', 'P')}{suffix}"
                task.successors.append(break_id)
                breaks_after.setdefault(idx, []).append(SimpleTask(
                    id=break_id,
                    name=f"Pause: {persons[person_id].name} ({interval.note or interval.duration})",
                    duration=interval.duration,
                    cost=0.0,
                    is_break=True,
                ))

    result: List[SimpleTask] = []
    for idx, task in enumerate(tasks):
        result.append(task)
        result.extend(breaks_after.get(idx, []))
    return result
