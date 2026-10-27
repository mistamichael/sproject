"""
Tests für lib/api.py (ProjectSession) und den MCP-Server
=========================================================
"""

import asyncio
from pathlib import Path

import pytest

from lib.api import ApiError, ProjectSession
from lib.models import load_project
from lib.schedule import build_schedule

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))


@pytest.fixture
def session() -> ProjectSession:
    s = ProjectSession()
    s.new_project("Garage", project_start="2026-04-01")
    fundament = s.add_task({"name": "Fundament", "duration": "3d"})
    mauern = s.add_task({"name": "Mauern", "duration": "5d"})
    dach = s.add_task({"name": "Dach", "duration": "2d"})
    s.add_dependency(fundament, mauern)
    s.add_dependency(str(mauern), dach)       # IDs dürfen auch als Text kommen
    return s


def test_build_and_calculate(session):
    result = session.calculate()
    assert result["duration_days"] == 10.0
    assert [c["id"] for c in result["critical_path"]] == [1, 2, 3]
    assert result["start"] == "2026-04-01"
    assert session.validate() == []


def test_add_task_returns_id(session):
    assert session.add_task({"name": "Abnahme"}) == 4
    assert session.add_task({"id": "A-1", "name": "eigene ID"}) == "A-1"
    assert session.add_task({"id": "10", "name": "Zahl als Text"}) == 10
    with pytest.raises(ApiError):
        session.add_task({"id": 2, "name": "doppelt"})


def test_get_task_is_normalized(session):
    tid = session.add_task({"name": "Prüfung", "duration": "5"})
    assert session.get_task(tid) == {"id": tid, "name": "Prüfung", "duration": "5d"}
    assert session.update_task(tid, {"duration": "2"})["duration"] == "2d"
    with pytest.raises(ApiError):
        session.get_task(99)


def test_invalid_input_changes_nothing(session):
    before = session.get_project()
    with pytest.raises(ApiError):
        session.update_task(2, {"duration": "xx"})
    with pytest.raises(ApiError):
        session.add_dependency(1, 99)
    with pytest.raises(ApiError):
        session.add_dependency(1, 2, "XY")
    assert session.get_project() == before


def test_cycle_is_reported(session):
    session.add_dependency(3, 1)
    issues = session.validate()
    assert len(issues) == 1 and "Zyklische" in issues[0]


def test_remove_task_cleans_successors(session):
    assert session.remove_task(2) == [1, 3]
    assert all(2 not in t.get("successors", []) for t in session.get_project()["tasks"])


def test_dependency_types(session):
    session.add_dependency(1, 3, "aa")
    task = session.get_project()["tasks"][0]
    assert task["successors"] == [2] and task["successors_aa"] == [3]
    session.remove_dependency(1, 3)
    assert session.get_project()["tasks"][0]["successors_aa"] == []


def test_resources_and_persons(session):
    session.upsert_item("persons", {"id": "P1", "name": "Anna", "role": "Maurer", "hourly_rate": 50})
    session.upsert_item("resources", {"id": "R1", "type": "person", "person_id": "P1"})
    session.update_task(2, {"resources": ["R1"]})
    assert session.validate() == []
    assert session.calculate()["total_costs"] == pytest.approx(5 * 8 * 50)
    session.update_task(2, {"resources": ["R9"]})
    assert session.validate() == ["Task 2: unbekannte Ressource R9"]
    with pytest.raises(ApiError):
        session.upsert_item("resting_times", {"after_hours": 6, "duration": "30m"})


def test_save_roundtrip(session, tmp_path):
    session.set_uncertainty(2, ["4d", "8d"], {"probability": 0.2, "delay": "2d"})
    path = Path(session.save(tmp_path / "garage.json"))
    reloaded = ProjectSession()
    reloaded.load(path)
    assert reloaded.get_project() == session.get_project()
    assert load_project(path).tasks[1].duration_range == ["4d", "8d"]


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.name)
def test_examples_lossless_and_same_result(example):
    s = ProjectSession()
    s.load(example)
    project = load_project(example)
    assert s.get_project() == project.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)
    start = project.project_start or "2026-03-02"
    expected = build_schedule(project, start_date=start, cfg_dir=s.cfg_dir).cpm
    assert s.calculate(start_date=start)["duration_days"] == round(expected.project_end_days, 4)


