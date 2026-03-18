"""
Network Diagram Generator (PERT/CPM Network)
=============================================

Generiert einen Netzplan (Dependency Graph) aus CPM-Ergebnissen
mit Auflistung von Task-IDs, Dauer und Abhängigkeiten.
"""

from typing import Dict, List, Set, Union, Tuple
from models.cpm import CPMResult, CPMTaskResult


def _format_duration(duration: float, time_unit: str = 'days') -> str:
    """Formatiert Dauer in der gegebenen Zeiteinheit"""
    if time_unit == 'minutes':
        return f"{int(duration)}m"
    elif time_unit == 'hours':
        return f"{duration:.1f}h"
    else:  # days
        return f"{duration:.0f}d"


def generate_mermaid_network(
    result: CPMResult,
    show_critical_path: bool = True,
    show_slack: bool = True
) -> str:
    """
    Generiert einen Mermaid-Flowchart für den Netzplan.

    Args:
        result: CPMResult mit berechneten Tasks
        show_critical_path: Markiere kritische Tasks
        show_slack: Zeige Puffer-Informationen

    Returns:
        Mermaid-Diagramm als String
    """
    lines = []
    lines.append("graph TD")
    lines.append("")

    # Erstelle Node-Definitionen
    for task_id, task in result.tasks.items():
        # Skip Blocker-Tasks (Wochenenden)
        if isinstance(task_id, str) and task_id.startswith('WE-'):
            continue

        # Format: [ID] Task Name
        duration = _format_duration(task.duration, result.time_unit)
        label = f"[{task_id}]<br/>{task.name}<br/>({duration})"

        if show_slack and task.puffer > 0:
            puffer = _format_duration(task.puffer, result.time_unit)
            label += f"<br/>GP: {puffer}"

        # Formatiere Node basierend auf kritischheit
        if task.is_critical and show_critical_path:
            # Kritischer Task: rote Box
            lines.append(f'    N{task_id}["<b>{label}</b>"]:::critical')
        else:
            # Normaler Task: blaue Box
            lines.append(f'    N{task_id}["{label}"]')

    lines.append("")

    # Erstelle Edges (Abhängigkeiten)
    for task_id, task in result.tasks.items():
        # Skip Blocker-Tasks
        if isinstance(task_id, str) and task_id.startswith('WE-'):
            continue

        for succ_id in task.successors:
            # Skip Blocker-Tasks
            if isinstance(succ_id, str) and succ_id.startswith('WE-'):
                continue

            if succ_id in result.tasks:
                # Edge-Style basierend auf kritischheit
                source_critical = task.is_critical
                target_critical = result.tasks[succ_id].is_critical

                if source_critical and target_critical:
                    # Beider kritisch: dicke rote Linie
                    lines.append(f'    N{task_id} -->|critical| N{succ_id}')
                else:
                    # Normal: dünne Linie
                    lines.append(f'    N{task_id} --> N{succ_id}')

    lines.append("")

    # Styling
    lines.append('    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px')
    lines.append('    classDef normal fill:#4472c4,stroke:#2f5496,color:#fff')

    return "\n".join(lines)


def generate_network_csv(result: CPMResult) -> str:
    """
    Generiert Netzplan-Daten im CSV-Format.

    Args:
        result: CPMResult mit berechneten Tasks

    Returns:
        CSV-Daten als String
    """
    lines = []
    lines.append("TaskID,Task Name,Duration,FAZ,FEZ,SAZ,SEZ,GP,FP,Successors,IsCritical")

    sorted_tasks = sorted(
        result.tasks.items(),
        key=lambda x: x[1].faz
    )

    for task_id, task in sorted_tasks:
        # Skip Blocker-Tasks
        if isinstance(task_id, str) and task_id.startswith('WE-'):
            continue

        successors = ";".join(str(s) for s in task.successors if not (isinstance(s, str) and s.startswith('WE-')))
        is_critical = "JA" if task.is_critical else "NEIN"

        line = f'"{task_id}","{task.name}",{task.duration:.1f},{task.faz:.1f},{task.fez:.1f},{task.saz:.1f},{task.sez:.1f},{task.puffer:.1f},{task.free_puffer:.1f},"{successors}",{is_critical}'
        lines.append(line)

    return "\n".join(lines)
