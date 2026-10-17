"""
Time axis
=========

Umrechnung der CPM-Zeit (Arbeitstage seit Projektstart) in Zeitpunkte und
Achsenbeschriftungen. Gemeinsam genutzt von den Plotly-Charts (lib/charts.py)
und den matplotlib-Diagrammen der GUI.

Die Achse ist linear in Arbeitstagen und wird mit Kalenderdaten des
WorkCalendar beschriftet – Wochenenden, Feiertage und die Zeit außerhalb des
Arbeitstags kommen auf der Achse nicht vor.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from .durations import format_time_value, hours_per_day
from .models.cpm import CPMResult

_MAX_TICKS = 25

_WEEKDAYS = {'de': ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
             'en': ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}


def point_in_time(result: CPMResult, workdays: float, is_end: bool = False) -> datetime:
    """Kurzform für result.date_at (siehe dort)."""
    return result.date_at(workdays, is_end)


def axis_ticks(result: CPMResult, lang: str = 'de',
               end: Optional[float] = None) -> Tuple[List[float], List[str]]:
    """
    Tick-Positionen (Arbeitstage) und Beschriftungen (Kalender), höchstens ~25 Ticks.
    end: Achsenende (Standard: Projektende), z. B. für Simulationen über das Planende hinaus.
    """
    end = max(end if end is not None else result.project_end_days, 1 / hours_per_day())
    hour = 1 / hours_per_day()
    steps = [hour / 12, hour / 4, hour / 2, hour, 2 * hour, 0.5, 1, 2, 5, 10, 20, 50, 100, 250]
    step = next((st for st in steps if end / st <= _MAX_TICKS), steps[-1])
    values = [i * step for i in range(int(end / step) + 2)]
    if result.project_start is None:
        return values, [format_time_value(v, result.time_unit) for v in values]

    weekdays = _WEEKDAYS.get(lang, _WEEKDAYS['de'])

    def label(v: float) -> str:
        t = point_in_time(result, v)
        if end <= 1:                          # innerhalb eines Arbeitstags: nur Uhrzeit
            return f"{t:%H:%M}"
        if step < 1:
            return f"{weekdays[t.weekday()]} {t:%d.%m. %H:%M}"
        return f"{weekdays[t.weekday()]} {t:%d.%m.%y}"

    return values, [label(v) for v in values]
