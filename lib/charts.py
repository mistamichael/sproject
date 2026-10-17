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
        'delay': 'Verschoben um', 'waits': 'wartet auf', 'span': 'Belegt (Urlaub/Teilzeit)',
        'missed': 'VERFEHLT', 'deadline': 'Deadline',
        'baseline': 'Baseline', 'done': 'Erledigt', 'status_date': 'Stichtag',
        'variance': 'Abweichung zur Baseline', 'remaining': 'Restarbeit',
    },
    'en': {
        'critical': 'Critical', 'normal': 'Normal', 'break': 'Break', 'float': 'Float',
        'gantt': 'Gantt', 'resources': 'Resource utilisation', 'duration': 'Project duration',
        'start': 'Start', 'end': 'End', 'res': 'Resources',
        'delay': 'Delayed by', 'waits': 'waits for', 'span': 'Occupied (vacation/part-time)',
        'missed': 'MISSED', 'deadline': 'Deadline',
        'baseline': 'Baseline', 'done': 'Done', 'status_date': 'Status date',
        'variance': 'Variance to baseline', 'remaining': 'Remaining work',
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
    if t.leveling_delay > 1e-9:
        reason = f" ({lb['waits']}: {', '.join(map(str, t.resource_predecessors))})" if t.resource_predecessors else ""
        lines.append(f"{lb['delay']}: {fmt(t.leveling_delay)}{reason}")
    if t.span > t.duration + 1e-9:
        lines.append(f"{lb['span']}: {fmt(t.span)}")
    if t.remaining is not None:
        lines.append(f"{lb['remaining']}: {fmt(t.remaining)}")
    if t.baseline_variance is not None:
        sign = "+" if t.baseline_variance > 1e-9 else ""
        lines.append(f"{lb['variance']}: {sign}{fmt(t.baseline_variance)}")
    if t.deadline is not None:
        status = f" – {lb['missed']}" if t.deadline_missed else ""
        lines.append(f"Deadline: {fmt(t.deadline)}{status}")
    return "<br>".join(lines)


def _bar_trace(bars: Sequence[_Bar], name: str, color: str, unit, lb, *, show_float: bool = False) -> go.Bar:
    if show_float:
        base = [b.task.fez for b in bars]
        length = [b.task.sez - b.task.fez for b in bars]
        hover = [f"{lb['float']}: {format_time_value(b.task.puffer, unit)}" for b in bars]
    else:
        base = [b.task.faz for b in bars]
        length = [max(b.task.span, _MIN_WIDTH) for b in bars]   # Nulldauer sichtbar machen
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
    _add_tracking(fig, result, bars, lb)
    deadlines = [(b, b.task.deadline) for b in bars if b.task.deadline is not None]
    with_deadline = [b for b, _ in deadlines]
    if deadlines:
        hover = [f"Deadline {b.label}: {point_in_time(result, d, is_end=True):%Y-%m-%d %H:%M}"
                 if result.project_start else f"Deadline {b.label}" for b, d in deadlines]
        fig.add_trace(go.Scatter(
            name=lb['deadline'], mode="markers", x=[d for _, d in deadlines],
            y=[b.label for b in with_deadline], hoverinfo="text", hovertext=hover,
            marker=dict(symbol="diamond", size=12, color=["#8B0000" if b.task.deadline_missed else "#2E7D32"
                                                           for b in with_deadline]),
        ))

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


def _add_tracking(fig: go.Figure, result: CPMResult, bars: Sequence[_Bar], lb: Dict[str, str]) -> None:
    """Baseline (dünner grauer Balken unter dem Task), erledigter Anteil und Stichtag-Linie."""
    planned = [b for b in bars if b.task.baseline_start is not None and b.task.baseline_finish is not None]
    if planned:
        fig.add_trace(go.Bar(
            name=lb['baseline'], orientation="h", y=[b.label for b in planned],
            base=[b.task.baseline_start for b in planned],
            x=[max(b.task.baseline_finish - b.task.baseline_start, _MIN_WIDTH) for b in planned],  # type: ignore[operator]
            width=0.2, offset=0.25, marker=dict(color="#7F7F7F"), hoverinfo="skip",
        ))
    status = result.status_date
    started = [b for b in bars if b.task.status]
    if started:
        ends = [b.task.fez if b.task.status == 'done' else min(b.task.fez, status or b.task.fez) for b in started]
        fig.add_trace(go.Bar(
            name=lb['done'], orientation="h", y=[b.label for b in started], base=[b.task.faz for b in started],
            x=[max(e - b.task.faz, 0.0) for e, b in zip(ends, started)],
            width=0.3, marker=dict(color="#2E7D32"), hoverinfo="skip",
        ))
    if status is not None:
        fig.add_vline(x=status, line=dict(color="#2E7D32", dash="dash", width=2),
                      annotation_text=lb['status_date'], annotation_position="top")


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
            x=[max(b.task.span, _MIN_WIDTH) for b in bars],
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


# ---------------------------------------------------------------------------
# Szenarien
# ---------------------------------------------------------------------------

def build_scenario_figures(outcomes, title: str) -> List[go.Figure]:
    """Vergleichsbalken (Projektdauer je Szenario) und Tabelle mit allen Kennzahlen."""
    from .scenarios import comparison_rows

    unit = outcomes[0].schedule.cpm.time_unit
    names = [o.name for o in outcomes]
    def color(i: int, o) -> str:
        if i == 0:
            return "#4472C4"                                   # Basisplan
        worse = o.delta_days > 1e-9 or o.deadline_violations > outcomes[0].deadline_violations
        return "#C0392B" if worse else "#2E7D32"

    colors = [color(i, o) for i, o in enumerate(outcomes)]
    bars = go.Figure(go.Bar(
        orientation="h", y=names, x=[o.duration_days for o in outcomes], marker=dict(color=colors),
        text=[f"{format_time_value(o.duration_days, unit)}  ({o.delta_text(unit)})" for o in outcomes],
        textposition="auto", hovertext=[o.description for o in outcomes], hoverinfo="text+x",
    ))
    bars.update_layout(title=f"{title} – Szenarien", height=max(250, 110 + 45 * len(outcomes)),
                       margin=dict(l=10, r=10, t=60, b=40), xaxis_title="Arbeitstage")
    bars.update_yaxes(autorange="reversed")

    rows = comparison_rows(outcomes)
    table = go.Figure(go.Table(
        header=dict(values=rows[0], fill_color="#4472C4", font=dict(color="white"), align="left"),
        cells=dict(values=[list(col) for col in zip(*rows[1:])], align="left"),
    ))
    table.update_layout(height=max(200, 80 + 30 * len(outcomes)), margin=dict(l=10, r=10, t=10, b=10))
    return [bars, table]


# ---------------------------------------------------------------------------
# Monte-Carlo-Simulation
# ---------------------------------------------------------------------------

def build_simulation_figures(sim, title: str, lang: str = 'de') -> List[go.Figure]:
    """Histogramm des Projektendes mit Summenkurve und Perzentilen, Kritikalität, Kennzahlen."""
    from plotly.subplots import make_subplots
    from .simulation import PERCENTILES, summary_rows, top_critical

    result = sim.result
    end = max(sim.ends[-1], result.project_end_days)
    bins = min(30, max(5, len(set(round(e, 3) for e in sim.ends))))
    width = max((sim.ends[-1] - sim.ends[0]) / bins, 1e-6)
    counts = [0] * bins
    for e in sim.ends:
        counts[min(int((e - sim.ends[0]) / width), bins - 1)] += 1
    centers = [sim.ends[0] + (i + 0.5) * width for i in range(bins)]

    hist = make_subplots(specs=[[{"secondary_y": True}]])
    hist.add_trace(go.Bar(x=centers, y=counts, width=width * 0.95, name="Läufe", marker=dict(color="#4472C4")),
                   secondary_y=False)
    hist.add_trace(go.Scatter(x=sim.ends, y=[(i + 1) / len(sim.ends) for i in range(len(sim.ends))],
                              mode="lines", name="Summenkurve", line=dict(color="#C0392B")),
                   secondary_y=True)
    marks = [(f"P{p}", sim.percentile(p), "#7F7F7F") for p in PERCENTILES]
    marks.append(("Plan", result.project_end_days, "#2E7D32"))
    if result.baseline_end is not None:
        marks.append(("Baseline", result.baseline_end, "#000000"))
    for label, x, color in marks:
        hist.add_vline(x=x, line=dict(color=color, dash="dash"), annotation_text=label, annotation_position="top")
    values, labels = axis_ticks(result, lang, end=end + width)
    hist.update_xaxes(tickvals=values, ticktext=labels, tickangle=-45,
                      range=[min(sim.ends[0], result.project_end_days) - width, end + width])
    hist.update_yaxes(title_text="Läufe", secondary_y=False)
    hist.update_yaxes(title_text="Wahrscheinlichkeit fertig", tickformat=".0%", range=[0, 1.02], dtick=0.2,
                      secondary_y=True)
    hist.update_layout(title=f"{title} – Monte-Carlo-Simulation ({sim.runs} Läufe)", height=480,
                       margin=dict(l=10, r=10, t=80, b=100), legend=dict(orientation="h", y=1.08))

    critical = top_critical(sim, limit=15)
    crit = go.Figure(go.Bar(orientation="h", y=[f"[{tid}] {name}" for tid, name, _ in critical],
                            x=[sim.criticality[_task_key(sim, tid)] for tid, _, _ in critical],
                            marker=dict(color="#C0392B"), text=[r for _, _, r in critical], textposition="auto"))
    crit.update_layout(title="Kritikalität: Anteil der Läufe auf dem kritischen Pfad",
                       height=max(250, 100 + 28 * len(critical)), margin=dict(l=10, r=10, t=60, b=40))
    crit.update_xaxes(tickformat=".0%", range=[0, 1])
    crit.update_yaxes(autorange="reversed")

    rows = summary_rows(sim)
    table = go.Figure(go.Table(
        header=dict(values=["Kennzahl", "Wert"], fill_color="#4472C4", font=dict(color="white"), align="left"),
        cells=dict(values=[[r[0] for r in rows], [r[1] for r in rows]], align="left"),
    ))
    table.update_layout(height=max(200, 60 + 28 * len(rows)), margin=dict(l=10, r=10, t=10, b=10))
    return [hist, table, crit]


def _task_key(sim, tid_text: str):
    return next(tid for tid in sim.criticality if str(tid) == tid_text)
