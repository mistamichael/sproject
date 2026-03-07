"""
Excel Report Generator for Gantt Charts and Resource Lists
===========================================================

Generates Excel worksheets with Gantt charts and resource allocation diagrams.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import configparser

try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# Import models - try relative import first, then absolute
try:
    from .models import PersonProject, Report, GanttReport, ResourceListReport
    from .models.cpm import CPMResult
    from .utils import format_time_value_auto, add_workdays
except (ImportError, ValueError):
    from models import PersonProject, Report, GanttReport, ResourceListReport
    from models.cpm import CPMResult
    from utils import format_time_value_auto, add_workdays


def load_excel_export_config(cfg_dir: Path) -> Dict[str, Any]:
    """
    Lädt Excel-Export-Konfiguration aus excel_export.cfg und defaults.cfg.

    Args:
        cfg_dir: Verzeichnis mit Konfigurationsdateien

    Returns:
        Dictionary mit Konfigurationswerten (alle Sektionen)
    """
    config = configparser.ConfigParser()

    # Lade zuerst excel_export.cfg, dann defaults.cfg als Fallback
    excel_config_file = cfg_dir / "excel_export.cfg"
    defaults_config_file = cfg_dir / "defaults.cfg"

    # Default-Werte für alle Sektionen
    defaults = {
        'Gantt_resolution': {
            'threshold_hours_min': 60,
            'threshold_halfday_min': 240,
            'work_start_hour': 7,
            'work_end_hour': 20,
            'working_days': 'mon,tue,wed,thu,fri',
        },
        'GanttChart': {
            'color_start': '8B7AB8',
            'color_end': '4472C4',
            'critical_border_color': 'FF0000',
            'slack_bar_transparency': 180,
            'bar_height': 20,
            'timeline_header_height': 25,
            'col_width_id': 12,
            'col_width_name': 20,
            'col_width_start': 12,
            'col_width_end': 12,
            'col_width_effort': 10,
        },
        'ResourceList': {
            'col_width_resource': 20,
            'col_width_task': 25,
            'col_width_start': 12,
            'col_width_end': 12,
            'col_width_duration': 10,
            'color_person': '8B7AB8',
            'color_machine': 'FFA500',
            'color_material': '90EE90',
            'weekend_background_color': 'F0F0F0',
        }
    }

    # Lade excel_export.cfg falls vorhanden
    if excel_config_file.exists():
        config.read(excel_config_file, encoding='utf-8')
    # Fallback auf defaults.cfg
    elif defaults_config_file.exists():
        config.read(defaults_config_file, encoding='utf-8')

    # Überschreibe Defaults mit Werten aus Config-Datei
    for section_name, section_defaults in defaults.items():
        if section_name in config:
            for key, default_value in section_defaults.items():
                if key in config[section_name]:
                    value = config[section_name][key]
                    # Konvertiere basierend auf Default-Typ
                    # WICHTIG: bool vor int prüfen, da bool eine Subklasse von int ist
                    if isinstance(default_value, bool):
                        defaults[section_name][key] = value.lower() in ('true', 'yes', '1', 'on')
                    elif isinstance(default_value, int):
                        defaults[section_name][key] = int(value)
                    elif isinstance(default_value, float):
                        defaults[section_name][key] = float(value)
                    else:
                        defaults[section_name][key] = value

    return defaults


# Backwards compatibility alias
def load_gantt_config(cfg_dir: Path) -> Dict[str, Any]:
    """
    Lädt Gantt-Chart-Konfiguration (backwards compatibility).

    Gibt nur die GanttChart-Sektion zurück für Kompatibilität mit altem Code.
    """
    full_config = load_excel_export_config(cfg_dir)
    return full_config['GanttChart']


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Konvertiert Hex-Farbe zu RGB.

    Args:
        hex_color: Hex-Farbe (mit oder ohne #)

    Returns:
        RGB-Tupel (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Konvertiert RGB zu Hex-Farbe.

    Args:
        rgb: RGB-Tupel (r, g, b)

    Returns:
        Hex-Farbe ohne #
    """
    return '{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2])


