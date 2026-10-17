"""
Mermaid/SVG Export Generator via kroki-API
===========================================

Generiert Gantt-Charts und Diagramme im SVG-Format über Mermaid und kroki-API.
"""

import base64
import zlib
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import models - try relative import first, then absolute
from .models.cpm import CPMResult


def encode_kroki_url(diagram: str) -> str:
    """
    Kodiert ein Mermaid-Diagramm für die kroki-API.

    Args:
        diagram: Mermaid-Diagramm als String

    Returns:
        Base64-kodierter, komprimierter String für kroki
    """
    compressed = zlib.compress(diagram.encode('utf-8'))
    return base64.urlsafe_b64encode(compressed).decode('utf-8')


def generate_mermaid_gantt(result: CPMResult, project_name: str = "Project") -> str:
    """
    Generiert ein Mermaid Gantt-Chart aus CPM-Ergebnissen mit Berücksichtigung der Zeit-Auflösung.
    Zeigt auch Wochenenden und Feiertage als Sektionen an.

    Args:
        result: CPMResult mit berechneten Task-Daten
        project_name: Name des Projekts

    Returns:
        Mermaid-Gantt-Diagramm als String
    """
    from datetime import timedelta

    lines = []
    lines.append("gantt")
    lines.append(f"    title {project_name}")

    # Bestimme Zeit-Einheit und entsprechende Formate
    time_unit = getattr(result, 'time_unit', 'days')

    if time_unit == 'minutes':
        # Für Minuten: zeige Datum + Uhrzeit
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %d.%m")
    elif time_unit == 'hours':
        # Für Stunden: zeige Datum + Uhrzeit
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %d.%m")
    else:
        # Für Tage: zeige nur Datum
        lines.append("    dateFormat  YYYY-MM-DD")
        lines.append("    axisFormat  %d.%m")

    lines.append("")

    # Zeitspanne des Projekts (gleiche Umrechnung wie alle Ausgaben: CPMResult.date_at)
    if result.project_start is None or not result.tasks:
        return "\n".join(lines)
    first_day = result.date_at(min(task.faz for task in result.tasks.values()))
    last_day = result.date_at(result.project_end_days, is_end=True)

    # Zeige Wochenenden als Sektion
    if result.skip_weekends and time_unit == 'days':
        lines.append("    section Wochenenden")

        # Iteriere über alle Tage und markiere Wochenenden
        current_date = first_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_check_date = last_day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        weekend_start = None

        while current_date <= end_check_date:
            is_weekend = current_date.weekday() >= 5  # 5=Sa, 6=So

            if is_weekend and weekend_start is None:
                weekend_start = current_date
            elif not is_weekend and weekend_start is not None:
                # Wochenende endet
                weekend_end = current_date - timedelta(days=1)
                we_label = weekend_start.strftime('%d.%m')
                lines.append(f"    WE {we_label} :crit, {weekend_start.strftime('%Y-%m-%d')}, {weekend_end.strftime('%Y-%m-%d')}")
                weekend_start = None

            current_date += timedelta(days=1)

        # Letztes Wochenende falls noch offen
        if weekend_start is not None:
            weekend_end = end_check_date - timedelta(days=1)
            we_label = weekend_start.strftime('%d.%m')
            lines.append(f"    WE {we_label} :crit, {weekend_start.strftime('%Y-%m-%d')}, {weekend_end.strftime('%Y-%m-%d')}")

    # Zeige Feiertage als Sektion
    if result.skip_holidays and result.holidays:
        lines.append("    section Feiertage")

        for holiday_str in sorted(result.holidays):
            try:
                holiday_date = datetime.strptime(holiday_str, '%Y-%m-%d')
                # Prüfe ob Feiertag im Projektbereich liegt
                if first_day.date() <= holiday_date.date() <= last_day.date():
                    name = result.holidays[holiday_str] if isinstance(result.holidays, dict) else ''
                    holiday_label = f"{holiday_date.strftime('%d.%m')} {name}".strip()
                    lines.append(f"    {holiday_label} :crit, {holiday_str}, {holiday_str}")
            except ValueError:
                pass

    # Gruppiere Tasks
    lines.append("    section Tasks")

    # tasks ist ein Dictionary: {task_id: CPMTaskResult}
    for task_id, task in result.tasks.items():
        # Skip Weekend-Blocker Tasks
        if result.is_blocker(task_id):
            continue

        # Task-Name
        task_name = task.name.replace(":", "").replace(",", "")  # Bereinige Sonderzeichen

        # Kritische Tasks markieren
        if task.is_critical:
            task_label = f"[{task_id}] {task_name} (KRIT)"
            task_status = "crit"
        else:
            task_label = f"[{task_id}] {task_name}"
            task_status = ""

        # Berechne Start- und Enddatum für den Task basierend auf Zeit-Einheit
        start_str, end_str = mermaid_span(result, task.faz, task.fez)

        # Mermaid-Syntax: task_id, task_status, start, duration/end
        if task_status:
            lines.append(f"    {task_label} :{task_status}, {start_str}, {end_str}")
        else:
            lines.append(f"    {task_label} :{start_str}, {end_str}")

    return "\n".join(lines)


def mermaid_span(result: CPMResult, faz: float, fez: float) -> tuple:
    """
    (Start, Ende) eines Balkens im Mermaid-Format. Mit reinem Datum ist das Mermaid-Ende
    exklusiv – daher der Tag nach dem letzten Arbeitstag.
    """
    start = result.date_at(faz)
    end = result.date_at(fez, is_end=True) if fez > faz else start
    if result.time_unit in ('minutes', 'hours'):
        return start.strftime('%Y-%m-%d %H:%M'), end.strftime('%Y-%m-%d %H:%M')
    return start.strftime('%Y-%m-%d'), (end + timedelta(days=1)).strftime('%Y-%m-%d')


def export_mermaid_to_svg(mermaid_diagram: str, output_path: Path,
                          kroki_url: str = "https://kroki.io") -> bool:
    """
    Exportiert ein Mermaid-Diagramm als SVG über die kroki-API.

    Args:
        mermaid_diagram: Mermaid-Diagramm als String
        output_path: Pfad zur Ausgabe-SVG-Datei
        kroki_url: URL zur kroki-API (default: https://kroki.io)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not REQUESTS_AVAILABLE:
        print("FEHLER: requests-Bibliothek nicht verfügbar. Installiere mit: pip install requests")
        return False

    try:
        # Erstelle kroki-URL
        encoded = encode_kroki_url(mermaid_diagram)
        url = f"{kroki_url}/mermaid/svg/{encoded}"

        # Lade SVG von kroki
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Speichere SVG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"INFO: SVG erfolgreich exportiert nach: {output_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"FEHLER: Konnte SVG nicht von kroki laden: {e}")
        return False
    except Exception as e:
        print(f"FEHLER: SVG-Export fehlgeschlagen: {e}")
        return False


def export_cpm_to_svg(result: CPMResult, output_path: Path,
                      project_name: str = "Project",
                      kroki_url: str = "https://kroki.io") -> bool:
    """
    Exportiert CPM-Ergebnisse als SVG-Gantt-Chart über Mermaid/kroki.

    Args:
        result: CPMResult mit berechneten Task-Daten
        output_path: Pfad zur Ausgabe-SVG-Datei
        project_name: Name des Projekts
        kroki_url: URL zur kroki-API (default: https://kroki.io)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    # Generiere Mermaid-Diagramm
    mermaid = generate_mermaid_gantt(result, project_name)

    # Exportiere als SVG
    return export_mermaid_to_svg(mermaid, output_path, kroki_url)
