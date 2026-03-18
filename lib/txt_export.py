"""
TXT Export Generator
====================

Generiert ASCII-Text-Reports aus CPM-Ergebnissen.
Sektionsreihenfolge und Überschriften werden aus cfg/txt_export.cfg gelesen.
"""

import csv
import io
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    from .models.cpm import CPMResult
    from .utils import format_time_value, format_time_value_auto, add_workdays, is_system_task, load_export_config
except (ImportError, ValueError):
    from models.cpm import CPMResult  # type: ignore[no-redef]
    from utils import format_time_value, format_time_value_auto, add_workdays, is_system_task, load_export_config  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

_SEP_WIDE  = "=" * 70
_SEP_THIN  = "-" * 70

_DEFAULT_SECTION_ORDER = ['summary', 'critical_path', 'netplan', 'tasklist', 'resource_list', 'cost_overview']

_DEFAULT_HEADINGS = {
    'summary':       'PROJEKTZUSAMMENFASSUNG',
    'critical_path': 'KRITISCHER PFAD',
    'netplan': 'NETZPLAN TABELLE',
    'tasklist':      'ALLE TASKS',
    'resource_list': 'VERANTWORTLICHE',
    'cost_overview': 'KOSTENÜBERSICHT',
}


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_txt_config(cfg_dir: Optional[Path] = None) -> tuple:
    """
    Lädt txt_export.cfg.

    Returns:
        (section_order, headings)
    """
    section_order, headings = load_export_config(
        cfg_dir, 'txt_export.cfg', _DEFAULT_SECTION_ORDER, _DEFAULT_HEADINGS
    )
    # [de]-Überschriften groß schreiben wie die Defaults
    headings = {k: v.upper() for k, v in headings.items()}
    return section_order, headings


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def _section_header(heading: str) -> List[str]:
    return [_SEP_WIDE, heading, _SEP_WIDE, ""]


