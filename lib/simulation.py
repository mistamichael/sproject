"""
Monte-Carlo-Simulation
======================

Rechnet den Plan viele Male mit zufälligen Abweichungen und leitet daraus
Wahrscheinlichkeiten ab ("mit 80 % fertig bis …").

Unsicherheit kommt aus drei Quellen:

- Task.duration_range [min, max]: Dauer dreiecksverteilt, wahrscheinlichster Wert = duration
- Task.risk {probability, delay}: Startverzögerung, die mit probability eintritt
- Scenario.probability: das Szenario wird im Lauf mit dieser Wahrscheinlichkeit angewendet

Für die Laufzeit nutzt jeder Lauf nur die Prioritätsregel der Ressourcenplanung,
die im Basisplan gewonnen hat; Ruhepausen, Gantt und Kosten werden nicht
gerechnet (Pausen hängen als Seitenzweig und ändern das Projektende nicht).
"""

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .durations import format_time_value, parse_duration_to_days
from .models.cpm import CPMCalculator, CPMResult
from .models.dependencies import TaskId
from .models.project import Project
from .scenarios import apply_scenario
from .schedule import Schedule, build_schedule
from .time_axis import point_in_time

PERCENTILES = (50, 80, 90)


@dataclass
class SimulationResult:
    runs: int
    base: Schedule                                   # Basisplan (Kalender, Startdatum, Baseline)
    ends: List[float]                                # Projektende je Lauf (Arbeitstage, sortiert)
    criticality: Dict[TaskId, float]                 # Anteil der Läufe, in denen der Task kritisch war
    deadline_hit: Dict[TaskId, float] = field(default_factory=dict)   # Anteil der Läufe mit gehaltener Deadline
    scenario_hits: Dict[str, float] = field(default_factory=dict)     # tatsächliche Eintrittshäufigkeit

    @property
    def result(self) -> CPMResult:
        return self.base.cpm

    def percentile(self, p: float) -> float:
        """Nearest-Rank-Perzentil des Projektendes."""
        index = max(math.ceil(p / 100 * len(self.ends)) - 1, 0)
        return self.ends[index]

    def probability_by(self, workdays: float) -> float:
        """Anteil der Läufe, die bis workdays fertig sind."""
        return sum(1 for e in self.ends if e <= workdays + 1e-9) / len(self.ends)

    @property
    def mean(self) -> float:
        return sum(self.ends) / len(self.ends)

    def date(self, workdays: float) -> Optional[datetime]:
        return point_in_time(self.result, workdays, is_end=True) if self.result.project_start else None


def has_uncertainty(project: Project) -> bool:
    expanded = project.expand()
    return (any(t.duration_range or t.risk for t in expanded.tasks)
            or any(s.probability for s in project.scenarios or []))


def simulate(project: Project, runs: int = 300, seed: Optional[int] = None,
             start_date: Union[str, datetime, None] = None, cfg_dir: Optional[Path] = None) -> SimulationResult:
    """
    Raises:
        ValueError: wenn das Projekt keine Unsicherheiten enthält
    """
    if runs < 1:
        raise ValueError("runs muss mindestens 1 sein")
    if not has_uncertainty(project):
        raise ValueError("Keine Unsicherheiten definiert (duration_range, risk oder Szenario mit probability)")

    base = build_schedule(project, start_date=start_date, cfg_dir=cfg_dir)
    result = base.cpm
    calendar, holidays = result.calendar, (result.holidays if result.skip_holidays else None)
    expanded = project.expand()
    risky_scenarios = [s for s in project.scenarios or [] if s.probability]
    rng = random.Random(seed)

    ends: List[float] = []
    critical_count: Dict[TaskId, int] = {}
    deadline_ok: Dict[TaskId, int] = {}
    scenario_count = {s.name: 0 for s in risky_scenarios}

    for _ in range(runs):
        variant = expanded
        for scenario in risky_scenarios:
            if rng.random() < (scenario.probability or 0.0):
                variant = apply_scenario(variant, scenario)
                scenario_count[scenario.name] += 1
        variant = variant.model_copy(update={"tasks": [_sample(t, rng) for t in variant.tasks]})

        run = CPMCalculator(variant, result.project_start, calendar=calendar, holidays=holidays,
                            leveling_rule=result.leveling_rule).calculate()
        ends.append(run.project_end_days)
        for tid, task in run.tasks.items():
            if task.is_critical and not task.is_system:
                critical_count[tid] = critical_count.get(tid, 0) + 1
            if task.deadline is not None:
                deadline_ok[tid] = deadline_ok.get(tid, 0) + (0 if task.deadline_missed else 1)

    return SimulationResult(
        runs=runs,
        base=base,
        ends=sorted(ends),
        criticality={tid: n / runs for tid, n in critical_count.items()},
        deadline_hit={tid: n / runs for tid, n in deadline_ok.items()},
        scenario_hits={name: n / runs for name, n in scenario_count.items()},
    )


def _sample(task, rng: random.Random):
    """Task mit zufälliger Dauer (duration_range) und ggf. eingetretenem Risiko."""
    updates = {}
    if task.duration_range:
        planned = parse_duration_to_days(task.duration or 0)
        low, high = (parse_duration_to_days(x) for x in task.duration_range)
        mode = min(max(planned, low), high)
        updates["duration"] = f"{rng.triangular(low, high, mode):.6f}d"
    if task.risk and rng.random() < task.risk.probability:
        delay = parse_duration_to_days(task.delay or 0) + parse_duration_to_days(task.risk.delay)
        updates["delay"] = f"{delay:.6f}d"
    return task.model_copy(update=updates) if updates else task


# ---------------------------------------------------------------------------
# Aufbereitung
# ---------------------------------------------------------------------------

def summary_rows(sim: SimulationResult) -> List[List[str]]:
    """(Kennzahl, Wert) für Konsole und Reports."""
    unit = sim.result.time_unit
    fmt = '%Y-%m-%d %H:%M' if unit != 'days' else '%Y-%m-%d'

    def when(days: float) -> str:
        moment = sim.date(days)
        return f"{moment:{fmt}} ({format_time_value(days, unit)})" if moment else format_time_value(days, unit)

    rows = [["Läufe", str(sim.runs)],
            ["Plan (ohne Streuung)", when(sim.result.project_end_days)],
            ["Plan wird gehalten mit", f"{sim.probability_by(sim.result.project_end_days):.0%}"]]
    rows += [[f"P{p} (zu {p} % fertig bis)", when(sim.percentile(p))] for p in PERCENTILES]
    rows += [["Frühestes / spätestes Ende", f"{when(sim.ends[0])} / {when(sim.ends[-1])}"]]
    if sim.result.baseline_end is not None:
        rows.append(["Baseline-Ende wird gehalten mit", f"{sim.probability_by(sim.result.baseline_end):.0%}"])
    for tid, rate in sim.deadline_hit.items():
        rows.append([f"Deadline Task {tid} wird gehalten mit", f"{rate:.0%}"])
    for name, rate in sim.scenario_hits.items():
        rows.append([f"Szenario '{name}' eingetreten", f"{rate:.0%}"])
    return rows


def top_critical(sim: SimulationResult, limit: int = 10) -> List[List[str]]:
    """Tasks, die am häufigsten auf dem kritischen Pfad lagen."""
    names = {tid: t.name for tid, t in sim.result.tasks.items()}
    ranked = sorted(sim.criticality.items(), key=lambda kv: -kv[1])[:limit]
    return [[str(tid), names.get(tid, ""), f"{rate:.0%}"] for tid, rate in ranked]
