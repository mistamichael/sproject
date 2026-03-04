"""
Utility functions for sproject
===============================

Common utility functions used across the project.
"""

from typing import Union, Literal, List
from datetime import datetime, timedelta


# =============================================================================
# Duration Parsing & Conversion
# =============================================================================

def parse_duration_to_days(duration: Union[str, int, float]) -> float:
    """
    Konvertiert einen Duration-Wert zu Tagen (float).

    Unterstützt: Zahlen (10), Strings mit Einheit ("10d", "2w", "8h", "30m")

    Args:
        duration: Kann int, float oder str sein

    Returns:
        Dauer in Tagen als float

    Examples:
        >>> parse_duration_to_days("10d")
        10.0
        >>> parse_duration_to_days("2w")
        10.0
        >>> parse_duration_to_days("40h")
        5.0
        >>> parse_duration_to_days("480m")
        1.0
    """
    # Falls bereits eine Zahl, direkt zurückgeben
    if isinstance(duration, (int, float)):
        return float(duration)

    # String-Verarbeitung
    if isinstance(duration, str):
        duration_str = duration.strip()
        if not duration_str or duration_str == "0":
            return 0.0

        if duration_str.endswith('d'):
            return float(duration_str[:-1])
        elif duration_str.endswith('w'):
            return float(duration_str[:-1]) * 5  # 5 Arbeitstage
        elif duration_str.endswith('h'):
            return float(duration_str[:-1]) / 8  # 8h Arbeitstag
        elif duration_str.endswith('m'):
            return float(duration_str[:-1]) / 480  # 8h * 60min = 480 Minuten pro Tag
        else:
            # Fallback: versuche als Zahl zu parsen (Tage)
            try:
                return float(duration_str)
            except ValueError:
                return 0.0

    return 0.0


def parse_duration_to_minutes(duration: Union[str, int, float]) -> float:
    """
    Konvertiert einen Duration-Wert zu Minuten (float).

    Args:
        duration: Kann int, float oder str sein ("40m", "1h", "2d")

    Returns:
        Dauer in Minuten als float

    Examples:
        >>> parse_duration_to_minutes("40m")
        40.0
        >>> parse_duration_to_minutes("1h")
        60.0
        >>> parse_duration_to_minutes("1d")
        480.0
    """
    if isinstance(duration, (int, float)):
        return float(duration)

    duration_str = str(duration).strip()

    if duration_str.endswith('m'):
        return float(duration_str[:-1])
    elif duration_str.endswith('h'):
        return float(duration_str[:-1]) * 60
    elif duration_str.endswith('d'):
        return float(duration_str[:-1]) * 8 * 60  # 8h Arbeitstag
    elif duration_str.endswith('w'):
        return float(duration_str[:-1]) * 5 * 8 * 60  # 5 Arbeitstage
    else:
        try:
            return float(duration_str)
        except:
            return 0.0


def detect_time_unit(durations: List[Union[str, int, float]]) -> Literal['minutes', 'hours', 'days']:
    """
    Erkennt die dominante Zeiteinheit in einer Liste von Dauern.

    Args:
        durations: Liste von Duration-Werten

    Returns:
        'minutes', 'hours' oder 'days'

    Examples:
        >>> detect_time_unit(["10m", "20m", "5h"])
        'minutes'
        >>> detect_time_unit(["10d", "20d", "5d"])
        'days'
    """
    unit_counts = {'m': 0, 'h': 0, 'd': 0}

    for duration in durations:
        if isinstance(duration, str):
            duration_str = duration.strip()
            if duration_str.endswith('m'):
                unit_counts['m'] += 1
            elif duration_str.endswith('h'):
                unit_counts['h'] += 1
            elif duration_str.endswith('d'):
                unit_counts['d'] += 1
            elif duration_str.endswith('w'):
                unit_counts['d'] += 1

    # Finde die häufigste Einheit
    max_unit = max(unit_counts, key=unit_counts.get)
    if max_unit == 'm':
        return 'minutes'
    elif max_unit == 'h':
        return 'hours'
    else:
        return 'days'