def _generate_summary(result: CPMResult, project_name: str, heading: str) -> List[str]:
    lines = _section_header(heading)
    project_duration = max(task.fez for task in result.tasks.values())
    lines.append(f"Projekt:            {project_name}")
    lines.append(f"Projektdauer:       {format_time_value_auto(project_duration)}")
    lines.append(f"Zeiteinheit:        {result.time_unit}")
    if result.project_start:
        end_date = add_workdays(result.project_start, project_duration)
        lines.append(f"Startdatum:         {result.project_start.strftime('%Y-%m-%d')}")
        lines.append(f"Enddatum:           {end_date.strftime('%Y-%m-%d')}")
    non_break = [t for t in result.tasks.values()
                 if not t.is_break and not is_system_task(t.id)]
    lines.append(f"Anzahl Tasks:       {len(non_break)}")
    lines.append(f"Kritische Tasks:    {len([t for t in non_break if t.is_critical])}")
    if result.calculation_date:
        lines.append(f"Erstellt am:        {result.calculation_date.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    return lines


def _generate_critical_path(result: CPMResult, heading: str) -> List[str]:
    lines = _section_header(heading)
    if result.critical_path:
        cp_tasks = [result.tasks[tid] for tid in result.critical_path
                    if tid in result.tasks
                    and not is_system_task(tid)
                    and not result.tasks[tid].is_break]
        if cp_tasks:
            for task in cp_tasks:
                dur = format_time_value(task.duration, result.time_unit)
                lines.append(f"  [{task.id}] {task.name:<35} Dauer: {dur}")
        else:
            lines.append("  (keine kritischen Tasks gefunden)")
    else:
        lines.append("  (kein kritischer Pfad vorhanden)")
    lines.append("")
    return lines


def _generate_netplan(result: CPMResult, heading: str) -> List[str]:
    """
    Tabellarische Netzplandarstellung via generate_network_csv.
    Enthält zusätzlich die Nachfolger-Spalte gegenüber der tasklist.
    """
    lines = _section_header(heading)

    col_id   = 7
    col_name = 30
    col_val  = 8
    col_succ = 20

    header = (f"{'ID':<{col_id}} {'Name':<{col_name}} {'Dauer':<{col_val}} "
              f"{'FAZ':<{col_val}} {'FEZ':<{col_val}} "
              f"{'SAZ':<{col_val}} {'SEZ':<{col_val}} "
              f"{'GP':<{col_val}} {'FP':<{col_val}} "
              f"{'Nachfolger':<{col_succ}} Krit.")
    lines.append(header)
    lines.append(_SEP_THIN)

    csv_text = result.to_network_csv()
    reader = csv.reader(io.StringIO(csv_text))
    next(reader)  # CSV-Header überspringen

    for parts in reader:
        if len(parts) < 11:
            continue
        tid, name, dur, faz, fez, saz, sez, gp, fp, successors, is_crit = parts[:11]

        name_out = name if len(name) <= col_name else name[:col_name - 3] + "..."
        succ_out = successors.replace(';', ', ')
        if len(succ_out) > col_succ:
            succ_out = succ_out[:col_succ - 3] + "..."

        lines.append(
            f"{tid:<{col_id}} {name_out:<{col_name}} "
            f"{float(dur):<{col_val}.1f} "
            f"{float(faz):<{col_val}.1f} "
            f"{float(fez):<{col_val}.1f} "
            f"{float(saz):<{col_val}.1f} "
            f"{float(sez):<{col_val}.1f} "
            f"{float(gp):<{col_val}.1f} "
            f"{float(fp):<{col_val}.1f} "
            f"{succ_out:<{col_succ}} "
            f"{'JA' if is_crit == 'JA' else ''}"
        )

    lines.append(_SEP_THIN)
    lines.append("")
    return lines


def _generate_tasklist(result: CPMResult, heading: str) -> List[str]:
    lines = _section_header(heading)
    tu = result.time_unit

    col_id   = 7
    col_name = 30
    col_val  = 8

    header = (f"{'ID':<{col_id}} {'Name':<{col_name}} {'Dauer':<{col_val}} "
              f"{'FAZ':<{col_val}} {'FEZ':<{col_val}} "
              f"{'SAZ':<{col_val}} {'SEZ':<{col_val}} "
              f"{'GP':<{col_val}} {'FP':<{col_val}} Krit.")
    lines.append(header)
    lines.append(_SEP_THIN)

    task_ids = sorted(
        [tid for tid in result.tasks
         if not is_system_task(tid)
         and not result.tasks[tid].is_break],
        key=lambda x: result.tasks[x].faz
    )

    for tid in task_ids:
        task = result.tasks[tid]
        name = task.name if len(task.name) <= col_name else task.name[:col_name - 3] + "..."
        lines.append(
            f"{str(tid):<{col_id}} {name:<{col_name}} "
            f"{format_time_value(task.duration, tu):<{col_val}} "
            f"{format_time_value(task.faz, tu):<{col_val}} "
            f"{format_time_value(task.fez, tu):<{col_val}} "
            f"{format_time_value(task.saz, tu):<{col_val}} "
            f"{format_time_value(task.sez, tu):<{col_val}} "
            f"{format_time_value(task.puffer, tu):<{col_val}} "
            f"{format_time_value(task.free_puffer, tu):<{col_val}} "
            f"{'JA' if task.is_critical else ''}"
        )

    lines.append(_SEP_THIN)
    lines.append("")
    return lines


def _generate_cost_overview(result: CPMResult, heading: str,
                            project: Optional[Any] = None) -> List[str]:
    """Kostenübersicht auf Basis von Personen-/Ressourcen-Stundensätzen."""
    lines = _section_header(heading)

    try:
        from cost_calculator import calculate_project_costs
    except ImportError:
        try:
            from .cost_calculator import calculate_project_costs
        except ImportError:
            lines.append("  (Kostenberechnung nicht verfügbar)")
            lines.append("")
            return lines

    costs = calculate_project_costs(project, result)
    if not costs:
        lines.append("  (keine Kostendaten – Stundensätze fehlen)")
        lines.append("")
        return lines

    col_name  = 28
    col_h     =  8
    col_rate  =  9
    col_prov  = 12
    col_labor = 13
    col_total = 13

    header = (
        f"  {'Ressource':<{col_name}} {'Stunden':>{col_h}} {'€/h':>{col_rate}} "
        f"{'Bereitst.€':>{col_prov}} {'Lohnkosten€':>{col_labor}} {'Gesamt €':>{col_total}}"
    )
    lines.append(header)
    lines.append("  " + _SEP_THIN)

    for e in costs.entries:
        lines.append(
            f"  {e.resource_name:<{col_name}} "
            f"{e.hours_worked:>{col_h}.1f} "
            f"{e.hourly_rate:>{col_rate}.2f} "
            f"{e.provisioning_costs:>{col_prov}.2f} "
            f"{e.labor_costs:>{col_labor}.2f} "
            f"{e.total_costs:>{col_total}.2f}"
        )

    lines.append("  " + _SEP_THIN)
    pad = col_name + col_h + col_rate + 4
    if costs.total_person_costs > 0:
        lines.append(
            f"  {'Personalkosten:':<{pad}} "
            f"{'':>{col_prov}} {'':>{col_labor}} {costs.total_person_costs:>{col_total}.2f}"
        )
    if costs.total_machine_costs > 0:
        lines.append(
            f"  {'Maschinenkosten (Lohn):':<{pad}} "
            f"{'':>{col_prov}} {costs.total_machine_costs:>{col_labor}.2f} {'':>{col_total}}"
        )
    if costs.total_provisioning_costs > 0:
        lines.append(
            f"  {'Bereitstellungskosten:':<{pad}} "
            f"{costs.total_provisioning_costs:>{col_prov}.2f} {'':>{col_labor}} {'':>{col_total}}"
        )
    lines.append("  " + _SEP_THIN)
    lines.append(
        f"  {'GESAMTKOSTEN:':<{pad}} "
        f"{'':>{col_prov}} {'':>{col_labor}} {costs.total_costs:>{col_total}.2f} €"
    )
    lines.append("")
    return lines


def _generate_resource_list(result: CPMResult, heading: str,
                             project: Optional[Any] = None) -> List[str]:
    lines = _section_header(heading)

    if not project or not hasattr(project, 'tasks'):
        lines.append("  (keine Ressourcen-Informationen verfügbar)")
        lines.append("")
        return lines

    # Ressourcen-Zuordnung aus den Projekt-Tasks aufbauen
    resource_usage: Dict[str, List[str]] = {}
    for orig_task in project.tasks:
        if hasattr(orig_task, 'resources') and orig_task.resources:
            for res_id in orig_task.resources:
                resource_usage.setdefault(res_id, []).append(str(orig_task.id))

    if not resource_usage:
        lines.append("  (keine Ressourcen-Zuordnungen gefunden)")
        lines.append("")
        return lines

    resource_names: Dict[str, str] = {}
    if project and hasattr(project, 'resources'):
        for res in project.resources:
            resource_names[res.id] = getattr(res, 'name', res.id)

    tu = result.time_unit
    col_res  = 25
    col_task = 8
    col_val  = 8

    header = f"  {'Ressource':<{col_res}} {'Tasks':<{col_task*3}}  {'Frühester Start':<{col_val*2}}"
    lines.append(header)
    lines.append("  " + _SEP_THIN)

    for res_id in sorted(resource_usage.keys()):
        task_ids      = resource_usage[res_id]
        res_name      = resource_names.get(res_id, res_id)
        task_ids_str  = ", ".join(task_ids[:8])
        if len(task_ids) > 8:
            task_ids_str += f" (+{len(task_ids) - 8})"
        lines.append(f"  {res_name:<{col_res}} [{task_ids_str}]")

        # Detail: Tasks mit Zeitwerten
        for tid_str in task_ids:
            if tid_str in result.tasks:
                t = result.tasks[tid_str]
                lines.append(
                    f"    [{tid_str}] {t.name[:28]:<28}  "
                    f"FAZ: {format_time_value(t.faz, tu):<8} "
                    f"FEZ: {format_time_value(t.fez, tu):<8} "
                    f"{'KRIT' if t.is_critical else ''}"
                )
        lines.append("")

    if project and project.persons:
        lines.append(_SEP_THIN)
        lines.append("Personen:")
        lines.append("")
        for person in project.persons:
            cost  = f"{person.cost_per_hour}€/h" if getattr(person, 'cost_per_hour', None) else "n/a"
            avail = f"{person.available_hours}h"  if getattr(person, 'available_hours', None) else "n/a"
            lines.append(f"  {person.name:<25} Kosten: {cost:<10} Verfügbar: {avail}")
        lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Public export function
# ---------------------------------------------------------------------------

def export_cpm_to_txt(
    result: CPMResult,
    output_path: Path,
    project_name: Optional[str] = None,
    project: Optional[object] = None,
    cfg_dir: Optional[Path] = None,
) -> bool:
    """
    Exportiert CPM-Ergebnisse als strukturierte ASCII-Textdatei.

    Sektionsreihenfolge und Überschriften werden aus cfg/txt_export.cfg gelesen.

    Args:
        result:       CPM-Berechnungsergebnis
        output_path:  Pfad zur Ausgabe-TXT-Datei
        project_name: Projektname (default: result.project_name)
        project:      Projekt-Objekt (optional, für Ressourcen-Details)
        cfg_dir:      Verzeichnis der Konfigurationsdateien (default: cfg/)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        section_order, headings = _load_txt_config(cfg_dir)
        name = project_name or result.project_name

        generators = {
            'summary':       lambda: _generate_summary(result, name, headings['summary']),
            'critical_path': lambda: _generate_critical_path(result, headings['critical_path']),
            'netplan': lambda: _generate_netplan(result, headings['netplan']),
            'tasklist':      lambda: _generate_tasklist(result, headings['tasklist']),
            'resource_list': lambda: _generate_resource_list(result, headings['resource_list'], project),
            'cost_overview': lambda: _generate_cost_overview(result, headings['cost_overview'], project),
        }

        all_lines: List[str] = []
        all_lines.append(_SEP_WIDE)
        all_lines.append(f"{name} - CPM REPORT")
        all_lines.append(f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        all_lines.append(_SEP_WIDE)
        all_lines.append("")

        for section_name in section_order:
            if section_name not in generators:
                print(f"WARNUNG: Unbekannte Sektion '{section_name}' – wird übersprungen.")
                continue
            all_lines.extend(generators[section_name]())

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_lines))

        print(f"INFO: TXT erfolgreich exportiert nach: {output_path}")
        return True

    except Exception as e:
        print(f"FEHLER: TXT-Export fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
