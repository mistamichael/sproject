"""
Laden → Speichern aller Beispiel-Projekte muss das JSON unverändert lassen.
"""

import json
from pathlib import Path

import pytest

from lib.models import load_project, save_project

EXAMPLES = sorted((Path(__file__).resolve().parent.parent / "examples").glob("*.json"))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_json_round_trip(example: Path, tmp_path: Path) -> None:
    out = tmp_path / example.name
    save_project(load_project(example), out)
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(example.read_text(encoding="utf-8"))
