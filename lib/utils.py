"""
Utility functions for sproject
===============================

Common utility functions used across the project.
"""

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union, Literal, List, Tuple, Dict, Optional
from datetime import datetime, timedelta



def get_cfg_dir() -> Path:
    """Gibt das cfg-Verzeichnis zurück.

    Liest zuerst die Umgebungsvariable PV_CFG (aus setenv.bat);
    fällt auf get_project_root() / 'cfg' zurück wenn nicht gesetzt.
    """
    env_cfg = os.environ.get('PV_CFG')
    if env_cfg:
        return Path(env_cfg)
    return get_cfg_dir()


# =============================================================================
# Color Utilities
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Konvertiert Hex-Farbe (mit oder ohne #) zu RGB-Tupel."""
    hex_color = hex_color.lstrip('#')
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Konvertiert RGB-Tupel zu Hex-Farbe ohne #."""
    return '{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2])


def interpolate_color(color_start: str, color_end: str, position: float) -> str:
    """
    Interpoliert linear zwischen zwei Hex-Farben.

    Args:
        color_start: Start-Farbe (Hex ohne #)
        color_end:   End-Farbe (Hex ohne #)
        position:    Position zwischen 0.0 und 1.0

    Returns:
        Interpolierte Hex-Farbe ohne #
    """
    s = hex_to_rgb(color_start)
    e = hex_to_rgb(color_end)
    r = int(s[0] + (e[0] - s[0]) * position)
    g = int(s[1] + (e[1] - s[1]) * position)
    b = int(s[2] + (e[2] - s[2]) * position)
    return rgb_to_hex((r, g, b))


# =============================================================================
# Constants
# =============================================================================

def _read_hours_per_workday() -> int:
    """Liest hours_per_day aus defaults.cfg [WorkingHours], Fallback 8."""
    cfg_file = get_cfg_dir() / "defaults.cfg"
    config = configparser.ConfigParser()
    if cfg_file.exists():
        config.read(cfg_file, encoding='utf-8')
    return config.getint('WorkingHours', 'hours_per_day', fallback=8)


HOURS_PER_WORKDAY: int = _read_hours_per_workday()
MINUTES_PER_WORKDAY: int = HOURS_PER_WORKDAY * 60


# =============================================================================
# Task Utilities
# =============================================================================

def is_system_task(task_id) -> bool:
    """Gibt True zurück wenn task_id ein System-Task ist (z.B. Wochenend-Blocker 'WE-...')."""
    return isinstance(task_id, str) and task_id.startswith('WE-')


def format_task_field(field: str, task, time_unit: Literal['minutes', 'hours', 'days'], task_id=None) -> str:
    """
    Formatiert ein CPM-Task-Feld als String für Diagramme und Tabellen.

    Args:
        field:     Feldname: id, name, duration/d/dauer, faz, fez, saz, sez, gp, fp
        task:      CPMTaskResult-Objekt
        time_unit: Zeiteinheit ('minutes', 'hours', 'days')
        task_id:   Optionale Task-ID (überschreibt task.id für das 'id'-Feld)

    Returns:
        Formatierter String, oder '' für unbekannte Felder
    """
    f = field.lower()
    if f == 'id':
        tid = task_id if task_id is not None else task.id
        return f"[{tid}]"
    elif f == 'name':
        return task.name
    elif f in ('d', 'duration', 'dauer'):
        return f"D:{format_time_value(task.duration, time_unit)}"
    elif f == 'faz':
        return f"FAZ:{format_time_value(task.faz, time_unit)}"
    elif f == 'fez':
        return f"FEZ:{format_time_value(task.fez, time_unit)}"
    elif f == 'saz':
        return f"SAZ:{format_time_value(task.saz, time_unit)}"
    elif f == 'sez':
        return f"SEZ:{format_time_value(task.sez, time_unit)}"
    elif f == 'gp':
        return f"GP:{format_time_value(task.puffer, time_unit)}"
    elif f == 'fp':
        return f"FP:{format_time_value(task.free_puffer, time_unit)}"
    return ''


def convert_cpm_time_to_datetime(cpm_time: float, start_date: datetime, time_unit: str) -> datetime:
    """
    Konvertiert einen CPM-internen Zeitwert (in Tagen) zu einem Kalender-Datum.

    CPM-Werte (FAZ, FEZ, SAZ, SEZ) sind intern immer in Tagen, aber je nach
    time_unit mit unterschiedlicher Auflösung (Minuten, Stunden, Tage).

    Args:
        cpm_time:   CPM-Zeitwert in Tagen
        start_date: Projektstartdatum
        time_unit:  Zeiteinheit ('minutes', 'hours', 'days')

    Returns:
        Absolutes Datum/Uhrzeit
    """
    if time_unit == 'minutes':
        total_minutes = cpm_time * MINUTES_PER_WORKDAY
        days    = int(total_minutes // MINUTES_PER_WORKDAY)
        minutes = int(total_minutes % MINUTES_PER_WORKDAY)
        return start_date + timedelta(days=days, minutes=minutes)
    elif time_unit == 'hours':
        total_hours = cpm_time * HOURS_PER_WORKDAY
        days  = int(total_hours // HOURS_PER_WORKDAY)
        hours = int(total_hours % HOURS_PER_WORKDAY)
        return start_date + timedelta(days=days, hours=hours)
    else:
        return start_date + timedelta(days=cpm_time)


def load_labels(cfg_dir: Optional[Path] = None, lang: str = 'de') -> Dict[str, str]:
    """
    Lädt Beschriftungen aus der [lang]-Sektion von defaults.cfg.

    Args:
        cfg_dir: Verzeichnis der .cfg-Dateien (None → get_cfg_dir())
        lang:    Sprachkürzel ('de' oder 'en')

    Returns:
        Dict mit Beschriftungs-Schlüsseln und -Werten
    """
    if cfg_dir is None:
        cfg_dir = get_cfg_dir()
    config = configparser.ConfigParser()
    defaults_file = cfg_dir / 'defaults.cfg'
    if defaults_file.exists():
        config.read(defaults_file, encoding='utf-8')
    labels: Dict[str, str] = {}
    if config.has_section(lang):
        for key, val in config.items(lang):
            if val:
                labels[key] = val
    return labels


def load_export_config(
    cfg_dir: Optional[Path],
    filename: str,
    default_order: List[str],
    default_headings: Dict[str, str],
    lang: str = 'de',
) -> Tuple[List[str], Dict[str, str]]:
    """
    Generischer Loader für Export-Config-Dateien.

    Liest section_order aus [sections] und Überschriften aus [lang].
    Reihenfolge: Python-Defaults → defaults.cfg [lang] → export-spezifisch [lang].

    Args:
        cfg_dir:          Verzeichnis der .cfg-Dateien (None → ../cfg relativ zur Lib)
        filename:         Dateiname der Config (z.B. 'txt_export.cfg')
        default_order:    Fallback-Sektionsreihenfolge
        default_headings: Fallback-Überschriften
        lang:             Sprachkürzel ('de' oder 'en')

    Returns:
        (section_order, headings)
    """
    if cfg_dir is None:
        cfg_dir = get_cfg_dir()
    config = configparser.ConfigParser()
    # Erst defaults.cfg (gemeinsame [lang]-Basis), dann export-spezifisch (überschreibt)
    defaults_file = cfg_dir / 'defaults.cfg'
    if defaults_file.exists():
        config.read(defaults_file, encoding='utf-8')
    cfg_file = cfg_dir / filename
    if cfg_file.exists():
        config.read(cfg_file, encoding='utf-8')

    raw_order = config.get('sections', 'section_order', fallback=None)
    section_order = (
        [s.strip() for s in raw_order.split(',') if s.strip()]
        if raw_order else list(default_order)
    )

    headings = dict(default_headings)
    if config.has_section(lang):
        for key, val in config.items(lang):
            if val:
                headings[key] = val

    return section_order, headings


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
    # Handle infinity values
    import math
    if math.isinf(days):
        return "inf"

    if unit == 'minutes':
        minutes = days * 480  # 8h * 60min
        return f"{minutes:.1f}m"
    elif unit == 'hours':
        hours = days * 8
        return f"{hours:.1f}h"
    else:
        return f"{days:.1f}d"


def convert_days_to_time_unit(days: float, unit: Literal['minutes', 'hours', 'days']) -> float:
    """
    Konvertiert einen Zeitwert von Tagen in die gewünschte Zeiteinheit (nur numerischer Wert).

    Args:
        days: Zeitwert in Tagen
        unit: Ziel-Einheit ('minutes', 'hours' oder 'days')

    Returns:
        Konvertierter numerischer Wert

    Examples:
        >>> convert_days_to_time_unit(1.0, 'minutes')
        480.0
        >>> convert_days_to_time_unit(1.0, 'hours')
        8.0
        >>> convert_days_to_time_unit(1.0, 'days')
        1.0
    """
    import math
    if math.isinf(days) or math.isnan(days):
        return days

    if unit == 'minutes':
        return days * 480  # 1 Tag = 8h * 60min = 480min
    elif unit == 'hours':
        return days * 8  # 1 Tag = 8h
    else:  # days
        return days


def get_time_unit_label(unit: Literal['minutes', 'hours', 'days']) -> str:
    """
    Gibt das Kürzel für eine Zeiteinheit zurück.

    Args:
        unit: Zeiteinheit ('minutes', 'hours' oder 'days')

    Returns:
        Kürzel (z.B. 'min', 'h', 'd')

    Examples:
        >>> get_time_unit_label('minutes')
        'min'
        >>> get_time_unit_label('hours')
        'h'
        >>> get_time_unit_label('days')
        'd'
    """
    labels = {
        'minutes': 'min',
        'hours': 'h',
        'days': 'd'
    }
    return labels.get(unit, 'd')


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
    # Handle infinity values
    import math
    if math.isinf(days):
        return "inf"

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
    # Handle infinity values
    import math
    if math.isinf(days):
        return "inf"

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
    Unterstützt positive und negative Werte.

    Args:
        start_date: Startdatum
        days: Anzahl der Arbeitstage (kann negativ sein für Rückwärtsrechnung)

    Returns:
        Neues Datum

    Examples:
        >>> start = datetime(2026, 3, 3)  # Dienstag
        >>> result = add_workdays(start, 1.0)
        >>> result.day
        4  # Mittwoch
        >>> result = add_workdays(start, -1.0)
        >>> result.day
        2  # Montag
    """
    # Handle infinity values
    import math
    if math.isinf(days):
        if days > 0:
            return datetime(9999, 12, 31)  # Far future
        else:
            return datetime(1900, 1, 1)     # Far past

    current = start_date
    days_to_add = int(days)
    fraction = days - days_to_add

    # Vorwärts (positive Tage)
    if days_to_add > 0:
        while days_to_add > 0:
            current += timedelta(days=1)
            # Überspringe Wochenenden (5=Samstag, 6=Sonntag)
            if current.weekday() < 5:
                days_to_add -= 1
    # Rückwärts (negative Tage)
    elif days_to_add < 0:
        while days_to_add < 0:
            current -= timedelta(days=1)
            # Überspringe Wochenenden (5=Samstag, 6=Sonntag)
            if current.weekday() < 5:
                days_to_add += 1

    # Füge Bruchteil hinzu (ohne Wochenend-Check)
    if fraction != 0:
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
# Person Data Collection
# =============================================================================

@dataclass
class PersonEntry:
    """Aufbereitete Personen-Daten für den Export."""
    name:            str
    hourly_rate:     Optional[float]
    absences:        List[str]   # Abwesenheiten im Projektzeitraum [proj_start, proj_end]
    absences_buffer: List[str]   # Abwesenheiten im Verzögerungspuffer (proj_end, proj_end_buffer]


def _collect_absences_in_window(
    person: Any,
    holidays: Optional[Any],
    win_start: Any,
    win_end: Any,
    exclusive_start: bool = False,
) -> List[str]:
    """
    Gibt Abwesenheits-Labels für eine Person innerhalb eines Zeitfensters zurück.

    Args:
        person:          Person-Objekt mit optionalem .vacation
        holidays:        Set von Feiertagsdaten ('YYYY-MM-DD') oder None
        win_start:       Fenster-Anfang (datetime oder None → kein unteres Limit)
        win_end:         Fenster-Ende   (datetime oder None → kein oberes Limit)
        exclusive_start: True → win_start ist exklusiv (Puffer beginnt nach proj_end)
    """
    absences: List[str] = []

    def _in_window(d: datetime) -> bool:
        after = (d > win_start) if exclusive_start else (d >= win_start)
        return (win_start is None or after) and (win_end is None or d <= win_end)

    for vac in (getattr(person, 'vacation', None) or []):
        try:
            if getattr(vac, 'date', None):
                d = datetime.strptime(vac.date, '%Y-%m-%d')
                if _in_window(d):
                    label = vac.date
                    if vac.description:
                        label += f" ({vac.description})"
                    absences.append(label)
            elif getattr(vac, 'from_', None) and getattr(vac, 'to', None):
                d_from = datetime.strptime(vac.from_, '%Y-%m-%d')
                d_to   = datetime.strptime(vac.to,    '%Y-%m-%d')
                # Zeitraum überlappt das Fenster
                if (win_start is None or d_to >= win_start) and (win_end is None or d_from <= win_end):
                    label = f"{vac.from_} – {vac.to}"
                    if vac.description:
                        label += f" ({vac.description})"
                    absences.append(label)
        except ValueError:
            pass

    if holidays and win_start and win_end:
        for h_date in sorted(holidays):
            try:
                d = datetime.strptime(h_date, '%Y-%m-%d')
                if _in_window(d):
                    name = holidays[h_date] if isinstance(holidays, dict) else 'Feiertag'
                    absences.append(f"{h_date} ({name})")
            except ValueError:
                pass

    return absences


def collect_person_entries(persons: List[Any], result: Any) -> List['PersonEntry']:
    """
    Bereitet Personen-Daten (Stundensatz, Abwesenheiten) für den Export auf.

    Zwei Zeitfenster:
    - absences:        [proj_start, proj_end]         — exakter Projektzeitraum
    - absences_buffer: (proj_end, proj_end_buffer]    — Verzögerungsrisiko

    Puffergröße: min(N_personen × 3, 30) Arbeitstage
    (Annahme: je Person ≥ 3 Krankheitstage innerhalb von 30 Arbeitstagen)

    Args:
        persons: Liste von Person-Objekten
        result:  CPMResult (für project_start, tasks, holidays)

    Returns:
        Liste von PersonEntry
    """
    proj_start = getattr(result, 'project_start', None)
    proj_end   = None
    proj_end_buffer = None

    if proj_start and getattr(result, 'tasks', None):
        max_fez_days  = max(t.fez for t in result.tasks.values())
        proj_end      = add_workdays(proj_start, max_fez_days)
        buffer_days   = min(len(persons) * 3, 30)
        proj_end_buffer = add_workdays(proj_end, buffer_days)

    holidays = getattr(result, 'holidays', None)

    entries: List[PersonEntry] = []
    for person in persons:
        hourly_rate = getattr(person, 'hourly_rate', None)
        absences = _collect_absences_in_window(
            person, holidays, proj_start, proj_end, exclusive_start=False
        )
        absences_buffer = _collect_absences_in_window(
            person, holidays, proj_end, proj_end_buffer, exclusive_start=True
        ) if proj_end else []
        entries.append(PersonEntry(
            name=person.name,
            hourly_rate=hourly_rate,
            absences=absences,
            absences_buffer=absences_buffer,
        ))

    return entries


@dataclass
class ResourceDetailEntry:
    """Ressourcen-Detail-Zeile für den Export (Ressource ↔ Person ↔ Typ)."""
    resource_id:   str
    resource_name: str
    person_name:   str   # Leer wenn keine Person verknüpft
    resource_type: str


def collect_resource_details(resources: List[Any], persons: List[Any]) -> List['ResourceDetailEntry']:
    """
    Erzeugt eine flache Liste von Ressourcen-Details (Name, Person, Typ).

    Args:
        resources: Liste von Ressource-Objekten (.id, .name, .type, .person_id)
        persons:   Liste von Person-Objekten (.id, .name)

    Returns:
        Liste von ResourceDetailEntry, sortiert nach resource_id
    """
    person_lookup = {p.id: p.name for p in persons}
    entries: List[ResourceDetailEntry] = []
    for res in sorted(resources, key=lambda r: r.id):
        person_name = ''
        if hasattr(res, 'person_id') and res.person_id:
            person_name = person_lookup.get(res.person_id, res.person_id)
        entries.append(ResourceDetailEntry(
            resource_id=res.id,
            resource_name=getattr(res, 'name', res.id),
            person_name=person_name,
            resource_type=getattr(res, 'type', 'unknown'),
        ))
    return entries


# =============================================================================
# Resource Data Collection
# =============================================================================

@dataclass
class ResourceData:
    """Gesammelte Ressourcen-Daten aus einem Projekt-Objekt."""
    resource_usage:  Dict[str, List[str]]  # res_id → [task_id strings]
    resource_names:  Dict[str, str]        # res_id → Anzeigename
    resources:       List[Any]             # rohe Ressource-Objekte
    persons:         List[Any]             # rohe Person-Objekte


def collect_resource_data(project: Any) -> Optional['ResourceData']:
    """
    Sammelt Ressourcen- und Personen-Daten aus einem Projekt-Objekt.

    Args:
        project: Projekt-Objekt mit .tasks, .resources und .persons

    Returns:
        ResourceData oder None wenn keine Ressourcen vorhanden
    """
    if not project or not hasattr(project, 'tasks'):
        return None

    resource_usage: Dict[str, List[str]] = {}
    for orig_task in project.tasks:
        if hasattr(orig_task, 'resources') and orig_task.resources:
            for res_id in orig_task.resources:
                resource_usage.setdefault(res_id, []).append(str(orig_task.id))

    if not resource_usage:
        return None

    resource_names: Dict[str, str] = {}
    resources: List[Any] = []
    if hasattr(project, 'resources'):
        resources = list(project.resources)
        for res in resources:
            resource_names[res.id] = getattr(res, 'name', res.id)

    persons: List[Any] = list(project.persons) if hasattr(project, 'persons') and project.persons else []

    return ResourceData(
        resource_usage=resource_usage,
        resource_names=resource_names,
        resources=resources,
        persons=persons,
    )


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
