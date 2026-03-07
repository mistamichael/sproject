"""
Cycle and Loop expansion logic for Projects
============================================

Provides expansion functionality for InstanceTask and LoopTask.
"""

from typing import List, Union, Optional, Dict, Any
import math
import re

from .tasks import SimpleTask, InstanceTask, LoopTask
from .resources import Resource

# Import utils - try relative import first, then absolute
try:
    from ..utils import generate_cycle_id, parse_cycle_id
except (ImportError, ValueError):
    from utils import generate_cycle_id, parse_cycle_id


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
    expanded_tasks = []

    # Erstelle Dictionary für schnelles Lookup ob ein Task expandiert wird
    instance_task_ids = {
        t.id for t in all_tasks
        if isinstance(t, InstanceTask)
    }

    for cycle_num in range(1, num_instances + 1):
        # Expandiere Dependencies
        new_dependencies = []
        for dep_id in (task.dependencies or []):
            if dep_id in instance_task_ids:
                # Dependency ist auch ein InstanceTask -> verknüpfe mit gleichem Zyklus
                # Hole Präfix des Dependency-Tasks
                dep_task = next((t for t in all_tasks if t.id == dep_id), None)
                if dep_task and isinstance(dep_task, InstanceTask):
                    dep_prefix = dep_task.cycle_prefix or 'P'
                    new_dependencies.append(generate_cycle_id(dep_id, cycle_num, dep_prefix))
                else:
                    new_dependencies.append(dep_id)
            else:
                # Normale Dependency
                new_dependencies.append(dep_id)

        # Erstelle expandierten Task
        current_cycle_id = generate_cycle_id(task.id, cycle_num, prefix)
        expanded_task = SimpleTask(
            id=current_cycle_id,
            name=task.name,
            duration=task.duration,
            resources=task.resources,
            dependencies=new_dependencies,
            # Zusätzliche Metadaten
            original_id=task.id,
            cycle_number=cycle_num,
            cycle_prefix=prefix
        )

        # Verkette Zyklen: Füge den aktuellen Zyklus als Nachfolger (dependency) des vorherigen hinzu.
        # Da dependencies = Nachfolger (successors), muss der VORHERIGE Task den AKTUELLEN als Nachfolger haben.
        # Falsch wäre: prev_cycle an current's dependencies anfügen (das kehrt die Reihenfolge um).
        if cycle_num > 1 and expanded_tasks:
            prev_task = expanded_tasks[-1]
            if current_cycle_id not in prev_task.dependencies:
                prev_task.dependencies.append(current_cycle_id)

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
    expanded_tasks = []

    # Falls keine Subtasks definiert sind, erstelle einen zusammengefassten Task (Legacy)
    if not task.subtasks:
        loop_duration = _calculate_loop_duration(task, resources)

        for cycle_num in range(1, num_loops + 1):
            task_resources = _collect_resources_from_subtasks(task, cycle_num)

            if cycle_num == 1:
                dependencies = task.dependencies.copy() if task.dependencies else []
            else:
                dependencies = []

            current_cycle_id = generate_cycle_id(task.id, cycle_num, prefix)
            expanded_task = SimpleTask(
                id=current_cycle_id,
                name=f"{task.name} #{cycle_num}",
                duration=loop_duration,
                resources=task_resources,
                dependencies=dependencies,
                original_id=task.id,
                cycle_number=cycle_num,
                cycle_prefix=prefix
            )

            if cycle_num > 1 and expanded_tasks:
                prev_task = expanded_tasks[-1]
                if current_cycle_id not in prev_task.dependencies:
                    prev_task.dependencies.append(current_cycle_id)

            expanded_tasks.append(expanded_task)

        return expanded_tasks

    # Neue Logik: Expandiere Subtasks als separate Tasks
    for cycle_num in range(1, num_loops + 1):
        cycle_subtasks = []

        for subtask_idx, subtask in enumerate(task.subtasks):
            # Berechne Dauer für diesen Subtask
            subtask_duration = _calculate_subtask_duration(subtask, resources)

            # Sammle Ressourcen für diesen Subtask
            subtask_resources = _parse_subtask_resources(subtask, cycle_num)

            # Erstelle Task-ID: z.B. "2-F1-BEL" (Beladen), "2-F1-TRA" (Transport)
            subtask_suffix = subtask.name[:3].upper()
            subtask_id = f"{generate_cycle_id(task.id, cycle_num, prefix)}-{subtask_suffix}"

            # Erstelle den Task zunächst ohne Dependencies
            expanded_task = SimpleTask(
                id=subtask_id,
                name=f"{subtask.name} #{cycle_num}",
                duration=subtask_duration,
                resources=subtask_resources,
                dependencies=[],  # Wird unten gesetzt
                original_id=task.id,
                cycle_number=cycle_num,
                cycle_prefix=prefix
            )

            # Setze Dependencies (Nachfolger!) korrekt:
            # dependencies = Liste der Nachfolger (Tasks die NACH diesem kommen)
            if cycle_num == 1 and subtask_idx == 0:
                # Erster Subtask im ersten Zyklus hat originale Dependencies
                expanded_task.dependencies = task.dependencies.copy() if task.dependencies else []

            # Der vorherige Task soll auf den aktuellen Task zeigen (als Nachfolger)
            if subtask_idx > 0:
                # Vorheriger Subtask im gleichen Zyklus zeigt auf aktuellen
                cycle_subtasks[subtask_idx - 1].dependencies.append(expanded_task.id)
            elif cycle_num > 1 and expanded_tasks:
                # Letzter Subtask des vorherigen Zyklus zeigt auf ersten Subtask des aktuellen
                expanded_tasks[-1].dependencies.append(expanded_task.id)

            cycle_subtasks.append(expanded_task)

        # Füge alle Subtasks dieses Zyklus hinzu
        expanded_tasks.extend(cycle_subtasks)

    return expanded_tasks


