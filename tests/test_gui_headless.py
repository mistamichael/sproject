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

from gui.i18n import t                                   # noqa: E402
from moncapro.models import load_project                     # noqa: E402
from gui.examples import examples_dir                  # noqa: E402
from moncapro.paths import get_cfg_dir                  # noqa: E402
from moncapro.schedule import build_schedule                  # noqa: E402

EXAMPLES = examples_dir("de")

# Projektnamen aus den Dateien lesen, nicht als Text im Test festschreiben
TANK_NAME = load_project(EXAMPLES / "tankdesign.json").project
PIZZA_NAME = load_project(EXAMPLES / "pizza.json").project


@pytest.fixture
def editor():
    dpg.create_context()
    from gui.app import create_app
    app = create_app()
    yield app
    dpg.destroy_context()


def _sidebar_example_paths():
    children = dpg.get_item_children("sidebar_example_list", 1)
    return [dpg.get_item_user_data(c)[1] for c in children if dpg.get_item_user_data(c)]


def test_sidebar_examples_follow_the_language(editor):
    """Die Beispielliste zeigt die Fassung der aktiven Sprache und wird beim Wechsel neu aufgebaut."""
    from gui.components.sidebar import refresh_example_list
    from gui.i18n import get_language, set_language

    previous = get_language()      # nicht über _switch_language: das würde gui.cfg überschreiben
    try:
        for lang in ("en", "de"):
            set_language(lang)
            refresh_example_list(editor)
            paths = _sidebar_example_paths()
            assert paths and all(p.parent.name == lang for p in paths), lang
            assert [p.name for p in paths] == sorted(f.name for f in examples_dir(lang).glob("*.json"))
    finally:
        set_language(previous)


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
    # run_calculation fängt Fehler ab (z. B. beim Zeichnen der Diagramme) und meldet sie nur in der Statuszeile
    assert not dpg.get_value("statusbar_text").startswith(t("status.calc_error", error="")),         dpg.get_value("statusbar_text")
    expected = build_schedule(load_project(example), cfg_dir=get_cfg_dir())
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


# ---------------------------------------------------------------------------
# Verbindung zum sproject-Server (gui/server_link.py)
# ---------------------------------------------------------------------------

class _Server:
    """Echter sproject-Server (uvicorn) auf freiem Port in einem Hintergrund-Thread."""

    def __init__(self):
        import socket
        import tempfile
        import threading

        import uvicorn

        from moncapro.api import ProjectSession
        from moncapro.mcp.server import build_server

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.session = ProjectSession()
        self.session.backup_dir = Path(tempfile.mkdtemp(prefix="sproject_backup_"))
        app = build_server(self.session, port=self.port).streamable_http_app()
        self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning"))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        self._wait(lambda: self.server.started, "Server startet nicht")

    @staticmethod
    def _wait(condition, message, timeout=15.0):
        import time
        deadline = time.time() + timeout
        while not condition():
            assert time.time() < deadline, message
            time.sleep(0.02)

    def stop(self):
        self.server.should_exit = True
        self.server.force_exit = True      # nicht auf offene Streams warten
        self.thread.join(timeout=5)


def _pump(link, condition, message, timeout=15.0):
    """Wie die Render-Schleife: process() aufrufen, bis condition() gilt (Abfrage sofort statt jede Sekunde)."""
    import time
    deadline = time.time() + timeout
    while not condition():
        assert time.time() < deadline, message
        link.process(now=time.monotonic() + 3600)
        time.sleep(0.01)


def _claude(port, *calls):
    """Zweiter MCP-Client (wie Claude Code): ruft Werkzeuge nacheinander auf, gibt die Ergebnisse zurück."""
    import asyncio

    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def run():
        results = []
        async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for tool, args in calls:
                    res = await session.call_tool(tool, args)
                    results.append(res)
        return results

    return asyncio.run(run())


@pytest.fixture
def server():
    srv = _Server()
    yield srv
    srv.stop()


def test_server_link_shares_one_project(editor, server):
    """GUI und Claude arbeiten über den einen Server am selben Projekt – in beide Richtungen."""
    from gui.server_link import ServerLink

    editor.load_from_file(EXAMPLES / "tankdesign.json")
    link = ServerLink(editor, port=server.port)
    link.backup_dir = server.session.backup_dir
    assert link.connect()
    _pump(link, lambda: link.connected, "verbindet nicht")

    # 1. Server war leer → das GUI-Projekt landet auf dem Server
    _pump(link, lambda: server.session.project is not None, "GUI-Projekt nicht übertragen")
    assert server.session.project.project == TANK_NAME
    count = len(server.session.project.tasks)

    # 2. Claude fügt einen Task hinzu → erscheint in der GUI
    added, = _claude(server.port, ("add_task", {"task": {"name": "Abnahme durch Claude", "duration": "1d"}}))
    assert not added.isError
    _pump(link, lambda: any(r.name == "Abnahme durch Claude" for r in editor.task_rows), "Claude-Task fehlt in der GUI")
    assert len(editor.project.tasks) == count + 1

    # 3. Eingabe in der GUI → landet auf dem Server
    dpg.set_value("inp_project_name", "In der GUI umbenannt")
    _pump(link, lambda: server.session.project.project == "In der GUI umbenannt", "GUI-Eingabe nicht übertragen")

    link.disconnect()
    assert link.state == "disconnected"


