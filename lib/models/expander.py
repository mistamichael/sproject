"""
Cycle and Loop expansion logic for Projects
============================================

Provides expansion functionality for InstanceTask and LoopTask.
"""

import ast
import math
import operator
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from ..durations import parse_duration_to_minutes
from .dependencies import SUCCESSOR_FIELDS
from .resources import Resource
from .tasks import InstanceTask, LoopTask, SimpleTask

if TYPE_CHECKING:
    from .project import Project


def generate_cycle_id(task_id: Union[int, str], cycle_number: int, prefix: str) -> str:
    """
    Zyklus-ID im Format "task_id-prefix+cycle_number".

    Examples:
        >>> generate_cycle_id(2, 1, "P")
        '2-P1'
    """
    return f"{task_id}-{prefix}{cycle_number}"


def parse_cycle_id(cycle_id: str) -> tuple:
    """
    Gegenstück zu generate_cycle_id: (task_id, cycle_number, prefix).

    Examples:
        >>> parse_cycle_id("2-P1")
        (2, 1, 'P')
    """
    match = re.match(r'^(.+)-([A-Z]+)(\d+)$', cycle_id)
    if not match:
        return cycle_id, 0, ''
    task_id_str, prefix, number_str = match.groups()
    try:
        task_id: Union[int, str] = int(task_id_str)
    except ValueError:
        task_id = task_id_str
    return task_id, int(number_str), prefix


# =============================================================================
# Projekt-Expansion
# =============================================================================

def expand_project(project: 'Project') -> 'Project':
    """
    Expandiert alle InstanceTasks und LoopTasks eines Projekts in SimpleTasks.

    - Verweise auf einen Instance- oder Loop-Task zeigen danach auf die erste
      Instanz bzw. den ersten Zyklus (die Instanzen sind untereinander verkettet).
    - Bei Projekten mit Personen und resting_times werden Pausen eingefügt.
    - Alle übrigen Projektfelder bleiben erhalten.

    Gibt project unverändert zurück, wenn nichts zu tun ist.
    """
    has_instances = any(isinstance(t, InstanceTask) for t in project.tasks)
    has_loops = any(isinstance(t, LoopTask) for t in project.tasks)
    needs_breaks = bool(project.persons and project.resting_times)
    if not (has_instances or has_loops or needs_breaks):
        return project
    if has_instances and project.order_volume is None:
        raise ValueError("order_volume muss für Cycle-Expansion gesetzt sein")
    if has_loops and project.total_volume is None:
        raise ValueError("total_volume muss für Loop-Expansion gesetzt sein")

    order_volume = project.order_volume or 0
    total_volume = project.total_volume or 0
    expanded: List[SimpleTask] = []
    redirect: Dict[Union[int, str], Union[int, str]] = {}
    for task in project.tasks:
        parts: List[SimpleTask]
        if isinstance(task, InstanceTask):
            parts = expand_instance_task(task, order_volume, project.tasks)
            if parts:
                redirect[task.id] = parts[0].id
        elif isinstance(task, LoopTask):
            parts = expand_loop_task(task, total_volume, project.resources or [])
            if parts:
                redirect[task.id] = parts[0].id
        else:
            parts = [task.model_copy(deep=True)]
        expanded.extend(parts)

    for task in expanded:
        for field in SUCCESSOR_FIELDS.values():
            setattr(task, field, [redirect.get(dep, dep) for dep in getattr(task, field)])

    if needs_breaks:
        from .rest_breaks import insert_rest_breaks
        expanded = insert_rest_breaks(expanded, project)

    return project.model_copy(update={"tasks": expanded})


