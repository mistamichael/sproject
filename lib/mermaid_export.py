"""
Mermaid/SVG Export Generator via kroki-API
===========================================

Generiert Gantt-Charts und Diagramme im SVG-Format über Mermaid und kroki-API.
"""

import base64
import zlib
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import models - try relative import first, then absolute
try:
    from .models.cpm import CPMResult
    from .utils import format_time_value_auto
except (ImportError, ValueError):
    from models.cpm import CPMResult
    from utils import format_time_value_auto


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
        lines.append("    axisFormat  %H:%M")
    elif time_unit == 'hours':
        # Für Stunden: zeige Datum + Uhrzeit
        lines.append("    dateFormat  YYYY-MM-DD HH:mm")
        lines.append("    axisFormat  %H:%M")
    else:
        # Für Tage: zeige nur Datum
        lines.append("    dateFormat  YYYY-MM-DD")
        lines.append("    axisFormat  %d.%m")

    lines.append("")

    # Gruppiere Tasks (optional, hier einfache Variante)
    lines.append("    section Tasks")

    # tasks ist ein Dictionary: {task_id: CPMTaskResult}
    for task_id, task in result.tasks.items():
        # Task-Name
        task_name = task.name.replace(":", "").replace(",", "")  # Bereinige Sonderzeichen

        # Kritische Tasks markieren
        if task.is_critical:
            task_label = f"[{task_id}] {task_name} (KRIT)"
            task_status = "crit"
        else:
            task_label = f"[{task_id}] {task_name}"
            task_status = ""

        # Startdatum aus FAZ berechnen
        if hasattr(result, 'project_start') and result.project_start:
            start_date = result.project_start
        else:
            start_date = datetime.now()

        # Berechne Start- und Enddatum für den Task basierend auf Zeit-Einheit
        if time_unit == 'minutes':
            # FAZ/FEZ sind in Tagen, aber die Auflösung ist Minuten
            # Berechne die Minuten-Offset innerhalb des Tages
            total_minutes_start = task.faz * 480  # 1 Tag = 480 Minuten (8h * 60)
            total_minutes_end = task.fez * 480

            # Extrahiere Tage und Minuten
            days_start = int(total_minutes_start // 480)
            minutes_start = int(total_minutes_start % 480)
            days_end = int(total_minutes_end // 480)
            minutes_end = int(total_minutes_end % 480)

            # Berechne DateTime
            task_start = start_date + timedelta(days=days_start, minutes=minutes_start)
            task_end = start_date + timedelta(days=days_end, minutes=minutes_end)

            # Formatiere mit Uhrzeit
            start_str = task_start.strftime('%Y-%m-%d %H:%M')
            end_str = task_end.strftime('%Y-%m-%d %H:%M')

        elif time_unit == 'hours':
            # FAZ/FEZ sind in Tagen, aber die Auflösung ist Stunden
            # 1 Tag = 8 Stunden
            total_hours_start = task.faz * 8
            total_hours_end = task.fez * 8

            # Extrahiere Tage und Stunden
            days_start = int(total_hours_start // 8)
            hours_start = int(total_hours_start % 8)
            days_end = int(total_hours_end // 8)
            hours_end = int(total_hours_end % 8)

            # Berechne DateTime
            task_start = start_date + timedelta(days=days_start, hours=hours_start)
            task_end = start_date + timedelta(days=days_end, hours=hours_end)

            # Formatiere mit Uhrzeit
            start_str = task_start.strftime('%Y-%m-%d %H:%M')
            end_str = task_end.strftime('%Y-%m-%d %H:%M')
        else:
            # Für Tage: verwende nur Datum
            task_start = start_date + timedelta(days=task.faz)
            task_end = start_date + timedelta(days=task.fez)

            # Formatiere Datum
            start_str = task_start.strftime('%Y-%m-%d')
            end_str = task_end.strftime('%Y-%m-%d')

        # Mermaid-Syntax: task_id, task_status, start, duration/end
        if task_status:
            lines.append(f"    {task_label} :{task_status}, {start_str}, {end_str}")
        else:
            lines.append(f"    {task_label} :{start_str}, {end_str}")

    return "\n".join(lines)


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