def interpolate_color(color_start: str, color_end: str, position: float) -> str:
    """
    Interpoliert zwischen zwei Farben.

    Args:
        color_start: Start-Farbe (Hex)
        color_end: End-Farbe (Hex)
        position: Position zwischen 0.0 und 1.0

    Returns:
        Interpolierte Farbe (Hex)
    """
    rgb_start = hex_to_rgb(color_start)
    rgb_end = hex_to_rgb(color_end)

    r = int(rgb_start[0] + (rgb_end[0] - rgb_start[0]) * position)
    g = int(rgb_start[1] + (rgb_end[1] - rgb_start[1]) * position)
    b = int(rgb_start[2] + (rgb_end[2] - rgb_start[2]) * position)

    return rgb_to_hex((r, g, b))


def is_working_day(date: datetime, working_days_str: str) -> bool:
    """
    Prüft ob ein Datum ein Arbeitstag ist basierend auf working_days Config.

    Args:
        date: Zu prüfendes Datum
        working_days_str: Kommaseparierte Liste von Wochentagen (mon,tue,wed,thu,fri,sat,sun)

    Returns:
        True wenn Arbeitstag, False sonst
    """
    weekday_map = {
        0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'
    }
    current_weekday = weekday_map[date.weekday()]
    working_days = [day.strip().lower() for day in working_days_str.split(',')]
    return current_weekday in working_days


def get_timeline_range(result: CPMResult, loadunit: str, resolution_config: Dict[str, Any]) -> Tuple[datetime, datetime, str]:
    """
    Berechnet Zeitbereich und Granularität für Timeline basierend auf minimaler Task-Dauer.

    Args:
        result: CPM-Berechnungsergebnis
        loadunit: Zeiteinheit (hours, days, etc.)
        resolution_config: Gantt_resolution Config-Werte

    Returns:
        (start_date, end_date, granularity)
        granularity kann sein: 'hours', 'halfdays', 'days'
    """
    # Berechne Projektende
    project_duration = max(task.fez for task in result.tasks.values())
    start_date = result.project_start
    end_date = add_workdays(start_date, project_duration)

    # Finde minimale Task-Dauer (ignoriere Pausen)
    min_task_duration_days = float('inf')
    for task in result.tasks.values():
        # Überspringe Pausen-Tasks
        is_break = hasattr(task, 'is_break') and task.is_break
        if not is_break and task.duration > 0:
            min_task_duration_days = min(min_task_duration_days, task.duration)

    # Wenn keine regulären Tasks gefunden wurden, verwende Standardwert
    if min_task_duration_days == float('inf'):
        min_task_duration_days = 1.0

    # Prüfe zuerst result.time_unit für direkte Zuordnung
    if hasattr(result, 'time_unit'):
        if result.time_unit == 'minutes':
            # Minuten-Projekt → Minuten-Granularität
            granularity = 'minutes'
            return (start_date, end_date, granularity)
        elif result.time_unit == 'hours':
            # Stunden-Projekt → Stunden-Granularität
            granularity = 'hours'
            return (start_date, end_date, granularity)
        # Für 'days' verwenden wir die normale Logik unten

    # Konvertiere minimale Dauer in Minuten (8h Arbeitstag = 1 Tag)
    min_task_duration_min = min_task_duration_days * 8 * 60

    # Bestimme Granularität basierend auf Config-Schwellenwerten (Fallback)
    threshold_hours = resolution_config['threshold_hours_min']
    threshold_halfday = resolution_config['threshold_halfday_min']

    if min_task_duration_min < threshold_hours:
        granularity = 'hours'
    elif min_task_duration_min < threshold_halfday:
        granularity = 'halfdays'
    else:
        granularity = 'days'

    # Überschreibe mit loadunit falls angegeben
    if loadunit == 'hours':
        granularity = 'hours'
    elif loadunit == 'days':
        granularity = 'days'

    return start_date, end_date, granularity


