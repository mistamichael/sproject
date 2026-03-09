"""
Markdown Export Generator
==========================

Generiert Markdown-Reports aus CPM-Ergebnissen mit drei Abschnitten:
1. CPM Analyse (Projektzusammenfassung, kritischer Pfad, Knoten)
2. Gantt Chart (als Mermaid-Diagramm)
3. Resource List (Ressourcenauslastung)
"""

from pathlib import Path
from typing import Optional, Dict, List, Set
from datetime import datetime

# Import models and utilities
try:
    from .models.cpm import CPMResult, CPMTaskResult
    from .models.project import PersonProject, SimpleProject, CycleProject, LoopProject
    from .models.resources import Resource, Person
    from .utils import format_time_value
    from .mermaid_export import generate_mermaid_gantt
    from .network_diagram import generate_network_text, generate_mermaid_network
except (ImportError, ValueError):
    from models.cpm import CPMResult, CPMTaskResult
    from models.project import PersonProject, SimpleProject, CycleProject, LoopProject
    from models.resources import Resource, Person
    from utils import format_time_value
    from mermaid_export import generate_mermaid_gantt
    from network_diagram import generate_network_text, generate_mermaid_network


def _format_node_box(task: CPMTaskResult, time_unit: str = 'days') -> str:
    """
    Formatiert einen CPM-Knoten als Text-Box mit 3 Zeilen:
    Zeile 1: ID | Name | Dauer
    Zeile 2: FAZ | GP | FEZ
    Zeile 3: SAZ | FP | SEZ

    Args:
        task: CPM Task Result
        time_unit: Zeiteinheit für Formatierung

    Returns:
        Formatierter Text-Box String
    """
    # Formatiere Werte
    duration = format_time_value(task.duration, time_unit)
    faz = format_time_value(task.faz, time_unit)
    fez = format_time_value(task.fez, time_unit)
    saz = format_time_value(task.saz, time_unit)
    sez = format_time_value(task.sez, time_unit)
    gp = format_time_value(task.puffer, time_unit)  # Gesamtpuffer
    fp = format_time_value(task.free_puffer, time_unit)  # Freier Puffer

    # Kürze Namen falls zu lang
    name = task.name if len(task.name) <= 40 else task.name[:37] + "..."

    return f"""```
┌─────────────────────────────────────────────┐
│ ID: {str(task.id):<10} │ {name:<30} │
│ Dauer: {duration:<36} │
├─────────────────────────────────────────────┤
│ FAZ: {faz:<10} │ GP: {gp:<10} │ FEZ: {fez:<10} │
├─────────────────────────────────────────────┤
│ SAZ: {saz:<10} │ FP: {fp:<10} │ SEZ: {sez:<10} │
└─────────────────────────────────────────────┘
```"""