def _collect_resources_from_subtasks(task: LoopTask, cycle_num: int = 1) -> Optional[List[str]]:
    """
    Sammelt alle eindeutigen Ressourcen aus den Subtasks eines LoopTasks.

    Unterstützt Notation:
    - "R_PERS1&L1" = R_PERS1 und L1 zusammen
    - "R_PERS1&L1|R_PERS2&L2" = R_PERS1 mit L1 ODER R_PERS2 mit L2 (rotierend)

    Args:
        task: LoopTask mit Subtasks
        cycle_num: Zyklus-Nummer für Rotation von alternativen Ressourcen

    Returns:
        Liste von Ressourcen-IDs oder None
    """
    if not task.subtasks:
        return None

    all_resources = []
    for subtask in task.subtasks:
        if hasattr(subtask, 'resources') and subtask.resources:
            for res_spec in subtask.resources:
                # Parse Ressourcen-Spezifikation
                parsed = _parse_resource_spec(res_spec, cycle_num)
                all_resources.extend(parsed)

    # Entferne Duplikate
    unique_resources = []
    for res_id in all_resources:
        if res_id not in unique_resources:
            unique_resources.append(res_id)

    return unique_resources if unique_resources else None


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
    if hasattr(task, 'loop_count') and task.loop_count is not None:
        return task.loop_count

    loop_until = task.loop_until or ''

    # 2. Parse "total_volume <= 0" Bedingung
    if 'total_volume' in loop_until:
        # 2a. Verwende volume_per_cycle falls angegeben
        if hasattr(task, 'volume_per_cycle') and task.volume_per_cycle:
            num_cycles = math.ceil(total_volume / task.volume_per_cycle)
            return max(1, num_cycles)

        # 2b. Hole LKW-Ressourcen (für Erdaushub-ähnliche Projekte)
        trucks = [r for r in resources if hasattr(r, 'type') and r.type == 'truck']

        if trucks and hasattr(trucks[0], 'capacity'):
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
                duration = _parse_duration_to_minutes(duration_str)
            total_minutes += duration

    return f"{total_minutes:.1f}m"


