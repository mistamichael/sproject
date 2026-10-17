"""
Plotly-Charts: Figuren aus dem Schedule und HTML-Export (ohne Bildexport/Chrome).
"""

from pathlib import Path

import pytest

pytest.importorskip("plotly")

from lib.charts import build_figures, build_gantt_figure, write_html   # noqa: E402
from lib.models import load_project                                      # noqa: E402
from lib.schedule import build_schedule                                  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))


def _schedule(name: str):
    project = load_project(ROOT / "examples" / f"{name}.json")
    if not project.project_start:
        project.project_start = "2026-03-02"
    return build_schedule(project, cfg_dir=ROOT / "cfg")


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_every_task_has_a_visible_bar(example):
    schedule = _schedule(example.stem)
    fig = build_gantt_figure(schedule)
    task_bars = [(y, x) for trace in fig.data if trace.name != "Puffer" for y, x in zip(trace.y, trace.x)]
    expected = [t for t in schedule.cpm.tasks.values() if not t.is_blocker]
    assert len(task_bars) == len(expected)
    assert all(x > 0 for _, x in task_bars)


def test_axis_skips_holidays():
    # hausbau startet 01.04.2026: Karfreitag (03.04.) und Ostermontag (06.04.) fehlen auf der Achse
    fig = build_gantt_figure(_schedule("hausbau"))
    labels = list(fig.layout.xaxis.ticktext)
    assert not any("03.04." in label or "06.04." in label for label in labels)


def test_html_contains_all_figures(tmp_path):
    schedule = _schedule("software_simple")
    figures = build_figures(schedule)
    assert len(figures) == 2            # Gantt + Ressourcen
    html = write_html(figures, tmp_path / "c.html", schedule.name, embed_plotlyjs=False).read_text(encoding="utf-8")
    assert html.count("Plotly.newPlot") == 2 and "cdn.plot.ly" in html
