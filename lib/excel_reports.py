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
    from .cpm_calculator import SimpleCPMCalculator
    from .utils import format_time_value_auto
except (ImportError, ValueError):
    from models import PersonProject, Report, GanttReport, ResourceListReport
    from cpm_calculator import SimpleCPMCalculator
    from utils import format_time_value_auto


def load_gantt_config(cfg_dir: Path) -> Dict[str, Any]:
    """
    Lädt Gantt-Chart-Konfiguration aus defaults.cfg.

    Args:
        cfg_dir: Verzeichnis mit Konfigurationsdateien

    Returns:
        Dictionary mit Konfigurationswerten
    """
    config = configparser.ConfigParser()
    config_file = cfg_dir / "defaults.cfg"

    # Default-Werte
    defaults = {
        'color_start': '8B7AB8',
        'color_end': '4472C4',
        'critical_border_color': 'FF0000',
        'slack_bar_transparency': 180,
        'bar_height': 20,
        'timeline_header_height': 25,
    }

    if config_file.exists():
        config.read(config_file, encoding='utf-8')
        if 'GanttChart' in config:
            for key in defaults.keys():
                if key in config['GanttChart']:
                    value = config['GanttChart'][key]
                    # Konvertiere numerische Werte
                    if key in ['slack_bar_transparency', 'bar_height', 'timeline_header_height']:
                        defaults[key] = int(value)
                    else:
                        defaults[key] = value

    return defaults


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


def get_timeline_range(calc: SimpleCPMCalculator, loadunit: str) -> Tuple[datetime, datetime, str]:
    """
    Berechnet Zeitbereich und Granularität für Timeline.

    Args:
        calc: CPM Calculator mit berechneten Daten
        loadunit: Zeiteinheit (hours, days, etc.)

    Returns:
        (start_date, end_date, granularity)
        granularity kann sein: 'hours', 'days', 'weeks'
    """
    # Berechne Projektende
    project_duration = max(data['fez'] for data in calc.cpm_data.values())
    start_date = calc.start_date
    end_date = calc._add_workdays(start_date, project_duration)

    # Bestimme Granularität
    duration_days = (end_date - start_date).days

    if loadunit == 'hours' or duration_days <= 1:
        granularity = 'hours'
    elif duration_days <= 7:
        granularity = 'days'
    else:
        granularity = 'days'  # Bei >7 Tagen auch days, aber mit Kalenderwochen

    return start_date, end_date, granularity