def _evaluate_duration_formula(formula: str, resources: List[Resource]) -> float:
    """
    Wertet eine Dauer-Formel oder resource-Referenz aus.

    Args:
        formula: String wie "resource.truck.capacity / resource.B1.loading_speed_per_min"
                 oder "resource.truck.transport_cycle_fixed"
        resources: Verfügbare Ressourcen

    Returns:
        Dauer in Minuten
    """
    # Erstelle Resource-Lookup-Dictionary
    resource_dict = {r.id: r for r in resources if r.id}

    # Prüfe auf einfache Referenz ohne Operatoren
    simple_pattern = r'^resource\.(\w+)\.(\w+)$'
    simple_match = re.match(simple_pattern, formula.strip())

    if simple_match:
        resource_id, attr = simple_match.groups()
        # Hole Ressource
        if resource_id in ['truck', 'current_truck', 'any_truck']:
            trucks = [r for r in resources if r.type == 'truck']
            if trucks:
                value = getattr(trucks[0], attr, 0)
                return _parse_duration_to_minutes(value)
        elif resource_id in resource_dict:
            resource = resource_dict[resource_id]
            value = getattr(resource, attr, 0)
            return _parse_duration_to_minutes(value)
        return 0.0

    # Extrahiere Werte aus resources für komplexe Formeln
    pattern = r'resource\.(\w+)\.(\w+)'
    matches = re.findall(pattern, formula)

    # Ersetze durch tatsächliche Werte
    formula_eval = formula
    for resource_id, attr in matches:
        if resource_id in ['truck', 'current_truck', 'any_truck']:
            trucks = [r for r in resources if r.type == 'truck']
            if trucks:
                value = getattr(trucks[0], attr, 0)
                formula_eval = formula_eval.replace(f'resource.{resource_id}.{attr}', str(value))
        elif resource_id in resource_dict:
            resource = resource_dict[resource_id]
            value = getattr(resource, attr, 0)
            formula_eval = formula_eval.replace(f'resource.{resource_id}.{attr}', str(value))

    # Evaluiere Formel
    try:
        result = eval(formula_eval)
        return float(result)
    except:
        return 0.0


def _parse_duration_to_minutes(duration_value: Any) -> float:
    """
    Parst Dauer-Wert zu Minuten.

    Args:
        duration_value: Kann int, float oder str sein

    Returns:
        Dauer in Minuten
    """
    if isinstance(duration_value, (int, float)):
        return float(duration_value)

    duration_str = str(duration_value).strip()

    if duration_str.endswith('m'):
        return float(duration_str[:-1])
    elif duration_str.endswith('h'):
        return float(duration_str[:-1]) * 60
    elif duration_str.endswith('d'):
        return float(duration_str[:-1]) * 8 * 60  # 8h Arbeitstag
    else:
        try:
            return float(duration_str)
        except:
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
    if hasattr(subtask, 'duration_formula') and subtask.duration_formula:
        duration_minutes = _evaluate_duration_formula(subtask.duration_formula, resources)
        return f"{duration_minutes:.1f}m"

    # Prüfe auf duration
    if hasattr(subtask, 'duration') and subtask.duration:
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
    """
    Extrahiert die Ressourcen eines Subtasks mit Rotation.

    Args:
        subtask: Subtask mit resources Feld
        cycle_num: Zyklus-Nummer für Rotation

    Returns:
        Liste von Ressourcen-IDs oder None
    """
    if not hasattr(subtask, 'resources') or not subtask.resources:
        return None

    all_resources = []
    for res_spec in subtask.resources:
        # Parse Ressourcen-Spezifikation (unterstützt & und |)
        parsed = _parse_resource_spec(res_spec, cycle_num)
        all_resources.extend(parsed)

    # Entferne Duplikate
    unique_resources = []
    for res_id in all_resources:
        if res_id not in unique_resources:
            unique_resources.append(res_id)

    return unique_resources if unique_resources else None
