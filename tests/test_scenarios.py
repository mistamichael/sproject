"""
Szenarien: Änderungen anwenden und mit dem Basisplan vergleichen.
"""

import pytest

from lib.models import Person, Project, Resource, SimpleTask
from lib.models.scenario import Scenario, ScenarioChange
from lib.scenarios import BASE_NAME, apply_scenario, compare_scenarios, find_scenario

START = "2026-03-02 08:00:00"     # Montag


def _project(scenarios=()):
    return Project(
        project="p", project_start=START,
        persons=[Person(id="P1", name="Anna", role="x", hourly_rate=50)],
        resources=[Resource(id="R1", person_id="P1"), Resource(id="M1", type="machine")],
        tasks=[
            SimpleTask(id=1, name="Vorbereitung", duration="1d", resources=["R1"], successors=[2]),
            SimpleTask(id="T-1", name="Transport 1", duration="2d", resources=["M1"], successors=["T-2"]),
            SimpleTask(id="T-2", name="Transport 2", duration="2d", resources=["M1"]),
            SimpleTask(id=2, name="Montage", duration="2d", resources=["R1"]),
        ],
        scenarios=list(scenarios) or None,
    )


def _change(**kwargs):
    return ScenarioChange.model_validate(kwargs)


def test_task_pattern_and_duration_factor():
    variant = apply_scenario(_project(), Scenario(name="s", changes=[_change(task="T-*", duration_factor=1.5)]))
    assert [t.duration for t in variant.tasks if str(t.id).startswith("T-")] == ["3.0000d", "3.0000d"]


def test_any_task_field_can_be_set_and_is_validated():
    variant = apply_scenario(_project(), Scenario(name="s", changes=[_change(task=2, delay="1d", deadline="2026-03-04")]))
    montage = next(t for t in variant.tasks if t.id == 2)
    assert (montage.delay, montage.deadline) == ("1d", "2026-03-04")
    with pytest.raises(ValueError):
        apply_scenario(_project(), Scenario(name="s", changes=[_change(task=2, duration="viel")]))
    with pytest.raises(ValueError, match="unbekannte Task-Felder"):
        apply_scenario(_project(), Scenario(name="s", changes=[_change(task=2, dauer="2d")]))


def test_unknown_targets_are_reported():
    for change in (_change(task="X*"), _change(resource="NOPE", unavailable=[]), _change(person="NOPE", vacation=[])):
        with pytest.raises(ValueError, match="Szenario 's'"):
            apply_scenario(_project(), Scenario(name="s", changes=[change]))
    with pytest.raises(ValueError):
        _change(task=1, person="P1")                     # genau ein Ziel


def test_compare_against_base_plan_without_touching_the_input():
    scenarios = [
        Scenario(name="Anna krank", changes=[_change(person="P1", vacation=[{"from": "2026-03-03", "to": "2026-03-04", "description": "krank"}])]),
        Scenario(name="Maschine defekt", changes=[_change(resource="M1", unavailable=[{"date": "2026-03-02", "description": "Defekt"}])]),
        Scenario(name="Montage verzögert", changes=[_change(task=2, delay="3d")]),
    ]
    project = _project(scenarios)
    outcomes = compare_scenarios(project)
    by_name = {o.name: o for o in outcomes}
    assert outcomes[0].name == BASE_NAME and outcomes[0].duration_days == 4    # Transporte 2+2 Tage
    assert by_name["Anna krank"].duration_days == 5                            # Mo, (Di+Mi krank), Do–Fr
    assert by_name["Maschine defekt"].delta_days == pytest.approx(1)
    assert by_name["Montage verzögert"].duration_days == 6                     # 1 + 3 Wartezeit + 2
    assert project.persons[0].vacation is None and project.resources[1].unavailable is None
    assert find_scenario(project, "Anna krank").name == "Anna krank"