def expand_instance_task(
    task: InstanceTask,
    order_volume: int,
    all_tasks: List[Union[SimpleTask, InstanceTask, LoopTask]]
) -> List[SimpleTask]:
    """
    Expandiert einen InstanceTask in mehrere SimpleTask-Instanzen.

    Args:
        task: Der zu expandierende InstanceTask
        order_volume: Gesamtanzahl der zu produzierenden Einheiten
        all_tasks: Alle Tasks im Projekt (um Abhängigkeiten zu prüfen)

    Returns:
        Liste von SimpleTask-Instanzen

    Examples:
        >>> task = InstanceTask(id=2, name="Pizza backen", duration="15m", instances="order_volume")
        >>> expanded = expand_instance_task(task, order_volume=12, all_tasks=[])
        >>> len(expanded)
        12
        >>> expanded[0].id
        '2-P1'
    """
    # Bestimme Anzahl Instanzen
    if isinstance(task.instances, str) and task.instances == "order_volume":
        num_instances = order_volume
    else:
        num_instances = int(task.instances)

    prefix = task.cycle_prefix or 'P'
    expanded_tasks: List[SimpleTask] = []

    # Erstelle Dictionary für schnelles Lookup ob ein Task expandiert wird
    instance_task_ids = {
        t.id for t in all_tasks
        if isinstance(t, InstanceTask)
    }

    for cycle_num in range(1, num_instances + 1):
        # Expandiere Nachfolger
        new_successors: List[Union[int, str]] = []
        for dep_id in (task.successors or []):
            if dep_id in instance_task_ids:
                # Nachfolger ist auch ein InstanceTask -> verknüpfe mit gleichem Zyklus
                dep_task = next((t for t in all_tasks if t.id == dep_id), None)
                if dep_task and isinstance(dep_task, InstanceTask):
                    dep_prefix = dep_task.cycle_prefix or 'P'
                    new_successors.append(generate_cycle_id(dep_id, cycle_num, dep_prefix))
                else:
                    new_successors.append(dep_id)
            else:
                new_successors.append(dep_id)

        # Erstelle expandierten Task
        current_cycle_id = generate_cycle_id(task.id, cycle_num, prefix)
        expanded_task = SimpleTask(
            id=current_cycle_id,
            name=task.name,
            duration=task.duration,
            resources=task.resources,
            successors=new_successors,
            # Zusätzliche Metadaten
            original_id=task.id,
            cycle_number=cycle_num,
            cycle_prefix=prefix
        )

        # Verkette Zyklen: Vorgänger-Task bekommt aktuellen als Nachfolger.
        if cycle_num > 1 and expanded_tasks:
            prev_task = expanded_tasks[-1]
            if current_cycle_id not in prev_task.successors:
                prev_task.successors.append(current_cycle_id)

        expanded_tasks.append(expanded_task)

    return expanded_tasks


