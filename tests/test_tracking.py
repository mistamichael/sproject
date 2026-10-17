"""
Plan gegen Ist: Stichtag, Ist-Werte, Baseline.
"""

import pytest

from lib.baseline import create_baseline
from lib.models import Project, SimpleTask
from lib.models.cpm import CPMCalculator
from lib.models.tracking import Actual
from lib.report_data import tracking_summary
from lib.schedule import build_schedule
from lib.work_calendar import WorkCalendar

START = "2026-03-02 08:00:00"     # Montag


def _project(**kwargs):
    return Project(project="p", project_start=START, tasks=[
        SimpleTask(id=1, name="A", duration="2d", successors=[2]),
        SimpleTask(id=2, name="B", duration="4d", successors=[3]),
        SimpleTask(id=3, name="C", duration="1d"),
    ], **kwargs)


def _calc(project):
    return CPMCalculator(project, calendar=WorkCalendar()).calculate()


def test_done_task_keeps_actual_dates_and_successors_follow():
    result = _calc(_project(status_date="2026-03-04", actuals={
        "1": Actual(start="2026-03-02", finish="2026-03-04")}))     # 3 statt 2 Tage
    a = result.tasks[1]
    assert (a.status, a.faz, a.fez) == ("done", 0, 3)
    assert result.tasks[2].faz == 3
    assert not a.is_critical                                         # Erledigtes ist nicht mehr kritisch


def test_in_progress_task_continues_from_status_date_with_remaining_work():
    result = _calc(_project(status_date="2026-03-05", actuals={
        "1": Actual(start="2026-03-02", finish="2026-03-03"),
        "2": Actual(start="2026-03-04", progress=0.25)}))            # 1 von 4 Tagen erledigt
    b = result.tasks[2]
    assert b.status == "in_progress" and b.remaining == pytest.approx(3)
    assert (b.faz, b.fez) == (2, pytest.approx(4 + 3))               # ab Ende Do (Stichtag) noch 3 Tage


def test_not_started_tasks_start_no_earlier_than_status_date():
    result = _calc(_project(status_date="2026-03-10"))               # nichts begonnen, Stichtag Di nächste Woche
    assert result.tasks[1].faz == pytest.approx(7)                   # Ende Di = 7 Arbeitstage


def test_baseline_variance_and_slip():
    project = _project()
    project.baseline = create_baseline(build_schedule(project))
    project.status_date = "2026-03-03"
    project.actuals = {"1": Actual(start="2026-03-02", finish="2026-03-04")}   # ein Tag Verzug
    result = _calc(project)
    assert result.tasks[3].baseline_variance == pytest.approx(1)
    assert result.slip == pytest.approx(1)
    summary = dict(tracking_summary(result))
    assert summary["Verzug"] == "+1.0d" and summary["Erledigt / laufend"] == "1 / 0"


def test_without_tracking_data_nothing_changes():
    result = _calc(_project())
    assert result.status_date is None and result.baseline_end is None
    assert tracking_summary(result) == []
