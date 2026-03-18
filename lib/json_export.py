"""
JSON Export Generator
=====================

Generiert konfigurierbaren JSON-Output aus CPM-Ergebnissen.
Welche Sektionen exportiert werden, steuert cfg/json_export.cfg.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from .models.cpm import CPMResult
    from .utils import format_time_value, add_workdays, is_system_task, load_export_config
except (ImportError, ValueError):
    from models.cpm import CPMResult
    from utils import format_time_value, add_workdays, is_system_task, load_export_config


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

_DEFAULT_SECTION_ORDER = [
    'summary', 'critical_path', 'tasks', 'gantt_chart', 'resource_list', 'cost_overview', 'settings'
]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_json_config(cfg_dir: Optional[Path] = None) -> List[str]:
    """Lädt json_export.cfg und gibt die section_order zurück."""
    section_order, _ = load_export_config(
        cfg_dir, 'json_export.cfg', _DEFAULT_SECTION_ORDER, {}
    )
    return section_order


# ---------------------------------------------------------------------------
# Section builders (return dict, not string)
# ---------------------------------------------------------------------------

def _build_summary(result: CPMResult, project_name: str) -> Dict[str, Any]:
    """Projektmetadaten aus result.export_to_dict() plus berechnete Felder."""
    base = result.export_to_dict(include_dates=False)
    data: Dict[str, Any] = {
        'project':          project_name,
        'project_duration': base.get('project_duration', ''),
        'time_unit':        result.time_unit,
        'num_tasks':        len([t for t in result.tasks.values()
                                 if not t.is_break and not is_system_task(t.id)]),
        'num_critical':     len([t for t in result.tasks.values() if t.is_critical]),
    }
    if base.get('project_start'):
        data['project_start'] = base['project_start']
        project_duration = max(task.fez for task in result.tasks.values())
        data['project_end'] = add_workdays(result.project_start, project_duration).strftime('%Y-%m-%d')
    if base.get('calculation_date'):
        data['calculation_date'] = base['calculation_date']
    return data


def _build_critical_path(result: CPMResult) -> List[Dict[str, Any]]:
    """Kritischer Pfad aus result.critical_path mit Namen und Dauer."""
    out = []
    for tid in result.critical_path:
        if tid not in result.tasks:
            continue
        task = result.tasks[tid]
        if task.is_break or is_system_task(tid):
            continue
        out.append({
            'id':       str(tid),
            'name':     task.name,
            'duration': format_time_value(task.duration, result.time_unit),
        })
    return out


def _build_tasks(result: CPMResult) -> List[Dict[str, Any]]:
    """
    Nutzt result.export_to_dict() als Basis und gibt nur die Tasks-Liste zurück.
    Die Felder D/FB/FE/SB/SE/GP/FP aus export_to_dict werden auf
    duration/faz/fez/saz/sez/gp/fp umbenannt für lesbarere JSON-Keys.
    """
    base = result.export_to_dict(include_dates=True)
    out = []
    for t in base.get('tasks', []):
        cpm_raw = t.get('cpm', {})
        entry: Dict[str, Any] = {
            'id':          str(t['id']),
            'name':        t['name'],
            'duration':    t.get('duration'),
            'is_critical': cpm_raw.get('is_critical', False),
            'cpm': {
                'faz': cpm_raw.get('FB'),
                'fez': cpm_raw.get('FE'),
                'saz': cpm_raw.get('SB'),
                'sez': cpm_raw.get('SE'),
                'gp':  cpm_raw.get('GP'),
                'fp':  cpm_raw.get('FP'),
            },
        }
        if 'dates' in cpm_raw:
            dates = cpm_raw['dates']
            entry['cpm']['dates'] = {
                'faz_date': dates.get('fb_date'),
                'fez_date': dates.get('fe_date'),
                'saz_date': dates.get('sb_date'),
                'sez_date': dates.get('se_date'),
            }
        out.append(entry)
    return out


def _build_resources(result: CPMResult, project: Optional[object]) -> Optional[Dict[str, Any]]:
    if not project or not hasattr(project, 'tasks'):
        return None

    resource_usage: Dict[str, List[str]] = {}
    for orig_task in project.tasks:
        if hasattr(orig_task, 'resources') and orig_task.resources:
            for res_id in orig_task.resources:
                resource_usage.setdefault(res_id, []).append(str(orig_task.id))

    if not resource_usage:
        return None

    resource_details: Dict[str, Any] = {}
    if hasattr(project, 'resources'):
        for res in project.resources:
            resource_details[res.id] = {
                'name': getattr(res, 'name', res.id),
                'type': getattr(res, 'type', 'unknown'),
            }
            if hasattr(res, 'person_id') and res.person_id:
                resource_details[res.id]['person_id'] = res.person_id

    persons_out: List[Dict[str, Any]] = []
    if project and project.persons:
        for person in project.persons:
            p: Dict[str, Any] = {'id': person.id, 'name': person.name}
            if getattr(person, 'cost_per_hour', None):
                p['cost_per_hour'] = person.cost_per_hour
            if getattr(person, 'available_hours', None):
                p['available_hours'] = person.available_hours
            persons_out.append(p)

    assignments = []
    for res_id, task_ids in sorted(resource_usage.items()):
        assignments.append({
            'resource_id':   res_id,
            'resource_name': resource_details.get(res_id, {}).get('name', res_id),
            'task_ids':      task_ids,
        })

    out: Dict[str, Any] = {'assignments': assignments}
    if resource_details:
        out['resources'] = list(resource_details.values())
    if persons_out:
        out['persons'] = persons_out
    return out


def _build_costs(result: CPMResult, project: Optional[object]) -> Optional[Dict[str, Any]]:
    """Kostenrechnung als JSON-Objekt."""
    try:
        from cost_calculator import calculate_project_costs
    except ImportError:
        try:
            from .cost_calculator import calculate_project_costs
        except ImportError:
            return None

    costs = calculate_project_costs(project, result)
    if not costs:
        return None

    entries = []
    for e in costs.entries:
        entries.append({
            'resource_id':         e.resource_id,
            'resource_name':       e.resource_name,
            'resource_type':       e.resource_type,
            'hours_worked':        e.hours_worked,
            'hourly_rate':         e.hourly_rate,
            'provisioning_costs':  e.provisioning_costs,
            'labor_costs':         e.labor_costs,
            'total_costs':         e.total_costs,
        })

    return {
        'entries':                  entries,
        'total_person_costs':       costs.total_person_costs,
        'total_machine_costs':      costs.total_machine_costs,
        'total_provisioning_costs': costs.total_provisioning_costs,
        'total_costs':              costs.total_costs,
    }


def _build_settings(result: CPMResult) -> Dict[str, Any]:
    return {
        'skip_weekends': result.skip_weekends,
        'skip_holidays': result.skip_holidays,
        'holidays':      sorted(result.holidays) if result.holidays else [],
    }


# ---------------------------------------------------------------------------
# Public export function
# ---------------------------------------------------------------------------

def export_cpm_to_json(
    result: CPMResult,
    output_path: Path,
    project_name: Optional[str] = None,
    project: Optional[object] = None,
    cfg_dir: Optional[Path] = None,
    gantt_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Exportiert CPM-Ergebnisse als strukturierte JSON-Datei.

    Welche Sektionen enthalten sind, steuert cfg/json_export.cfg.

    Args:
        result:       CPM-Berechnungsergebnis
        output_path:  Pfad zur Ausgabe-JSON-Datei
        project_name: Projektname (default: result.project_name)
        project:      Projekt-Objekt (optional, für Ressourcen-Details)
        cfg_dir:      Verzeichnis der Konfigurationsdateien (default: cfg/)
        gantt_data:   Optionaler Gantt-Schedule (Phase 2, aus GanttCalculator)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        section_order = _load_json_config(cfg_dir)
        name = project_name or result.project_name

        output: Dict[str, Any] = {}

        section_builders = {
            'summary':        lambda: _build_summary(result, name),
            'critical_path':  lambda: _build_critical_path(result),
            'tasks':          lambda: _build_tasks(result),
            'gantt_chart':    lambda: gantt_data,
            'resource_list':  lambda: _build_resources(result, project),
            'cost_overview':  lambda: _build_costs(result, project),
            'settings':       lambda: _build_settings(result),
        }

        for section in section_order:
            if section not in section_builders:
                print(f"WARNUNG: Unbekannte JSON-Sektion '{section}' – wird übersprungen.")
                continue
            value = section_builders[section]()
            if value is not None:
                output[section] = value

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)

        print(f"INFO: JSON erfolgreich exportiert nach: {output_path}")
        return True

    except Exception as e:
        print(f"FEHLER: JSON-Export fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