def test_server_link_takes_server_project_and_resolves_conflict(editor, server):
    """Hat der Server schon ein Projekt, übernimmt die GUI es; bei gleichzeitiger Änderung gewinnt der Server."""
    from gui.server_link import ServerLink

    server.session.load(EXAMPLES / "pizza.json")
    editor.load_from_file(EXAMPLES / "tankdesign.json")
    editor.dirty = True
    asked = []
    link = ServerLink(editor, port=server.port, confirm=lambda msg, yes, no: (asked.append(msg), yes()))
    link.backup_dir = server.session.backup_dir
    link.connect()
    _pump(link, lambda: link.connected, "verbindet nicht")
    assert asked, "ungespeicherte GUI-Änderungen ohne Rückfrage verworfen"
    assert editor.project.project == PIZZA_NAME

    # gleichzeitig: GUI ändert lokal, Claude ändert auf dem Server
    dpg.set_value("inp_project_name", "GUI-Name")
    _claude(server.port, ("patch_project", {"fields": {"project": "Claude-Name"}}))
    _pump(link, lambda: editor.project.project == "Claude-Name", "Server-Stand nicht übernommen")
    assert server.session.project.project == "Claude-Name"
    assert dpg.get_value("statusbar_text").startswith(t("status.server_conflict"))
    link.disconnect()


def test_server_link_without_server_offers_start(editor):
    from gui.server_link import ServerLink
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    link = ServerLink(editor, port=port)
    assert link.connect() is False
    assert link.state == "disconnected"
    assert dpg.get_value("statusbar_text") == t("status.server_not_found", url=link.url)


def test_claude_replaces_project_while_gui_connected(editor, server):
    """Claude legt ein neues Projekt an: Server sichert, Claude bekommt eine Warnung, die GUI einen Hinweis
    – und noch nicht übertragene GUI-Eingaben werden ebenfalls gesichert."""
    from gui.server_link import ServerLink

    editor.load_from_file(EXAMPLES / "tankdesign.json")
    infos = []
    link = ServerLink(editor, port=server.port, inform=infos.append)
    link.backup_dir = server.session.backup_dir
    link.connect()
    _pump(link, lambda: link.connected and server.session.project is not None, "verbindet nicht")

    dpg.set_value("inp_project_name", "Ungesendete GUI-Eingabe")       # noch nicht übertragen
    result, = _claude(server.port, ("new_project", {"name": "Aus Excel"}))
    warning = result.structuredContent["result"]["warning"]
    assert TANK_NAME in warning and "Aus Excel" in warning   # Claude erfährt es

    _pump(link, lambda: infos, "kein Hinweis in der GUI")
    assert editor.project.project == "Aus Excel"
    switch = server.session.last_switch
    assert switch["backup"] in infos[0]
    assert load_project(switch["backup"]).project == TANK_NAME   # Server-Sicherung
    local = [p for p in server.session.backup_dir.glob("*.json") if "Ungesendete" in p.name]
    assert len(local) == 1 and str(local[0]) in infos[0]                  # GUI-Eingaben gesichert
    link.disconnect()


def test_gui_opens_other_file_while_connected(editor, server):
    """Die GUI öffnet eine andere Datei: Server sichert, Claudes nächster Aufruf wird abgelehnt und gemeldet."""
    import asyncio
    import threading

    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from gui.server_link import ServerLink

    editor.load_from_file(EXAMPLES / "tankdesign.json")
    link = ServerLink(editor, port=server.port)
    link.backup_dir = server.session.backup_dir
    link.connect()
    _pump(link, lambda: link.connected and server.session.project is not None, "verbindet nicht")

    # Claude hält eine Sitzung offen: erst ein Aufruf, dann wechselt die GUI, dann zwei weitere Aufrufe
    gui_switched, results = threading.Event(), []

    async def claude():
        async with streamable_http_client(f"http://127.0.0.1:{server.port}/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                results.append(await session.call_tool("get_overview", {}))
                await asyncio.get_running_loop().run_in_executor(None, gui_switched.wait, 30)
                results.append(await session.call_tool("add_task", {"task": {"name": "X", "duration": "1d"}}))
                results.append(await session.call_tool("add_task", {"task": {"name": "X", "duration": "1d"}}))

    thread = threading.Thread(target=lambda: asyncio.run(claude()))
    thread.start()
    _pump(link, lambda: results, "Claude-Aufruf fehlt")

    editor.load_from_file(EXAMPLES / "pizza.json")                       # Wechsel in der GUI
    _pump(link, lambda: server.session.project.project == PIZZA_NAME, "GUI-Wechsel nicht übertragen")
    switch = server.session.last_switch
    assert switch["old"] == TANK_NAME and switch["reason"] == "replace_project"
    assert load_project(switch["backup"]).project == TANK_NAME
    _pump(link, lambda: dpg.get_value("statusbar_text").startswith(t("status.server_replaced_by_gui", text="")[:20]),
          "keine Meldung in der GUI")

    gui_switched.set()
    thread.join(timeout=30)
    blocked, retried = results[1], results[2]
    assert blocked.isError and "NICHT ausgeführt" in blocked.content[0].text and switch["backup"] in blocked.content[0].text
    assert not retried.isError                                            # zweiter Versuch läuft
    assert server.session.project.project == PIZZA_NAME
    link.disconnect()