def format_time_value(days: float, unit: Literal['minutes', 'hours', 'days']) -> str:
    """
    Formatiert einen Zeitwert (in Tagen) basierend auf der gewünschten Einheit.

    Args:
        days: Zeitwert in Tagen
        unit: Ziel-Einheit ('minutes', 'hours' oder 'days')

    Returns:
        Formatierter String (z.B. "120m", "2.5h", "1d")

    Examples:
        >>> format_time_value(0.125, 'minutes')  # 60 min
        '60.0m'
        >>> format_time_value(0.125, 'hours')  # 1h
        '1.0h'
        >>> format_time_value(1.0, 'days')
        '1.0d'
    """
    if unit == 'minutes':
        minutes = days * 480  # 8h * 60min
        return f"{minutes:.1f}m"
    elif unit == 'hours':
        hours = days * 8
        return f"{hours:.1f}h"
    else:
        return f"{days:.1f}d"


def format_time_value_auto(days: float) -> str:
    """
    Formatiert einen Zeitwert (in Tagen) mit automatischer Einheiten-Wahl.

    Wählt automatisch die beste Einheit basierend auf der Größe:
    - < 0.125 Tage (< 1h) -> Minuten
    - < 1 Tag -> Stunden
    - >= 1 Tag -> Tage

    Args:
        days: Zeitwert in Tagen

    Returns:
        Formatierter String mit optimaler Einheit

    Examples:
        >>> format_time_value_auto(0.0104)  # ~5 min
        '5.0m'
        >>> format_time_value_auto(0.25)  # 2h
        '2.0h'
        >>> format_time_value_auto(5.5)  # 5.5 Tage
        '5.5d'
    """
    # Behandle negative Null-Werte (durch Rundungsfehler)
    if abs(days) < 0.0001:
        days = 0.0

    minutes = days * 480  # 8h * 60min
    hours = days * 8

    if days < 0.125:  # < 1 Stunde
        return f"{minutes:.1f}m"
    elif days < 1.0:  # < 1 Tag
        return f"{hours:.1f}h"
    else:
        return f"{days:.1f}d"


def format_datetime_value(days: float, unit: Literal['minutes', 'hours', 'days'],
                         start_date: datetime) -> str:
    """
    Formatiert einen Zeitwert als Zeitangabe oder Datum+Uhrzeit.

    Args:
        days: Zeitwert in Tagen
        unit: Zeiteinheit ('minutes', 'hours' oder 'days')
        start_date: Projektstartdatum

    Returns:
        Formatierter String basierend auf Zeiteinheit

    Examples:
        >>> start = datetime(2026, 3, 3)
        >>> format_datetime_value(0.125, 'hours', start)  # 1h
        '1.00h'
        >>> format_datetime_value(10.0, 'days', start)
        '2026-03-17'
    """
    if unit == 'minutes':
        minutes = days * 480
        if minutes < 1440:  # < 24h
            hours = minutes / 60
            return f"{hours:.2f}h"
        else:
            # Berechne Datum und Uhrzeit
            dt = add_workdays(start_date, days)
            return dt.strftime('%Y-%m-%d %H:%M')
    elif unit == 'hours':
        hours = days * 8
        if hours < 24:
            return f"{hours:.2f}h"
        else:
            dt = add_workdays(start_date, days)
            return dt.strftime('%Y-%m-%d %H:%M')
    else:
        # Tage-Format: verwende Datum
        dt = add_workdays(start_date, days)
        return dt.strftime('%Y-%m-%d')


# =============================================================================
# Date & Workday Calculations
# =============================================================================

