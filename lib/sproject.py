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

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_GRAPH_SUPPORT = True
except ImportError:
    HAS_GRAPH_SUPPORT = False

from tjp_models import TJPRegistry
from cpm_calculator import SimpleCPMCalculator


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
    Lädt TJPRegistry mit allen Konfigurationsdateien.

    Args:
        cfg_dir: Verzeichnis mit persons.json, reports.json, workinghours_absences.json
        project_file: Pfad zur Projektdatei
        logger: Logger-Instanz

    Returns:
        TJPRegistry-Instanz oder None bei Fehler
    """
    persons_path = cfg_dir / "persons.json"
    wh_path = cfg_dir / "workinghours_absences.json"
    reports_path = cfg_dir / "reports.json"

    required_files = [persons_path, wh_path, reports_path, project_file]

    for file_path in required_files:
        if not file_path.exists():
            logger.error(f"Erforderliche Datei fehlt: {file_path}")
            return None

    try:
        logger.info(f"Lade Registry aus:")
        logger.info(f"  - Personen: {persons_path}")
        logger.info(f"  - Arbeitszeiten: {wh_path}")
        logger.info(f"  - Reports: {reports_path}")
        logger.info(f"  - Projekt: {project_file}")

        registry = TJPRegistry.load(
            persons_path=persons_path,
            wh_path=wh_path,
            project_path=project_file,
            reports_path=reports_path,
        )

        logger.info("Registry erfolgreich geladen")
        return registry

    except Exception as e:
        logger.error(f"Fehler beim Laden der Registry: {e}", exc_info=True)
        return None


def create_dependency_graph(project_file: Path, output_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> bool:
    """
    Erstellt ein Abhängigkeitsdiagramm aus einer Projektdatei mit CPM-Daten.

    Args:
        project_file: Pfad zur Projektdatei (JSON)
        output_dir: Ausgabeverzeichnis für das Bild (Standard: gleiches Verzeichnis wie Projektdatei)
        logger: Logger-Instanz

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not HAS_GRAPH_SUPPORT:
        if logger:
            logger.error("Graphenerstellung nicht verfügbar. Bitte installieren Sie: pip install matplotlib networkx")
        else:
            print("ERROR: Graphenerstellung nicht verfügbar. Bitte installieren Sie: pip install matplotlib networkx")
        return False

    try:
        # Lade Projektdaten
        with open(project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'tasks' not in data:
            if logger:
                logger.error(f"Keine 'tasks' in Projektdatei gefunden: {project_file}")
            return False

        # Berechne CPM-Daten
        calc = SimpleCPMCalculator(data)
        calc.calculate()
        cpm_data = calc.cpm_data

        # Erstelle gerichteten Graphen
        G = nx.DiGraph()

        # Füge Knoten und Kanten hinzu
        for task in data['tasks']:
            task_id = task['id']
            task_name = task.get('name', f'Task {task_id}')

            # Hole CPM-Daten für diesen Task
            cpm = cpm_data.get(task_id, {})
            fb = cpm.get('faz', 0)
            fe = cpm.get('fez', 0)
            sb = cpm.get('saz', 0)
            se = cpm.get('sez', 0)
            gp = cpm.get('puffer', 0)
            fp = cpm.get('free_puffer', 0)
            is_critical = cpm.get('is_critical', False)

            # Erstelle Label mit CPM-Informationen
            # Format: FB am Anfang, FE am Ende der ersten Zeile
            #         SB am Anfang, SE am Ende der zweiten Zeile
            #         GP und FP in separatem Bereich
            G.add_node(task_id,
                      task_name=task_name,
                      fb=fb, fe=fe, sb=sb, se=se,
                      gp=gp, fp=fp,
                      is_critical=is_critical)

            # Füge Kanten für Abhängigkeiten hinzu
            for dep in task.get('dependencies', []):
                G.add_edge(task_id, dep)

        # Erstelle Plot
        plt.figure(figsize=(16, 10))

        # Berechne hierarchisches Layout von links nach rechts
        # Verwende topologische Sortierung für Layer-Zuweisung
        try:
            # Versuche topologische Sortierung (funktioniert nur bei DAGs)
            layers = {}
            for node in nx.topological_sort(G):
                # Layer basiert auf der maximalen Distanz von Startknoten
                predecessors = list(G.predecessors(node))
                if not predecessors:
                    layers[node] = 0
                else:
                    layers[node] = max(layers[p] for p in predecessors) + 1
        except:
            # Falls kein DAG, verwende einfaches Layout
            layers = {node: 0 for node in G.nodes()}

        # Erstelle Positionen basierend auf Layern (links nach rechts)
        pos = {}
        layer_counts = {}
        for node, layer in layers.items():
            if layer not in layer_counts:
                layer_counts[layer] = 0
            layer_counts[layer] += 1

        layer_positions = {}
        for node, layer in layers.items():
            if layer not in layer_positions:
                layer_positions[layer] = 0

            x = layer * 3  # Horizontaler Abstand zwischen Layern
            # Vertikale Position zentriert für jeden Layer
            max_in_layer = sum(1 for n, l in layers.items() if l == layer)
            y = layer_positions[layer] * 2 - (max_in_layer - 1)
            layer_positions[layer] += 1

            pos[node] = (x, y)

        # Zeichne Kanten zuerst (im Hintergrund)
        nx.draw_networkx_edges(G, pos, edge_color='gray',
                               arrows=True, arrowsize=20,
                               arrowstyle='->', width=2,
                               connectionstyle='arc3,rad=0.1')

        # Zeichne Rechteck-Knoten mit matplotlib patches und CPM-Daten
        from matplotlib.patches import FancyBboxPatch, Rectangle
        ax = plt.gca()

        for node, (x, y) in pos.items():
            # Hole Node-Attribute
            node_attrs = G.nodes[node]
            task_name = node_attrs.get('task_name', str(node))
            fb = node_attrs.get('fb', 0)
            fe = node_attrs.get('fe', 0)
            sb = node_attrs.get('sb', 0)
            se = node_attrs.get('se', 0)
            gp = node_attrs.get('gp', 0)
            fp = node_attrs.get('fp', 0)
            is_critical = node_attrs.get('is_critical', False)

            # Farben basierend auf kritischem Pfad
            if is_critical:
                box_color = '#ffcccc'  # Helles Rot für kritische Tasks
                edge_color = '#cc0000'  # Dunkelrot
                edge_width = 3
            else:
                box_color = 'lightblue'
                edge_color = 'darkblue'
                edge_width = 2

            # Hauptbox (größer für CPM-Daten)
            # Breite: 2.2, Höhe: 1.2
            main_box = FancyBboxPatch(
                (x - 1.1, y - 0.6), 2.2, 1.2,
                boxstyle="round,pad=0.05",
                edgecolor=edge_color,
                facecolor=box_color,
                linewidth=edge_width,
                alpha=0.9
            )
            ax.add_patch(main_box)

            # Obere Zeile: FB links, Task-Name mitte, FE rechts
            plt.text(x - 0.95, y + 0.35, f'{fb:.0f}',
                    ha='left', va='center', fontsize=8, fontweight='bold')
            plt.text(x, y + 0.35, task_name,
                    ha='center', va='center', fontsize=9, fontweight='bold')
            plt.text(x + 0.95, y + 0.35, f'{fe:.0f}',
                    ha='right', va='center', fontsize=8, fontweight='bold')

            # Mittlere Zeile: Task-ID
            plt.text(x, y + 0.05, f'ID: {node}',
                    ha='center', va='center', fontsize=7, style='italic')

            # Untere Zeile: SB links, SE rechts
            plt.text(x - 0.95, y - 0.25, f'{sb:.0f}',
                    ha='left', va='center', fontsize=8, fontweight='bold')
            plt.text(x + 0.95, y - 0.25, f'{se:.0f}',
                    ha='right', va='center', fontsize=8, fontweight='bold')

            # Puffer-Kasten unter dem Hauptkasten
            puffer_box_y = y - 0.9
            puffer_box = Rectangle(
                (x - 1.1, puffer_box_y - 0.15), 2.2, 0.3,
                edgecolor=edge_color,
                facecolor='lightyellow' if is_critical else 'lightgreen',
                linewidth=1.5,
                alpha=0.8
            )
            ax.add_patch(puffer_box)

            # Puffer-Text
            plt.text(x - 0.55, puffer_box_y, f'GP: {gp:.1f}',
                    ha='center', va='center', fontsize=7, fontweight='bold')
            plt.text(x + 0.55, puffer_box_y, f'FP: {fp:.1f}',
                    ha='center', va='center', fontsize=7, fontweight='bold')

        project_name = data.get('project', project_file.stem)
        plt.title(f'{project_name} - Netzplan mit CPM-Daten\n(FB=Frühester Beginn, FE=Frühestes Ende, SB=Spätester Beginn, SE=Spätestes Ende, GP=Gesamtpuffer, FP=Freier Puffer)',
                  fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()

        # Bestimme Ausgabepfad
        if output_dir is None:
            output_dir = project_file.parent

        output_file = output_dir / f"{project_file.stem}_graph.svg"

        # Speichere Graph als SVG
        plt.savefig(output_file, format='svg', bbox_inches='tight')
        plt.close()

        if logger:
            logger.info(f"Graph gespeichert als: {output_file}")
        else:
            print(f"Graph gespeichert als: {output_file}")

        return True

    except Exception as e:
        if logger:
            logger.error(f"Fehler beim Erstellen des Graphen: {e}", exc_info=True)
        else:
            print(f"ERROR: Fehler beim Erstellen des Graphen: {e}")
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
  %(prog)s --data-dir examples --create-graph
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
        "--create-graph",
        action="store_true",
        help="Erstellt Abhängigkeitsdiagramm(e) für die Projektdatei(en)"
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

        # Wenn nur Graph erstellen gewünscht ist
        if args.create_graph:
            if create_dependency_graph(project_file, args.output_dir, logger):
                success_count += 1
            continue

        # Wenn CPM-Berechnung gewünscht ist
        if args.calculate_cpm:
            try:
                calc = SimpleCPMCalculator.from_file(project_file)

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

        # Normale Projektverarbeitung
        registry = load_registry(args.cfg_dir, project_file, logger)
        if registry is None:
            logger.error(f"Fehler beim Laden von {project_file.name}")
            continue

        process_project(registry, logger)
        success_count += 1

    logger.info("=" * 60)
    logger.info(f"Fertig: {success_count}/{len(project_files)} Projekte erfolgreich verarbeitet")
    logger.info("=" * 60)

    return 0 if success_count == len(project_files) else 1


if __name__ == "__main__":
    sys.exit(main())
