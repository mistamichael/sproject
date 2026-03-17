"""
Markdown Export Generator
==========================

Generiert Markdown-Reports aus CPM-Ergebnissen.
Sektionsreihenfolge und Überschriften werden aus cfg/markdown_export.cfg gelesen.
"""

import configparser
from pathlib import Path
from typing import Optional, Dict, List, Callable
from datetime import datetime

# Import models and utilities
try:
    from .models.cpm import CPMResult, CPMTaskResult
    from .models.project import PersonProject, SimpleProject, CycleProject, LoopProject
    from .models.resources import Resource, Person
    from .utils import format_time_value
    from .mermaid_export import generate_mermaid_gantt
    from .network_diagram import generate_mermaid_network
except (ImportError, ValueError):
    from models.cpm import CPMResult, CPMTaskResult
    from models.project import PersonProject, SimpleProject, CycleProject, LoopProject
    from models.resources import Resource, Person
    from utils import format_time_value
    from mermaid_export import generate_mermaid_gantt
    from network_diagram import generate_mermaid_network


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_DEFAULT_SECTION_ORDER = ['summary', 'critical_path', 'netplan', 'netplan_ascii', 'tasklist', 'gantt_chart']

_DEFAULT_HEADINGS = {
    'summary':       'Projektzusammenfassung',
    'critical_path': 'Kritischer Pfad',
    'netplan':       'Netzplan',
    'netplan_ascii': 'Netzplan ASCII',
    'tasklist':      'Alle Tasks',
    'gantt_chart':   'Gantt Chart (mit Wochenenden)',
    'resource_list': 'Resource List',
}

_DEFAULT_MERMAID = {
    'show_critical_path': True,
    'show_slack':         False,
    'critical_color':     'ff6b6b',
    'critical_border':    'c92a2a',
    'normal_color':       '4472c4',
    'normal_border':      '2f5496',
}

# Standardmäßige Zeilen im Netzplan-Knoten (klassisches Netzplan-Layout)
_DEFAULT_NODE_ROWS = [
    ['faz', 'duration', 'fez'],
    ['id', 'name'],
    ['saz', 'gp', 'sez'],
    ['fp'],
]


def _load_md_config(cfg_dir: Optional[Path] = None) -> tuple:
    """
    Lädt markdown_export.cfg.

    Returns:
        (section_order, headings, mermaid_cfg) mit Fallback auf Defaults.
    """
    if cfg_dir is None:
        cfg_dir = Path(__file__).parent.parent / "cfg"

    cfg_file = cfg_dir / "markdown_export.cfg"
    config = configparser.ConfigParser()
    if cfg_file.exists():
        config.read(cfg_file, encoding='utf-8')

    # Section order
    raw_order = config.get('sections', 'section_order', fallback=None)
    section_order = (
        [s.strip() for s in raw_order.split(',') if s.strip()]
        if raw_order else _DEFAULT_SECTION_ORDER
    )

    # Headings (alle bekannten Schlüssel + alle in [de] definierten)
    headings = dict(_DEFAULT_HEADINGS)
    if config.has_section('de'):
        for key, val in config.items('de'):
            if val:
                headings[key] = val

    # Mermaid netplan config
    mermaid_cfg = dict(_DEFAULT_MERMAID)
    if config.has_section('MermaidNetplan'):
        sec = config['MermaidNetplan']
        mermaid_cfg['show_critical_path'] = sec.getboolean('show_critical_path', _DEFAULT_MERMAID['show_critical_path'])
        mermaid_cfg['show_slack']         = sec.getboolean('show_slack',         _DEFAULT_MERMAID['show_slack'])
        for key in ('critical_color', 'critical_border', 'normal_color', 'normal_border'):
            val = sec.get(key, fallback=None)
            if val:
                mermaid_cfg[key] = val

    # Netzplan-Knoten Inhalt (konfigurierbare Zeilen)
    node_rows = [list(row) for row in _DEFAULT_NODE_ROWS]
    if config.has_section('netplan_content'):
        sec = config['netplan_content']
        parsed_rows = []
        i = 1
        while True:
            val = sec.get(f'row_{i}', fallback=None)
            if val is None:
                break
            fields = [f.strip().lower() for f in val.split(',') if f.strip()]
            if fields:
                parsed_rows.append(fields)
            i += 1
        if parsed_rows:
            node_rows = parsed_rows
    mermaid_cfg['node_rows'] = node_rows

    return section_order, headings, mermaid_cfg


