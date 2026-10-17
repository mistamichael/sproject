"""
Export configuration
====================

Gemeinsamer Loader für Beschriftungen und Sektionsreihenfolgen der Exporte
(defaults.cfg [lang] + <format>_export.cfg).
"""

import configparser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .paths import get_cfg_dir


def _read(cfg_dir: Optional[Path], *filenames: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    base = cfg_dir or get_cfg_dir()
    for name in filenames:
        cfg_file = base / name
        if cfg_file.exists():
            config.read(cfg_file, encoding='utf-8')
    return config


def _section_values(config: configparser.ConfigParser, section: str) -> Dict[str, str]:
    if not config.has_section(section):
        return {}
    return {key: val for key, val in config.items(section) if val}


def load_labels(cfg_dir: Optional[Path] = None, lang: str = 'de') -> Dict[str, str]:
    """Beschriftungen aus der [lang]-Sektion von defaults.cfg."""
    return _section_values(_read(cfg_dir, 'defaults.cfg'), lang)


def load_export_config(
    cfg_dir: Optional[Path],
    filename: str,
    default_order: List[str],
    default_headings: Dict[str, str],
    lang: str = 'de',
) -> Tuple[List[str], Dict[str, str]]:
    """
    Liest section_order aus [sections] und Überschriften aus [lang].

    Priorität: Python-Defaults → defaults.cfg [lang] → <filename> [lang].

    Returns:
        (section_order, headings)
    """
    config = _read(cfg_dir, 'defaults.cfg', filename)
    raw_order = config.get('sections', 'section_order', fallback=None)
    section_order = (
        [s.strip() for s in raw_order.split(',') if s.strip()]
        if raw_order else list(default_order)
    )
    headings = {**default_headings, **_section_values(config, lang)}
    return section_order, headings