def expand_loop_task(
    task: LoopTask,
    total_volume: Union[int, float],
    resources: List[Resource]
) -> List[SimpleTask]:
    """
    Expandiert einen LoopTask in mehrere SimpleTask-Iterationen.
    Subtasks werden als separate Tasks expandiert.

    Args:
        task: Der zu expandierende LoopTask
        total_volume: Gesamtvolumen (für loop_until Bedingung)
        resources: Verfügbare Ressourcen (für Kapazitätsberechnung)

    Returns:
        Liste von SimpleTask-Instanzen (Subtasks * Anzahl Loops)

    Examples:
        >>> task = LoopTask(id=3, name="Fahrt", is_loop=True, loop_until="total_volume <= 0")
        >>> resources = [Resource(id="truck", type="truck", capacity=15)]
        >>> expanded = expand_loop_task(task, total_volume=225, resources=resources)
        >>> len(expanded)
        15
    """
    # Berechne Anzahl der Loop-Iterationen
    num_loops = _calculate_loop_count(task, total_volume, resources)

    prefix = task.cycle_prefix or 'F'
    expanded_tasks: List[SimpleTask] = []

    # Falls keine Subtasks definiert sind, erstelle einen zusammengefassten Task (Legacy)
    if not task.subtasks:
        loop_duration = _calculate_loop_duration(task, resources)

        for cycle_num in range(1, num_loops + 1):
            task_resources = _collect_resources_from_subtasks(task, cycle_num)

            successors: List[Union[int, str]] = list(task.successors) if cycle_num == 1 else []

            current_cycle_id = generate_cycle_id(task.id, cycle_num, prefix)
            expanded_task = SimpleTask(
                id=current_cycle_id,
                name=f"{task.name} #{cycle_num}",
                duration=loop_duration,
                resources=task_resources,
                successors=successors,
                original_id=task.id,
                cycle_number=cycle_num,
                cycle_prefix=prefix
            )

            if cycle_num > 1 and expanded_tasks:
                prev_task = expanded_tasks[-1]
                if current_cycle_id not in prev_task.successors:
                    prev_task.successors.append(current_cycle_id)

            expanded_tasks.append(expanded_task)

        return expanded_tasks

    # Neue Logik: Expandiere Subtasks als separate Tasks
    for cycle_num in range(1, num_loops + 1):
        cycle_subtasks: List[SimpleTask] = []

        for subtask_idx, subtask in enumerate(task.subtasks):
            # Berechne Dauer für diesen Subtask
            subtask_duration = _calculate_subtask_duration(subtask, resources)

            # Sammle Ressourcen für diesen Subtask
            subtask_resources = _parse_subtask_resources(subtask, cycle_num)

            # Erstelle Task-ID mit Nummerierung: z.B. "2-P1.1" (Pizza formen & belegen)
            # Falls ID schon im Subtask definiert, verwende diese; sonst generiere Nummer
            if subtask.id:
                subtask_id = subtask.id
            else:
                # Nummeriere Subtasks: P1.1, P1.2, P1.3, etc.
                subtask_id = f"{generate_cycle_id(task.id, cycle_num, prefix)}.{subtask_idx + 1}"

            # Erstelle den Task zunächst ohne Nachfolger
            expanded_task = SimpleTask(
                id=subtask_id,
                name=f"{subtask.name} #{cycle_num}",
                duration=subtask_duration,
                resources=subtask_resources,
                successors=[],  # Wird unten gesetzt
                original_id=task.id,
                cycle_number=cycle_num,
                cycle_prefix=prefix
            )

            # NUR der erste Subtask des ersten Zyklus erbt die Nachfolger des Loop-Tasks
            if cycle_num == 1 and subtask_idx == 0:
                expanded_task.successors = task.successors.copy() if task.successors else []

            # Der vorherige Task soll auf den aktuellen Task zeigen (als Nachfolger)
            if subtask_idx > 0:
                cycle_subtasks[subtask_idx - 1].successors.append(expanded_task.id)
            elif cycle_num > 1 and expanded_tasks:
                # Inter-Cycle Dependency: nur wenn dieselbe Ressource verwendet wird
                # Das ermöglicht Parallelisierung: während Pizza #1 backt, kann Pizza #2 geformt werden
                prev_subtask = task.subtasks[subtask_idx] if subtask_idx < len(task.subtasks) else None
                if prev_subtask:
                    prev_resources = _parse_subtask_resources(prev_subtask, cycle_num - 1)
                    curr_resources = _parse_subtask_resources(subtask, cycle_num)

                    # Vergleiche Ressourcen: erstelle Dependency nur wenn mindestens eine Ressource gleich ist
                    if prev_resources and curr_resources:
                        shared_resources = set(prev_resources) & set(curr_resources)
                        if shared_resources:
                            # Finde den Task des gleichen Subtask-Index aus dem vorherigen Zyklus
                            prev_cycle_id = f"{generate_cycle_id(task.id, cycle_num - 1, prefix)}.{subtask_idx + 1}"
                            # Suche diesen Task in expanded_tasks
                            for earlier_task in reversed(expanded_tasks):
                                if earlier_task.id == prev_cycle_id:
                                    earlier_task.successors.append(expanded_task.id)
                                    break

            cycle_subtasks.append(expanded_task)

        # Füge alle Subtasks dieses Zyklus hinzu
        expanded_tasks.extend(cycle_subtasks)

    return expanded_tasks


