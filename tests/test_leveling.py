"""
Ressourcenplanung: Personenkonflikte, Kapazitäten, Urlaub, Teilzeit, feste Termine.
"""

import pytest

from lib.models import Person, Project, Resource, SimpleTask
from lib.models.cpm import CPMCalculator
from lib.models.resources import TimeRange, VacationEntry, WorkHoursOverride
from lib.report_data import collect_deadline_violations
from lib.time_axis import point_in_time
from lib.work_calendar import WorkCalendar

START = "2026-03-02 08:00:00"     # Montag


def _calc(tasks, resources=(), persons=()):
    project = Project(project="p", project_start=START, tasks=list(tasks),
                      resources=list(resources) or None, persons=list(persons) or None)
    return CPMCalculator(project, calendar=WorkCalendar()).calculate()


def _person(pid="P1", **kwargs):
    return Person(id=pid, name=pid, role="x", hourly_rate=50, **kwargs)


def test_person_cannot_work_on_two_tasks_at_once():
    result = _calc(
        [SimpleTask(id=1, name="A", duration="2d", resources=["R1"]),
         SimpleTask(id=2, name="B", duration="3d", resources=["R1"])],
        resources=[Resource(id="R1", person_id="P1")], persons=[_person()],
    )
    first, second = sorted(result.tasks.values(), key=lambda t: t.faz)
    assert first.faz == 0 and second.faz == first.fez and result.project_end_days == 5
    assert second.resource_predecessors == [first.id]
    assert set(result.critical_path) == {1, 2}     # Wartebeziehung macht beide kritisch


def test_parallel_slots_of_machine_and_unlimited_material():
    result = _calc(
        [SimpleTask(id=i, name=f"T{i}", duration="1d", resources=["OVEN", "MAT"]) for i in range(1, 4)],
        resources=[Resource(id="OVEN", type="oven", capacity=2), Resource(id="MAT", type="material")],
    )
    assert sorted(t.faz for t in result.tasks.values()) == [0, 0, 1]


def test_truck_capacity_is_load_not_parallel_trips():
    result = _calc(
        [SimpleTask(id=1, name="Fahrt 1", duration="1d", resources=["L1"]),
         SimpleTask(id=2, name="Fahrt 2", duration="1d", resources=["L1"])],
        resources=[Resource(id="L1", type="truck", capacity=12)],
    )
    assert result.project_end_days == 2


def test_vacation_interrupts_task():
    # 3 Tage Arbeit ab Mo, Urlaub am Di → Mo, Mi, Do
    person = _person(vacation=[VacationEntry(date="2026-03-03", description="Urlaub")])
    result = _calc([SimpleTask(id=1, name="A", duration="3d", resources=["R1"])],
                   resources=[Resource(id="R1", person_id="P1")], persons=[person])
    task = result.tasks[1]
    assert (task.duration, task.span) == (3, 4)
    assert point_in_time(result, task.fez, is_end=True).day == 5     # Ende Do 05.03.


def test_part_time_slows_task_down():
    person = _person(workinghours_override=WorkHoursOverride(
        description="halbtags", days=["mon", "tue", "wed", "thu", "fri"],
        hours=[TimeRange.model_validate({"from": "08:00", "to": "12:00"})]))
    result = _calc([SimpleTask(id=1, name="A", duration="2d", resources=["R1"])],
                   resources=[Resource(id="R1", person_id="P1")], persons=[person])
    assert result.tasks[1].span == pytest.approx(4)


def test_not_before_delays_start():
    result = _calc([SimpleTask(id=1, name="Lieferung", duration="1d", not_before="2026-03-04")])
    assert result.tasks[1].faz == 2                    # Mi = 2 Arbeitstage nach Mo


def test_missed_deadline_gives_negative_float():
    result = _calc([
        SimpleTask(id=1, name="A", duration="3d", successors=[2]),
        SimpleTask(id=2, name="Abnahme", duration="1d", deadline="2026-03-04"),
    ])
    late = result.tasks[2]
    assert late.deadline_missed and late.puffer < 0 and late.is_critical
    assert [t.id for t in result.deadline_violations] == [2]
    violation = collect_deadline_violations(result)[0]
    assert (violation.deadline, violation.end) == ("2026-03-04", "2026-03-05")


def test_deadline_reduces_float_without_violation():
    result = _calc([
        SimpleTask(id=1, name="A", duration="1d"),
        SimpleTask(id=2, name="Lang", duration="5d"),
        SimpleTask(id=3, name="B", duration="1d", deadline="2026-03-03"),   # Ende Di
    ])
    assert result.tasks[3].puffer == pytest.approx(1)  # statt 4 Tage bis Projektende
    assert not result.deadline_violations
