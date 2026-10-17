"""
Durations
=========

Einzige Stelle für Dauer-Parsing und Zeit-Umrechnung.

Intern rechnet CPM immer in Arbeitstagen. Wie viele Stunden ein Arbeitstag
und wie viele Tage eine Woche hat, steht in cfg/defaults.cfg [WorkingHours]
und wird hier genau einmal gelesen.
"""

import configparser
import math
from functools import lru_cache
from typing import Literal, Sequence, Tuple, Union

from .paths import get_cfg_dir

TimeUnit = Literal['minutes', 'hours', 'days']
DurationValue = Union[str, int, float]


@lru_cache(maxsize=1)
def _working_hours() -> Tuple[float, float]:
    """Liest (hours_per_day, days_per_week) aus defaults.cfg, Fallback (8, 5)."""
    config = configparser.ConfigParser()
    cfg_file = get_cfg_dir() / "defaults.cfg"
    if cfg_file.exists():
        config.read(cfg_file, encoding='utf-8')
    return (
        config.getfloat('WorkingHours', 'hours_per_day', fallback=8.0),
        config.getfloat('WorkingHours', 'days_per_week', fallback=5.0),
    )


def hours_per_day() -> float:
    return _working_hours()[0]


def minutes_per_day() -> float:
    return hours_per_day() * 60


def _minutes_per_unit() -> dict:
    mpd = minutes_per_day()
    return {'m': 1.0, 'h': 60.0, 'd': mpd, 'w': mpd * _working_hours()[1]}


# =============================================================================
# Parsing
# =============================================================================

def parse_duration_to_minutes(duration: DurationValue) -> float:
    """
    Konvertiert eine Dauer in Arbeitsminuten.

    Zahlen ohne Einheit werden als Minuten interpretiert, unparsbare Werte als 0.

    Examples:
        >>> parse_duration_to_minutes("40m")
        40.0
        >>> parse_duration_to_minutes("1h")
        60.0
        >>> parse_duration_to_minutes("1d")   # bei hours_per_day = 8
        480.0
    """
    if isinstance(duration, (int, float)):
        return float(duration)
    text = str(duration).strip()
    if not text:
        return 0.0
    factor = _minutes_per_unit().get(text[-1])
    try:
        return float(text[:-1]) * factor if factor else float(text)
    except ValueError:
        return 0.0


def parse_duration_to_days(duration: DurationValue) -> float:
    """
    Konvertiert eine Dauer in Arbeitstage.

    Zahlen ohne Einheit werden als Tage interpretiert, unparsbare Werte als 0.

    Examples:
        >>> parse_duration_to_days("10d")
        10.0
        >>> parse_duration_to_days("2w")
        10.0
        >>> parse_duration_to_days("40h")
        5.0
    """
    if isinstance(duration, (int, float)):
        return float(duration)
    text = str(duration).strip()
    if not text:
        return 0.0
    if text[-1] in _minutes_per_unit():
        return parse_duration_to_minutes(text) / minutes_per_day()
    try:
        return float(text)
    except ValueError:
        return 0.0


def validate_duration_string(duration: str) -> bool:
    """True, wenn duration eine Zahl mit optionaler Einheit (m, h, d, w) ist."""
    if not duration or not isinstance(duration, str):
        return False
    text = duration.strip()
    number = text[:-1] if text and text[-1] in _minutes_per_unit() else text
    try:
        float(number)
        return True
    except ValueError:
        return False


def detect_time_unit(durations: Sequence[DurationValue]) -> TimeUnit:
    """
    Erkennt die häufigste Zeiteinheit in einer Liste von Dauern (Wochen zählen als Tage).

    Examples:
        >>> detect_time_unit(["10m", "20m", "5h"])
        'minutes'
    """
    counts = {'m': 0, 'h': 0, 'd': 0}
    for duration in durations:
        if isinstance(duration, str) and duration.strip():
            suffix = duration.strip()[-1]
            suffix = 'd' if suffix == 'w' else suffix
            if suffix in counts:
                counts[suffix] += 1
    best = max(counts, key=lambda k: counts[k])
    return {'m': 'minutes', 'h': 'hours'}.get(best, 'days')  # type: ignore[return-value]


# =============================================================================
# Umrechnung & Formatierung
# =============================================================================

def convert_days_to_time_unit(days: float, unit: TimeUnit) -> float:
    """Rechnet Arbeitstage in die Einheit unit um (nur numerisch)."""
    if math.isinf(days) or math.isnan(days):
        return days
    if unit == 'minutes':
        return days * minutes_per_day()
    if unit == 'hours':
        return days * hours_per_day()
    return days


def get_time_unit_label(unit: TimeUnit) -> str:
    """Kürzel für eine Zeiteinheit: 'min', 'h' oder 'd'."""
    return {'minutes': 'min', 'hours': 'h', 'days': 'd'}.get(unit, 'd')


def format_time_value(days: float, unit: TimeUnit) -> str:
    """
    Formatiert Arbeitstage in der Einheit unit.

    Examples:
        >>> format_time_value(0.125, 'hours')   # bei hours_per_day = 8
        '1.0h'
        >>> format_time_value(1.0, 'days')
        '1.0d'
    """
    if math.isinf(days):
        return "inf"
    suffix = {'minutes': 'm', 'hours': 'h'}.get(unit, 'd')
    return f"{convert_days_to_time_unit(days, unit):.1f}{suffix}"


def format_time_value_auto(days: float) -> str:
    """Formatiert Arbeitstage mit passender Einheit: < 1h in Minuten, < 1 Tag in Stunden."""
    if math.isinf(days):
        return "inf"
    if abs(days) < 0.0001:
        days = 0.0
    if days * hours_per_day() < 1.0:
        return format_time_value(days, 'minutes')
    if days < 1.0:
        return format_time_value(days, 'hours')
    return format_time_value(days, 'days')