def _generate_cpm_analyse_section(result: CPMResult, project_name: str = "Project") -> str:
    """
    Generiert die CPM Analyse Sektion mit Projektzusammenfassung und Knoten.

    Args:
        result: CPM Berechnungsergebnis
        project_name: Projektname

    Returns:
        Markdown-formatierter CPM Analyse Text
    """
    lines = []
    lines.append("## CPM Analyse")
    lines.append("")

    # Projektzusammenfassung
    lines.append("### Projektzusammenfassung")
    lines.append("")
    lines.append(f"- **Projekt:** {project_name}")
    lines.append(f"- **Projektdauer:** {result.project_duration}")

    if result.project_start:
        start_str = result.project_start.strftime('%Y-%m-%d %H:%M') if isinstance(result.project_start, datetime) else str(result.project_start)
        lines.append(f"- **Startdatum:** {start_str}")

        # Berechne geschätztes Enddatum falls möglich
        if result.tasks:
            max_sez = max(task.sez for task in result.tasks.values())
            if max_sez > 0:
                from datetime import timedelta
                estimated_end = result.project_start + timedelta(days=max_sez)
                end_str = estimated_end.strftime('%Y-%m-%d %H:%M')
                lines.append(f"- **Enddatum (geschätzt):** {end_str}")

    lines.append(f"- **Zeiteinheit:** {result.time_unit}")
    lines.append(f"- **Anzahl Tasks:** {len(result.tasks)}")

    # Kritischer Pfad
    critical_tasks = [task for task in result.tasks.values() if task.is_critical]
    lines.append(f"- **Kritische Tasks:** {len(critical_tasks)}")
    lines.append("")

    # Kritischer Pfad Details
    lines.append("### Kritischer Pfad")
    lines.append("")

    if result.critical_path:
        critical_path_tasks = [result.tasks[tid] for tid in result.critical_path if tid in result.tasks]

        if critical_path_tasks:
            lines.append("Der kritische Pfad besteht aus folgenden Tasks:")
            lines.append("")
            for task in critical_path_tasks:
                duration = format_time_value(task.duration, result.time_unit)
                lines.append(f"- **[{task.id}]** {task.name} (Dauer: {duration})")
        else:
            lines.append("*Keine kritischen Tasks gefunden.*")
    else:
        lines.append("*Kein kritischer Pfad vorhanden.*")

    lines.append("")

    # Netzplan (Dependency Graph)
    if result.tasks:
        lines.append("### Netzplan")
        lines.append("")

        # Text-basierter Netzplan mit Dauer und Zeiten
        network_text = generate_network_text(result, include_duration=True, include_times=True)
        # Entferne die erste Zeile "### Netzplan" da wir sie schon hinzugefügt haben
        network_lines = network_text.split('\n')[2:]
        lines.extend(network_lines)
        lines.append("")

    # Alle Tasks Tabelle
    lines.append("### Alle Tasks")
    lines.append("")
    lines.append("| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")

    for task_id, task in result.tasks.items():
        duration = format_time_value(task.duration, result.time_unit)
        faz = format_time_value(task.faz, result.time_unit)
        fez = format_time_value(task.fez, result.time_unit)
        saz = format_time_value(task.saz, result.time_unit)
        sez = format_time_value(task.sez, result.time_unit)
        gp = format_time_value(task.puffer, result.time_unit)  # Gesamtpuffer
        fp = format_time_value(task.free_puffer, result.time_unit)  # Freier Puffer
        krit = "JA" if task.is_critical else ""

        # Kürze Name für Tabelle
        name = task.name if len(task.name) <= 35 else task.name[:32] + "..."

        lines.append(f"| {task_id} | {name} | {duration} | {faz} | {fez} | {saz} | {sez} | {gp} | {fp} | {krit} |")

    lines.append("")

    return "\n".join(lines)


