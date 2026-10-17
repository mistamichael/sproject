"""
Tests für gui/task_rows.py – verlustfreier Round-Trip Tasks ↔ Tabellenzeilen.
"""

from pathlib import Path

import pytest

from gui.task_rows import TaskRow, new_subtask_row, new_task_row, rows_to_tasks, tasks_to_rows
from lib.models import InstanceTask, LoopTask, SimpleTask, SubTask, load_project

EXAMPLES = sorted((Path(__file__).resolve().parent.parent / "examples").glob("*.json"))


def _dump(tasks):
    return [t.model_dump(by_alias=True, exclude_none=True) for t in tasks]


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_round_trip_without_edits_is_lossless(example):
    project = load_project(example)
    assert _dump(rows_to_tasks(tasks_to_rows(project.tasks))) == _dump(project.tasks)


def test_round_trip_keeps_task_types_and_extra_fields():
    tasks = [
        SimpleTask(id=1, name="Pause", duration="30m", is_break=True, description="d", custom="x"),
        InstanceTask(id=2, name="Pizza", duration="15m", instances="order_volume", cycle_prefix="P"),
        LoopTask(id="L", name="Loop", loop_until="total_volume <= 0", cost=12.5, resources=["R1"],
                 subtasks=[SubTask(name="Laden", duration_formula="resource.truck.capacity / 2",
                                   required_resources=["R2"])]),
    ]
    result = rows_to_tasks(tasks_to_rows(tasks))
    assert [type(t) for t in result] == [SimpleTask, InstanceTask, LoopTask]
    assert _dump(result) == _dump(tasks)


def test_edits_are_applied():
    rows = tasks_to_rows([SimpleTask(id=1, name="A", duration="1d", description="keep")])
    rows[0].name = "B"
    rows[0].duration = "2d"
    rows[0].successors_str = "2, 3[AA]"
    rows[0].resources = "R1, R2"
    rows[0].cost = "10"
    task = rows_to_tasks(rows)[0]
    assert (task.name, task.duration, task.successors, task.successors_aa) == ("B", "2d", [2], [3])
    assert task.resources == ["R1", "R2"] and task.cost == 10.0
    assert task.description == "keep"


def test_new_rows_and_orphan_subtasks():
    rows = [TaskRow(row_type="subtask", name="orphan", parent_id="X")]
    rows.append(new_task_row(rows, is_loop=True, name="Loop"))
    rows.append(new_subtask_row(rows[-1].id, "Sub"))
    rows.append(new_task_row(rows, is_loop=False, name="Simple"))
    tasks = rows_to_tasks(rows)
    assert [t.name for t in tasks] == ["Loop", "Simple"]
    assert [s.name for s in tasks[0].subtasks] == ["Sub"]
    assert (tasks[0].id, tasks[1].id) == (1, 2)
