"""
Ressourcen-Farben für die GUI
=============================

Ressourcen ohne eigene Farbe bekommen eine Farbe aus der Palette in
gui.cfg [resources_colours] (Fallback: defaults.cfg [ResourceAutoColor]).
"""

import configparser
from typing import Dict, List, Optional, Tuple

from lib.colors import DEFAULT_PALETTE, hex_to_rgb, interpolate_palette
from lib.paths import get_cfg_dir

RGB = Tuple[int, int, int]


def _palette() -> List[str]:
    cfg = configparser.ConfigParser()
    cfg_dir = get_cfg_dir()
    cfg.read([str(cfg_dir / "gui.cfg"), str(cfg_dir / "defaults.cfg")], encoding="utf-8")

    if cfg.has_section("resources_colours"):
        raw = cfg.get("resources_colours", "palette", fallback="").strip()
        if raw:
            return [c.strip() for c in raw.split(",") if c.strip()]
        start = cfg.get("resources_colours", "color_start", fallback="").strip()
        end = cfg.get("resources_colours", "color_end", fallback="").strip()
        if start and end:
            return [start, end]
    elif cfg.has_section("ResourceAutoColor"):
        return [
            cfg.get("ResourceAutoColor", "color_start", fallback="4472C4").strip(),
            cfg.get("ResourceAutoColor", "color_end", fallback="8B7AB8").strip(),
        ]
    return list(DEFAULT_PALETTE)


def _own_color(resource) -> Optional[RGB]:
    try:
        return hex_to_rgb(resource.color) if resource.color else None
    except ValueError:
        return None


def resource_color_map(project) -> Dict[str, RGB]:
    """resource_id → (R, G, B): eigene Farbe der Ressource, sonst gleichmäßig über die
    Palette verteilt (sortiert nach ID)."""
    if not project or not project.resources:
        return {}
    palette = _palette()
    resources = sorted(project.resources, key=lambda r: r.id)
    n = len(resources)
    return {
        r.id: _own_color(r) or hex_to_rgb(interpolate_palette(palette, i / (n - 1) if n > 1 else 0.0))
        for i, r in enumerate(resources)
    }


def next_resource_color(project) -> str:
    """Vorschlagsfarbe (Hex ohne #) für eine neue Ressource."""
    n_existing = len(project.resources) if project and project.resources else 0
    return interpolate_palette(_palette(), n_existing / max(n_existing, 1))
