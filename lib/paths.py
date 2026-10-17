"""
Paths
=====

Auflösung der Projektverzeichnisse über die PV_*-Umgebungsvariablen
(gesetzt durch bin/setenv.*), mit Fallback relativ zum Projekt-Root.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_dir(var: str, default: str) -> Path:
    value = os.environ.get(var)
    return Path(value) if value else PROJECT_ROOT / default


def get_cfg_dir() -> Path:
    """Konfigurationsverzeichnis ($PV_CFG oder <root>/cfg)."""
    return _env_dir('PV_CFG', 'cfg')


def get_results_dir(create: bool = True) -> Path:
    """Ausgabeverzeichnis für Exporte ($PV_RESULTS oder <root>/results)."""
    path = _env_dir('PV_RESULTS', 'results')
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_work_dir() -> Path:
    """Default-Speicherort für neue Projekte ($PV_WORK oder aktuelles Verzeichnis)."""
    value = os.environ.get('PV_WORK')
    return Path(value) if value else Path.cwd()