def test_mcp_server_tools():
    from mcp_server.server import build_server

    mcp = build_server(ProjectSession())

    async def run():
        names = {t.name for t in await mcp.list_tools()}
        assert {"new_project", "add_task", "add_dependency", "calculate", "save_project",
                "get_revision", "get_state"} <= names
        await mcp.call_tool("new_project", {"name": "X", "project_start": "2026-04-01"})
        _, a = await mcp.call_tool("add_task", {"task": {"name": "A", "duration": "2"}})
        _, b = await mcp.call_tool("add_task", {"task": {"name": "B", "duration": "1d"}})
        assert a["result"] == {"id": 1, "name": "A", "duration": "2d"}   # gespeicherter Task samt ID
        await mcp.call_tool("add_dependency", {"predecessor": a["result"]["id"], "successor": b["result"]["id"]})
        _, result = await mcp.call_tool("calculate", {})
        return result

    result = asyncio.run(run())
    assert result["result"]["duration_days"] == 3.0


def test_revision_and_conflict(session):
    rev = session.revision
    session.update_task(1, {"duration": "4d"})
    assert session.revision == rev + 1
    state = session.state()
    assert state["revision"] == rev + 1 and state["project"]["tasks"][0]["duration"] == "4d"

    data = state["project"]
    data["project"] = "von der GUI"
    session.replace_project(data, base_revision=state["revision"])      # passender Stand → übernommen
    assert session.get_project()["project"] == "von der GUI"

    data["project"] = "veraltet"
    with pytest.raises(ApiError, match="Konflikt"):
        session.replace_project(data, base_revision=state["revision"])  # inzwischen geändert
    assert session.get_project()["project"] == "von der GUI"


def test_state_without_project():
    assert ProjectSession().state() == {"revision": 0, "generation": 0, "last_switch": None,
                                        "project": None, "path": None}


def test_switch_backs_up_and_warns(session, tmp_path):
    """Ersetzt ein Aufruf das ganze Projekt, wird der bisherige Stand gesichert und gemeldet."""
    session.backup_dir = tmp_path
    generation = session.generation
    info = session.new_project("Neubau")
    assert session.generation == generation + 1
    switch = session.last_switch
    assert switch["old"] == "Garage" and switch["new"] == "Neubau" and switch["reason"] == "new_project"
    assert "Garage" in info["warning"] and switch["backup"] in info["warning"]
    backup = Path(switch["backup"])
    assert backup.parent == tmp_path
    assert [t["name"] for t in load_project(backup).model_dump()["tasks"]] == ["Fundament", "Mauern", "Dach"]

    session.load(EXAMPLES[0])                                   # load ist ebenfalls ein Wechsel
    assert session.last_switch["old"] == "Neubau" and len(list(tmp_path.glob("*.json"))) == 2

    data = session.get_project()
    session.replace_project(data)                              # ohne base_revision = Wechsel
    assert session.last_switch["reason"] == "replace_project"
    rev = session.revision
    session.replace_project(data, base_revision=rev)            # mit base_revision = normale Änderung
    assert session.last_switch["reason"] == "replace_project" and len(list(tmp_path.glob("*.json"))) == 3


def test_switch_without_previous_project_or_with_invalid_data(tmp_path):
    s = ProjectSession()
    s.backup_dir = tmp_path
    assert "warning" not in s.new_project("Erstes")              # nichts ersetzt → keine Sicherung
    assert s.last_switch is None and not list(tmp_path.iterdir())
    with pytest.raises(ApiError):
        s.replace_project({"tasks": "kaputt"})                   # ungültig → kein Wechsel, keine Sicherung
    assert s.get_project()["project"] == "Erstes" and not list(tmp_path.iterdir())


def test_second_http_server_refuses_busy_port():
    import socket

    from mcp_server.server import main, port_in_use

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        port = sock.getsockname()[1]
        assert port_in_use("127.0.0.1", port)
        assert main(["--http", "--port", str(port)]) == 1