# ---------------------------------------------------------------------------
# Individual section generators
# ---------------------------------------------------------------------------

def _generate_summary_section(result: CPMResult, project_name: str, heading: str) -> str:
    lines = [f"### {heading}", ""]
    lines.append(f"- **Projekt:** {project_name}")
    lines.append(f"- **Projektdauer:** {result.project_duration}")

    if result.project_start:
        start_str = (
            result.project_start.strftime('%Y-%m-%d %H:%M')
            if isinstance(result.project_start, datetime)
            else str(result.project_start)
        )
        lines.append(f"- **Startdatum:** {start_str}")

        if result.tasks:
            max_sez = max(task.sez for task in result.tasks.values())
            if max_sez > 0:
                from datetime import timedelta
                estimated_end = result.project_start + timedelta(days=max_sez)
                lines.append(f"- **Enddatum (geschätzt):** {estimated_end.strftime('%Y-%m-%d %H:%M')}")

    lines.append(f"- **Zeiteinheit:** {result.time_unit}")
    lines.append(f"- **Anzahl Tasks:** {len(result.tasks)}")

    critical_tasks = [t for t in result.tasks.values() if t.is_critical]
    lines.append(f"- **Kritische Tasks:** {len(critical_tasks)}")
    lines.append("")
    return "\n".join(lines)


def _generate_critical_path_section(result: CPMResult, heading: str) -> str:
    lines = [f"### {heading}", ""]

    if result.critical_path:
        cp_tasks = [result.tasks[tid] for tid in result.critical_path if tid in result.tasks]
        if cp_tasks:
            lines.append("Der kritische Pfad besteht aus folgenden Tasks:")
            lines.append("")
            for task in cp_tasks:
                duration = format_time_value(task.duration, result.time_unit)
                lines.append(f"- **[{task.id}]** {task.name} (Dauer: {duration})")
        else:
            lines.append("*Keine kritischen Tasks gefunden.*")
    else:
        lines.append("*Kein kritischer Pfad vorhanden.*")

    lines.append("")
    return "\n".join(lines)


