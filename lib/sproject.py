#!/usr/bin/env python3
"""
sproject CLI
============

Berechnet Projektdateien (CPM, Kalender, Kosten) und exportiert Reports.

    python -m lib.sproject --project examples/tankdesign.json --export json,txt
    python lib/sproject.py --project examples/tankdesign.json
"""

import argparse
import re
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

if __package__ in (None, ""):
    # Direkter Skript-Aufruf (python lib/sproject.py): Paket 'lib' bekannt machen (PEP 366)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import lib  # noqa: F401
    __package__ = "lib"

from .durations import format_time_value_auto
from .export_config import load_labels
from .exporters import EXPORTERS, ExportOptions, export_schedule
from .baseline import create_baseline
from .models import load_project, save_project
from .models.cpm import CPMResult
from .paths import get_results_dir
from .report_data import deadline_warning_lines, tracking_summary
from .scenarios import apply_scenario, compare_scenarios, comparison_rows, find_scenario
from .schedule import build_schedule
from .simulation import simulate, summary_rows, top_critical


def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """Logging in Datei ($PV_LOG oder ./log) und auf die Konsole."""
    log_dir = log_dir or Path(os.environ.get("PV_LOG", "log"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"sproject_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("sproject")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.info(f"Logging initialisiert: {log_file}")
    return logger


def find_project_files(data_dir: Path) -> List[Path]:
    """project*.json im Verzeichnis; falls keine vorhanden, alle *.json."""
    if not data_dir.exists():
        return []
    return list(data_dir.glob("project*.json")) or list(data_dir.glob("*.json"))


def print_cpm_summary(result: CPMResult, labels: Optional[dict] = None) -> None:
    """Druckt die CPM-Zusammenfassung auf die Konsole."""
    lb = labels or {}

    def label(key: str, default: str) -> str:
        return lb.get(key, default)

    project_duration = result.project_end_days

    print("=" * 70)
    print(f"{label('label_project', 'Projekt')}: {result.project_name}")
    print(f"{label('label_duration', 'Projektdauer')}: {format_time_value_auto(project_duration)}")
    if result.project_start:
        print(f"{label('label_start', 'Startdatum')}: {result.project_start.strftime('%Y-%m-%d')}")
        print(f"{label('label_end', 'Enddatum (geschätzt)')}: {result.date_at(project_duration, is_end=True).strftime('%Y-%m-%d')}")
    for label_text, value in tracking_summary(result):
        print(f"{label_text}: {value}")
    for warning in deadline_warning_lines(result):
        print(f"WARNUNG – Deadline verfehlt: {warning}")
    print("=" * 70)
    print()
    print(f"{label('label_crit_path', 'Kritischer Pfad')}:")
    for task_id in result.critical_path:
        task = result.tasks[task_id]
        print(f"  [{task_id}] {task.name:<30} ({label('dauer', 'Dauer')}: {format_time_value_auto(task.duration)})")
    print()
    print("=" * 70)
    print(f"{label('label_all_tasks', 'Alle Tasks')}:")
    cols = [label(k, d) for k, d in [('id', 'ID'), ('name', 'Name'), ('dauer', 'Dauer'), ('faz', 'FAZ'),
                                     ('fez', 'FEZ'), ('saz', 'SAZ'), ('sez', 'SEZ'), ('gp', 'GP'), ('fp', 'FP')]]
    print(f"{cols[0]:<7} {cols[1]:<30} {cols[2]:<8} {cols[3]:<6} {cols[4]:<6} {cols[5]:<6} "
          f"{cols[6]:<6} {cols[7]:<6} {cols[8]:<6} {label('krit', 'Krit.')}")
    print("-" * 70)
    for task_id in sorted(result.tasks, key=lambda x: result.tasks[x].faz):
        task = result.tasks[task_id]
        critical_marker = label('label_yes', 'JA') if task.is_critical else ""
        print(
            f"{str(task_id):<7} {task.name:<30} {format_time_value_auto(task.duration):<8} "
            f"{task.faz:<6.1f} {task.fez:<6.1f} {task.saz:<6.1f} {task.sez:<6.1f} "
            f"{format_time_value_auto(task.puffer):<6} {format_time_value_auto(task.free_puffer):<6} {critical_marker}"
        )
    print("=" * 70)


def _print_scenarios(outcomes) -> None:
    _print_table(comparison_rows(outcomes))


def _print_table(rows: List[List[str]]) -> None:
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    print("=" * 70)
    for n, row in enumerate(rows):
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
        if n == 0:
            print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    print("=" * 70)


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="sproject - Projektplanung mit CPM, Ressourcen, Kalender und Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --project examples/tankdesign.json
  %(prog)s  # Verarbeitet alle project*.json Dateien im data Ordner
        """,
    )
    parser.add_argument("--project", type=Path,
                        help="Projektdatei. Ohne Angabe: alle project*.json im data-Ordner.")
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("PV_DATA", "data")),
                        help="Verzeichnis mit Projektdateien (Standard: $PV_DATA oder 'data')")
    parser.add_argument("--cfg-dir", type=Path, default=Path(os.environ.get("PV_CFG", "cfg")),
                        help="Konfigurationsverzeichnis (Standard: $PV_CFG oder 'cfg')")
    parser.add_argument("--verbose", "-v", action="store_true", help="Ausführliche Ausgabe")
    parser.add_argument("--output-dir", type=Path,
                        help="Ausgabeverzeichnis (Standard: $PV_RESULTS oder 'results')")
    parser.add_argument("--start-date", type=str,
                        help="Projektstart (YYYY-MM-DD), überschreibt project_start")
    parser.add_argument("--export", type=str, default="json",
                        help=f"Exportformate, kommagetrennt: {', '.join(EXPORTERS)} (Standard: json)")
    parser.add_argument("--scenarios", action="store_true",
                        help="Alle Szenarien der Projektdatei mit dem Basisplan vergleichen")
    parser.add_argument("--scenario", type=str,
                        help="Ein Szenario (Name) statt des Basisplans rechnen und exportieren")
    parser.add_argument("--simulate", type=int, metavar="N",
                        help="Monte-Carlo-Simulation mit N Läufen (Unsicherheiten aus duration_range, risk, "
                             "Szenarien mit probability)")
    parser.add_argument("--seed", type=int, help="Zufallsstartwert für reproduzierbare Simulationen")
    parser.add_argument("--save-baseline", action="store_true",
                        help="Berechneten Plan als Baseline in die Projektdatei schreiben (Plan/Ist-Vergleich)")
    parser.add_argument("--lang", type=str, default="de", choices=["de", "en"],
                        help="Sprache der Report-Beschriftungen (Standard: de)")
    return parser.parse_args(argv)


def _process(project_file: Path, args: argparse.Namespace, formats: List[str], logger: logging.Logger) -> bool:
    """Berechnet und exportiert eine Projektdatei. False, wenn ein Export fehlschlägt."""
    project = load_project(project_file)
    stem = project_file.stem
    if args.scenarios:
        _print_scenarios(compare_scenarios(project, start_date=args.start_date, cfg_dir=args.cfg_dir))
    if args.scenario:
        scenario = find_scenario(project, args.scenario)
        logger.info(f"Szenario: {scenario.name}")
        project = apply_scenario(project, scenario)
        stem = f"{stem}_{re.sub(r'[^A-Za-z0-9]+', '_', scenario.name).strip('_')}"
    schedule = build_schedule(project, start_date=args.start_date, cfg_dir=args.cfg_dir)
    if args.simulate:
        sim = simulate(project, runs=args.simulate, seed=args.seed,
                       start_date=args.start_date, cfg_dir=args.cfg_dir)
        _print_table([["Kennzahl", "Wert"]] + summary_rows(sim))
        _print_table([["Task", "Name", "kritisch in"]] + top_critical(sim))
    if len(schedule.project.tasks) != len(project.tasks):
        logger.info(f"  -> {len(schedule.project.tasks)} Tasks nach Expansion")

    print_cpm_summary(schedule.cpm, labels=load_labels(args.cfg_dir, lang=args.lang))

    if args.save_baseline and args.scenario:
        logger.warning("--save-baseline wird bei --scenario ignoriert")
    elif args.save_baseline:
        project.baseline = create_baseline(schedule)
        save_project(project, project_file)
        logger.info(f"Baseline gespeichert in: {project_file}")

    options = ExportOptions(
        out_dir=args.output_dir or get_results_dir(),
        file_stem=stem,
        cfg_dir=args.cfg_dir,
        lang=args.lang,
        simulation_runs=args.simulate or 300,
        seed=args.seed,
    )
    ok = True
    for fmt in formats:
        try:
            for path in export_schedule(schedule, [fmt], options):
                logger.info(f"{fmt.upper()} gespeichert in: {path}")
        except ImportError as e:
            logger.warning(f"{fmt.upper()}-Export übersprungen: {e}")
        except Exception as e:
            logger.error(f"{fmt.upper()}-Export fehlgeschlagen: {e}")
            ok = False
    return ok


def main(argv: Optional[List[str]] = None) -> int:
    """Exit-Code 0, wenn alle Projektdateien erfolgreich verarbeitet wurden."""
    args = _parse_args(argv)

    formats = [fmt.strip().lower() for fmt in args.export.split(',') if fmt.strip()]
    unknown = [fmt for fmt in formats if fmt not in EXPORTERS]
    if unknown:
        print(f"Ungültiges Exportformat: {', '.join(unknown)}. Erlaubt: {', '.join(EXPORTERS)}")
        return 1

    logger = setup_logging()
    if args.verbose:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    if args.project:
        if not args.project.exists():
            logger.error(f"Projektdatei nicht gefunden: {args.project}")
            return 1
        project_files = [args.project]
    else:
        project_files = find_project_files(args.data_dir)
        if not project_files:
            logger.error(f"Keine project*.json Dateien gefunden in: {args.data_dir}")
            return 1
        logger.info(f"Gefundene Projektdateien ({len(project_files)}): {', '.join(p.name for p in project_files)}")

    success_count = 0
    for project_file in project_files:
        logger.info(f"Verarbeite: {project_file.name}")
        try:
            if _process(project_file, args, formats, logger):
                success_count += 1
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung für {project_file.name}: {e}", exc_info=True)

    logger.info(f"Fertig: {success_count}/{len(project_files)} Projekte erfolgreich verarbeitet")
    return 0 if success_count == len(project_files) else 1


if __name__ == "__main__":
    sys.exit(main())
