"""
Alle sichtbaren Texte der GUI nur mit Zeichen, die die Schrift darstellt
=======================================================================

Dear PyGui lädt aus der Schrift nur die Bereiche aus cfg/gui.cfg ([font] ranges) plus den Standardbereich
(ASCII und Latin-1), und nur Zeichen, die die Schriftdatei besitzt. Alles andere erscheint als Platzhalter
("?" oder Kästchen) – zum Beispiel Emoji, ✔, ✕, ⚠ oder ▶ in Segoe UI. Ist die Schriftdatei vorhanden, wird gegen ihren
Glyphenvorrat geprüft (braucht fonttools), sonst nur gegen die Bereiche.
Der Test prüft die Übersetzungen und alle Zeichenketten im GUI-Code (ohne Docstrings und Kommentare).
"""

import ast
import importlib.metadata
from pathlib import Path

import pytest

from gui.gui_config import load_gui_config
from gui.i18n import _TRANSLATIONS

GUI_DIR = Path(__file__).resolve().parent.parent / "gui"


def _font_glyphs():
    """Zeichen, die die konfigurierte Schriftdatei tatsächlich enthält (None, wenn die Datei fehlt)."""
    path = load_gui_config().section("font").get("path", "")
    if not path or not Path(path).exists():
        return None
    ttlib = pytest.importorskip("fontTools.ttLib")
    return set(ttlib.TTFont(path).getBestCmap())


def _allowed():
    """Darstellbar: die Schrift besitzt das Zeichen und (nur Dear PyGui 1.x) sein Bereich wird geladen."""
    ranges = [(0x20, 0xFF)] + [tuple(r) for r in load_gui_config().section("font").get("ranges", [])]
    if int(importlib.metadata.version("dearpygui").split(".")[0]) >= 2:
        ranges = [(0, 0x10FFFF)]                          # Bereiche sind dort automatisch
    glyphs = _font_glyphs()
    return lambda ch: ch in "\n\t" or (any(a <= ord(ch) <= b for a, b in ranges) and (glyphs is None or ord(ch) in glyphs))


def _bad_chars(text, allowed):
    return sorted({ch for ch in text if not allowed(ch)})


def _string_literals(path: Path):
    """Zeichenketten des Moduls ohne Modul-, Klassen- und Funktions-Docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.lineno, node.value


def test_translations_use_only_displayable_characters():
    allowed = _allowed()
    problems = {f"{lang}:{key}": _bad_chars(text, allowed)
                for lang, texts in _TRANSLATIONS.items() for key, text in texts.items() if _bad_chars(text, allowed)}
    assert not problems, problems


def test_code_strings_use_only_displayable_characters():
    allowed = _allowed()
    problems = {f"{p.relative_to(GUI_DIR.parent).as_posix()}:{line}": _bad_chars(text, allowed)
                for p in sorted(GUI_DIR.rglob("*.py")) for line, text in _string_literals(p) if _bad_chars(text, allowed)}
    assert not problems, problems
