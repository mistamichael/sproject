"""
TaskRow – Tabellenzeilen der Aufgaben-Tabelle
=============================================

Flache Zeilen für die GUI-Tabelle (Loop-Tasks mit ihren Subtasks als eigene
Zeilen). Jede Zeile kennt das Original-Objekt (source); beim Zurückschreiben
werden nur die in der Tabelle bearbeitbaren Felder geändert. Alle anderen
Felder (Task-Typ, description, is_break, duration_formula, Zusatzfelder …)
bleiben dadurch erhalten.

Kein Dear-PyGui-Code – die Umwandlung ist ohne GUI testbar.
"""

from dataclasses import dataclass
from typing import Any, List, Literal, Optional, Union

from lib.models.dependencies import format_dependencies, parse_dependencies, parse_task_id
from lib.models.tasks import InstanceTask, LoopTask, SimpleTask, SubTask

RowType = Literal["simple", "loop", "subtask"]
AnyTask = Union[SimpleTask, InstanceTask, LoopTask]


@dataclass
class TaskRow:
    row_type: RowType
    id: str = ""
    name: str = ""
    duration: str = ""
    resources: str = ""         # "R1, R2"
    successors_str: str = ""    # "3, 5[AA]"
    cost: str = ""
    parent_id: str = ""         # nur Subtasks: ID des Loop-Tasks
    source: Optional[Union[AnyTask, SubTask]] = None

    @property
    def is_loop(self) -> bool:
        return self.row_type == "loop"

    @property
    def is_subtask(self) -> bool:
        return self.row_type == "subtask"

    @property
    def resource_list(self) -> List[str]:
        return [r.strip() for r in self.resources.split(",") if r.strip()]


def _fmt(value: Any) -> str:
    return "" if value is None else str(value)


def _fmt_resources(resources: Optional[List[str]]) -> str:
    return ", ".join(resources or [])


# ---------------------------------------------------------------------------
# Modell → Zeilen
# ---------------------------------------------------------------------------

def tasks_to_rows(tasks: List[AnyTask]) -> List[TaskRow]:
    """Flacht Project.tasks (inkl. Subtasks) in Tabellenzeilen ab."""
    rows: List[TaskRow] = []
    for task in tasks:
        is_loop = isinstance(task, LoopTask)
        rows.append(TaskRow(
            row_type="loop" if is_loop else "simple",
            id=str(task.id),
            name=task.name,
            duration="" if is_loop else (task.duration or ""),
            resources=_fmt_resources(task.resources),
            successors_str=format_dependencies(task.dependencies),
            cost=_fmt(task.cost),
            source=task,
        ))
        if isinstance(task, LoopTask):
            for sub in task.subtasks:
                rows.append(TaskRow(
                    row_type="subtask",
                    id=sub.id or "",
                    name=sub.name,
                    duration=sub.duration or sub.duration_formula or "",
                    resources=_fmt_resources(sub.resources),
                    parent_id=str(task.id),
                    source=sub,
                ))
    return rows


# ---------------------------------------------------------------------------
# Zeilen → Modell
# ---------------------------------------------------------------------------

def _parse_cost(text: str) -> Optional[float]:
    try:
        return float(text) if text.strip() else None
    except ValueError:
        return None


def _keep_if_unchanged(source: Any, field: str, shown: str, parsed: Any) -> Any:
    """Original-Wert behalten, wenn die Zeile ihn unverändert anzeigt (ID-Typ, None vs. [] …)."""
    if source is None:
        return parsed
    original = getattr(source, field)
    formatted = _fmt_resources(original) if field == "resources" else _fmt(original)
    return original if formatted == shown else parsed


def _row_to_subtask(row: TaskRow) -> SubTask:
    source = row.source if isinstance(row.source, SubTask) else None
    update = {
        "id": row.id or None,
        "name": row.name,
        "resources": _keep_if_unchanged(source, "resources", row.resources, row.resource_list or None),
    }
    # Eine unveränderte Formel bleibt duration_formula, sonst wird der Wert zur Dauer
    if not (source and source.duration_formula and row.duration == source.duration_formula):
        update["duration"] = row.duration or None
    return source.model_copy(update=update) if source else SubTask(**update)


def _row_to_task(row: TaskRow, subtasks: List[SubTask]) -> AnyTask:
    source = row.source if isinstance(row.source, (SimpleTask, InstanceTask, LoopTask)) else None
    if source is not None and row.is_loop != isinstance(source, LoopTask):
        source = None
    update = {
        "id": _keep_if_unchanged(source, "id", row.id, parse_task_id(row.id)),
        "name": row.name,
        "resources": _keep_if_unchanged(source, "resources", row.resources, row.resource_list or None),
        "cost": _keep_if_unchanged(source, "cost", row.cost, _parse_cost(row.cost)),
    }
    task: AnyTask
    if row.is_loop:
        update["subtasks"] = subtasks
        task = source.model_copy(update=update) if source else LoopTask(loop_until="total_volume <= 0", **update)
    else:
        update["duration"] = _keep_if_unchanged(source, "duration", row.duration, row.duration or "0d")
        task = source.model_copy(update=update) if source else SimpleTask(**update)

    if source is None or format_dependencies(source.dependencies) != row.successors_str:
        task.set_dependencies(parse_dependencies(row.successors_str))
    return task


def rows_to_tasks(rows: List[TaskRow]) -> List[AnyTask]:
    """Rekonstruiert Project.tasks aus den Zeilen (verwaiste Subtasks werden ignoriert)."""
    tasks: List[AnyTask] = []
    i = 0
    while i < len(rows):
        row = rows[i]
        i += 1
        if row.is_subtask:
            continue
        subtasks: List[SubTask] = []
        if row.is_loop:
            while i < len(rows) and rows[i].is_subtask and rows[i].parent_id == row.id:
                subtasks.append(_row_to_subtask(rows[i]))
                i += 1
        tasks.append(_row_to_task(row, subtasks))
    return tasks


# ---------------------------------------------------------------------------
# Neue Zeilen
# ---------------------------------------------------------------------------

def next_task_id(rows: List[TaskRow]) -> str:
    numeric = [int(r.id) for r in rows if not r.is_subtask and r.id.isdigit()]
    return str(max(numeric, default=0) + 1)


def new_task_row(rows: List[TaskRow], is_loop: bool, name: str) -> TaskRow:
    return TaskRow(
        row_type="loop" if is_loop else "simple",
        id=next_task_id(rows),
        name=name,
        duration="" if is_loop else "1d",
    )


def new_subtask_row(parent_id: str, name: str) -> TaskRow:
    return TaskRow(row_type="subtask", name=name, parent_id=parent_id)
