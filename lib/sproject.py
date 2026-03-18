#!/usr/bin/env python3
"""
Projekt Rechner
Erzeugt aus den Angaben zu Resourcen, Urlaubstagen und Projekt-Angaben Reports,
wie z.B. einen Resourcenplan über der Zeit, ein Gant-Diagramm mit kritischen Pfad oder einen Kostenplan
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from excel_reports import (
    load_excel_export_config,
    create_summary_sheet,
    create_critical_path_sheet,
    create_tasklist_sheet,
    create_netplan_table_sheet,
)
from mermaid_export import export_cpm_to_svg
from markdown_export import export_cpm_to_markdown
from txt_export import export_cpm_to_txt as _txt_export
from json_export import export_cpm_to_json as _json_export
from models.resources import Person
from models.cpm import CPMResult
from models.gantt import GanttCalculator


def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Richtet Logging ein mit Ausgabe in Datei und Konsole.

    Args:
        log_dir: Verzeichnis für Logdateien (nutzt %PV_LOG% falls gesetzt)

    Returns:
        Konfigurierter Logger
    """
    if log_dir is None:
        log_dir_str = os.environ.get("PV_LOG", "log")
        log_dir = Path(log_dir_str)

    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"sproject_{timestamp}.log"

    logger = logging.getLogger("sproject")
    logger.setLevel(logging.DEBUG)

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialisiert: {log_file}")
    return logger


def find_project_files(data_dir: Path) -> List[Path]:
    """
    Findet alle project*.json und *.json Dateien im data Verzeichnis.

    Args:
        data_dir: Verzeichnis zum Durchsuchen

    Returns:
        Liste von Pfaden zu Projektdateien
    """
    if not data_dir.exists():
        return []

    # Suche zuerst nach project*.json, dann nach allen *.json
    project_files = list(data_dir.glob("project*.json"))
    if not project_files:
        project_files = list(data_dir.glob("*.json"))

    return project_files


def print_cpm_summary(result: CPMResult) -> None:
    """
    Druckt CPM-Zusammenfassung auf die Konsole.

    Args:
        result: CPM-Berechnungsergebnis
    """
    from utils import format_time_value_auto

    critical_path = result.critical_path
    project_duration = max(task.fez for task in result.tasks.values())

    print("=" * 70)
    print(f"Projekt: {result.project_name}")
    print(f"Projektdauer: {format_time_value_auto(project_duration)}")
    if result.project_start:
        from utils import add_workdays
        print(f"Startdatum: {result.project_start.strftime('%Y-%m-%d')}")
        print(f"Enddatum (geschaetzt): {add_workdays(result.project_start, project_duration).strftime('%Y-%m-%d')}")
    print("=" * 70)
    print()
    print("Kritischer Pfad:")
    for task_id in critical_path:
        task = result.tasks[task_id]
        duration_str = format_time_value_auto(task.duration)
        print(f"  [{task_id}] {task.name:<30} (Dauer: {duration_str})")
    print()
    print("=" * 70)
    print("Alle Tasks:")
    print(f"{'ID':<7} {'Name':<30} {'Dauer':<8} {'FAZ':<6} {'FEZ':<6} {'SAZ':<6} {'SEZ':<6} {'GP':<6} {'FP':<6} {'Krit.'}")
    print("-" * 70)

    # Sortiere Tasks topologisch (nach FAZ)
    sorted_task_ids = sorted(result.tasks.keys(), key=lambda x: result.tasks[x].faz)

    for task_id in sorted_task_ids:
        task = result.tasks[task_id]
        critical_marker = "JA" if task.is_critical else ""
        duration_str = format_time_value_auto(task.duration)
        gp_str = format_time_value_auto(task.puffer)  # Gesamtpuffer
        fp_str = format_time_value_auto(task.free_puffer)  # Freier Puffer

        id_str = str(task_id)

        print(
            f"{id_str:<7} {task.name:<30} {duration_str:<8} "
            f"{task.faz:<6.1f} {task.fez:<6.1f} {task.saz:<6.1f} "
            f"{task.sez:<6.1f} {gp_str:<6} {fp_str:<6} {critical_marker}"
        )
    print("=" * 70)


