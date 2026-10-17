"""
Baseline
========

Friert den aktuell berechneten Plan als Baseline ein. Gespeichert werden
Kalenderdaten (nicht Arbeitstag-Offsets), damit der Vergleich auch nach
Änderungen am Projektstart oder Kalender eindeutig bleibt.
"""

from datetime import datetime

from .models.tracking import Baseline, BaselineTask
from .schedule import Schedule
from .time_axis import point_in_time

_FMT = "%Y-%m-%d %H:%M"


def create_baseline(schedule: Schedule) -> Baseline:
    """Baseline aus dem berechneten Plan (Pausen und Kalender-Blocker ausgenommen)."""
    result = schedule.cpm
    if result.project_start is None:
        raise ValueError("Für eine Baseline braucht das Projekt ein Startdatum")
    return Baseline(
        created=datetime.now().strftime(_FMT),
        project_end=point_in_time(result, result.project_end_days, is_end=True).strftime(_FMT),
        tasks={
            str(tid): BaselineTask(
                start=point_in_time(result, t.faz).strftime(_FMT),
                finish=point_in_time(result, t.fez, is_end=True).strftime(_FMT),
            )
            for tid, t in result.tasks.items() if not t.is_system
        },
    )