def _resolve_resources(specs: Optional[List[str]], cycle_num: int) -> Optional[List[str]]:
    """Löst Ressourcen-Spezifikationen (mit & und |) für einen Zyklus auf, ohne Duplikate."""
    resolved: List[str] = []
    for spec in specs or []:
        resolved.extend(_parse_resource_spec(spec, cycle_num))
    return list(dict.fromkeys(resolved)) or None


def _collect_resources_from_subtasks(task: LoopTask, cycle_num: int = 1) -> Optional[List[str]]:
    """Alle Ressourcen aller Subtasks eines LoopTasks für einen Zyklus."""
    return _resolve_resources([spec for sub in task.subtasks for spec in (sub.resources or [])], cycle_num)


def _parse_resource_spec(spec: str, cycle_num: int) -> List[str]:
    """
    Parst eine Ressourcen-Spezifikation mit & und | Notation.

    Beispiele:
    - "R_PERS3&B1" -> ["R_PERS3", "B1"]
    - "R_PERS1&L1|R_PERS2&L2" -> ["R_PERS1", "L1"] (ungerade Zyklen) oder ["R_PERS2", "L2"] (gerade Zyklen)

    Args:
        spec: Ressourcen-Spezifikation
        cycle_num: Zyklus-Nummer für Rotation

    Returns:
        Liste von Ressourcen-IDs
    """
    # Prüfe auf OR-Notation (|)
    if '|' in spec:
        alternatives = spec.split('|')
        # Rotiere zwischen Alternativen basierend auf Zyklus-Nummer
        selected_idx = (cycle_num - 1) % len(alternatives)
        selected = alternatives[selected_idx].strip()
        # Parse die ausgewählte Alternative
        return _parse_resource_spec(selected, cycle_num)

    # Prüfe auf AND-Notation (&)
    if '&' in spec:
        parts = spec.split('&')
        return [part.strip() for part in parts]

    # Einfache Ressource (keine spezielle Notation)
    return [spec.strip()]


def _calculate_loop_count(
    task: LoopTask,
    total_volume: Union[int, float],
    resources: List[Resource]
) -> int:
    """
    Berechnet die Anzahl der Loop-Iterationen basierend auf loop_until Bedingung.

    Args:
        task: LoopTask mit loop_until Bedingung
        total_volume: Gesamtvolumen
        resources: Verfügbare Ressourcen

    Returns:
        Anzahl der Iterationen
    """
    # 1. Expliziter loop_count hat höchste Priorität
    if task.loop_count is not None:
        return task.loop_count

    loop_until = task.loop_until or ''

    # 2. Parse "total_volume <= 0" Bedingung
    if 'total_volume' in loop_until:
        # 2a. Verwende volume_per_cycle falls angegeben
        if task.volume_per_cycle:
            num_cycles = math.ceil(total_volume / task.volume_per_cycle)
            return max(1, num_cycles)

        # 2b. Hole LKW-Ressourcen (für Erdaushub-ähnliche Projekte)
        trucks = [r for r in resources if r.type == 'truck']

        if trucks:
            # Nimm capacity des ersten LKWs
            truck_capacity = trucks[0].capacity or 15

            # Anzahl Zyklen = total_volume / truck_capacity (aufgerundet)
            num_cycles = math.ceil(total_volume / truck_capacity)

            return max(1, num_cycles)

        # 2c. Fallback wenn keine capacity gefunden
        return max(1, int(total_volume))

    # 3. Fallback: Default 10 Iterationen
    return 10