def _generate_netplan_section(result: CPMResult, heading: str, mermaid_cfg: dict) -> str:
    lines = [f"### {heading}", ""]

    diagram = _build_mermaid_network(result, mermaid_cfg)
    lines.append("```mermaid")
    lines.append(diagram)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _generate_netplan_ascii_section(result: CPMResult, heading: str, mermaid_cfg: dict) -> str:
    """
    Generiert einen ASCII-Netzplan aus dem CPM-Ergebnis.

    Tasks werden nach topologischen Stufen (längster Pfad vom Start) gruppiert.
    Jeder Task erscheint als Box mit konfigurierbarem Inhalt (node_rows aus mermaid_cfg).
    Nachfolger werden mit einem Pfeil unterhalb der Box aufgelistet.
    Kritische Tasks werden mit [*] markiert.
    """
    from collections import defaultdict

    lines = [f"### {heading}", ""]

    def _is_blocker(tid) -> bool:
        return isinstance(tid, str) and tid.startswith('WE-')

    task_ids = [tid for tid in result.tasks if not _is_blocker(tid)]
    node_rows = mermaid_cfg.get('node_rows', _DEFAULT_NODE_ROWS)
    tu = result.time_unit

    # ----------------------------------------------------------------
    # Stufen-Berechnung: Länge des längsten Pfads vom Startknoten
    # ----------------------------------------------------------------
    levels: dict = {}

    def get_level(tid):
        if tid in levels:
            return levels[tid]
        task = result.tasks[tid]
        preds = [p for p in task.predecessors if p in result.tasks and not _is_blocker(p)]
        levels[tid] = 0 if not preds else max(get_level(p) for p in preds) + 1
        return levels[tid]

    for tid in task_ids:
        get_level(tid)

    by_level: dict = defaultdict(list)
    for tid, lvl in levels.items():
        by_level[lvl].append(tid)
    for lvl in by_level:
        by_level[lvl].sort(key=lambda t: result.tasks[t].faz)

    # ----------------------------------------------------------------
    # Box-Renderer
    # ----------------------------------------------------------------
    def _field_str(field: str, task) -> str:
        f = field.lower()
        if f == 'id':
            return f"[{task.id}]"
        elif f == 'name':
            return task.name
        elif f in ('d', 'duration', 'dauer'):
            return f"D:{format_time_value(task.duration, tu)}"
        elif f == 'faz':
            return f"FAZ:{format_time_value(task.faz, tu)}"
        elif f == 'fez':
            return f"FEZ:{format_time_value(task.fez, tu)}"
        elif f == 'saz':
            return f"SAZ:{format_time_value(task.saz, tu)}"
        elif f == 'sez':
            return f"SEZ:{format_time_value(task.sez, tu)}"
        elif f == 'gp':
            return f"GP:{format_time_value(task.puffer, tu)}"
        elif f == 'fp':
            return f"FP:{format_time_value(task.free_puffer, tu)}"
        return ''

    def render_box(tid, task) -> List[str]:
        crit = " [*]" if task.is_critical else ""
        header = f" [{tid}] {task.name}{crit}"

        # id und name stehen bereits im Box-Header → in Content-Zeilen überspringen
        _header_fields = {'id', 'name'}
        content_lines = []
        for row in node_rows:
            parts = [_field_str(f, task) for f in row if f.lower() not in _header_fields]
            parts = [p for p in parts if p]
            if parts:
                content_lines.append("  " + "  ".join(parts))

        width = max(len(header), *(len(cl) for cl in content_lines), 0) + 2
        sep = "+" + "-" * width + "+"
        box = [sep, "|" + header.ljust(width) + "|"]
        if content_lines:
            box.append("|" + " " * width + "|")
            for cl in content_lines:
                box.append("|" + cl.ljust(width) + "|")
        box.append(sep)
        return box

    # ----------------------------------------------------------------
    # Ausgabe
    # ----------------------------------------------------------------
    ascii_lines = ["[*] = Kritischer Pfad", ""]

    max_level = max(by_level.keys()) if by_level else 0
    for lvl in sorted(by_level.keys()):
        ascii_lines.append(f"--- Stufe {lvl} " + "-" * 50)
        ascii_lines.append("")
        for tid in by_level[lvl]:
            task = result.tasks[tid]
            ascii_lines.extend(render_box(tid, task))

            succs = [s for s in task.successors if s in result.tasks and not _is_blocker(s)]
            if succs:
                ascii_lines.append("  |")
                for succ_id in succs:
                    succ_name = result.tasks[succ_id].name
                    ascii_lines.append(f"  +--> [{succ_id}] {succ_name}")
            ascii_lines.append("")
        if lvl < max_level:
            ascii_lines.append("")

    lines.append("```")
    lines.extend(ascii_lines)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _build_mermaid_network(result: CPMResult, mermaid_cfg: dict) -> str:
    """
    Erzeugt einen Mermaid flowchart mit ID + Name in den Knoten
    und typisierten Pfeilen für die Abhängigkeiten:
      EA (Ende→Anfang, Standard): -->
      AA (Anfang→Anfang):         ==>  (dicke Linie)
      EE (Ende→Ende):             --o  (Kreis-Ende)
      AE (Anfang→Ende):           -.-> (gestrichelt)
    """
    show_critical = mermaid_cfg['show_critical_path']
    show_slack    = mermaid_cfg['show_slack']
    crit_color    = mermaid_cfg['critical_color']
    crit_border   = mermaid_cfg['critical_border']
    norm_color    = mermaid_cfg['normal_color']
    norm_border   = mermaid_cfg['normal_border']

    node_rows = mermaid_cfg.get('node_rows', _DEFAULT_NODE_ROWS)

    def _field_value(field: str, task, task_id) -> str:
        """Gibt den formatierten Wert für ein Knoten-Feld zurück."""
        f = field.lower()
        tu = result.time_unit
        if f == 'id':
            return f"[{task_id}]"
        elif f == 'name':
            return task.name
        elif f in ('d', 'duration', 'dauer'):
            return f"D:{format_time_value(task.duration, tu)}"
        elif f == 'faz':
            return f"FAZ:{format_time_value(task.faz, tu)}"
        elif f == 'fez':
            return f"FEZ:{format_time_value(task.fez, tu)}"
        elif f == 'saz':
            return f"SAZ:{format_time_value(task.saz, tu)}"
        elif f == 'sez':
            return f"SEZ:{format_time_value(task.sez, tu)}"
        elif f == 'gp':
            return f"GP:{format_time_value(task.puffer, tu)}"
        elif f == 'fp':
            return f"FP:{format_time_value(task.free_puffer, tu)}"
        return ''

    def _build_label(task, task_id) -> str:
        row_strings = []
        for row in node_rows:
            parts = [_field_value(f, task, task_id) for f in row]
            parts = [p for p in parts if p]
            if parts:
                row_strings.append(' | '.join(parts))
        return '<br/>'.join(row_strings)

    lines = ["graph TD", ""]

    # Knoten
    for task_id, task in result.tasks.items():
        if isinstance(task_id, str) and task_id.startswith('WE-'):
            continue

        label = _build_label(task, task_id)

        if show_critical and task.is_critical:
            lines.append(f'    N{task_id}["<b>{label}</b>"]:::critical')
        else:
            lines.append(f'    N{task_id}["{label}"]')

    lines.append("")

    # Kanten — nach Beziehungstyp
    # Mermaid-Syntax:
    #   EA: A --> B          (solid, Pfeilspitze)
    #   AA: A ==> B          (dick, Pfeilspitze)
    #   EE: A --o B          (solid, Kreis)
    #   AE: A -.-> B         (gestrichelt, Pfeilspitze)
    def _is_blocker(tid) -> bool:
        return isinstance(tid, str) and tid.startswith('WE-')

    for task_id, task in result.tasks.items():
        if _is_blocker(task_id):
            continue

        edges = [
            (task.successors_ea, '-->'),
            (task.successors_aa, '==>'),
            (task.successors_ee, '--o'),
            (task.successors_ae, '-..->'),
        ]
        for succ_list, arrow in edges:
            for succ_id in succ_list:
                if _is_blocker(succ_id) or succ_id not in result.tasks:
                    continue
                lines.append(f'    N{task_id} {arrow} N{succ_id}')

    lines.append("")
    lines.append(f'    classDef critical fill:#{crit_color},stroke:#{crit_border},color:#fff,stroke-width:3px')
    lines.append(f'    classDef normal   fill:#{norm_color},stroke:#{norm_border},color:#fff')

    return "\n".join(lines)


