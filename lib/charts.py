"""
Charts (Plotly)
===============

Gantt- und Ressourcen-Diagramm als Plotly-Figuren aus einem Schedule.
Eine Figur lässt sich als interaktives HTML (jeder Browser) oder als
SVG/PNG/PDF (über kaleido, benötigt einen lokalen Chrome) speichern.

Die x-Achse ist die CPM-Zeit in Arbeitstagen (linear); beschriftet wird sie
mit den Kalenderdaten des WorkCalendar. Wochenenden, Feiertage und die Zeit
außerhalb des Arbeitstags kommen dadurch gar nicht erst auf der Achse vor.
(Plotly-rangebreaks lassen Balken verschwinden, die auf einer Lückengrenze
beginnen oder enden – bei Arbeitszeitplänen der Normalfall.)
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import plotly.graph_objects as go

from .colors import interpolate_color, load_auto_color_range
from .durations import format_time_value, hours_per_day
from .models.cpm import CPMResult, CPMTaskResult
from .schedule import Schedule
from .time_axis import axis_ticks, point_in_time

_COLOR_CRITICAL = "#C0392B"
_COLOR_NORMAL = "#4472C4"
_COLOR_BREAK = "#A0A0A0"
_COLOR_FLOAT = "rgba(68, 114, 196, 0.25)"
_ROW_HEIGHT = 26
_MIN_WIDTH = 0.005           # Arbeitstage – Mindestbreite für Tasks ohne Dauer

_LABELS = {
    'de': {
        'critical': 'Kritisch', 'normal': 'Normal', 'break': 'Pause', 'float': 'Puffer',
        'gantt': 'Gantt', 'resources': 'Ressourcenauslastung', 'duration': 'Projektdauer',
        'start': 'Start', 'end': 'Ende', 'res': 'Ressourcen',
    },
    'en': {
        'critical': 'Critical', 'normal': 'Normal', 'break': 'Break', 'float': 'Float',
        'gantt': 'Gantt', 'resources': 'Resource utilisation', 'duration': 'Project duration',
        'start': 'Start', 'end': 'End', 'res': 'Resources',
    },
}


def _axis(result: CPMResult, lang: str) -> dict:
    """Plotly-Achse: linear in Arbeitstagen, beschriftet mit Kalenderdaten."""
    values, labels = axis_ticks(result, lang)
    end = max(result.project_end_days, 1 / hours_per_day())
    return dict(tickvals=values, ticktext=labels, tickangle=-45, range=[-0.02 * end, end * 1.02],
                zeroline=False, showgrid=True)


# ---------------------------------------------------------------------------
# Gantt
# ---------------------------------------------------------------------------

@dataclass
class _Bar:
    label: str
    start: datetime
    end: datetime
    late_end: datetime
    task: CPMTaskResult
    resources: str


def _bars(schedule: Schedule) -> List[_Bar]:
    result = schedule.cpm
    resources = {t.id: ", ".join(t.resources or []) for t in schedule.project.tasks}
    bars = []
    for tid, task in sorted(result.tasks.items(), key=lambda kv: kv[1].faz):
        if task.is_blocker:
            continue
        bars.append(_Bar(
            label=f"[{tid}] {task.name}",
            start=point_in_time(result, task.faz),
            end=point_in_time(result, task.fez, is_end=True),
            late_end=point_in_time(result, task.sez, is_end=True),
            task=task,
            resources=resources.get(tid, ""),
        ))
    return bars


def _hover(bar: _Bar, unit, lb: Dict[str, str]) -> str:
    t = bar.task
    fmt = lambda v: format_time_value(v, unit)  # noqa: E731
    lines = [
        f"<b>{bar.label}</b>",
        f"{lb['start']}: {bar.start:%Y-%m-%d %H:%M}   {lb['end']}: {bar.end:%Y-%m-%d %H:%M}",
        f"D: {fmt(t.duration)}   FAZ: {fmt(t.faz)}   FEZ: {fmt(t.fez)}",
        f"SAZ: {fmt(t.saz)}   SEZ: {fmt(t.sez)}",
        f"GP: {fmt(t.puffer)}   FP: {fmt(t.free_puffer)}",
    ]
    if bar.resources:
        lines.append(f"{lb['res']}: {bar.resources}")
    return "<br>".join(lines)


def _bar_trace(bars: Sequence[_Bar], name: str, color: str, unit, lb, *, show_float: bool = False) -> go.Bar:
    if show_float:
        base = [b.task.fez for b in bars]
        length = [b.task.sez - b.task.fez for b in bars]
        hover = [f"{lb['float']}: {format_time_value(b.task.puffer, unit)}" for b in bars]
    else:
        base = [b.task.faz for b in bars]
        length = [max(b.task.duration, _MIN_WIDTH) for b in bars]   # Nulldauer sichtbar machen
        hover = [_hover(b, unit, lb) for b in bars]
    return go.Bar(
        name=name, orientation="h", y=[b.label for b in bars], base=base, x=length,
        marker=dict(color=color), hovertext=hover, hoverinfo="text",
    )


def build_gantt_figure(schedule: Schedule, lang: str = 'de') -> go.Figure:
    """Gantt-Diagramm: kritische/normale Tasks, Pausen und Gesamtpuffer."""
    result = schedule.cpm
    lb = _LABELS.get(lang, _LABELS['de'])
    unit = result.time_unit
    bars = _bars(schedule)

    groups = [
        (lb['critical'], _COLOR_CRITICAL, [b for b in bars if b.task.is_critical and not b.task.is_break]),
        (lb['normal'], _COLOR_NORMAL, [b for b in bars if not b.task.is_critical and not b.task.is_break]),
        (lb['break'], _COLOR_BREAK, [b for b in bars if b.task.is_break]),
    ]
    fig = go.Figure()
    floating = [b for b in bars if b.task.puffer > 1e-9 and not b.task.is_system]
    if floating:
        fig.add_trace(_bar_trace(floating, lb['float'], _COLOR_FLOAT, unit, lb, show_float=True))
    for name, color, group in groups:
        if group:
            fig.add_trace(_bar_trace(group, name, color, unit, lb))

    fig.update_layout(
        title=f"{schedule.name} – {lb['duration']}: {result.project_duration}",
        barmode="overlay",
        height=max(300, 120 + _ROW_HEIGHT * len(bars)),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
        margin=dict(l=10, r=10, t=80, b=90),
    )
    fig.update_yaxes(categoryorder="array", categoryarray=[b.label for b in bars], autorange="reversed")
    fig.update_xaxes(**_axis(result, lang))
    return fig


# ---------------------------------------------------------------------------
# Ressourcen
# ---------------------------------------------------------------------------

def _resource_colors(schedule: Schedule) -> Dict[str, str]:
    resources = schedule.project.resources or []
    start, end = load_auto_color_range()
    n = len(resources)
    return {
        r.id: f"#{r.color}" if r.color else f"#{interpolate_color(start, end, i / max(n - 1, 1))}"
        for i, r in enumerate(sorted(resources, key=lambda r: r.id))
    }


def build_resource_figure(schedule: Schedule, lang: str = 'de') -> Optional[go.Figure]:
    """Ressourcen-Diagramm: eine Zeile je Ressource, Balken = Tasks. None ohne Ressourcen."""
    result = schedule.cpm
    resources = {r.id: r for r in (schedule.project.resources or [])}
    if not resources:
        return None
    lb = _LABELS.get(lang, _LABELS['de'])
    colors = _resource_colors(schedule)
    bars_by_task = {b.task.id: b for b in _bars(schedule)}

    fig = go.Figure()
    rows: List[str] = []
    for res_id, res in sorted(resources.items()):
        row = f"{res.name or res_id} ({res_id})"
        bars = [bars_by_task[t.id] for t in schedule.project.tasks
                if res_id in (t.resources or []) and t.id in bars_by_task]
        if not bars:
            continue
        rows.append(row)
        fig.add_trace(go.Bar(
            name=row, orientation="h", y=[row] * len(bars), base=[b.task.faz for b in bars],
            x=[max(b.task.duration, _MIN_WIDTH) for b in bars],
            marker=dict(color=colors.get(res_id, _COLOR_NORMAL), line=dict(width=1, color="white")),
            hovertext=[_hover(b, result.time_unit, lb) for b in bars], hoverinfo="text",
        ))

    fig.update_layout(
        title=f"{schedule.name} – {lb['resources']}",
        barmode="overlay",
        height=max(250, 120 + 40 * len(rows)),
        showlegend=False,
        margin=dict(l=10, r=10, t=60, b=90),
    )
    fig.update_yaxes(categoryorder="array", categoryarray=rows, autorange="reversed")
    fig.update_xaxes(**_axis(result, lang))
    return fig


def build_figures(schedule: Schedule, lang: str = 'de') -> List[go.Figure]:
    figures = [build_gantt_figure(schedule, lang)]
    resource_figure = build_resource_figure(schedule, lang)
    if resource_figure is not None:
        figures.append(resource_figure)
    return figures


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def write_html(figures: Sequence[go.Figure], path: Path, title: str, embed_plotlyjs: bool = True) -> Path:
    """
    Alle Figuren in eine HTML-Datei. embed_plotlyjs=True: offline lesbar (~4 MB),
    False: plotly.js wird aus dem Netz (CDN) geladen.
    """
    parts = []
    for i, fig in enumerate(figures):
        include = (True if embed_plotlyjs else "cdn") if i == 0 else False
        parts.append(fig.to_html(full_html=False, include_plotlyjs=include))
    html = (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head>\n<body style='font-family:sans-serif'>\n"
        + "\n".join(parts) + "\n</body></html>\n"
    )
    path.write_text(html, encoding="utf-8")
    return path


def write_image(fig: go.Figure, path: Path, width: int = 1400) -> Path:
    """SVG/PNG/PDF je nach Dateiendung (kaleido + lokaler Chrome)."""
    fig.write_image(str(path), width=width, height=fig.layout.height)
    return path