def export_cpm_to_txt(result: CPMResult, output_file: Path, project=None, cfg_dir: Path = None) -> None:
    """
    Exportiert CPM-Ergebnisse als strukturierte ASCII-Textdatei.

    Delegiert an txt_export.export_cpm_to_txt() – Sektionen und Überschriften
    werden aus cfg/txt_export.cfg gelesen.

    Args:
        result:      CPM-Berechnungsergebnis
        output_file: Ausgabedatei (.txt)
        project:     Projekt-Objekt (optional, für Ressourcen-Details)
        cfg_dir:     Konfigurationsverzeichnis (optional)
    """
    _txt_export(
        result,
        output_file,
        project_name=result.project_name,
        project=project,
        cfg_dir=cfg_dir,
    )


def create_default_person_from_config(cfg_dir: Path) -> Person:
    """
    Erstellt eine Default-Person aus der defaults.cfg.

    Args:
        cfg_dir: Verzeichnis mit Konfigurationsdateien

    Returns:
        Person-Objekt mit Werten aus defaults.cfg
    """
    import configparser

    config = configparser.ConfigParser()
    config_file = cfg_dir / "defaults.cfg"

    # Defaults
    person_data = {
        'id': 'default_resource',
        'name': 'Max Mustermann',
        'email': 'max@mustermann.com',
        'role': 'Default Resource',
        'hourly_rate': 100.0
    }

    if config_file.exists():
        config.read(config_file, encoding='utf-8')
        if 'Resource' in config:
            if 'id' in config['Resource']:
                person_data['id'] = config['Resource']['id']
            if 'name' in config['Resource']:
                person_data['name'] = config['Resource']['name']
            if 'email' in config['Resource']:
                person_data['email'] = config['Resource']['email']
            if 'hourly_rate' in config['Resource']:
                person_data['hourly_rate'] = float(config['Resource']['hourly_rate'])

    return Person(**person_data)



