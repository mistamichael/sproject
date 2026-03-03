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
from cpm_calculator import SimpleCPMCalculator
from svg_graph_generator import SVGGraphGenerator


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

    args = parser.parse_args()

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
                from models.project import CycleProject, LoopProject

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

                # Erstelle CPM Calculator mit expandiertem Projekt
                calc = SimpleCPMCalculator(project)

                # Setze Startdatum falls angegeben
                if args.start_date:
                    from datetime import datetime
                    calc.start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
                    logger.info(f"Verwende Startdatum: {args.start_date}")

                # Berechne CPM
                calc.calculate()

                # Ausgabe auf Konsole
                calc.print_summary()

                # Bestimme Ausgabedatei
                if args.output_dir:
                    output_file = args.output_dir / f"{project_file.stem}_cpm.json"
                else:
                    # Standard: results Ordner
                    results_dir = Path("results")
                    results_dir.mkdir(exist_ok=True)
                    output_file = results_dir / f"{project_file.stem}_cpm.json"

                # Exportiere zu JSON
                calc.export_to_json(output_file, include_dates=True)
                logger.info(f"CPM-Ergebnisse gespeichert in: {output_file}")
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
