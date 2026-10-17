"""
GUI-Tests ohne Fenster (Dear PyGui-Kontext ohne Viewport)
=========================================================

Prüft den Datenfluss Widgets ↔ Modell: Laden, Bearbeiten in den Tabellen,
Berechnen und Speichern.
"""

import json
from pathlib import Path

import pytest

dpg = pytest.importorskip("dearpygui.dearpygui")

from lib.models import load_project                     # noqa: E402
from lib.schedule import build_schedule                  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


@pytest.fixture
def editor():
    dpg.create_context()
    from gui.app import create_app
    app = create_app()
    yield app
    dpg.destroy_context()


def test_load_save_round_trip_is_lossless(editor, tmp_path):
    for example in sorted(EXAMPLES.glob("*.json")):
        editor.load_from_file(example)
        out = editor.save_to_file(tmp_path / example.name)
        original = load_project(example).model_dump(by_alias=True, exclude_none=True)
        saved = load_project(out).model_dump(by_alias=True, exclude_none=True)
        assert saved == original, example.name


def test_gui_calculation_matches_cli(editor):
    """B1: GUI rechnet über build_schedule – inkl. Expansion von Loop-Tasks."""
    example = EXAMPLES / "erdaushub.json"
    editor.load_from_file(example)
    editor.run_calculation()
    expected = build_schedule(load_project(example), cfg_dir=ROOT / "cfg")
    assert editor.schedule is not None
    assert editor.schedule.cpm.project_duration == expected.cpm.project_duration
    assert len(editor.schedule.cpm.tasks) == len(expected.cpm.tasks) > 2


def test_inline_edits_in_sections_are_saved(editor, tmp_path):
    """B5: Änderungen in Ressourcen-, Personen- und Ruhezeit-Tabellen landen im Modell."""
    editor.load_from_file(EXAMPLES / "fassadenbau.json")
    project = editor.project
    assert project.resources and project.persons and project.resting_times

    dpg.set_value("resources_content_0_name", "Neuer Name")
    dpg.set_value("persons_content_0_hourly_rate", "77.5")
    dpg.set_value("resting_times_content_0_duration", "20m")

    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    assert data["resources"][0]["name"] == "Neuer Name"
    assert data["persons"][0]["hourly_rate"] == 77.5
    assert data["resting_times"][0]["duration"] == "20m"


def test_task_edits_and_new_rows(editor):
    editor.load_from_file(EXAMPLES / "tankdesign.json")
    n = len(editor.project.tasks)
    dpg.set_value("task_0_name", "Umbenannt")
    editor.add_task_row()
    editor.sync_to_model()
    assert editor.project.tasks[0].name == "Umbenannt"
    assert len(editor.project.tasks) == n + 1


def test_report_export_uses_shared_exporters(editor, tmp_path):
    """B8: GUI-Exporte entsprechen den CLI-Exporten."""
    editor.load_from_file(EXAMPLES / "software_simple.json")
    editor.run_calculation()
    for fmt in ("txt", "md", "xlsx"):
        assert editor.export_report(fmt, tmp_path).exists()
    with pytest.raises(RuntimeError):
        editor.dirty = True     # invalidiert das Ergebnis
        editor.export_report("txt", tmp_path)
