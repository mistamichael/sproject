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


def test_uncertainty_edits_survive_task_rebuild(editor, tmp_path):
    """Unsicherheiten hängen an den Task-Objekten, die sync_to_model() neu aufbaut."""
    editor.load_from_file(EXAMPLES / "software_simple.json")
    assert editor.active_sections["uncertainty"] and editor.active_sections["scenarios"]
    task_id = editor.sections.uncertainty.shown_rows[0].task.id

    dpg.set_value("uncertainty_content_0_range_max", "80h")
    editor.run_calculation()                       # baut die Tasks neu auf
    dpg.set_value("uncertainty_content_0_risk_probability", "35")
    dpg.set_value("task_0_name", "Umbenannt")      # Tabellenänderung parallel

    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    task = next(t for t in data["tasks"] if t["id"] == task_id)
    assert task["duration_range"][1] == "80h"
    assert task["risk"]["probability"] == 0.35
    assert data["tasks"][0]["name"] == "Umbenannt"


def test_add_and_remove_uncertainty_and_scenarios(editor, tmp_path):
    editor.load_from_file(EXAMPLES / "tankdesign.json")
    first = editor.project.tasks[0]
    editor.sections._confirm_uncertainty({"task": f"{first.id}: {first.name}", "range_max": "20d",
                                          "risk_probability": "10", "risk_delay": "2d"})
    editor.sections._confirm_scenario({"name": "Lieferverzug", "probability": "25"})
    editor.sections._confirm_change({"scenario": "Lieferverzug", "target": "Task",
                                     "target_id": str(first.id), "change": "delay=5d"})
    dpg.set_value("scenarios_content_0_description", "Material kommt später")

    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    assert data["tasks"][0]["risk"] == {"probability": 0.1, "delay": "2d"}
    assert data["tasks"][0]["duration_range"][1] == "20d"
    assert data["scenarios"] == [{"name": "Lieferverzug", "description": "Material kommt später",
                                  "probability": 0.25, "changes": [{"task": first.id, "delay": "5d"}]}]

    editor.sections._remove_uncertainty(0)
    editor.sections._remove_change(0)
    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    assert "risk" not in data["tasks"][0] and "duration_range" not in data["tasks"][0]
    assert data["scenarios"][0]["changes"] == []


def _double_click_row(section, row: int) -> None:
    """Simuliert den Doppelklick-Handler auf eine Zelle der Zeile."""
    item = next(item for item, r in section._row_of_item.items() if r == row)
    section._on_row_double_click(None, (0, item))


def _press(dialog: str, label: str) -> None:
    def buttons(parent):
        for child in dpg.get_item_children(parent, 1) or []:
            if dpg.get_item_type(child) == "mvAppItemType::mvButton":
                yield child
            yield from buttons(child)
    button = next(b for b in buttons(dialog) if dpg.get_item_label(b) == label)
    dpg.get_item_callback(button)()


def test_double_click_opens_prefilled_edit_dialogs(editor, tmp_path):
    from gui.i18n import t
    editor.load_from_file(EXAMPLES / "software_simple.json")
    sections = editor.sections

    _double_click_row(sections.uncertainty, 0)
    assert dpg.get_value("edit_uncertainty_dialog_range_max") == "72h"
    assert dpg.get_value("edit_uncertainty_dialog_risk_probability") == "20"
    dpg.set_value("edit_uncertainty_dialog_range_max", "90h")
    dpg.set_value("edit_uncertainty_dialog_risk_probability", "")      # Risiko entfernen
    _press("edit_uncertainty_dialog", t("button.apply"))

    _double_click_row(sections.scenarios, 0)
    assert dpg.get_value("edit_scenario_dialog_probability") == "15"
    dpg.set_value("edit_scenario_dialog_name", "Alice zwei Wochen krank")
    _press("edit_scenario_dialog", t("button.apply"))

    _double_click_row(sections.scenario_changes, 1)                    # Backend 50 % aufwendiger
    assert dpg.get_value("edit_change_dialog_change") == "duration_factor=1.5"
    dpg.set_value("edit_change_dialog_change", "duration_factor=2")
    dpg.set_value("edit_change_dialog_scenario", "Abnahme bis 27.03.")  # in anderes Szenario verschieben
    _press("edit_change_dialog", t("button.apply"))

    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    task = next(t for t in data["tasks"] if t["id"] == 4)
    assert task["duration_range"] == ["32h", "90h"] and "risk" not in task
    names = [s["name"] for s in data["scenarios"]]
    assert names[0] == "Alice zwei Wochen krank"
    assert data["scenarios"][1]["changes"] == []
    assert data["scenarios"][2]["changes"][-1] == {"task": 4, "duration_factor": 2.0}


def test_add_resource_dialog_has_inline_color_picker(editor, tmp_path):
    """Im modalen Dialog klappt der Farbwähler auf (kein zweites modales Fenster)."""
    from gui.i18n import t
    editor.load_from_file(EXAMPLES / "fassadenbau.json")
    editor.sections.add_resource()
    picker, height = "add_resource_dialog_color_picker", dpg.get_item_height("add_resource_dialog")
    assert not dpg.is_item_shown(picker)

    dpg.set_value("add_resource_dialog_id", "R_KRAN")
    dpg.get_item_callback("add_resource_dialog_color_swatch")()          # Klick aufs Farbfeld
    assert dpg.is_item_shown(picker) and dpg.get_item_height("add_resource_dialog") > height
    dpg.set_value(picker, (200, 30, 40, 255))
    dpg.get_item_callback(picker)()                                      # Farbe gewählt
    assert dpg.get_value("add_resource_dialog_color") == "C81E28"
    _press("add_resource_dialog", t("button.add"))

    data = json.loads(editor.save_to_file(tmp_path / "out.json").read_text(encoding="utf-8"))
    assert next(r for r in data["resources"] if r["id"] == "R_KRAN")["color"] == "C81E28"


def test_swatch_without_own_color_shows_palette_color(editor):
    from gui.colors import resource_color_map
    editor.load_from_file(EXAMPLES / "software_simple.json")
    resource = editor.project.resources[0]
    assert not resource.color
    swatch = [round(v) for v in dpg.get_value("resources_content_0_color_swatch")[:3]]
    assert tuple(swatch) == resource_color_map(editor.project)[resource.id]


def test_range_warning_follows_task_table_edits(editor):
    """Dauer in der Aufgaben-Tabelle ändern → nach dem Berechnen warnt Sektion 6."""
    editor.load_from_file(EXAMPLES / "software_simple.json")
    assert not dpg.does_item_exist("uncertainty_content_warning")
    row = next(i for i, r in enumerate(editor.task_rows) if str(r.id) == "4")   # Backend, Bereich 32h–72h
    dpg.set_value(f"task_{row}_duration", "80h")
    editor.run_calculation()
    assert "4" in dpg.get_value("uncertainty_content_warning")

    dpg.set_value("uncertainty_content_0_range_max", "96h")                      # Bereich korrigieren
    editor.run_calculation()
    assert not dpg.does_item_exist("uncertainty_content_warning")


def test_report_export_uses_shared_exporters(editor, tmp_path):
    """B8: GUI-Exporte entsprechen den CLI-Exporten."""
    editor.load_from_file(EXAMPLES / "software_simple.json")
    editor.run_calculation()
    for fmt in ("txt", "md", "xlsx"):
        assert editor.export_report(fmt, tmp_path).exists()
    with pytest.raises(RuntimeError):
        editor.dirty = True     # invalidiert das Ergebnis
        editor.export_report("txt", tmp_path)
