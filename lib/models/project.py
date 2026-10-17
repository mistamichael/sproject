"""
Project model
=============

Einheitliches Projekt-Modell für alle JSON-Strukturen. Enthält nur Daten und
Validierung; Expansion und Berechnung liegen in expander.py und cpm.py.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from pydantic import BaseModel

from ..durations import detect_time_unit, TimeUnit
from .resources import Person, Resource, RestInterval
from .tasks import InstanceTask, LoopTask, SimpleTask
from .tracking import Actual, Baseline

if TYPE_CHECKING:
    from .cpm import CPMResult

_DATE_FORMATS = ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M')


def parse_start_date(value: Union[str, datetime, None]) -> Optional[datetime]:
    """'2026-03-03', '2026-03-03 09:00:00' oder datetime → datetime; None bleibt None."""
    if value is None or isinstance(value, datetime):
        return value
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Ungültiges Startdatum: {value!r} (erwartet YYYY-MM-DD [HH:MM[:SS]])")


class Project(BaseModel):
    """
    Projekt mit Tasks, optionalen Ressourcen, Personen und Ruhezeiten.

    Vorhandene Felder bestimmen das Verhalten:
    - order_volume + InstanceTask → Instanzen werden expandiert
    - total_volume + LoopTask    → Zyklen werden expandiert
    - persons                    → Personen-/Kostenauswertung aktiv
    """

    project: str
    project_start: Optional[str] = None

    # Zyklus-Projekte
    order_volume: Optional[int] = None

    # Loop-Projekte
    total_volume: Optional[Union[int, float]] = None
    total_hours: Optional[int] = None
    unit: Optional[str] = None

    resources: Optional[List[Resource]] = None
    persons: Optional[List[Person]] = None
    resting_times: Optional[List[RestInterval]] = None

    # Plan gegen Ist
    status_date: Optional[str] = None                 # Stichtag des Ist-Stands
    actuals: Optional[Dict[str, Actual]] = None       # Task-ID → Ist-Stand
    baseline: Optional[Baseline] = None               # eingefrorener Plan

    # Alle Task-Typen in einem Union (spezifischere zuerst)
    tasks: List[Union[LoopTask, InstanceTask, SimpleTask]] = []

    model_config = {
        'extra': 'allow',
    }

    def get_time_unit(self) -> TimeUnit:
        """Häufigste Zeiteinheit der Task-Dauern ('minutes', 'hours' oder 'days')."""
        durations = [task.duration for task in self.tasks if task.duration]
        return detect_time_unit(durations) if durations else 'days'

    def get_all_task_ids(self) -> List[Union[int, str]]:
        return [task.id for task in self.tasks]

    def expand(self) -> 'Project':
        """Expandiert Instance- und Loop-Tasks (siehe expander.expand_project)."""
        from .expander import expand_project
        return expand_project(self)

    # Ältere Namen – beide expandieren alle expandierbaren Tasks
    expand_cycles = expand
    expand_loops = expand

    def calculate_cpm(self, start_date: Union[str, datetime, None] = None,
                      cfg_dir: Optional[Path] = None) -> 'CPMResult':
        """
        CPM-Berechnung für dieses Projekt (ohne Expansion – dafür lib.schedule.build_schedule).

        Args:
            start_date: überschreibt project_start (str oder datetime)
            cfg_dir:    Konfigurationsverzeichnis (Kalender, Feiertage)
        """
        from .cpm import CPMCalculator
        start = parse_start_date(start_date) or parse_start_date(self.project_start)
        return CPMCalculator(self, start, cfg_dir=cfg_dir).calculate()


# ---------------------------------------------------------------------------
# Backward-Compat-Aliase für die früheren Projekt-Klassen
# ---------------------------------------------------------------------------
ProjectBase = Project
SimpleProject = Project
CycleProject = Project
LoopProject = Project
PersonProject = Project
