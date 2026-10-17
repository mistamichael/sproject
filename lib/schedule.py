"""
Schedule
========

Einziger Einstieg für den kompletten Rechenweg – CLI und GUI nutzen beide
build_schedule():

    Projekt → Expansion → CPM (Phase 1) → Gantt-Kalender (Phase 2) → Kosten
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .cost_calculator import CostBreakdown, calculate_project_costs
from .models.cpm import CPMResult
from .models.gantt import GanttCalculator, GanttResult
from .models.project import Project


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
    gantt = GanttCalculator(cpm).calculate()
    costs = calculate_project_costs(expanded, cpm)
    return Schedule(project=expanded, cpm=cpm, gantt=gantt, costs=costs)
