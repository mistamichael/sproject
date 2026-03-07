#!/usr/bin/env python3
"""
Projekt Rechner
Erzeugt aus den Angaben zu Resourcen, Urlaubstagen und Projekt-Angaben Reports,
wie z.B. einen Resourcenplan über der Zeit, ein Gant-Diagramm mit kritischen Pfad oder einen Kostenplan
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from tjp_models import TJPRegistry
from svg_graph_generator import SVGGraphGenerator
from excel_reports import add_report_sheets
from models.project import PersonProject
from models.reports import GanttReport, ResourceListReport
from models.resources import Person, PersonResource
from models.cpm import CPMResult


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
    print(f"{'ID':<7} {'Name':<30} {'Dauer':<8} {'FAZ':<6} {'FEZ':<6} {'SAZ':<6} {'SEZ':<6} {'Puffer':<8} {'Krit.'}")
    print("-" * 70)

    # Sortiere Tasks topologisch (nach FAZ)
    sorted_task_ids = sorted(result.tasks.keys(), key=lambda x: result.tasks[x].faz)

    for task_id in sorted_task_ids:
        task = result.tasks[task_id]
        critical_marker = "JA" if task.is_critical else ""
        duration_str = format_time_value_auto(task.duration)
        puffer_str = format_time_value_auto(task.puffer)

        id_str = str(task_id)

        print(
            f"{id_str:<7} {task.name:<30} {duration_str:<8} "
            f"{task.faz:<6.1f} {task.fez:<6.1f} {task.saz:<6.1f} "
            f"{task.sez:<6.1f} {puffer_str:<8} {critical_marker}"
        )
    print("=" * 70)


def export_cpm_to_txt(result: CPMResult, output_file: Path) -> None:
    """
    Exportiert CPM-Ergebnisse in Textformat (wie Konsolen-Ausgabe).

    Args:
        result: CPM-Berechnungsergebnis
        output_file: Ausgabedatei (.txt)
    """
    from utils import format_time_value_auto, add_workdays

    with open(output_file, 'w', encoding='utf-8') as f:
        critical_path = result.critical_path
        project_duration = max(task.fez for task in result.tasks.values())

        f.write("=" * 70 + "\n")
        f.write(f"Projekt: {result.project_name}\n")
        f.write(f"Projektdauer: {format_time_value_auto(project_duration)}\n")
        f.write(f"Startdatum: {result.project_start.strftime('%Y-%m-%d')}\n")
        f.write(f"Enddatum (geschaetzt): {add_workdays(result.project_start, project_duration).strftime('%Y-%m-%d')}\n")
        f.write("=" * 70 + "\n")
        f.write("\n")
        f.write("Kritischer Pfad:\n")
        for task_id in critical_path:
            task = result.tasks[task_id]
            duration_str = format_time_value_auto(task.duration)
            f.write(f"  [{task_id}] {task.name:<30} (Dauer: {duration_str})\n")
        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("Alle Tasks:\n")
        f.write(f"{'ID':<7} {'Name':<30} {'Dauer':<8} {'FAZ':<6} {'FEZ':<6} {'SAZ':<6} {'SEZ':<6} {'Puffer':<8} {'Krit.'}\n")
        f.write("-" * 70 + "\n")

        # Sortiere Tasks topologisch (nach FAZ)
        sorted_task_ids = sorted(result.tasks.keys(), key=lambda x: result.tasks[x].faz)

        for task_id in sorted_task_ids:
            task = result.tasks[task_id]
            critical_marker = "JA" if task.is_critical else ""
            duration_str = format_time_value_auto(task.duration)
            puffer_str = format_time_value_auto(task.puffer)

            id_str = str(task_id)

            f.write(
                f"{id_str:<7} {task.name:<30} {duration_str:<8} "
                f"{task.faz:<6.1f} {task.fez:<6.1f} {task.saz:<6.1f} "
                f"{task.sez:<6.1f} {puffer_str:<8} {critical_marker}\n"
            )
        f.write("=" * 70 + "\n")


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


def add_dynamic_reports(project, gantt: bool, resource_list: bool, cfg_dir: Path):
    """
    Fügt dynamisch Reports zu einem Projekt hinzu.

    Args:
        project: Projekt-Objekt
        gantt: Ob Gantt-Chart erstellt werden soll
        resource_list: Ob Resource-List erstellt werden soll
        cfg_dir: Verzeichnis mit Konfigurationsdateien

    Returns:
        Modifiziertes Projekt mit Reports und ggf. Default-Personen
    """
    from models.project import PersonProject, SimpleProject, LoopProject, CycleProject

    # Wenn keine Reports gewünscht, nichts tun
    if not gantt and not resource_list:
        return project

    # Erstelle Reports-Liste
    reports = []

    if gantt:
        reports.append(GanttReport(
            id="gantt_chart",
            name="Gantt Chart",
            headline="Projekt Zeitplan",
            type="gantt",
            columns=["Vorgang", "name", "start", "end", "effort", "chart"],
            timeformat="%Y-%m-%d",
            loadunit="days"
        ))

    if resource_list:
        reports.append(ResourceListReport(
            id="resource_view",
            name="Resource List",
            headline="Resourcendiagramm",
            type="resource_list",
            columns=["User", "Rolle", "start", "end", "chart"],
            timeformat="%Y-%m-%d",
            loadunit="days"
        ))

    # Wenn Projekt bereits PersonProject ist, füge Reports hinzu
    if isinstance(project, PersonProject):
        project.reports = reports
        return project

    # Ansonsten wandle in PersonProject um mit Default-Person
    default_person = create_default_person_from_config(cfg_dir)

    # Erstelle Default-Ressource
    default_resource = PersonResource(
        id=default_person.id,
        name=default_person.name,
        type="person",
        person_id=default_person.id
    )

    # Konvertiere zu PersonProject
    person_project = PersonProject(
        project=project.project,
        project_start=project.project_start if hasattr(project, 'project_start') else None,
        total_hours=None,
        unit="hours",
        persons=[default_person],
        resources=[default_resource],
        tasks=project.tasks,
        reports=reports
    )

    return person_project


def export_cpm_to_xlsx(result: CPMResult, output_file: Path, project=None, cfg_dir: Path = None) -> None:
    """
    Exportiert CPM-Ergebnisse in Excel-Format.

    Args:
        result: CPM-Berechnungsergebnis
        output_file: Ausgabedatei (.xlsx)
        project: Optional - Projekt-Daten für Report-Sheets (PersonProject)
        cfg_dir: Optional - Verzeichnis mit Konfigurationsdateien
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from utils import format_time_value_auto, add_workdays

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CPM Analyse"

        # Header-Stil
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        # Projekt-Informationen
        project_duration = max(task.fez for task in result.tasks.values())
        ws['A1'] = "Projekt:"
        ws['B1'] = result.project_name
        ws['A2'] = "Projektdauer:"
        ws['B2'] = format_time_value_auto(project_duration)
        ws['A3'] = "Startdatum:"
        ws['B3'] = result.project_start.strftime('%Y-%m-%d')
        ws['A4'] = "Enddatum:"
        ws['B4'] = add_workdays(result.project_start, project_duration).strftime('%Y-%m-%d')

        # Leere Zeile
        row = 6

        # Tabellen-Header mit Zeiteinheit
        from utils import get_time_unit_label
        unit_label = get_time_unit_label(result.time_unit)
        headers = ['ID', 'Name', 'Dauer', f'FAZ ({unit_label})', f'FEZ ({unit_label})',
                   f'SAZ ({unit_label})', f'SEZ ({unit_label})', 'Puffer', 'Kritisch']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        # Daten - sortiere Tasks topologisch (nach FAZ)
        sorted_task_ids = sorted(result.tasks.keys(), key=lambda x: result.tasks[x].faz)

        row += 1
        from utils import convert_days_to_time_unit
        for task_id in sorted_task_ids:
            task = result.tasks[task_id]
            ws.cell(row=row, column=1, value=str(task_id))
            ws.cell(row=row, column=2, value=task.name)
            ws.cell(row=row, column=3, value=format_time_value_auto(task.duration))
            ws.cell(row=row, column=4, value=round(convert_days_to_time_unit(task.faz, result.time_unit), 1))
            ws.cell(row=row, column=5, value=round(convert_days_to_time_unit(task.fez, result.time_unit), 1))
            ws.cell(row=row, column=6, value=round(convert_days_to_time_unit(task.saz, result.time_unit), 1))
            ws.cell(row=row, column=7, value=round(convert_days_to_time_unit(task.sez, result.time_unit), 1))
            ws.cell(row=row, column=8, value=format_time_value_auto(task.puffer))
            ws.cell(row=row, column=9, value="JA" if task.is_critical else "")

            # Kritische Tasks hervorheben
            if task.is_critical:
                for col in range(1, 10):
                    ws.cell(row=row, column=col).fill = PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid")

            row += 1

        # Spaltenbreiten anpassen
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 8
        ws.column_dimensions['F'].width = 8
        ws.column_dimensions['G'].width = 8
        ws.column_dimensions['H'].width = 10
        ws.column_dimensions['I'].width = 10

        # Füge Report-Sheets hinzu, falls vorhanden
        if project and isinstance(project, PersonProject) and project.reports:
            if cfg_dir is None:
                cfg_dir = Path(os.environ.get("PV_CFG", "cfg"))
            add_report_sheets(wb, project, result, cfg_dir)

        wb.save(output_file)
    except ImportError:
        raise ImportError("openpyxl ist nicht installiert. Installieren Sie es mit: pip install openpyxl")