def create_timeline_header(ws, start_col: int, start_row: int, start_date: datetime,
                          end_date: datetime, granularity: str, working_days: str = 'mon,tue,wed,thu,fri') -> int:
    """
    Erstellt Timeline-Header (Zeitstrahl) in Excel.

    Args:
        ws: Worksheet
        start_col: Start-Spalte für Timeline
        start_row: Start-Zeile für Header
        start_date: Projekt-Startdatum
        end_date: Projekt-Enddatum
        granularity: 'minutes', 'hours', 'halfdays', 'days'
        working_days: Kommaseparierte Liste von Arbeitstagen (z.B. 'mon,tue,wed,thu,fri')

    Returns:
        Anzahl der Zeilen, die für den Header verwendet wurden
    """
    duration_days = (end_date - start_date).days

    # Header-Stil
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    header_font = Font(bold=True, size=9)
    header_alignment = Alignment(horizontal='center', vertical='center')
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    current_col = start_col
    rows_used = 1

    if granularity == 'minutes':
        # Minuten-basierte Timeline (für sehr kurze Projekte wie Pizza-Produktion)
        # Zeige Stunden (0-7) pro Arbeitstag, jede Spalte = 1 Stunde = 60 Minuten
        # time_unit_factor=480 sorgt dafür, dass Minuten korrekt auf Spalten gemappt werden
        rows_used = 2  # Datum + Stunde

        # Extrahiere working_days Konfiguration
        weekday_names = {0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'}
        weekend_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")

        # Zeile 1: Datum mit einer Spalte pro Arbeitsstunde
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_col_start = current_col

        while current_date.date() <= end_date.date():
            is_workday = is_working_day(current_date, working_days)
            hours_for_day = 8 if is_workday else 1  # 8 Stunden für Arbeitstage, 1 Spalte für Nicht-Arbeitstage

            # Merge Datum über alle Stunden des Tages
            if hours_for_day > 1:
                ws.merge_cells(
                    start_row=start_row,
                    start_column=current_col,
                    end_row=start_row,
                    end_column=current_col + hours_for_day - 1
                )

            cell = ws.cell(row=start_row, column=current_col,
                         value=current_date.strftime('%d.%m') if is_workday else current_date.strftime('%d.%m'))
            cell.fill = weekend_fill if not is_workday else header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

            # Zeile 2: Stunden (0-7 für 8-Stunden-Tag) oder Wochentag-Kürzel
            if is_workday:
                for hour in range(8):
                    cell = ws.cell(row=start_row + 1, column=current_col + hour, value=f'{hour}h')
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = border
                    ws.column_dimensions[get_column_letter(current_col + hour)].width = 5
            else:
                # Nicht-Arbeitstag: Wochentag-Kürzel
                weekday_label = weekday_names[current_date.weekday()]
                cell = ws.cell(row=start_row + 1, column=current_col, value=weekday_label)
                cell.fill = weekend_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(current_col)].width = 5

            current_col += hours_for_day
            current_date += timedelta(days=1)

    elif granularity == 'hours':
        # Stunden-basierte Timeline (nur Arbeitsstunden pro Tag)
        # Zeige 8 Stunden pro Arbeitstag (Standard aus defaults.cfg)
        rows_used = 2  # Datum + Stunde

        # Extrahiere working_days Konfiguration
        weekday_names = {0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'}
        weekend_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")

        # Zeile 1: Datum mit einer Spalte pro Arbeitsstunde
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_col_start = current_col

        while current_date.date() <= end_date.date():
            is_workday = is_working_day(current_date, working_days)
            hours_for_day = 8 if is_workday else 1  # 8 Stunden für Arbeitstage, 1 Spalte für Nicht-Arbeitstage

            # Merge Datum über alle Stunden des Tages
            if hours_for_day > 1:
                ws.merge_cells(
                    start_row=start_row,
                    start_column=current_col,
                    end_row=start_row,
                    end_column=current_col + hours_for_day - 1
                )

            cell = ws.cell(row=start_row, column=current_col,
                         value=current_date.strftime('%d.%m') if is_workday else current_date.strftime('%d.%m'))
            cell.fill = weekend_fill if not is_workday else header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

            # Zeile 2: Stunden (0-7 für 8-Stunden-Tag) oder Wochentag-Kürzel
            if is_workday:
                for hour in range(8):
                    cell = ws.cell(row=start_row + 1, column=current_col + hour, value=str(hour))
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = border
                    ws.column_dimensions[get_column_letter(current_col + hour)].width = 4
            else:
                # Nicht-Arbeitstag: Wochentag-Kürzel
                weekday_label = weekday_names[current_date.weekday()]
                cell = ws.cell(row=start_row + 1, column=current_col, value=weekday_label)
                cell.fill = weekend_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(current_col)].width = 4

            current_col += hours_for_day
            current_date += timedelta(days=1)

    elif granularity == 'halfdays':
        # Halbtages-basierte Timeline (Vormittag/Nachmittag)
        # Arbeitstage: 2 Spalten (VM/NM)
        # Nicht-Arbeitstage: 1 Spalte pro Tag (Sa, So)
        rows_used = 2  # Datum und VM/NM/Sa/So

        # Stilvorlagen
        weekend_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        weekday_names = {0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'}

        # Erste Pass: Berechne Spalten pro Datum und erstelle Mapping
        date_col_mapping = {}  # Datum -> (start_col, num_cols, is_workday)
        temp_date = start_date
        temp_col = start_col

        while temp_date <= end_date:
            is_workday = is_working_day(temp_date, working_days)
            num_cols = 2 if is_workday else 1  # Arbeitstag = 2 Spalten, sonst 1
            date_col_mapping[temp_date.date()] = (temp_col, num_cols, is_workday)
            temp_col += num_cols
            temp_date += timedelta(days=1)

        # Zeile 1: Datum-Header mit Merging
        current_date = start_date
        while current_date <= end_date:
            start_col_for_date, num_cols, is_workday = date_col_mapping[current_date.date()]

            # Merge Spalten wenn mehrere
            if num_cols > 1:
                ws.merge_cells(
                    start_row=start_row,
                    start_column=start_col_for_date,
                    end_row=start_row,
                    end_column=start_col_for_date + num_cols - 1
                )

            cell = ws.cell(row=start_row, column=start_col_for_date,
                         value=current_date.strftime('%d.%m'))
            cell.fill = weekend_fill if not is_workday else header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

            current_date += timedelta(days=1)

        # Zeile 2: VM/NM für Arbeitstage, Wochentag-Kürzel für Nicht-Arbeitstage
        current_date = start_date

        while current_date <= end_date:
            start_col_for_date, num_cols, is_workday = date_col_mapping[current_date.date()]

            if is_workday:
                # Arbeitstag: Vormittag und Nachmittag
                # Vormittag
                cell = ws.cell(row=start_row + 1, column=start_col_for_date, value='VM')
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(start_col_for_date)].width = 5

                # Nachmittag
                cell = ws.cell(row=start_row + 1, column=start_col_for_date + 1, value='NM')
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(start_col_for_date + 1)].width = 5
            else:
                # Nicht-Arbeitstag: Wochentag-Kürzel (Sa, So, etc.)
                weekday_label = weekday_names[current_date.weekday()]
                cell = ws.cell(row=start_row + 1, column=start_col_for_date, value=weekday_label)
                cell.fill = weekend_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(start_col_for_date)].width = 5

            current_date += timedelta(days=1)

    elif granularity == 'days':
        # Wenn mehr als 7 Tage: Zeige Kalenderwochen
        if duration_days > 7:
            rows_used = 3  # Monat, Tag, KW

            # Zeile 1: Monat
            current_date = start_date
            month_start_col = current_col
            current_month = current_date.month
            month_days = 0

            while current_date <= end_date:
                if current_date.month != current_month:
                    # Merge Monatszellen
                    if month_days > 1:
                        ws.merge_cells(
                            start_row=start_row,
                            start_column=month_start_col,
                            end_row=start_row,
                            end_column=month_start_col + month_days - 1
                        )
                    cell = ws.cell(row=start_row, column=month_start_col,
                                 value=start_date.replace(day=1).strftime('%B %Y'))
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = border

                    month_start_col = current_col
                    current_month = current_date.month
                    month_days = 0

                month_days += 1
                current_date += timedelta(days=1)
                current_col += 1

            # Letzter Monat
            if month_days > 0:
                if month_days > 1:
                    ws.merge_cells(
                        start_row=start_row,
                        start_column=month_start_col,
                        end_row=start_row,
                        end_column=month_start_col + month_days - 1
                    )
                last_month_date = end_date.replace(day=1)
                cell = ws.cell(row=start_row, column=month_start_col,
                             value=last_month_date.strftime('%B %Y'))
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border

            # Zeile 2: Tage
            current_date = start_date
            current_col = start_col
            while current_date <= end_date:
                cell = ws.cell(row=start_row + 1, column=current_col, value=current_date.day)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(current_col)].width = 4

                current_date += timedelta(days=1)
                current_col += 1

            # Zeile 3: Kalenderwochen
            current_date = start_date
            current_col = start_col
            cw_start_col = current_col
            current_cw = current_date.isocalendar()[1]
            cw_days = 0

            while current_date <= end_date:
                date_cw = current_date.isocalendar()[1]

                if date_cw != current_cw:
                    # Merge KW-Zellen
                    if cw_days > 1:
                        ws.merge_cells(
                            start_row=start_row + 2,
                            start_column=cw_start_col,
                            end_row=start_row + 2,
                            end_column=cw_start_col + cw_days - 1
                        )
                    cell = ws.cell(row=start_row + 2, column=cw_start_col, value=f"KW{current_cw}")
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = border

                    cw_start_col = current_col
                    current_cw = date_cw
                    cw_days = 0

                cw_days += 1
                current_date += timedelta(days=1)
                current_col += 1

            # Letzte KW
            if cw_days > 0:
                if cw_days > 1:
                    ws.merge_cells(
                        start_row=start_row + 2,
                        start_column=cw_start_col,
                        end_row=start_row + 2,
                        end_column=cw_start_col + cw_days - 1
                    )
                cell = ws.cell(row=start_row + 2, column=cw_start_col, value=f"KW{current_cw}")
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border

        else:
            # Nur Tage (ohne KW)
            current_date = start_date
            while current_date <= end_date:
                cell = ws.cell(row=start_row, column=current_col,
                             value=current_date.strftime('%d.%m'))
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border
                ws.column_dimensions[get_column_letter(current_col)].width = 8

                current_date += timedelta(days=1)
                current_col += 1

    return rows_used