def create_timeline_header(ws, start_col: int, start_row: int, start_date: datetime,
                          end_date: datetime, granularity: str) -> int:
    """
    Erstellt Timeline-Header (Zeitstrahl) in Excel.

    Args:
        ws: Worksheet
        start_col: Start-Spalte für Timeline
        start_row: Start-Zeile für Header
        start_date: Projekt-Startdatum
        end_date: Projekt-Enddatum
        granularity: 'hours', 'days', 'weeks'

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

    if granularity == 'hours':
        # Stunden-basierte Timeline
        current_date = start_date
        while current_date <= end_date:
            cell = ws.cell(row=start_row, column=current_col, value=current_date.strftime('%H:%M'))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border
            ws.column_dimensions[get_column_letter(current_col)].width = 6

            current_date += timedelta(hours=1)
            current_col += 1

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
        cell.fill = PatternFill(start_color=color + '40', end_color=color + '40', fill_type="solid")

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
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

        if critical and border_color:
            # Rote Umrandung für kritischen Pfad
            border_side = Side(style='medium', color=border_color)
            if col_offset == faz_offset:
                cell.border = Border(left=border_side, top=border_side, bottom=border_side)
            elif col_offset == faz_offset + duration_cols - 1:
                cell.border = Border(right=border_side, top=border_side, bottom=border_side)
            else:
                cell.border = Border(top=border_side, bottom=border_side)


def create_gantt_chart(wb: Workbook, project: PersonProject, calc: SimpleCPMCalculator,
                      report: GanttReport, config: Dict[str, Any]) -> None:
    """
    Erstellt Gantt-Chart-Worksheet.

    Args:
        wb: Workbook
        project: Projekt-Daten
        calc: CPM Calculator mit berechneten Daten
        report: Gantt Report-Konfiguration
        config: Gantt-Konfiguration aus defaults.cfg
    """
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

    # Setze Spaltenbreiten
    ws.column_dimensions['A'].width = 12  # Vorgang
    ws.column_dimensions['B'].width = 20  # name
    ws.column_dimensions['C'].width = 12  # start
    ws.column_dimensions['D'].width = 12  # end
    ws.column_dimensions['E'].width = 10  # effort

    # Timeline berechnen
    start_date, end_date, granularity = get_timeline_range(calc, report.loadunit)

    # Timeline-Header (ab Spalte 6 = 'chart')
    chart_start_col = len(report.columns)
    timeline_rows = create_timeline_header(ws, chart_start_col, row, start_date, end_date, granularity)

    # Daten-Zeilen
    data_start_row = row + timeline_rows
    current_row = data_start_row

    # Sortiere Tasks nach FAZ (Frühester Anfangszeitpunkt), dann nach ID
    sorted_task_ids = sorted(
        calc.cpm_data.keys(),
        key=lambda x: (calc.cpm_data[x]['faz'], str(x))
    )

    # Kritischer Pfad
    critical_path = calc.get_critical_path()

    # Farb-Interpolation
    num_tasks = len(sorted_task_ids)

    for task_idx, task_id in enumerate(sorted_task_ids):
        data = calc.cpm_data[task_id]

        # Interpoliere Farbe
        if num_tasks > 1:
            color_position = task_idx / (num_tasks - 1)
        else:
            color_position = 0.0

        bar_color = interpolate_color(config['color_start'], config['color_end'], color_position)

        # Spalte A: Vorgang (Task-ID)
        ws.cell(row=current_row, column=1, value=str(task_id))

        # Spalte B: name (Task-Name, nicht Person!)
        ws.cell(row=current_row, column=2, value=data['name'])

        # Spalte C: start (leer, da nicht in Task-Daten)
        ws.cell(row=current_row, column=3, value='')

        # Spalte D: end (leer, da nicht in Task-Daten)
        ws.cell(row=current_row, column=4, value='')

        # Spalte E: effort
        ws.cell(row=current_row, column=5, value=format_time_value_auto(data['duration']))

        # Spalte F+: chart (Balkendiagramm)
        # Berechne Positionen
        if granularity == 'hours':
            time_unit_factor = 24  # 1 Tag = 24 Stunden
        else:
            time_unit_factor = 1  # 1 Tag = 1 Spalte

        faz_offset = int(data['faz'] * time_unit_factor)
        duration_cols = max(1, int(data['duration'] * time_unit_factor))
        sez_offset = int(data['sez'] * time_unit_factor)

        is_critical = task_id in critical_path

        draw_gantt_bar(
            ws, current_row, chart_start_col, faz_offset, duration_cols, sez_offset,
            bar_color, is_critical, config
        )

        current_row += 1


def create_resource_list(wb: Workbook, project: PersonProject, calc: SimpleCPMCalculator,
                        report: ResourceListReport, config: Dict[str, Any]) -> None:
    """
    Erstellt Resource-List-Worksheet.

    Args:
        wb: Workbook
        project: Projekt-Daten
        calc: CPM Calculator mit berechneten Daten
        report: Resource List Report-Konfiguration
        config: Gantt-Konfiguration aus defaults.cfg
    """
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

    # Setze Spaltenbreiten
    ws.column_dimensions['A'].width = 20  # User
    ws.column_dimensions['B'].width = 20  # Rolle
    ws.column_dimensions['C'].width = 12  # start
    ws.column_dimensions['D'].width = 12  # end

    # Timeline berechnen
    start_date, end_date, granularity = get_timeline_range(calc, report.loadunit)

    # Timeline-Header (ab Spalte 5 = 'chart')
    chart_start_col = len(report.columns)
    timeline_rows = create_timeline_header(ws, chart_start_col, row, start_date, end_date, granularity)

    # Daten-Zeilen (Personen)
    data_start_row = row + timeline_rows
    current_row = data_start_row

    # Erstelle Person -> Tasks Mapping
    person_tasks = {}
    for person in project.persons:
        person_tasks[person.id] = []

    # Sammle Tasks pro Person
    for task_id in calc.cpm_data.keys():
        task = next((t for t in project.tasks if t.id == task_id), None)
        if task and task.resources:
            for res_id in task.resources:
                res = next((r for r in project.resources if r.id == res_id), None)
                if res and hasattr(res, 'person_id'):
                    person_tasks[res.person_id].append(task_id)

    # Farb-Interpolation für Tasks
    all_task_ids = sorted(calc.cpm_data.keys(), key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0)
    num_tasks = len(all_task_ids)
    task_colors = {}
    for task_idx, task_id in enumerate(all_task_ids):
        if num_tasks > 1:
            color_position = task_idx / (num_tasks - 1)
        else:
            color_position = 0.0
        task_colors[task_id] = interpolate_color(config['color_start'], config['color_end'], color_position)

    # Zeige Personen
    for person in project.persons:
        # Spalte A: User
        ws.cell(row=current_row, column=1, value=person.name)

        # Spalte B: Rolle
        ws.cell(row=current_row, column=2, value=person.role if hasattr(person, 'role') else '')

        # Spalte C: start (leer)
        ws.cell(row=current_row, column=3, value='')

        # Spalte D: end (leer)
        ws.cell(row=current_row, column=4, value='')

        # Spalte E+: chart (Balken für Tasks)
        if granularity == 'hours':
            time_unit_factor = 24
        else:
            time_unit_factor = 1

        for task_id in person_tasks[person.id]:
            data = calc.cpm_data[task_id]

            faz_offset = int(data['faz'] * time_unit_factor)
            duration_cols = max(1, int(data['duration'] * time_unit_factor))

            bar_color = task_colors[task_id]

            # Zeichne Balken (ohne Puffer, nur Dauer)
            for col_offset in range(faz_offset, faz_offset + duration_cols):
                cell = ws.cell(row=current_row, column=chart_start_col + col_offset)
                cell.fill = PatternFill(start_color=bar_color, end_color=bar_color, fill_type="solid")

        current_row += 1


def add_report_sheets(wb: Workbook, project: PersonProject, calc: SimpleCPMCalculator,
                     cfg_dir: Path) -> None:
    """
    Fügt Report-Worksheets zur Excel-Datei hinzu.

    Args:
        wb: Workbook
        project: Projekt-Daten (PersonProject mit reports)
        calc: CPM Calculator mit berechneten Daten
        cfg_dir: Verzeichnis mit Konfigurationsdateien
    """
    if not project.reports:
        return

    # Lade Gantt-Konfiguration
    config = load_gantt_config(cfg_dir)

    for report in project.reports:
        if isinstance(report, GanttReport):
            create_gantt_chart(wb, project, calc, report, config)
        elif isinstance(report, ResourceListReport):
            create_resource_list(wb, project, calc, report, config)
        # Weitere Report-Typen können hier hinzugefügt werden
