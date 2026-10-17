"""
Fachliche Regeln der Berechnung (Expansion, Rückwärtsrechnung, Pausen, Festkosten).
"""

from lib.cost_calculator import calculate_project_costs
from lib.models import InstanceTask, Person, Project, Resource, SimpleTask
from lib.models.resources import RestInterval
from lib.work_calendar import WorkCalendar
from lib.models.cpm import CPMCalculator


def _cpm(project: Project):
    return CPMCalculator(project, calendar=WorkCalendar()).calculate()


def test_predecessor_of_instance_task_points_to_first_instance():
    project = Project(project="p", order_volume=3, tasks=[
        SimpleTask(id=1, name="Vorbereitung", duration="1h", successors=[2]),
        InstanceTask(id=2, name="Pizza", duration="15m", instances="order_volume"),
    ])
    expanded = project.expand()
    assert expanded.tasks[0].successors == ["2-P1"]
    assert [t.id for t in expanded.tasks[1:]] == ["2-P1", "2-P2", "2-P3"]


def test_end_nodes_get_float_up_to_project_end():
    project = Project(project="p", tasks=[
        SimpleTask(id=1, name="Start", duration="1d", successors=[2, 3]),
        SimpleTask(id=2, name="Lang", duration="5d"),
        SimpleTask(id=3, name="Kurz", duration="2d"),
    ])
    result = _cpm(project)
    assert result.tasks[3].puffer == 3.0 and not result.tasks[3].is_critical
    assert result.tasks[2].is_critical
    assert result.critical_path == [1, 2]


def test_rest_breaks_without_loop_tasks():
    project = Project(
        project="p",
        persons=[Person(id="P1", name="Anna", role="x", hourly_rate=50, rest_intervals="resting_times")],
        resources=[Resource(id="R1", person_id="P1")],
        resting_times=[RestInterval(after_hours=6, duration="30m")],
        tasks=[SimpleTask(id=1, name="Arbeit", duration="8h", resources=["R1"])],
    )
    expanded = project.expand()
    assert [t.id for t in expanded.tasks] == [1, "1-BRK-P1"]
    assert expanded.tasks[1].is_break


def test_task_cost_is_fixed_price():
    project = Project(
        project="p",
        persons=[Person(id="P1", name="Anna", role="x", hourly_rate=100)],
        resources=[Resource(id="R1", person_id="P1")],
        tasks=[
            SimpleTask(id=1, name="Normal", duration="1d", resources=["R1"]),
            SimpleTask(id=2, name="Festpreis", duration="1d", resources=["R1"], cost=250.0),
            SimpleTask(id=3, name="Kostenlos", duration="1d", resources=["R1"], cost=0.0),
        ],
    )
    costs = calculate_project_costs(project, _cpm(project))
    assert costs is not None
    assert costs.entries[0].hours_worked == 8.0          # nur Task 1 zählt als Lohn
    assert costs.total_fixed_costs == 250.0
    assert costs.total_costs == 800.0 + 250.0
