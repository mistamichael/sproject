"""
Monte-Carlo-Simulation: Unsicherheiten aus duration_range, risk und Szenarien.
"""

import pytest

from lib.models import Project, SimpleTask
from lib.models.base import TaskRisk
from lib.models.scenario import Scenario, ScenarioChange
from lib.simulation import simulate, summary_rows

START = "2026-03-02 08:00:00"     # Montag


def _project(**task_kwargs):
    return Project(project="p", project_start=START, tasks=[
        SimpleTask(id=1, name="A", duration="2d", successors=[2], **task_kwargs),
        SimpleTask(id=2, name="B", duration="3d"),
        SimpleTask(id=3, name="Neben", duration="1d"),
    ])


def test_requires_uncertainty():
    with pytest.raises(ValueError, match="Keine Unsicherheiten"):
        simulate(_project(), runs=10)


def test_duration_range_is_reproducible_and_bounded():
    project = _project(duration_range=["1d", "6d"])
    first, second = simulate(project, runs=200, seed=7), simulate(project, runs=200, seed=7)
    assert first.ends == second.ends
    assert 4 <= first.ends[0] and first.ends[-1] <= 9                 # A ∈ [1, 6] + B (3)
    assert first.percentile(50) <= first.percentile(80) <= first.percentile(90)
    assert first.criticality[1] == 1.0 and 3 not in first.criticality  # Nebentask nie kritisch


def test_certain_risk_always_delays():
    sim = simulate(_project(risk=TaskRisk(probability=1.0, delay="2d")), runs=20, seed=1)
    assert set(sim.ends) == {7.0}                                       # 2 + 2 Verzögerung + 3
    assert sim.probability_by(sim.result.project_end_days) == 0.0


def test_scenario_probability():
    def with_scenario(p):
        project = _project()
        project.scenarios = [Scenario(name="B länger", probability=p,
                                      changes=[ScenarioChange.model_validate({"task": 2, "duration": "5d"})])]
        return simulate(project, runs=50, seed=3)

    assert set(with_scenario(1.0).ends) == {7.0}
    rare = with_scenario(0.0001)
    assert set(rare.ends) == {5.0} and rare.scenario_hits["B länger"] == 0.0
    rows = dict((r[0], r[1]) for r in summary_rows(rare))
    assert rows["Läufe"] == "50" and rows["Plan wird gehalten mit"] == "100%"
