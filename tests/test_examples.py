"""
Tests für die Beispielprojekte in examples/de und examples/en
==============================================================

Beide Sprachfassungen müssen dieselben Dateien, dieselbe Struktur und dieselben Rechenergebnisse haben –
nur die Anzeigetexte unterscheiden sich. Dazu die Auswahl des Ordners in gui/examples.py.
"""

import json
from pathlib import Path

import pytest

from gui.examples import examples_dir, examples_root
from moncapro.models import load_project
from moncapro.schedule import build_schedule

DE = examples_root() / "de"
EN = examples_root() / "en"
NAMES = sorted(p.name for p in DE.glob("*.json"))

# Felder, deren Werte Logik tragen (IDs, Dauern, Abhängigkeiten, Formeln) und nicht übersetzt werden
LOGIC_KEYS = ("id", "duration", "successors", "successors_aa", "successors_ee", "resources", "person_id",
              "duration_formula", "loop_until")


def _skeleton(obj):
    """Struktur ohne Zeichenketten-Inhalte (Schlüssel, Zahlen, Wahrheitswerte bleiben)."""
    if isinstance(obj, dict):
        return {k: _skeleton(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_skeleton(v) for v in obj]
    return obj if isinstance(obj, (int, float, bool)) or obj is None else "str"


def _logic_values(obj):
    out = []

    def walk(x):
        if isinstance(x, dict):
            for key, value in x.items():
                if key in LOGIC_KEYS and not (isinstance(value, list) and any(isinstance(i, dict) for i in value)):
                    out.append((key, json.dumps(value)))
                walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)
    walk(obj)
    return out


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_both_languages_have_the_same_files():
    assert NAMES, "keine Beispiele in examples/de"
    assert NAMES == sorted(p.name for p in EN.glob("*.json"))


@pytest.mark.parametrize("name", NAMES)
def test_language_versions_differ_only_in_texts(name):
    de, en = _load(DE / name), _load(EN / name)
    assert _skeleton(de) == _skeleton(en)
    assert _logic_values(de) == _logic_values(en)


@pytest.mark.parametrize("name", NAMES)
def test_language_versions_calculate_the_same(name):
    def result(path):
        schedule = build_schedule(load_project(path), start_date="2026-03-02")
        return len(schedule.project.tasks), str(schedule.cpm.project_duration)

    assert result(DE / name) == result(EN / name)


def test_examples_dir_follows_the_language(monkeypatch, tmp_path):
    monkeypatch.setenv("PV_EXAMPLES", str(tmp_path))
    for lang in ("de", "en"):
        (tmp_path / lang).mkdir()
        (tmp_path / lang / "x.json").write_text("{}", encoding="utf-8")
    assert examples_dir("en") == tmp_path / "en"
    assert examples_dir("de") == tmp_path / "de"


def test_examples_dir_falls_back(monkeypatch, tmp_path):
    from moncapro.paths import get_examples_dir
    monkeypatch.setenv("PV_EXAMPLES", str(tmp_path))
    assert examples_dir("en") == get_examples_dir()                 # nichts vorhanden → Paket moncapro
    (tmp_path / "de").mkdir()
    (tmp_path / "de" / "x.json").write_text("{}", encoding="utf-8")
    assert examples_dir("en") == tmp_path / "de"                    # en fehlt → de