def export_cpm_to_xlsx(result: CPMResult, output_file: Path, project=None, cfg_dir: Path = None) -> None:
    """
    Exportiert CPM-Ergebnisse in Excel-Format.

    Die erzeugten Tabs werden über [sections] / section_order in cfg/excel_export.cfg gesteuert.
    Verfügbare Sektionen: summary, critical_path, tasklist, gantt_chart, resource_list

    Args:
        result:      CPM-Berechnungsergebnis
        output_file: Ausgabedatei (.xlsx)
        project:     Optional – Projekt-Daten für Gantt/Resource-Tabs (PersonProject)
        cfg_dir:     Optional – Verzeichnis mit Konfigurationsdateien
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl ist nicht installiert. Installieren Sie es mit: pip install openpyxl")

    if cfg_dir is None:
        cfg_dir = Path(os.environ.get("PV_CFG", "cfg"))

    # Konfiguration laden – enthält section_order und tab_names
    full_config = load_excel_export_config(cfg_dir)
    section_order = full_config['sections']['section_order']
    tab_names     = full_config['tab_names']

    wb = openpyxl.Workbook()
    # Das automatisch erzeugte leere Sheet entfernen
    wb.remove(wb.active)

    project_name = result.project_name

    for section in section_order:
        if section == 'summary':
            create_summary_sheet(wb, result, project_name,
                                 tab_name=tab_names.get('summary', 'Projektzusammenfassung'))

        elif section == 'critical_path':
            create_critical_path_sheet(wb, result,
                                       tab_name=tab_names.get('critical_path', 'Kritischer Pfad'))

        elif section == 'tasklist':
            create_tasklist_sheet(wb, result,
                                  tab_name=tab_names.get('tasklist', 'Alle Tasks'))

        elif section == 'netplan_table':
            create_netplan_table_sheet(wb, result,
                                       tab_name=tab_names.get('netplan_table', 'Netzplan'))

        elif section in ('gantt_chart', 'resource_list'):
            from models.reports import GanttReport, ResourceListReport
            from excel_reports import create_gantt_chart, create_resource_list
            if section == 'gantt_chart' and project:
                report = GanttReport(
                    id='gantt_chart',
                    name=tab_names.get('gantt_chart', 'Gantt Chart'),
                    headline=tab_names.get('gantt_chart', 'Gantt Chart'),
                    type='gantt',
                    columns=['ID', 'Name', 'Start', 'Ende', 'Aufwand', 'Diagramm'],
                    loadunit=result.time_unit,
                )
                create_gantt_chart(wb, project, result, report, full_config)
            elif section == 'resource_list' and project and project.persons:
                report = ResourceListReport(
                    id='resource_list',
                    name=tab_names.get('resource_list', 'Ressourcen'),
                    headline=tab_names.get('resource_list', 'Ressourcen'),
                    type='resource_list',
                    columns=['Ressource', 'Vorgang', 'Start', 'Ende', 'Diagramm'],
                    loadunit=result.time_unit,
                )
                create_resource_list(wb, project, result, report, full_config)

        else:
            logger.warning(f"Unbekannte Excel-Sektion '{section}' – wird übersprungen.")

    wb.save(output_file)


def main() -> int:
    """
    Hauptfunktion mit Argumentparsing.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    parser = argparse.ArgumentParser(
        description="sproject.py - Einfaches Projektmanagement mit Ressourcenverwaltung, Kalender und Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --project examples/tankdesign.json
  %(prog)s  # Verarbeitet alle project*.json Dateien im data Ordner
        """
    )

    parser.add_argument(
        "--project",
        type=Path,
        help="Pfad zur Projektdatei (project.json). Falls nicht angegeben, werden alle project*.json Dateien im data Ordner verwendet."
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.environ.get("PV_DATA", "data")),
        help="Verzeichnis mit Projektdateien (Standard: $PV_DATA oder 'data')"
    )

    parser.add_argument(
        "--cfg-dir",
        type=Path,
        default=Path(os.environ.get("PV_CFG", "cfg")),
        help="Verzeichnis mit Konfigurationsdateien (Standard: $PV_CFG oder 'cfg')"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Ausgabeverzeichnis für generierte Graphen (Standard: gleiches Verzeichnis wie Projektdatei)"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Projektstartdatum für CPM-Berechnung (YYYY-MM-DD, default: heute)"
    )

    parser.add_argument(
        "--export",
        type=str,
        default="json",
        help="Exportformate (kommagetrennt): txt, json, xlsx, svg, md (Standard: json). Beispiel: --export txt,json,xlsx,svg,md"
    )

    args = parser.parse_args()

    # Parse Export-Formate
    export_formats = [fmt.strip().lower() for fmt in args.export.split(',')]
    valid_formats = {'txt', 'json', 'xlsx', 'svg', 'md'}
    for fmt in export_formats:
        if fmt not in valid_formats:
            print(f"Ungültiges Exportformat: {fmt}. Erlaubt: txt, json, xlsx, svg, md")
            return 1

    # Logging einrichten
    logger = setup_logging()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("sproject.py gestartet")
    logger.info("=" * 60)

    # Projektdateien bestimmen
    project_files: List[Path] = []

    if args.project:
        if not args.project.exists():
            logger.error(f"Projektdatei nicht gefunden: {args.project}")
            return 1
        project_files = [args.project]
        logger.info(f"Verwende angegebene Projektdatei: {args.project}")
    else:
        project_files = find_project_files(args.data_dir)
        if not project_files:
            logger.error(f"Keine project*.json Dateien gefunden in: {args.data_dir}")
            return 1
        logger.info(f"Gefundene Projektdateien ({len(project_files)}):")
        for pf in project_files:
            logger.info(f"  - {pf}")

    # Verarbeite jede Projektdatei
    success_count = 0
    for project_file in project_files:
        logger.info("-" * 60)
        logger.info(f"Verarbeite: {project_file.name}")
        logger.info("-" * 60)

        try:
            # Lade Projekt mit Pydantic-Modellen
            from models import load_project
            from models.tasks import InstanceTask, LoopTask

            project = load_project(project_file)

            # Expandiere Cycle/Loop-Tasks falls nötig
            has_instance_tasks = any(isinstance(t, InstanceTask) for t in project.tasks)
            has_loop_tasks = any(isinstance(t, LoopTask) for t in project.tasks)

            if has_instance_tasks:
                logger.info(f"Expandiere Cycle-Tasks fuer {project_file.name}...")
                project = project.expand_cycles()
                logger.info(f"  -> {len(project.tasks)} Tasks nach Expansion")
            elif has_loop_tasks:
                logger.info(f"Expandiere Loop-Tasks fuer {project_file.name}...")
                project = project.expand_loops()
                logger.info(f"  -> {len(project.tasks)} Tasks nach Expansion")

            # Berechne CPM
            start_date = None
            if args.start_date:
                from datetime import datetime
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
                logger.info(f"Verwende Startdatum: {args.start_date}")

            result = project.calculate_cpm(start_date=start_date, cfg_dir=args.cfg_dir)

            # Ausgabe auf Konsole
            print_cpm_summary(result)

            # Bestimme Ausgabeverzeichnis
            if args.output_dir:
                output_dir = args.output_dir
            else:
                # Standard: results Ordner
                output_dir = Path("results")
                output_dir.mkdir(exist_ok=True)

            # Exportiere in gewünschte Formate
            for fmt in export_formats:
                if fmt == 'json':
                    output_file_network = output_dir / f"{project_file.stem}_network_plan.json"
                    # Gantt-Schedule (Phase 2) ermitteln falls möglich
                    gantt_data = None
                    try:
                        gantt_calc = GanttCalculator(
                            result,
                            skip_weekends=result.skip_weekends,
                            skip_holidays=result.skip_holidays,
                            holidays=result.holidays if result.skip_holidays else None,
                            cfg_dir=args.cfg_dir if hasattr(args, 'cfg_dir') else None
                        )
                        gantt_calc.calculate()
                        gantt_data = gantt_calc.export_to_dict()
                    except Exception as e:
                        logger.warning(f"Gantt-Schedule für JSON nicht verfügbar: {e}")

                    project_name_json = project.project if hasattr(project, 'project') else project_file.stem
                    _json_export(
                        result,
                        output_file_network,
                        project_name=project_name_json,
                        project=project,
                        cfg_dir=args.cfg_dir,
                        gantt_data=gantt_data,
                    )
                    logger.info(f"Netzplan (JSON) gespeichert in: {output_file_network}")
                elif fmt == 'txt':
                    output_file = output_dir / f"{project_file.stem}.txt"
                    project_name_txt = project.project if hasattr(project, 'project') else project_file.stem
                    export_cpm_to_txt(result, output_file, project=project, cfg_dir=args.cfg_dir)
                    logger.info(f"CPM-Ergebnisse (TXT) gespeichert in: {output_file}")
                elif fmt == 'xlsx':
                    output_file = output_dir / f"{project_file.stem}.xlsx"
                    try:
                        export_cpm_to_xlsx(result, output_file, project, args.cfg_dir)
                        logger.info(f"CPM-Ergebnisse (XLSX) gespeichert in: {output_file}")
                    except ImportError as ie:
                        logger.warning(f"XLSX-Export übersprungen: {ie}")
                elif fmt == 'svg':
                    output_file = output_dir / f"{project_file.stem}_gantt.svg"
                    try:
                        # Exportiere Gantt-Chart als SVG über Mermaid/kroki
                        project_name = project.project if hasattr(project, 'project') else project_file.stem
                        success = export_cpm_to_svg(result, output_file, project_name)
                        if success:
                            logger.info(f"CPM-Ergebnisse (SVG) gespeichert in: {output_file}")
                    except ImportError as ie:
                        logger.warning(f"SVG-Export übersprungen: {ie}")
                    except Exception as e:
                        logger.error(f"SVG-Export fehlgeschlagen: {e}")
                elif fmt == 'md':
                    output_file = output_dir / f"{project_file.stem}.md"
                    try:
                        # Exportiere CPM-Report als Markdown
                        project_name = project.project if hasattr(project, 'project') else project_file.stem
                        success = export_cpm_to_markdown(result, output_file, project_name, project)
                        if success:
                            logger.info(f"CPM-Ergebnisse (Markdown) gespeichert in: {output_file}")
                    except Exception as e:
                        logger.error(f"Markdown-Export fehlgeschlagen: {e}")

            success_count += 1
        except Exception as e:
            logger.error(f"Fehler bei CPM-Berechnung für {project_file.name}: {e}", exc_info=True)

    logger.info("=" * 60)
    logger.info(f"Fertig: {success_count}/{len(project_files)} Projekte erfolgreich verarbeitet")
    logger.info("=" * 60)

    return 0 if success_count == len(project_files) else 1


if __name__ == "__main__":
    sys.exit(main())
