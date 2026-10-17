"""
Scenarios
=========

Was-wäre-wenn-Varianten: Ein Szenario (Project.scenarios) wird auf eine Kopie
des expandierten Projekts angewendet und wie der Basisplan mit
build_schedule() gerechnet. compare_scenarios() stellt alle Varianten dem
Basisplan gegenüber.
"""

from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import Path
from typing import List, Optional, Union

from .durations import format_time_value
from .models.project import Project
from .models.scenario import Scenario
from .schedule import Schedule, build_schedule
from .time_axis import point_in_time

BASE_NAME = "Basisplan"


def find_scenario(project: Project, name: str) -> Scenario:
    for scenario in project.scenarios or []:
        if scenario.name == name:
            return scenario
    known = ", ".join(s.name for s in project.scenarios or []) or "keine"
    raise ValueError(f"Szenario '{name}' nicht gefunden (vorhanden: {known})")


def apply_scenario(project: Project, scenario: Scenario) -> Project:
    """
    Kopie des expandierten Projekts mit den Änderungen des Szenarios.

    Raises:
        ValueError: wenn eine Änderung keinen Task, keine Ressource bzw. Person trifft
    """
    from .durations import parse_duration_to_days

    variant = project.expand().model_copy(deep=True)
    variant.scenarios = None
    for change in scenario.changes:
        if change.task is not None:
            pattern = str(change.task)
            hits = [i for i, t in enumerate(variant.tasks) if fnmatchcase(str(t.id), pattern)]
            if not hits:
                raise ValueError(f"Szenario '{scenario.name}': kein Task passt zu '{pattern}'")
            for i in hits:
                task = variant.tasks[i]
                updates = dict(change.task_fields)
                unknown = [f for f in updates if f not in type(task).model_fields]
                if unknown:
                    raise ValueError(f"Szenario '{scenario.name}': unbekannte Task-Felder {unknown}")
                if change.duration_factor is not None:
                    days = parse_duration_to_days(task.duration or 0) * change.duration_factor
                    updates["duration"] = f"{days:.4f}d"
                # neu validieren, damit z. B. ungültige Dauern wie beim Laden abgelehnt werden
                variant.tasks[i] = type(task).model_validate({**task.model_dump(), **updates})
        elif change.resource is not None:
            resource = next((r for r in variant.resources or [] if r.id == change.resource), None)
            if resource is None:
                raise ValueError(f"Szenario '{scenario.name}': Ressource '{change.resource}' nicht gefunden")
            resource.unavailable = (resource.unavailable or []) + (change.unavailable or [])
        else:
            person = next((p for p in variant.persons or [] if p.id == change.person), None)
            if person is None:
                raise ValueError(f"Szenario '{scenario.name}': Person '{change.person}' nicht gefunden")
            person.vacation = (person.vacation or []) + (change.vacation or [])
    return variant


@dataclass
class ScenarioOutcome:
    name: str
    description: str
    schedule: Schedule
    end: Optional[datetime]
    duration_days: float
    delta_days: float              # gegenüber dem Basisplan (positiv = später)
    costs: Optional[float]
    deadline_violations: int

    def delta_text(self, unit) -> str:
        if abs(self.delta_days) < 1e-9:
            return "±0"
        return ("+" if self.delta_days > 0 else "") + format_time_value(self.delta_days, unit)


def _outcome(name: str, description: str, schedule: Schedule, base_days: float) -> ScenarioOutcome:
    result = schedule.cpm
    days = result.project_end_days
    return ScenarioOutcome(
        name=name,
        description=description,
        schedule=schedule,
        end=point_in_time(result, days, is_end=True) if result.project_start else None,
        duration_days=days,
        delta_days=days - base_days,
        costs=schedule.costs.total_costs if schedule.costs else None,
        deadline_violations=len(result.deadline_violations),
    )


def compare_scenarios(project: Project, start_date: Union[str, datetime, None] = None,
                      cfg_dir: Optional[Path] = None) -> List[ScenarioOutcome]:
    """Basisplan und alle Szenarien des Projekts – erster Eintrag ist der Basisplan."""
    base = build_schedule(project, start_date=start_date, cfg_dir=cfg_dir)
    base_days = base.cpm.project_end_days
    outcomes = [_outcome(BASE_NAME, "", base, base_days)]
    for scenario in project.scenarios or []:
        schedule = build_schedule(apply_scenario(project, scenario), start_date=start_date, cfg_dir=cfg_dir)
        outcomes.append(_outcome(scenario.name, scenario.description or "", schedule, base_days))
    return outcomes


def comparison_rows(outcomes: List[ScenarioOutcome]) -> List[List[str]]:
    """Tabelle für Konsole und Reports: Szenario, Ende, Dauer, Δ, Kosten, Deadlines."""
    unit = outcomes[0].schedule.cpm.time_unit
    fmt = '%Y-%m-%d %H:%M' if unit != 'days' else '%Y-%m-%d'
    rows = [["Szenario", "Ende", "Dauer", "Δ zum Basisplan", "Kosten", "Deadlines verfehlt"]]
    for o in outcomes:
        rows.append([
            o.name,
            o.end.strftime(fmt) if o.end else "–",
            format_time_value(o.duration_days, unit),
            o.delta_text(unit),
            f"{o.costs:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".") if o.costs is not None else "–",
            str(o.deadline_violations),
        ])
    return rows