def _generate_gantt_chart_section(result: CPMResult, project_name: str = "Project") -> str:
    """
    Generiert die Gantt Chart Sektion mit Mermaid-Diagramm (mit Wochenenden).

    Args:
        result: CPM Berechnungsergebnis
        project_name: Projektname

    Returns:
        Markdown-formatierter Gantt Chart Text
    """
    lines = []
    lines.append("## Gantt Chart (mit Wochenenden)")
    lines.append("")

    # Generiere Mermaid Gantt
    mermaid_diagram = generate_mermaid_gantt(result, project_name)

    lines.append("```mermaid")
    lines.append(mermaid_diagram)
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def _generate_resource_gantt_chart(
    resource_id: str,
    resource_name: str,
    task_ids: List[str],
    result: CPMResult,
    start_date: Optional[datetime] = None
) -> str:
    """
    Generiert ein Mermaid Gantt-Diagramm für eine einzelne Ressource mit adäquater Zeitauflösung.

    Args:
        resource_id: ID der Ressource
        resource_name: Name der Ressource
        task_ids: Liste der Task-IDs für diese Ressource
        result: CPM Berechnungsergebnis
        start_date: Startdatum des Projekts (optional)

    Returns:
        Mermaid Gantt-Diagramm als String
    """
    from datetime import timedelta

    lines = []
    lines.append("gantt")
    lines.append(f"    title Ressourcen-Auslastung: {resource_name}")

    # Bestimme Zeit-Einheit (wie in generate_mermaid_gantt)
    time_unit = getattr(result, 'time_unit', 'days')

    # Setze dateFormat und axisFormat basierend auf time_unit
    if time_unit == 'minutes':
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %H:%M")
    elif time_unit == 'hours':
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %H:%M")
    else:  # 'days'
        lines.append("    dateFormat  YYYY-MM-DD")
        lines.append("    axisFormat  %d.%m")

    lines.append("")

    # Sammle und sortiere Tasks für diese Ressource nach FAZ
    resource_tasks = []
    for task_id in task_ids:
        if str(task_id) in result.tasks:
            task = result.tasks[str(task_id)]
            resource_tasks.append((str(task_id), task.name, task.faz, task.fez))

    # Sortiere nach FAZ (Anfangszeit)
    resource_tasks.sort(key=lambda x: x[2])

    lines.append(f"    section {resource_name}")
    lines.append("")

    # Generiere Task-Einträge
    for idx, (task_id, task_name, faz, fez) in enumerate(resource_tasks):
        # Kürze Namen falls zu lang
        short_name = task_name if len(task_name) <= 25 else task_name[:22] + "..."

        if start_date:
            # Berechne absolute Daten basierend auf time_unit
            if time_unit == 'minutes':
                # FAZ/FEZ sind in Tagen, aber Auflösung ist Minuten
                # Berechne die Minuten-Offset innerhalb des Tages
                total_minutes_start = faz * 480  # 1 Tag = 480 Minuten (8h * 60)
                total_minutes_end = fez * 480

                # Extrahiere Tage und Minuten
                days_start = int(total_minutes_start // 480)
                minutes_start = int(total_minutes_start % 480)
                days_end = int(total_minutes_end // 480)
                minutes_end = int(total_minutes_end % 480)

                # Berechne DateTime
                task_start = start_date + timedelta(days=days_start, minutes=minutes_start)
                task_end = start_date + timedelta(days=days_end, minutes=minutes_end)

                # Formatiere mit Uhrzeit
                start_str = task_start.strftime('%Y-%m-%d %H:%M')
                end_str = task_end.strftime('%Y-%m-%d %H:%M')

            elif time_unit == 'hours':
                # FAZ/FEZ sind in Tagen, aber Auflösung ist Stunden
                # 1 Tag = 8 Stunden
                total_hours_start = faz * 8
                total_hours_end = fez * 8

                # Extrahiere Tage und Stunden
                days_start = int(total_hours_start // 8)
                hours_start = int(total_hours_start % 8)
                days_end = int(total_hours_end // 8)
                hours_end = int(total_hours_end % 8)

                # Berechne DateTime
                task_start = start_date + timedelta(days=days_start, hours=hours_start)
                task_end = start_date + timedelta(days=days_end, hours=hours_end)

                # Formatiere mit Uhrzeit
                start_str = task_start.strftime('%Y-%m-%d %H:%M')
                end_str = task_end.strftime('%Y-%m-%d %H:%M')

            else:  # 'days'
                task_start = start_date + timedelta(days=faz)
                task_end = start_date + timedelta(days=fez)

                start_str = task_start.strftime("%Y-%m-%d")
                end_str = task_end.strftime("%Y-%m-%d")

            # Generiere eindeutige ID
            task_ref = f"t{idx}"
            lines.append(f"    {short_name:<27} :{task_ref}, {start_str}, {end_str}")
        else:
            # Verwende relative Zeiten (Tage)
            duration = int(fez - faz)

            if idx == 0:
                lines.append(f"    {short_name:<27} :t{idx}, {duration}d")
            else:
                lines.append(f"    {short_name:<27} :after t{idx - 1}, {duration}d")

    return "\n".join(lines)


def _generate_resource_list_section(
    result: CPMResult,
    project: Optional[object] = None
) -> str:
    """
    Generiert die Resource List Sektion mit Ressourcenauslastung.

    Args:
        result: CPM Berechnungsergebnis
        project: Projekt-Objekt (optional, für detaillierte Ressourceninfos)

    Returns:
        Markdown-formatierter Resource List Text
    """
    lines = []
    lines.append("## Resource List")
    lines.append("")

    # Sammle alle verwendeten Ressourcen aus Tasks
    resource_usage: Dict[str, List[str]] = {}  # resource_id -> [task_ids]

    for task_id, task in result.tasks.items():
        # Hole resources aus dem ursprünglichen Project (falls verfügbar)
        if project and hasattr(project, 'tasks'):
            # Finde den originalen Task
            original_task = None
            for orig_task in project.tasks:
                if str(orig_task.id) == str(task_id) or str(getattr(orig_task, 'original_id', None)) == str(task_id):
                    original_task = orig_task
                    break

            if original_task and hasattr(original_task, 'resources') and original_task.resources:
                for res_id in original_task.resources:
                    if res_id not in resource_usage:
                        resource_usage[res_id] = []
                    resource_usage[res_id].append(str(task_id))

    if not resource_usage:
        lines.append("*Keine Ressourcen-Informationen verfügbar.*")
        lines.append("")
        return "\n".join(lines)

    # Erstelle Ressourcen-Tabelle
    lines.append("### Ressourcenauslastung (Textform)")
    lines.append("")
    lines.append("| Ressource | Anzahl Tasks | Tasks |")
    lines.append("|---|---|---|")

    for res_id in sorted(resource_usage.keys()):
        task_ids = resource_usage[res_id]
        task_count = len(task_ids)
        task_list = ", ".join(task_ids[:10])  # Zeige max 10 Tasks
        if len(task_ids) > 10:
            task_list += f" ... (+{len(task_ids) - 10} weitere)"

        lines.append(f"| {res_id} | {task_count} | {task_list} |")

    lines.append("")

    # Generiere Gantt-Diagramme für jede Ressource
    lines.append("### Ressourcenauslastung (Gantt-Diagramm)")
    lines.append("")

    # Hole Ressourcen-Namen aus Project falls verfügbar
    resource_names: Dict[str, str] = {}
    if project and hasattr(project, 'resources'):
        for res in project.resources:
            resource_names[res.id] = getattr(res, 'name', res.id)

    # Generiere Gantt für jede Ressource
    for res_id in sorted(resource_usage.keys()):
        task_ids = resource_usage[res_id]
        resource_name = resource_names.get(res_id, res_id)

        # Generiere Gantt-Diagramm
        gantt_chart = _generate_resource_gantt_chart(
            res_id,
            resource_name,
            task_ids,
            result,
            result.project_start
        )

        lines.append("```mermaid")
        lines.append(gantt_chart)
        lines.append("```")
        lines.append("")

    # Falls PersonProject: Zeige Personen-Details
    if project and isinstance(project, PersonProject):
        lines.append("### Personen")
        lines.append("")
        lines.append("| Person | Kosten/Stunde | Verfügbarkeit |")
        lines.append("|---|---|---|")

        for person in project.persons:
            cost = f"{person.cost_per_hour}€/h" if hasattr(person, 'cost_per_hour') and person.cost_per_hour else "n/a"
            avail = f"{person.available_hours}h" if hasattr(person, 'available_hours') and person.available_hours else "n/a"
            lines.append(f"| {person.name} | {cost} | {avail} |")

        lines.append("")

        # Ressourcen mit Person-Zuordnung
        if project.resources:
            lines.append("### Ressourcen-Details")
            lines.append("")
            lines.append("| Ressource | Person | Typ |")
            lines.append("|---|---|---|")

            for res in project.resources:
                person_name = ""
                if hasattr(res, 'person_id') and res.person_id:
                    # Finde Person
                    for person in project.persons:
                        if person.id == res.person_id:
                            person_name = person.name
                            break

                res_type = getattr(res, 'type', 'n/a')
                lines.append(f"| {res.id} | {person_name} | {res_type} |")

            lines.append("")

    return "\n".join(lines)


def export_cpm_to_markdown(
    result: CPMResult,
    output_path: Path,
    project_name: str = "Project",
    project: Optional[object] = None
) -> bool:
    """
    Exportiert CPM-Ergebnisse als Markdown-Datei mit drei Sektionen:
    1. CPM Analyse
    2. Gantt Chart
    3. Resource List

    Args:
        result: CPM Berechnungsergebnis
        output_path: Pfad zur Ausgabe-Markdown-Datei
        project_name: Projektname
        project: Projekt-Objekt (optional, für Ressourcen-Details)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        lines = []

        # Titel
        lines.append(f"# {project_name} - CPM Report")
        lines.append("")
        lines.append(f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. CPM Analyse
        lines.append(_generate_cpm_analyse_section(result, project_name))
        lines.append("")
        lines.append("---")
        lines.append("")

        # 2. Gantt Chart
        lines.append(_generate_gantt_chart_section(result, project_name))
        lines.append("")
        lines.append("---")
        lines.append("")

        # 3. Resource List
        lines.append(_generate_resource_list_section(result, project))

        # Schreibe Datei
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"INFO: Markdown erfolgreich exportiert nach: {output_path}")
        return True

    except Exception as e:
        print(f"FEHLER: Markdown-Export fehlgeschlagen: {e}")
        return False