def load_registry(cfg_dir: Path, project_file: Path, logger: logging.Logger) -> Optional[TJPRegistry]:
    """
    Lädt TJPRegistry aus der Projektdatei.

    Alle Konfigurationen (Personen, Arbeitszeiten, Reports) werden zukünftig
    in der Projekt-JSON mitgeliefert. Fehlende Angaben werden mit Defaults ergänzt.

    Args:
        cfg_dir: Verzeichnis mit Konfigurationsdateien (für zukünftige Verwendung)
        project_file: Pfad zur Projektdatei
        logger: Logger-Instanz

    Returns:
        TJPRegistry-Instanz oder None bei Fehler
    """
    try:
        logger.info(f"Lade Registry aus:")
        logger.info(f"  - Projekt: {project_file}")

        registry = TJPRegistry.load(
            project_path=project_file,
        )

        logger.info("Registry erfolgreich geladen")
        return registry

    except Exception as e:
        logger.warning(f"Datei {project_file.name} ist kein vollständiges ProjectFile-Format")
        logger.warning("Hinweis: Für CPM/Graph-Operationen verwenden Sie --calculate-cpm oder --create-svg-graph")
        logger.debug(f"Fehlerdetails: {e}", exc_info=True)
        return None


def create_svg_graph(project_file: Path, output_dir: Optional[Path] = None, cfg_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> bool:
    """
    Erstellt ein SVG-Abhängigkeitsdiagramm aus einer Projektdatei mit CPM-Daten unter Verwendung des node.svg Templates.

    Args:
        project_file: Pfad zur Projektdatei (JSON)
        output_dir: Ausgabeverzeichnis für das SVG (Standard: gleiches Verzeichnis wie Projektdatei)
        cfg_dir: Verzeichnis mit Konfigurationsdateien (Standard: $PV_CFG oder 'cfg')
        logger: Logger-Instanz

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Bestimme cfg_dir aus Umgebungsvariable falls nicht angegeben
        if cfg_dir is None:
            cfg_dir = Path(os.environ.get("PV_CFG", "cfg"))

        # Erstelle Generator und generiere SVG
        generator = SVGGraphGenerator(cfg_dir=cfg_dir, logger=logger)
        return generator.generate_svg(project_file, output_dir)

    except Exception as e:
        if logger:
            logger.error(f"Fehler beim Erstellen des SVG-Graphen: {e}", exc_info=True)
        else:
            print(f"ERROR: Fehler beim Erstellen des SVG-Graphen: {e}")
        return False


def process_project(registry: TJPRegistry, logger: logging.Logger) -> None:
    """
    Verarbeitet ein Projekt und erstellt Reports.

    Args:
        registry: Geladene TJPRegistry
        logger: Logger-Instanz
    """
    logger.info("Verarbeite Projekt...")
    print("\n" + registry.summary() + "\n")

    # Hier können weitere Verarbeitungsschritte hinzugefügt werden:
    # - Report-Generierung
    # - Gantt-Diagramm-Erstellung
    # - Ressourcenplanung
    # - Kostenberechnung

    logger.info("Projektverarbeitung abgeschlossen")


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
  %(prog)s --data-dir examples --create-svg-graph
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
        "--create-svg-graph",
        action="store_true",
        help="Erstellt SVG-Abhängigkeitsdiagramm(e) für die Projektdatei(en) unter Verwendung des cfg/node.svg Templates"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Ausgabeverzeichnis für generierte Graphen (Standard: gleiches Verzeichnis wie Projektdatei)"
    )

    parser.add_argument(
        "--calculate-cpm",
        action="store_true",
        help="Berechnet den kritischen Pfad (Critical Path Method) für die Projektdatei(en)"
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
        help="Exportformate (kommagetrennt): txt, json, xlsx (Standard: json). Beispiel: --export txt,json,xlsx"
    )

    parser.add_argument(
        "--gantt",
        action="store_true",
        help="Erstellt Gantt-Chart im Excel-Export (nur mit --export xlsx)"
    )

    parser.add_argument(
        "--resource",
        action="store_true",
        help="Erstellt Resource-List im Excel-Export (nur mit --export xlsx)"
    )

    args = parser.parse_args()

    # Parse Export-Formate
    export_formats = [fmt.strip().lower() for fmt in args.export.split(',')]
    valid_formats = {'txt', 'json', 'xlsx'}
    for fmt in export_formats:
        if fmt not in valid_formats:
            print(f"Ungültiges Exportformat: {fmt}. Erlaubt: txt, json, xlsx")
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

        # Wenn SVG-Graph erstellen gewünscht ist
        if args.create_svg_graph:
            if create_svg_graph(project_file, args.output_dir, args.cfg_dir, logger):
                success_count += 1
            continue

        # Wenn CPM-Berechnung gewünscht ist
        if args.calculate_cpm:
            try:
                # Lade Projekt mit Pydantic-Modellen
                from models import load_project
                from models.project import CycleProject, LoopProject, PersonProject
                from models.tasks import LoopTask

                project = load_project(project_file)

                # Expandiere Cycle/Loop-Tasks falls nötig
                if isinstance(project, CycleProject):
                    logger.info(f"Expandiere Cycle-Tasks fuer {project_file.name}...")
                    project = project.expand_cycles()
                    logger.info(f"  -> {len(project.tasks)} Tasks nach Expansion")
                elif isinstance(project, LoopProject):
                    logger.info(f"Expandiere Loop-Tasks fuer {project_file.name}...")
                    project = project.expand_loops()
                    logger.info(f"  -> {len(project.tasks)} Tasks nach Expansion")
                elif isinstance(project, PersonProject):
                    # Prüfe ob PersonProject Loop-Tasks enthält
                    has_loop_tasks = any(isinstance(task, LoopTask) for task in project.tasks)
                    if has_loop_tasks:
                        logger.info(f"Expandiere Loop-Tasks in PersonProject fuer {project_file.name}...")
                        project = project.expand_loops()
                        logger.info(f"  -> {len(project.tasks)} Tasks nach Expansion")

                # Berechne CPM mit neuer API
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
                        output_file = output_dir / f"{project_file.stem}_cpm.json"
                        output_data = result.export_to_dict(include_dates=True)
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(output_data, f, indent=2, ensure_ascii=False)
                        logger.info(f"CPM-Ergebnisse (JSON) gespeichert in: {output_file}")
                    elif fmt == 'txt':
                        output_file = output_dir / f"{project_file.stem}_cpm.txt"
                        export_cpm_to_txt(result, output_file)
                        logger.info(f"CPM-Ergebnisse (TXT) gespeichert in: {output_file}")
                    elif fmt == 'xlsx':
                        output_file = output_dir / f"{project_file.stem}_cpm.xlsx"
                        try:
                            # Füge dynamisch Reports hinzu wenn gewünscht
                            export_project = project
                            if args.gantt or args.resource:
                                export_project = add_dynamic_reports(
                                    project,
                                    args.gantt,
                                    args.resource,
                                    args.cfg_dir
                                )

                            export_cpm_to_xlsx(result, output_file, export_project, args.cfg_dir)
                            logger.info(f"CPM-Ergebnisse (XLSX) gespeichert in: {output_file}")
                        except ImportError as ie:
                            logger.warning(f"XLSX-Export übersprungen: {ie}")

                success_count += 1
            except Exception as e:
                logger.error(f"Fehler bei CPM-Berechnung für {project_file.name}: {e}", exc_info=True)
            continue

        # Normale Projektverarbeitung mit TJP-Registry
        registry = load_registry(args.cfg_dir, project_file, logger)
        if registry is None:
            # Zähle trotzdem als Erfolg, da CPM/Graph-Operationen möglich sind
            success_count += 1
            continue

        process_project(registry, logger)
        success_count += 1

    logger.info("=" * 60)
    logger.info(f"Fertig: {success_count}/{len(project_files)} Projekte erfolgreich verarbeitet")
    logger.info("=" * 60)

    return 0 if success_count == len(project_files) else 1


if __name__ == "__main__":
    sys.exit(main())
