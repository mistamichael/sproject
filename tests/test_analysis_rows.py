"""
Tests für gui/analysis_rows.py – Text ↔ Modell für Unsicherheiten und Szenarien.
"""

import pytest

from gui.analysis_rows import (
    ChangeRow, build_change, format_change, format_percent, parse_percent, set_change_target,
    set_change_text, set_range, set_risk_delay, set_risk_note, set_risk_probability,
)
from lib.models import SimpleTask
from lib.models.scenario import Scenario, ScenarioChange


def _task(**kwargs):
    return SimpleTask(id=1, name="T", duration="40h", **kwargs)


@pytest.mark.parametrize("text, expected", [("20", 0.2), ("20 %", 0.2), ("12,5", 0.125)])
def test_parse_percent(text, expected):
    assert parse_percent(text) == pytest.approx(expected)
    assert parse_percent("") is None


def test_percent_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        parse_percent("150")
    assert format_percent(0.15) == "15"


def test_range_missing_bound_is_planned_duration():
    task = _task()
    set_range(task, high="72h")
    assert task.duration_range == ["40h", "72h"]
    set_range(task, low="32h")
    assert task.duration_range == ["32h", "72h"]


def test_invalid_range_keeps_old_value_and_empty_removes_it():
    task = _task(duration_range=["32h", "72h"])
    set_range(task, low="99h")          # Min > Max
    set_range(task, high="abc")
    assert task.duration_range == ["32h", "72h"]
    set_range(task, low="", high="")
    assert task.duration_range is None


def test_risk_fields():
    task = _task()
    set_risk_probability(task, "20")
    set_risk_delay(task, "16h")
    set_risk_note(task, "API instabil")
    assert task.risk is not None
    assert (task.risk.probability, task.risk.delay, task.risk.note) == (0.2, "16h", "API instabil")
    set_risk_delay(task, "kaputt")
    assert task.risk.delay == "16h"
    set_risk_probability(task, "")
    assert task.risk is None


def test_task_change_round_trip():
    change = build_change("task", "2-F*.1", "duration_factor=1,5; deadline=2026-03-27; resources=R1, R2")
    assert change.task == "2-F*.1" and change.duration_factor == 1.5
    assert change.task_fields == {"deadline": "2026-03-27", "resources": ["R1", "R2"]}
    assert format_change(change) == "duration_factor=1.5; deadline=2026-03-27; resources=R1, R2"
    assert build_change("task", "4", "duration_factor=2").task == 4


def test_absence_change_round_trip():
    change = build_change("person", "DEV1", "2026-03-09 – 2026-03-13 (krank); 2026-04-01", "Ausfall")
    assert change.vacation is not None
    assert [(e.from_, e.to, e.date, e.description) for e in change.vacation] == [
        ("2026-03-09", "2026-03-13", None, "krank"), (None, None, "2026-04-01", "Ausfall")]
    assert format_change(change) == "2026-03-09 – 2026-03-13 (krank); 2026-04-01 (Ausfall)"


@pytest.mark.parametrize("kind, target, text", [
    ("task", "1", "unbekannt=1"), ("task", "1", "duration_factor"), ("task", "", "duration_factor=2"),
    ("task", "1", "duration_factor=0"), ("resource", "R1", ""),
])
def test_invalid_changes_are_rejected(kind, target, text):
    with pytest.raises(ValueError):
        build_change(kind, target, text)


def test_editing_a_change_replaces_it_in_the_scenario():
    scenario = Scenario(name="S", changes=[ScenarioChange(task=4, duration_factor=1.5)])
    row = ChangeRow(scenario, scenario.changes[0])
    set_change_text(row, "delay=2d")
    set_change_target(row, "5")
    assert scenario.changes == [row.change]
    assert row.change.task == 5 and row.change.task_fields == {"delay": "2d"}
    set_change_text(row, "Unsinn")       # ungültig → unverändert
    assert format_change(scenario.changes[0]) == "delay=2d"