def add_workdays(start_date: datetime, days: float) -> datetime:
    """
    Addiert Arbeitstage zu einem Datum (ohne Wochenenden).

    Args:
        start_date: Startdatum
        days: Anzahl der Arbeitstage

    Returns:
        Neues Datum

    Examples:
        >>> start = datetime(2026, 3, 3)  # Dienstag
        >>> result = add_workdays(start, 1.0)
        >>> result.day
        4  # Mittwoch
    """
    current = start_date
    days_to_add = int(days)
    fraction = days - days_to_add

    while days_to_add > 0:
        current += timedelta(days=1)
        # Überspringe Wochenenden (5=Samstag, 6=Sonntag)
        if current.weekday() < 5:
            days_to_add -= 1

    # Füge Bruchteil hinzu (ohne Wochenend-Check)
    if fraction > 0:
        current += timedelta(days=fraction)

    return current


def count_weekend_days(start_date: datetime, end_date: datetime) -> int:
    """
    Zählt Wochenendtage zwischen zwei Daten.

    Args:
        start_date: Startdatum (inklusiv)
        end_date: Enddatum (exklusiv)

    Returns:
        Anzahl der Wochenendtage
    """
    if start_date >= end_date:
        return 0

    count = 0
    current = start_date
    while current < end_date:
        if current.weekday() >= 5:  # Samstag oder Sonntag
            count += 1
        current += timedelta(days=1)

    return count


# =============================================================================
# ID & Naming Utilities
# =============================================================================

def generate_cycle_id(task_id: Union[int, str], cycle_number: int, prefix: str) -> str:
    """
    Generiert eine Zyklus-ID im Format "task_id-prefix+cycle_number".

    Args:
        task_id: Original Task-ID
        cycle_number: Zyklusnummer (1, 2, 3, ...)
        prefix: Präfix (z.B. "P" für Pizza, "F" für Fahrt)

    Returns:
        Zyklus-ID als String

    Examples:
        >>> generate_cycle_id(2, 1, "P")
        '2-P1'
        >>> generate_cycle_id("task_001", 5, "F")
        'task_001-F5'
    """
    return f"{task_id}-{prefix}{cycle_number}"


def parse_cycle_id(cycle_id: str) -> tuple[Union[int, str], int, str]:
    """
    Parst eine Zyklus-ID zurück in Komponenten.

    Args:
        cycle_id: Zyklus-ID (z.B. "2-P1", "2-F5")

    Returns:
        Tuple von (task_id, cycle_number, prefix)

    Examples:
        >>> parse_cycle_id("2-P1")
        (2, 1, 'P')
        >>> parse_cycle_id("task_001-F5")
        ('task_001', 5, 'F')
    """
    import re

    # Pattern: task_id-prefix+number
    pattern = r'^(.+)-([A-Z]+)(\d+)$'
    match = re.match(pattern, cycle_id)

    if match:
        task_id_str, prefix, number_str = match.groups()

        # Versuche task_id als int zu parsen
        try:
            task_id = int(task_id_str)
        except ValueError:
            task_id = task_id_str

        return task_id, int(number_str), prefix

    # Fallback
    return cycle_id, 0, ''


# =============================================================================
# Validation Utilities
# =============================================================================

def validate_duration_string(duration: str) -> bool:
    """
    Prüft ob ein Duration-String valide ist.

    Args:
        duration: Duration-String

    Returns:
        True wenn valide, False sonst

    Examples:
        >>> validate_duration_string("10d")
        True
        >>> validate_duration_string("5h")
        True
        >>> validate_duration_string("invalid")
        False
    """
    if not duration or not isinstance(duration, str):
        return False

    duration = duration.strip()
    valid_suffixes = ['d', 'w', 'h', 'm']

    if duration[-1] in valid_suffixes:
        try:
            float(duration[:-1])
            return True
        except ValueError:
            return False

    # Versuche als Zahl zu parsen
    try:
        float(duration)
        return True
    except ValueError:
        return False