def draw_gantt_bar(ws, row: int, start_col: int, faz_offset: int, duration_cols: int,
                  sez_offset: int, color: str, critical: bool, config: Dict[str, Any]) -> None:
    """
    Zeichnet Gantt-Balken mit zwei Rechtecken (transparent für Puffer, gefüllt für Dauer).

    Args:
        ws: Worksheet
        row: Zeile für den Balken
        start_col: Start-Spalte des Chart-Bereichs
        faz_offset: Offset für FAZ (Frühester Anfangszeitpunkt)
        duration_cols: Anzahl Spalten für Dauer
        sez_offset: Offset für SEZ (Spätester Endzeitpunkt)
        color: Balken-Farbe (Hex)
        critical: Ist Task auf kritischem Pfad?
        config: Gantt-Konfiguration
    """
    border_color = config['critical_border_color'] if critical else None

    # Transparenter Balken von FAZ bis SEZ (Puffer)
    for col_offset in range(faz_offset, sez_offset):
        cell = ws.cell(row=row, column=start_col + col_offset)
        # Transparente Füllung (hellere Version der Farbe)
        # Stelle sicher, dass color 6 Zeichen hat (füge 00 prefix hinzu falls nötig)
        color_normalized = color if len(color) >= 6 else "00" + color
        cell.fill = PatternFill(start_color=color_normalized + '40', end_color=color_normalized + '40', fill_type="solid")

        if critical and border_color:
            # Rote Umrandung für kritischen Pfad
            border_side = Side(style='medium', color=border_color)
            if col_offset == faz_offset:
                cell.border = Border(left=border_side, top=border_side, bottom=border_side)
            elif col_offset == sez_offset - 1:
                cell.border = Border(right=border_side, top=border_side, bottom=border_side)
            else:
                cell.border = Border(top=border_side, bottom=border_side)

    # Gefüllter Balken von FAZ bis FAZ+Dauer
    for col_offset in range(faz_offset, faz_offset + duration_cols):
        cell = ws.cell(row=row, column=start_col + col_offset)
        # Normalisiere Farbe (füge 00 prefix hinzu falls nötig)
        color_normalized = color if len(color) >= 6 else "00" + color
        cell.fill = PatternFill(start_color=color_normalized, end_color=color_normalized, fill_type="solid")

        if critical and border_color:
            # Rote Umrandung für kritischen Pfad
            border_side = Side(style='medium', color=border_color)
            if col_offset == faz_offset:
                cell.border = Border(left=border_side, top=border_side, bottom=border_side)
            elif col_offset == faz_offset + duration_cols - 1:
                cell.border = Border(right=border_side, top=border_side, bottom=border_side)
            else:
                cell.border = Border(top=border_side, bottom=border_side)


