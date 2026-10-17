"""
Schedule
========

Einziger Einstieg für den kompletten Rechenweg – CLI und GUI nutzen beide
build_schedule():

    Projekt → Expansion → CPM → Ruhepausen (nach Zeitplan) → CPM → Gantt-Kalender → Kosten
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, cast

from .cost_calculator import CostBreakdown, calculate_project_costs
from .models.cpm import CPMResult
from .models.gantt import GanttCalculator, GanttResult
from .models.project import Project
from .models.rest_breaks import insert_rest_breaks
from .models.tasks import SimpleTask


@dataclass(frozen=True)
class Schedule:
    """Ergebnis eines Rechenlaufs."""
    project: Project            # expandiertes Projekt (Grundlage aller Ergebnisse)
    cpm: CPMResult
    gantt: GanttResult
    costs: Optional[CostBreakdown]

    @property
    def name(self) -> str:
        return self.project.project


def build_schedule(project: Project,
                   start_date: Union[str, datetime, None] = None,
                   cfg_dir: Optional[Path] = None) -> Schedule:
    """
    Expandiert das Projekt und berechnet Netzplan, Kalenderdaten und Kosten.

    Args:
        project:    Projekt wie geladen (Instance-/Loop-Tasks werden hier expandiert)
        start_date: überschreibt project_start
        cfg_dir:    Konfigurationsverzeichnis (Kalender, Feiertage)
    """
    expanded = project.expand()
    cpm = expanded.calculate_cpm(start_date=start_date, cfg_dir=cfg_dir)

    # Ruhepausen nach dem tatsächlichen Zeitplan (FAZ) verteilen, dann neu rechnen
    if expanded.persons and expanded.resting_times:
        simple_tasks = cast(List[SimpleTask], expanded.tasks)   # nach expand() nur noch SimpleTasks
        tasks = insert_rest_breaks(simple_tasks, expanded, {tid: t.faz for tid, t in cpm.tasks.items()})
        if len(tasks) != len(expanded.tasks):
            expanded = expanded.model_copy(update={"tasks": tasks})
            cpm = expanded.calculate_cpm(start_date=start_date, cfg_dir=cfg_dir)
    gantt = GanttCalculator(cpm).calculate()
    costs = calculate_project_costs(expanded, cpm)
    return Schedule(project=expanded, cpm=cpm, gantt=gantt, costs=costs)
