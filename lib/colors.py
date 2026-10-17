"""
Colors
======

Hex-Farben (ohne '#') umrechnen und interpolieren, z. B. für automatische
Ressourcen-Farben.
"""

import configparser
from pathlib import Path
from typing import List, Optional, Tuple

from .paths import get_cfg_dir

DEFAULT_PALETTE = ["9B59B6", "3498DB", "27AE60", "F1C40F", "E67E22"]


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Konvertiert Hex-Farbe (mit oder ohne #) zu RGB-Tupel."""
    hex_color = hex_color.lstrip('#')
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Konvertiert RGB-Tupel zu Hex-Farbe ohne #."""
    return '{:02X}{:02X}{:02X}'.format(*rgb)


def interpolate_color(color_start: str, color_end: str, position: float) -> str:
    """Interpoliert linear zwischen zwei Hex-Farben (position 0.0 … 1.0)."""
    s = hex_to_rgb(color_start)
    e = hex_to_rgb(color_end)
    r, g, b = (int(s[i] + (e[i] - s[i]) * position) for i in range(3))
    return rgb_to_hex((r, g, b))


def interpolate_palette(palette: List[str], position: float) -> str:
    """Interpoliert entlang einer Palette mit mehreren Stützfarben (position 0.0 … 1.0)."""
    if len(palette) < 2:
        return palette[0] if palette else "888888"
    n_segments = len(palette) - 1
    scaled = position * n_segments
    idx = min(int(scaled), n_segments - 1)
    return interpolate_color(palette[idx], palette[idx + 1], scaled - idx)


def load_auto_color_range(cfg_dir: Optional[Path] = None) -> Tuple[str, str]:
    """Liest (color_start, color_end) aus defaults.cfg [ResourceAutoColor]."""
    config = configparser.ConfigParser()
    cfg_file = (cfg_dir or get_cfg_dir()) / "defaults.cfg"
    if cfg_file.exists():
        config.read(cfg_file, encoding='utf-8')
    return (
        config.get('ResourceAutoColor', 'color_start', fallback='4472C4').strip(),
        config.get('ResourceAutoColor', 'color_end', fallback='8B7AB8').strip(),
    )