def _generate_tasklist_section(result: CPMResult, heading: str) -> str:
    lines = [f"### {heading}", ""]
    lines.append("| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")

    for task_id, task in result.tasks.items():
        duration = format_time_value(task.duration, result.time_unit)
        faz = format_time_value(task.faz, result.time_unit)
        fez = format_time_value(task.fez, result.time_unit)
        saz = format_time_value(task.saz, result.time_unit)
        sez = format_time_value(task.sez, result.time_unit)
        gp  = format_time_value(task.puffer,      result.time_unit)
        fp  = format_time_value(task.free_puffer,  result.time_unit)
        krit = "JA" if task.is_critical else ""
        name = task.name if len(task.name) <= 35 else task.name[:32] + "..."
        lines.append(f"| {task_id} | {name} | {duration} | {faz} | {fez} | {saz} | {sez} | {gp} | {fp} | {krit} |")

    lines.append("")
    return "\n".join(lines)


def _generate_gantt_chart_section(result: CPMResult, project_name: str, heading: str) -> str:
    lines = [f"### {heading}", ""]
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
    start_date: Optional[datetime] = None,
    resource_color: Optional[str] = None
) -> str:
    from datetime import timedelta

    lines = []
    if resource_color:
        color = resource_color if len(resource_color) >= 6 else f"00{resource_color}"
        lines.append(f"%%{{init: {{'theme': 'base', 'themeVariables': {{'taskBkgColor': '#{color}', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}}}}%%")
    lines.append("gantt")
    lines.append(f"    title Ressourcen-Auslastung: {resource_name}")

    time_unit = getattr(result, 'time_unit', 'days')

    if time_unit in ('minutes', 'hours'):
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %H:%M")
    else:
        lines.append("    dateFormat  YYYY-MM-DD")
        lines.append("    axisFormat  %d.%m")

    if start_date:
        excludes = []
        if getattr(result, 'skip_weekends', True):
            excludes.append("weekends")
        if getattr(result, 'skip_holidays', False) and getattr(result, 'holidays', None):
            excludes.extend(sorted(result.holidays))
        if excludes:
            lines.append(f"    excludes    {', '.join(excludes)}")

    lines.append("")

    resource_tasks = []
    for task_id in task_ids:
        if str(task_id) in result.tasks:
            task = result.tasks[str(task_id)]
            resource_tasks.append((str(task_id), task.name, task.faz, task.fez))
    resource_tasks.sort(key=lambda x: x[2])

    lines.append(f"    section {resource_name}")
    lines.append("")

    for idx, (task_id, task_name, faz, fez) in enumerate(resource_tasks):
        short_name = task_name if len(task_name) <= 25 else task_name[:22] + "..."

        if start_date:
            if time_unit == 'minutes':
                total_minutes_start = faz * 480
                total_minutes_end   = fez * 480
                days_start    = int(total_minutes_start // 480)
                minutes_start = int(total_minutes_start % 480)
                days_end      = int(total_minutes_end   // 480)
                minutes_end   = int(total_minutes_end   % 480)
                task_start = start_date + timedelta(days=days_start, minutes=minutes_start)
                task_end   = start_date + timedelta(days=days_end,   minutes=minutes_end)
                start_str = task_start.strftime('%Y-%m-%d %H:%M')
                end_str   = task_end.strftime('%Y-%m-%d %H:%M')
            elif time_unit == 'hours':
                total_hours_start = faz * 8
                total_hours_end   = fez * 8
                days_start  = int(total_hours_start // 8)
                hours_start = int(total_hours_start % 8)
                days_end    = int(total_hours_end   // 8)
                hours_end   = int(total_hours_end   % 8)
                task_start = start_date + timedelta(days=days_start, hours=hours_start)
                task_end   = start_date + timedelta(days=days_end,   hours=hours_end)
                start_str = task_start.strftime('%Y-%m-%d %H:%M')
                end_str   = task_end.strftime('%Y-%m-%d %H:%M')
            else:
                task_start = start_date + timedelta(days=faz)
                task_end   = start_date + timedelta(days=fez)
                start_str  = task_start.strftime("%Y-%m-%d")
                end_str    = task_end.strftime("%Y-%m-%d")

            lines.append(f"    {short_name:<27} :t{idx}, {start_str}, {end_str}")
        else:
            duration = int(fez - faz)
            if idx == 0:
                lines.append(f"    {short_name:<27} :t{idx}, {duration}d")
            else:
                lines.append(f"    {short_name:<27} :after t{idx - 1}, {duration}d")

    return "\n".join(lines)


def _generate_resource_list_section(
    result: CPMResult,
    heading: str,
    project: Optional[object] = None
) -> str:
    lines = [f"### {heading}", ""]

    resource_usage: Dict[str, List[str]] = {}

    for task_id, task in result.tasks.items():
        if project and hasattr(project, 'tasks'):
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

    resource_names: Dict[str, str] = {}
    resource_colors: Dict[str, str] = {}
    if project and hasattr(project, 'resources'):
        for res in project.resources:
            resource_names[res.id] = getattr(res, 'name', res.id)
            if hasattr(res, 'color') and res.color:
                resource_colors[res.id] = res.color

    lines.append("#### Ressourcenauslastung (Textform)")
    lines.append("")
    lines.append("| Farbe | Ressource | Anzahl Tasks | Tasks |")
    lines.append("|---|---|---|---|")

    for res_id in sorted(resource_usage.keys()):
        task_ids   = resource_usage[res_id]
        task_list  = ", ".join(task_ids[:10])
        if len(task_ids) > 10:
            task_list += f" ... (+{len(task_ids) - 10} weitere)"
        resource_name = resource_names.get(res_id, res_id)
        color = resource_colors.get(res_id)
        if color:
            color_hex    = color if len(color) >= 6 else f"00{color}"
            color_marker = f'<span style="background-color:#{color_hex};padding:2px 6px;color:#fff;border-radius:3px;">■</span>'
        else:
            color_marker = '—'
        lines.append(f"| {color_marker} | {resource_name} ({res_id}) | {len(task_ids)} | {task_list} |")

    lines.append("")
    lines.append("#### Ressourcenauslastung (Gantt-Diagramm)")
    lines.append("")

    for res_id in sorted(resource_usage.keys()):
        task_ids      = resource_usage[res_id]
        resource_name = resource_names.get(res_id, res_id)
        resource_color = resource_colors.get(res_id)

        gantt_chart = _generate_resource_gantt_chart(
            res_id, resource_name, task_ids, result,
            result.project_start, resource_color
        )
        lines.append("```mermaid")
        lines.append(gantt_chart)
        lines.append("```")
        lines.append("")

    if project and isinstance(project, PersonProject):
        lines.append("#### Personen")
        lines.append("")
        lines.append("| Person | Kosten/Stunde | Verfügbarkeit |")
        lines.append("|---|---|---|")
        for person in project.persons:
            cost  = f"{person.cost_per_hour}€/h" if hasattr(person, 'cost_per_hour') and person.cost_per_hour else "n/a"
            avail = f"{person.available_hours}h"  if hasattr(person, 'available_hours') and person.available_hours else "n/a"
            lines.append(f"| {person.name} | {cost} | {avail} |")
        lines.append("")

        if project.resources:
            lines.append("#### Ressourcen-Details")
            lines.append("")
            lines.append("| Ressource | Person | Typ |")
            lines.append("|---|---|---|")
            for res in project.resources:
                person_name = ""
                if hasattr(res, 'person_id') and res.person_id:
                    for person in project.persons:
                        if person.id == res.person_id:
                            person_name = person.name
                            break
                res_type = getattr(res, 'type', 'n/a')
                res_name = getattr(res, 'name', res.id)
                lines.append(f"| {res_name} ({res.id}) | {person_name} | {res_type} |")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public export function
# ---------------------------------------------------------------------------

def export_cpm_to_markdown(
    result: CPMResult,
    output_path: Path,
    project_name: str = "Project",
    project: Optional[object] = None,
    cfg_dir: Optional[Path] = None
) -> bool:
    """
    Exportiert CPM-Ergebnisse als Markdown-Datei.

    Sektionsreihenfolge und Überschriften werden aus cfg/markdown_export.cfg gelesen.

    Args:
        result:       CPM Berechnungsergebnis
        output_path:  Pfad zur Ausgabe-Markdown-Datei
        project_name: Projektname
        project:      Projekt-Objekt (optional, für Ressourcen-Details)
        cfg_dir:      Verzeichnis der Konfigurationsdateien (default: cfg/)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        section_order, headings, mermaid_cfg = _load_md_config(cfg_dir)

        # Section-Generator-Registry
        def make_sections(result, project_name, project, headings, mermaid_cfg):
            return {
                'summary':       lambda: _generate_summary_section(result, project_name, headings['summary']),
                'critical_path': lambda: _generate_critical_path_section(result, headings['critical_path']),
                'netplan':       lambda: _generate_netplan_section(result, headings['netplan'], mermaid_cfg),
                'netplan_ascii': lambda: _generate_netplan_ascii_section(result, headings.get('netplan_ascii', 'Netzplan ASCII'), mermaid_cfg),
                'tasklist':      lambda: _generate_tasklist_section(result, headings['tasklist']),
                'gantt_chart':   lambda: _generate_gantt_chart_section(result, project_name, headings['gantt_chart']),
                'resource_list': lambda: _generate_resource_list_section(result, headings['resource_list'], project),
            }

        generators = make_sections(result, project_name, project, headings, mermaid_cfg)

        lines = []
        lines.append(f"# {project_name} - CPM Report")
        lines.append("")
        lines.append(f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Wrap everything in one top-level section
        lines.append("## CPM Analyse")
        lines.append("")

        for i, section_name in enumerate(section_order):
            if section_name not in generators:
                print(f"WARNUNG: Unbekannte Sektion '{section_name}' – wird übersprungen.")
                continue
            lines.append(generators[section_name]())
            if i < len(section_order) - 1:
                lines.append("---")
                lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"INFO: Markdown erfolgreich exportiert nach: {output_path}")
        return True

    except Exception as e:
        print(f"FEHLER: Markdown-Export fehlgeschlagen: {e}")
        return False
