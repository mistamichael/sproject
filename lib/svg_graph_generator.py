#!/usr/bin/env python3
"""
SVG Graph Generator für Netzpläne mit CPM-Daten

Erstellt SVG-Abhängigkeitsdiagramme aus Projektdaten unter Verwendung
eines konfigurierbaren Node-Templates.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    import networkx as nx
    HAS_GRAPH_SUPPORT = True
except ImportError:
    HAS_GRAPH_SUPPORT = False

from cpm_models import SimpleTaskFile


class SVGGraphConfig:
    """Konfigurationsklasse für SVG-Graph-Generierung"""

    def __init__(self, cfg_path: Path):
        """
        Lädt Konfiguration aus cfg/svg_nodes.cfg

        Args:
            cfg_path: Pfad zur Konfigurationsdatei
        """
        with open(cfg_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Node-Konfiguration
        node_cfg = self.config['node']
        self.template_file = node_cfg['template_file']
        self.node_width = node_cfg['width']
        self.node_height = node_cfg['height']

        # Layout-Konfiguration
        layout_cfg = self.config['layout']
        self.horizontal_spacing = layout_cfg['horizontal_spacing']
        self.vertical_spacing = layout_cfg['vertical_spacing']
        self.margin_left = layout_cfg['margin_left']
        self.margin_top = layout_cfg['margin_top']
        self.canvas_padding = layout_cfg['canvas_padding']

        # Papierformate
        self.paper_formats = {
            name: tuple(dims) for name, dims in self.config['paper_formats'].items()
            if not name.startswith('_')
        }

        # Farben
        color_cfg = self.config['colors']
        self.critical_path_color = color_cfg['critical_path']
        self.normal_path_color = color_cfg['normal_path']
        self.edge_color = color_cfg['edge']

        # Kanten-Konfiguration
        edge_cfg = self.config['edge']
        self.edge_stroke_width = edge_cfg['stroke_width']
        self.arrow_size = edge_cfg['arrow_size']
        # Offset der Verbindungspunkte relativ zum Node-Ursprung
        # Fallback: Mittelpunkt des konfigurierten Node-Rechtecks
        self.edge_offset_x = edge_cfg.get('offset_x', self.node_width / 2)
        self.edge_offset_y = edge_cfg.get('offset_y', self.node_height / 2)

        # Platzhalter
        self.placeholders = self.config['placeholders']


class SVGGraphGenerator:
    """Generator für SVG-Netzpläne"""

    def __init__(self, cfg_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        """
        Initialisiert den SVG-Graph-Generator

        Args:
            cfg_dir: Verzeichnis mit Konfigurationsdateien (Standard: $PV_CFG oder 'cfg')
            logger: Logger-Instanz
        """
        if cfg_dir is None:
            cfg_dir = Path(os.environ.get("PV_CFG", "cfg"))

        self.cfg_dir = cfg_dir
        self.logger = logger or logging.getLogger(__name__)

        # Lade Konfiguration
        cfg_path = cfg_dir / "svg_nodes.cfg"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {cfg_path}")

        self.config = SVGGraphConfig(cfg_path)

        # Lade Template
        template_path = cfg_dir / self.config.template_file
        if not template_path.exists():
            raise FileNotFoundError(f"SVG-Template nicht gefunden: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            self.node_template = f.read()

    def calculate_layout(self, data: Dict[str, Any]) -> Dict[int, Tuple[float, float]]:
        """
        Berechnet Layout-Positionen für alle Tasks

        Args:
            data: Projektdaten mit Tasks

        Returns:
            Dictionary mit task_id -> (x, y) Positionen
        """
        pos = {}

        if HAS_GRAPH_SUPPORT:
            # Erstelle gerichteten Graphen
            G = nx.DiGraph()
            for task in data['tasks']:
                task_id = task['id']
                G.add_node(task_id)
                for dep in task.get('dependencies', []):
                    G.add_edge(task_id, dep)

            # Berechne hierarchisches Layout
            try:
                layers = {}
                for node in nx.topological_sort(G):
                    predecessors = list(G.predecessors(node))
                    if not predecessors:
                        layers[node] = 0
                    else:
                        layers[node] = max(layers[p] for p in predecessors) + 1
            except:
                layers = {task['id']: i for i, task in enumerate(data['tasks'])}

            # Erstelle Positionen basierend auf Layern
            layer_positions = {}
            for task in data['tasks']:
                task_id = task['id']
                layer = layers.get(task_id, 0)

                if layer not in layer_positions:
                    layer_positions[layer] = 0

                x = self.config.margin_left + layer * self.config.horizontal_spacing
                y = self.config.margin_top + layer_positions[layer] * self.config.vertical_spacing
                layer_positions[layer] += 1

                pos[task_id] = (x, y)
        else:
            # Einfaches Layout ohne networkx: von oben nach unten
            for i, task in enumerate(data['tasks']):
                x = self.config.margin_left
                y = self.config.margin_top + i * self.config.vertical_spacing
                pos[task['id']] = (x, y)

        return pos

    def select_paper_format(self, pos: Dict[int, Tuple[float, float]]) -> Tuple[str, int, int]:
        """
        Wählt kleinstes passendes DIN-Format

        Args:
            pos: Dictionary mit Task-Positionen

        Returns:
            Tuple (format_name, width, height)
        """
        # Berechne benötigte Größe
        content_max_x = max(x for x, y in pos.values()) + self.config.node_width + self.config.canvas_padding
        content_max_y = max(y for x, y in pos.values()) + self.config.node_height + self.config.canvas_padding

        # Wähle kleinstes passendes Format
        selected_format = 'A4'
        canvas_width, canvas_height = self.config.paper_formats['A4']

        for format_name, (width, height) in self.config.paper_formats.items():
            if content_max_x <= width and content_max_y <= height:
                selected_format = format_name
                canvas_width, canvas_height = width, height
                break

        return selected_format, canvas_width, canvas_height

    def create_edges(self, data: Dict[str, Any], pos: Dict[int, Tuple[float, float]]) -> str:
        """
        Erstellt SVG-Kanten (Pfeile) zwischen Tasks

        Args:
            data: Projektdaten mit Tasks
            pos: Dictionary mit Task-Positionen

        Returns:
            SVG-String mit allen Kanten
        """
        svg_edges = []
        node_center_x = self.config.edge_offset_x
        node_center_y = self.config.edge_offset_y

        for task in data['tasks']:
            task_id = task['id']
            x1, y1 = pos[task_id]

            for dep_id in task.get('dependencies', []):
                if dep_id in pos:
                    x2, y2 = pos[dep_id]
                    # Pfeil vom Zentrum zum Zentrum
                    start_x = x1 + node_center_x
                    start_y = y1 + node_center_y
                    end_x = x2 + node_center_x
                    end_y = y2 + node_center_y

                    arrow = f'<line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" ' \
                            f'stroke="{self.config.edge_color}" stroke-width="{self.config.edge_stroke_width}" ' \
                            f'marker-end="url(#arrowhead)"/>'
                    svg_edges.append(arrow)

        return '\n    '.join(svg_edges)

    def create_node(self, task: Dict[str, Any], cpm: Dict[str, Any], x: float, y: float) -> str:
        """
        Erstellt SVG-Node aus Template

        Args:
            task: Task-Daten
            cpm: CPM-Daten für Task
            x: X-Position
            y: Y-Position

        Returns:
            SVG-String für Node
        """
        task_id = task['id']
        task_name = task.get('name', f'Task {task_id}')

        # Hole CPM-Daten
        fb = cpm.get('faz', 0)
        fe = cpm.get('fez', 0)
        sb = cpm.get('saz', 0)
        se = cpm.get('sez', 0)
        gp = cpm.get('puffer', 0)
        fp = cpm.get('free_puffer', 0)
        is_critical = cpm.get('is_critical', False)

        # Farbe basierend auf kritischem Pfad
        fill_color = self.config.critical_path_color if is_critical else self.config.normal_path_color

        # Erstelle Node-SVG durch Ersetzen der Platzhalter
        node_svg = self.node_template

        # Ersetze Platzhalter
        node_svg = node_svg.replace(f'>{self.config.placeholders["fb"]}<', f'>{fb:.0f}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["fe"]}<', f'>{fe:.0f}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["sb"]}<', f'>{sb:.0f}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["se"]}<', f'>{se:.0f}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["gp"]}<', f'>{gp:.1f}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["id"]}<', f'>{task_id}<')
        node_svg = node_svg.replace(f'>{self.config.placeholders["description"]}<', f'>{task_name}<')

        # Ersetze Füllfarbe
        node_svg = node_svg.replace(f'fill:{self.config.normal_path_color}', f'fill:{fill_color}')

        # Extrahiere <g>-Inhalt
        match = re.search(r'<g\s+id="layer1"[^>]*>(.*?)</g>', node_svg, re.DOTALL)
        if not match:
            return ""

        g_content = match.group(1)

        # Korrigiere Position mit Template-Offset
        template_transform_match = re.search(r'transform="translate\(([^,]+),([^)]+)\)"', node_svg)
        if template_transform_match:
            offset_x = float(template_transform_match.group(1))
            offset_y = float(template_transform_match.group(2))
            corrected_x = x - offset_x
            corrected_y = y - offset_y
        else:
            corrected_x = x
            corrected_y = y

        return f'<g transform="translate({corrected_x}, {corrected_y})">{g_content}</g>'

    def create_nodes(self, data: Dict[str, Any], cpm_data: Dict[int, Dict[str, Any]],
                     pos: Dict[int, Tuple[float, float]]) -> str:
        """
        Erstellt alle SVG-Nodes

        Args:
            data: Projektdaten mit Tasks
            cpm_data: CPM-Daten für alle Tasks
            pos: Dictionary mit Task-Positionen

        Returns:
            SVG-String mit allen Nodes
        """
        svg_nodes = []

        for task in data['tasks']:
            task_id = task['id']
            x, y = pos[task_id]
            cpm = cpm_data.get(task_id, {})

            node_svg = self.create_node(task, cpm, x, y)
            if node_svg:
                svg_nodes.append(node_svg)

        return '\n    '.join(svg_nodes)

    def generate_svg(self, project_file: Path, output_dir: Optional[Path] = None) -> bool:
        """
        Generiert SVG-Graph aus Projektdatei

        Args:
            project_file: Pfad zur Projektdatei (JSON)
            output_dir: Ausgabeverzeichnis (Standard: gleiches Verzeichnis wie Projektdatei)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Lade Projektdaten
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'tasks' not in data:
                self.logger.error(f"Keine 'tasks' in Projektdatei gefunden: {project_file}")
                return False

            # Berechne CPM-Daten
            task_file = SimpleTaskFile.model_validate(data)
            cpm_data = task_file.calculate_cpm_for_tasks()

            # Berechne Layout
            pos = self.calculate_layout(data)

            # Wähle Papierformat
            selected_format, canvas_width, canvas_height = self.select_paper_format(pos)
            self.logger.info(f"Verwende Format {selected_format} ({canvas_width}x{canvas_height} mm) für {len(data['tasks'])} Tasks")

            # Erstelle SVG-Elemente
            svg_edges = self.create_edges(data, pos)
            svg_nodes = self.create_nodes(data, cpm_data, pos)

            # Erstelle vollständiges SVG-Dokument
            svg_document = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="{canvas_width}mm"
   height="{canvas_height}mm"
   viewBox="0 0 {canvas_width} {canvas_height}"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="{self.config.arrow_size}" markerHeight="{self.config.arrow_size}"
            refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="{self.config.edge_color}" />
    </marker>
  </defs>
  <g id="main">
    <!-- Kanten -->
    {svg_edges}

    <!-- Nodes -->
    {svg_nodes}
  </g>
</svg>'''

            # Bestimme Ausgabepfad
            if output_dir is None:
                output_dir = project_file.parent

            output_file = output_dir / f"{project_file.stem}_graph_templated.svg"

            # Speichere SVG
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(svg_document)

            self.logger.info(f"SVG-Graph (template-basiert) gespeichert als: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des SVG-Graphen: {e}", exc_info=True)
            return False
