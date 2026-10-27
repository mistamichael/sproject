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
    s.add_task({"name": "Fundament", "duration": "3d"})
    s.add_task({"name": "Mauern", "duration": "5d"})
    s.add_task({"name": "Dach", "duration": "2d"})
    s.add_dependency(1, 2)
    s.add_dependency("2", 3)
    return s


def test_build_and_calculate(session):
    result = session.calculate()
    assert result["duration_days"] == 10.0
    assert [c["id"] for c in result["critical_path"]] == [1, 2, 3]
    assert result["start"] == "2026-04-01"
    assert session.validate() == []


def test_auto_ids_and_duplicates(session):
    assert session.add_task({"name": "Abnahme"})["id"] == 4
    with pytest.raises(ApiError):
        session.add_task({"id": 2, "name": "doppelt"})


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
        assert {"new_project", "add_task", "add_dependency", "calculate", "save_project"} <= names
        await mcp.call_tool("new_project", {"name": "X", "project_start": "2026-04-01"})
        await mcp.call_tool("add_task", {"task": {"name": "A", "duration": "2d"}})
        _, result = await mcp.call_tool("calculate", {})
        return result

    result = asyncio.run(run())
    assert result["result"]["duration_days"] == 2.0