def _calculate_loop_duration(
    task: LoopTask,
    resources: List[Resource]
) -> str:
    """
    Berechnet die Dauer eines Loop-Zyklus basierend auf Subtasks.

    Args:
        task: LoopTask mit Subtasks
        resources: Verfügbare Ressourcen (für Formeln)

    Returns:
        Dauer als String (z.B. "50m")
    """
    if not task.subtasks:
        return task.duration or '0m'

    # Summiere Subtask-Dauern
    total_minutes = 0.0

    for subtask in task.subtasks:
        # Prüfe auf duration_formula
        if subtask.duration_formula:
            duration = _evaluate_duration_formula(subtask.duration_formula, resources)
            total_minutes += duration
        elif subtask.duration:
            # Parse feste Dauer
            duration_str = subtask.duration
            # Falls es auf resource verweist
            if isinstance(duration_str, str) and 'resource.' in duration_str:
                duration = _evaluate_duration_formula(duration_str, resources)
            else:
                duration = parse_duration_to_minutes(duration_str)
            total_minutes += duration

    return f"{total_minutes:.1f}m"


_TRUCK_ALIASES = {'truck', 'current_truck', 'any_truck'}
_RE_RESOURCE_REF = re.compile(r'resource\.(\w+)\.(\w+)')

_BINARY_OPS: Dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_UNARY_OPS: Dict[type, Callable[[float], float]] = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_arithmetic(expression: str) -> float:
    """Wertet einen reinen Rechenausdruck aus (Zahlen, + - * / **, Klammern) – kein eval()."""
    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            return _BINARY_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Nicht erlaubter Ausdruck: {ast.dump(node)}")
    return _eval(ast.parse(expression, mode='eval'))


def _resource_value(resource_id: str, attr: str, resources: List[Resource]) -> Optional[Any]:
    """Wert von resource.<id>.<attr>; 'truck' & Co. meinen den ersten LKW."""
    if resource_id in _TRUCK_ALIASES:
        resource = next((r for r in resources if r.type == 'truck'), None)
    else:
        resource = next((r for r in resources if r.id == resource_id), None)
    return getattr(resource, attr, 0) if resource is not None else None


def _evaluate_duration_formula(formula: str, resources: List[Resource]) -> float:
    """
    Wertet eine Dauer-Formel in Minuten aus.

    Beispiele:
        "resource.truck.transport_cycle_fixed"                          → Dauer-Wert ("25m" o. ä.)
        "resource.truck.capacity / resource.B1.loading_speed_per_min"   → Rechenausdruck
    """
    simple = re.fullmatch(r'resource\.(\w+)\.(\w+)', formula.strip())
    if simple:
        value = _resource_value(simple.group(1), simple.group(2), resources)
        return parse_duration_to_minutes(value) if value is not None else 0.0

    def _substitute(match: re.Match) -> str:
        value = _resource_value(match.group(1), match.group(2), resources)
        return str(value) if value is not None else match.group(0)

    try:
        return _safe_arithmetic(_RE_RESOURCE_REF.sub(_substitute, formula))
    except (ValueError, SyntaxError, ZeroDivisionError, TypeError):
        return 0.0


def _calculate_subtask_duration(subtask, resources: List[Resource]) -> str:
    """
    Berechnet die Dauer eines einzelnen Subtasks.

    Args:
        subtask: Subtask mit duration oder duration_formula
        resources: Verfügbare Ressourcen

    Returns:
        Dauer als String (z.B. "8.0m", "40m")
    """
    # Prüfe auf duration_formula
    if subtask.duration_formula:
        duration_minutes = _evaluate_duration_formula(subtask.duration_formula, resources)
        return f"{duration_minutes:.1f}m"

    # Prüfe auf duration
    if subtask.duration:
        duration_str = subtask.duration
        # Falls es auf resource verweist
        if isinstance(duration_str, str) and 'resource.' in duration_str:
            duration_minutes = _evaluate_duration_formula(duration_str, resources)
            return f"{duration_minutes:.1f}m"
        else:
            # Direkte Dauer
            return duration_str

    return "0m"


def _parse_subtask_resources(subtask, cycle_num: int) -> Optional[List[str]]:
    """Ressourcen eines Subtasks für einen Zyklus (mit Rotation bei |)."""
    return _resolve_resources(subtask.resources, cycle_num)