def create_gantt_chart(wb: Workbook, project: PersonProject, result: CPMResult,
                      report: GanttReport, full_config: Dict[str, Any]) -> None:
    """
    Erstellt Gantt-Chart-Worksheet.

    Args:
        wb: Workbook
        project: Projekt-Daten
        result: CPM-Berechnungsergebnis
        report: Gantt Report-Konfiguration
        full_config: Vollständige Excel-Export-Konfiguration (alle Sektionen)
    """
    # Extrahiere die relevanten Config-Sektionen
    config = full_config['GanttChart']
    resolution_config = full_config['Gantt_resolution']

    ws = wb.create_sheet(title=report.name)

    # Headline
    ws['A1'] = report.headline
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:F1')

    # Spalten-Header
    row = 3
    for col_idx, col_name in enumerate(report.columns, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')

    # Setze Spaltenbreiten aus Config
    ws.column_dimensions['A'].width = config['col_width_id']
    ws.column_dimensions['B'].width = config['col_width_name']
    ws.column_dimensions['C'].width = config['col_width_start']
    ws.column_dimensions['D'].width = config['col_width_end']
    ws.column_dimensions['E'].width = config['col_width_effort']

    # Timeline berechnen mit Resolution-Config
    start_date, end_date, granularity = get_timeline_range(result, report.loadunit, resolution_config)

    # Timeline-Header (ab Spalte 6 = 'chart')
    chart_start_col = len(report.columns)
    working_days = resolution_config['working_days']
    timeline_rows = create_timeline_header(ws, chart_start_col, row, start_date, end_date, granularity, working_days)

    # Daten-Zeilen
    data_start_row = row + timeline_rows
    current_row = data_start_row

    # Sortiere Tasks nach FAZ (Frühester Anfangszeitpunkt), dann nach ID
    sorted_task_ids = sorted(
        result.tasks.keys(),
        key=lambda x: (result.tasks[x].faz, str(x))
    )

    # Kritischer Pfad
    critical_path = result.critical_path

    # Farb-Interpolation
    num_tasks = len(sorted_task_ids)

    for task_idx, task_id in enumerate(sorted_task_ids):
        task = result.tasks[task_id]

        # Prüfe ob Task eine Pause ist
        is_break = hasattr(task, 'is_break') and task.is_break

        # Interpoliere Farbe (Pausen werden grau)
        if is_break:
            bar_color = "D3D3D3"  # Grau für Pausen
        else:
            if num_tasks > 1:
                color_position = task_idx / (num_tasks - 1)
            else:
                color_position = 0.0
            bar_color = interpolate_color(config['color_start'], config['color_end'], color_position)

        # Spalte A: Vorgang (Task-ID)
        ws.cell(row=current_row, column=1, value=str(task_id))

        # Spalte B: name (Task-Name, nicht Person!)
        ws.cell(row=current_row, column=2, value=task.name)

        # Spalte C: start (leer, da nicht in Task-Daten)
        ws.cell(row=current_row, column=3, value='')

        # Spalte D: end (leer, da nicht in Task-Daten)
        ws.cell(row=current_row, column=4, value='')

        # Spalte E: effort
        ws.cell(row=current_row, column=5, value=format_time_value_auto(task.duration))

        # Spalte F+: chart (Balkendiagramm)
        # Berechne Positionen basierend auf Granularität
        # Hinweis: task.faz, task.duration sind in "Tagen" (1 Tag = 8 Arbeitsstunden aus defaults.cfg)
        if granularity == 'minutes':
            # Bei Minutenauflösung: 1 Arbeitstag = 480 Minuten
            time_unit_factor = 480  # 1 Arbeitstag = 480 Minuten
        elif granularity == 'hours':
            # Bei Stundenauflösung: 1 Arbeitstag = 8 Stunden (Standard aus defaults.cfg)
            # Die Timeline zeigt Stunden an, daher time_unit_factor = 8
            time_unit_factor = 8  # 1 Arbeitstag = 8 Arbeitsstunden
        elif granularity == 'halfdays':
            # Bei Halbtagesauflösung: 1 Tag = 2 Spalten (VM + NM)
            # Aber Nicht-Arbeitstage haben nur 1 Spalte - das wird in der Offset-Berechnung berücksichtigt
            time_unit_factor = 2  # 1 Arbeitstag = 2 halbe Tage
        else:
            # Bei Tagesauflösung: 1 Tag = 1 Spalte
            time_unit_factor = 1  # 1 Tag = 1 Spalte

        faz_offset = int(task.faz * time_unit_factor)
        duration_cols = max(1, int(task.duration * time_unit_factor))
        sez_offset = int(task.sez * time_unit_factor)

        is_critical = task_id in critical_path

        draw_gantt_bar(
            ws, current_row, chart_start_col, faz_offset, duration_cols, sez_offset,
            bar_color, is_critical, config
        )

        current_row += 1


def create_resource_list(wb: Workbook, project: PersonProject, result: CPMResult,
                        report: ResourceListReport, full_config: Dict[str, Any]) -> None:
    """
    Erstellt Resource-List-Worksheet.

    Args:
        wb: Workbook
        project: Projekt-Daten
        result: CPM-Berechnungsergebnis
        report: Resource List Report-Konfiguration
        full_config: Vollständige Excel-Export-Konfiguration (alle Sektionen)
    """
    # Extrahiere die relevanten Config-Sektionen
    config = full_config['GanttChart']  # Für Farben
    resource_config = full_config['ResourceList']
    resolution_config = full_config['Gantt_resolution']

    ws = wb.create_sheet(title=report.name)

    # Headline
    ws['A1'] = report.headline
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:E1')

    # Spalten-Header
    row = 3
    for col_idx, col_name in enumerate(report.columns, start=1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal='center')

    # Setze Spaltenbreiten aus Config
    ws.column_dimensions['A'].width = resource_config['col_width_resource']
    ws.column_dimensions['B'].width = resource_config['col_width_task']
    ws.column_dimensions['C'].width = resource_config['col_width_start']
    ws.column_dimensions['D'].width = resource_config['col_width_end']

    # Timeline berechnen mit Resolution-Config
    start_date, end_date, granularity = get_timeline_range(result, report.loadunit, resolution_config)

    # Timeline-Header (ab Spalte 5 = 'chart')
    chart_start_col = len(report.columns)
    working_days = resolution_config['working_days']
    timeline_rows = create_timeline_header(ws, chart_start_col, row, start_date, end_date, granularity, working_days)

    # Daten-Zeilen (Personen und Maschinen)
    data_start_row = row + timeline_rows
    current_row = data_start_row

    # Erstelle Ressource -> Tasks Mapping
    resource_tasks = {}
    for res in project.resources:
        resource_tasks[res.id] = []

    # Sammle Tasks pro Ressource
    for task_id in result.tasks.keys():
        task = next((t for t in project.tasks if t.id == task_id), None)
        if task and task.resources:
            for res_id in task.resources:
                if res_id in resource_tasks:
                    resource_tasks[res_id].append(task_id)

    # Erstelle Liste aller anzuzeigenden Ressourcen (Personen + Maschinen)
    display_resources = []

    # Erst Personen
    for person in project.persons:
        person_res = next((r for r in project.resources if hasattr(r, 'person_id') and r.person_id == person.id), None)
        if person_res:
            display_resources.append({
                'type': 'person',
                'id': person_res.id,
                'name': person.name,
                'role': person.role if hasattr(person, 'role') else '',
                'person_id': person.id,
                'color': person_res.color if hasattr(person_res, 'color') else None
            })

    # Dann Maschinen (machine, truck)
    for res in project.resources:
        if res.type in ['machine', 'truck']:
            display_resources.append({
                'type': res.type,
                'id': res.id,
                'name': res.name,
                'role': res.type.capitalize(),
                'person_id': None,
                'color': res.color if hasattr(res, 'color') else None
            })

    # Farb-Zuweisung für alle Ressourcen
    num_resources = len(display_resources)
    resource_colors = {}
    for res_idx, res_info in enumerate(display_resources):
        # Verwende benutzerdefinierte Farbe falls vorhanden, sonst interpolierte Farbe
        if res_info.get('color'):
            resource_colors[res_info['id']] = res_info['color']
        else:
            # Fallback: Farb-Interpolation
            if num_resources > 1:
                color_position = res_idx / (num_resources - 1)
            else:
                color_position = 0.0
            resource_colors[res_info['id']] = interpolate_color(config['color_start'], config['color_end'], color_position)

    # Zeitfaktor (analog zu Gantt-Chart)
    # task.faz, task.duration sind in "Tagen" (1 Tag = 8 Arbeitsstunden)
    if granularity == 'minutes':
        time_unit_factor = 480  # 1 Arbeitstag = 480 Minuten
    elif granularity == 'hours':
        time_unit_factor = 8  # 1 Arbeitstag = 8 Arbeitsstunden
    elif granularity == 'halfdays':
        time_unit_factor = 2  # 1 Arbeitstag = 2 halbe Tage
    else:
        time_unit_factor = 1  # 1 Tag = 1 Spalte

    # Zeige alle Ressourcen
    for res_info in display_resources:
        # Spalte A: Name
        ws.cell(row=current_row, column=1, value=res_info['name'])

        # Spalte B: Rolle/Typ
        ws.cell(row=current_row, column=2, value=res_info['role'])

        # Spalte C: start (leer)
        ws.cell(row=current_row, column=3, value='')

        # Spalte D: end (leer)
        ws.cell(row=current_row, column=4, value='')

        # Spalte E+: chart (Balken für Tasks)
        res_color = resource_colors[res_info['id']]

        for task_id in resource_tasks[res_info['id']]:
            task = result.tasks[task_id]

            faz_offset = int(task.faz * time_unit_factor)
            duration_cols = max(1, int(task.duration * time_unit_factor))

            # Prüfe ob Task eine Pause ist
            is_break = hasattr(task, 'is_break') and task.is_break

            # Zeichne Balken (ohne Puffer, nur Dauer)
            for col_offset in range(faz_offset, faz_offset + duration_cols):
                cell = ws.cell(row=current_row, column=chart_start_col + col_offset)
                if is_break:
                    # Pausen werden in Grau dargestellt
                    cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
                else:
                    # Normale Arbeitszeit in Ressourcenfarbe
                    cell.fill = PatternFill(start_color=res_color, end_color=res_color, fill_type="solid")

        current_row += 1

    # Färbe Wochenend-Spalten grau (nur leere Zellen)
    if granularity == 'days':
        weekend_fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
        duration_days = (end_date - start_date).days + 1

        for day_offset in range(duration_days):
            current_date = start_date + timedelta(days=day_offset)
            # Prüfe ob Wochenende (Samstag=5, Sonntag=6)
            if current_date.weekday() in [5, 6]:
                weekend_col = chart_start_col + day_offset
                # Färbe diese Spalte für alle Ressourcen-Zeilen (nur wenn leer)
                for row_offset in range(len(display_resources)):
                    cell = ws.cell(row=data_start_row + row_offset, column=weekend_col)
                    # Nur färben wenn Zelle noch keine Füllung hat (leer)
                    if not cell.fill or cell.fill.start_color.index in ['00000000', 'FFFFFFFF', None]:
                        cell.fill = weekend_fill


def add_report_sheets(wb: Workbook, project: PersonProject, result: CPMResult,
                     cfg_dir: Path) -> None:
    """
    Fügt Report-Worksheets zur Excel-Datei hinzu.

    Args:
        wb: Workbook
        project: Projekt-Daten (PersonProject mit reports)
        result: CPM-Berechnungsergebnis
        cfg_dir: Verzeichnis mit Konfigurationsdateien
    """
    if not project.reports:
        return

    # Lade Excel-Export-Konfiguration (alle Sektionen)
    full_config = load_excel_export_config(cfg_dir)

    for report in project.reports:
        if isinstance(report, GanttReport):
            create_gantt_chart(wb, project, result, report, full_config)
        elif isinstance(report, ResourceListReport):
            create_resource_list(wb, project, result, report, full_config)
        # Weitere Report-Typen können hier hinzugefügt werden
