"""
Beispielprojekte der GUI
========================

Die Beispiele liegen im Repository unter ``examples/de`` und ``examples/en`` (je Sprache eine Fassung).
Die GUI zeigt die Fassung der aktiven Sprache. Rückfall, wenn ein Ordner fehlt: ``examples/de``,
``examples/`` selbst, zuletzt die im Paket moncapro mitgelieferten Beispiele.

Ordner ändern: Umgebungsvariable ``PV_EXAMPLES`` (Standard: ``<Projektordner>/examples``).
"""

import os
from pathlib import Path
from typing import Optional

from moncapro.paths import get_examples_dir as _package_examples_dir

from gui.i18n import get_language

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def examples_root() -> Path:
    """Wurzel der Beispiele ($PV_EXAMPLES oder <Projektordner>/examples)."""
    value = os.environ.get("PV_EXAMPLES")
    return Path(value) if value else PROJECT_ROOT / "examples"


def examples_dir(lang: Optional[str] = None) -> Path:
    """Beispielordner für die Sprache ``lang`` (Standard: aktive GUI-Sprache)."""
    lang = lang or get_language()
    root = examples_root()
    for candidate in (root / lang, root / "de", root):
        if any(candidate.glob("*.json")):
            return candidate
    return _package_examples_dir()
