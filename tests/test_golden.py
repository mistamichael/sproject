"""
Golden-File-Tests über alle Beispielprojekte
=============================================

Verarbeitet jede Datei aus examples/ über die CLI und vergleicht die Exporte
(JSON, TXT, Markdown) mit den Referenzdateien in tests/golden/.

Referenzen neu erzeugen (nur nach bewusster Ergebnisänderung):

    UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))
GOLDEN_DIR = Path(__file__).parent / "golden"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"

# Feste Startzeit für Beispiele ohne project_start (sonst "heute" → nicht reproduzierbar)
FIXED_START = "2026-03-02"

# Zeilen mit Erzeugungszeitpunkt werden vor dem Vergleich entfernt
_VOLATILE = re.compile(r'.*("calculation_date"|Erstellt am|Created on|Generated).*\n?')


def _normalize(text: str) -> str:
    return _VOLATILE.sub("", text.replace("\r\n", "\n"))


def _run_cli(example: Path, work_dir: Path) -> Path:
    data = json.loads(example.read_text(encoding="utf-8"))
    data.setdefault("project_start", FIXED_START)
    project_file = work_dir / example.name
    project_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    out_dir = work_dir / "out"
    env = {**os.environ, "PV_CFG": str(ROOT / "cfg"), "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "lib" / "sproject.py"),
         "--project", str(project_file),
         "--output-dir", str(out_dir),
         "--cfg-dir", str(ROOT / "cfg"),
         "--export", "json,txt,md"],
        cwd=work_dir, env=env, capture_output=True, text=True, encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return out_dir


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_example_matches_golden(example: Path, tmp_path: Path) -> None:
    out_dir = _run_cli(example, tmp_path)
    outputs = {
        f"{example.stem}_network_plan.json": out_dir / f"{example.stem}_network_plan.json",
        f"{example.stem}.txt": out_dir / f"{example.stem}.txt",
        f"{example.stem}.md": out_dir / f"{example.stem}.md",
    }
    GOLDEN_DIR.mkdir(exist_ok=True)
    for name, produced in outputs.items():
        assert produced.exists(), f"{name} wurde nicht erzeugt"
        actual = _normalize(produced.read_text(encoding="utf-8"))
        golden = GOLDEN_DIR / name
        if UPDATE or not golden.exists():
            golden.write_text(actual, encoding="utf-8", newline="\n")
            continue
        expected = golden.read_text(encoding="utf-8")
        assert actual == expected, f"{name} weicht von der Referenz ab"
