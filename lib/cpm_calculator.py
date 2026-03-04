#!/usr/bin/env python3
"""
cpm_calculator.py
=================
Berechnet den kritischen Pfad (Critical Path Method) für einfache Projektdateien.
Unterstützt JSON-Dateien mit vereinfachter Struktur (wie tankdesign.json).

DEPRECATED: Diese Klasse wird in Zukunft durch Project.calculate_cpm() ersetzt.
Verwenden Sie stattdessen:
    from models import load_project
    project = load_project("file.json")
    result = project.calculate_cpm()
"""

import json
import warnings
from pathlib import Path
from typing import Any, Optional, Union
from datetime import datetime, timedelta

try:
    from config_loader import get_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class SimpleCPMCalculator:
    """
    Berechnet CPM für einfache Projektdateien ohne vollständige TJP-Struktur.

    DEPRECATED: Verwenden Sie stattdessen Project.calculate_cpm() aus dem models Package.
    Diese Klasse wird für Rückwärtskompatibilität beibehalten, delegiert aber
    an die neue Pydantic-basierte Implementierung.
    """

    def __init__(self, project_data: Union[dict, 'ProjectBase']):
        """
        Initialisiert den Calculator mit Projektdaten.

        Args:
            project_data: Dictionary mit 'project' und 'tasks' Keys ODER ProjectBase-Instanz
        """
        # Konvertiere dict zu Project falls nötig
        if isinstance(project_data, dict):
            try:
                from models import load_project_from_dict
            except ImportError:
                from .models import load_project_from_dict
            self.project = load_project_from_dict(project_data)
            self._is_legacy = True
        else:
            # Bereits ein Pydantic-Project
            self.project = project_data
            self._is_legacy = False

        # Für Rückwärtskompatibilität
        self.project_name = self.project.project
        self.tasks = [
            {
                'id': task.id,
                'name': task.name,
                'duration': task.duration,
                'dependencies': task.dependencies or []
            }
            for task in self.project.tasks
        ]

        # Lade Defaults aus Config
        if HAS_CONFIG:
            config = get_config()
            self.start_date = config.get_project_start_date()
            self.config = config
        else:
            self.start_date = datetime.now()
            self.config = None

        self.cpm_data = {}

        # Erkenne die dominante Zeiteinheit in den Tasks
        self.time_unit = self.project.get_time_unit()

        # Interner Calculator (wird bei Bedarf erstellt)
        self._calculator = None
        self._result = None

    @classmethod
    def from_file(cls, file_path: Path) -> 'SimpleCPMCalculator':
        """Lädt Projektdaten aus JSON-Datei."""
        try:
            from models import load_project
        except ImportError:
            from .models import load_project
        project = load_project(file_path)
        return cls(project)

    def calculate(self) -> dict[Union[int, str], dict[str, Any]]:
        """
        Führt die vollständige CPM-Berechnung durch.

        Returns:
            Dictionary mit task_id als Key und CPM-Daten
        """
        # Delegiere an neue Implementation
        try:
            from models.cpm import CPMCalculator
        except ImportError:
            from .models.cpm import CPMCalculator

        self._calculator = CPMCalculator(self.project, self.start_date)
        self._result = self._calculator.calculate()

        # Konvertiere zurück zu Legacy-Format für Rückwärtskompatibilität
        self.cpm_data = {}
        for task_id, task_result in self._result.tasks.items():
            self.cpm_data[task_id] = {
                'id': task_result.id,
                'name': task_result.name,
                'duration': task_result.duration,
                'successors': task_result.successors,
                'predecessors': task_result.predecessors,
                'faz': task_result.faz,
                'fez': task_result.fez,
                'saz': task_result.saz,
                'sez': task_result.sez,
                'puffer': task_result.puffer,
                'free_puffer': task_result.free_puffer,
                'is_critical': task_result.is_critical,
            }

        return self.cpm_data

    def _parse_duration(self, duration_value) -> float:
        """
        Parst Duration-Wert zu Tagen (float).
        Unterstützt: Zahlen (10), Strings mit Einheit ("10d", "2w", "8h")

        Args:
            duration_value: Kann int, float oder str sein

        Returns:
            Dauer in Tagen als float
        """
        # Falls bereits eine Zahl, direkt zurückgeben
        if isinstance(duration_value, (int, float)):
            return float(duration_value)

        # String-Verarbeitung
        if isinstance(duration_value, str):
            duration_str = duration_value.strip()
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

    def _detect_time_unit(self) -> str:
        """
        Erkennt die dominante Zeiteinheit in den Tasks.

        Returns:
            'minutes', 'hours' oder 'days'
        """
        unit_counts = {'m': 0, 'h': 0, 'd': 0}

        for task in self.tasks:
            duration_value = task.get('duration', 0)
            if isinstance(duration_value, str):
                duration_str = duration_value.strip()
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

    def _format_time_value(self, days: float) -> str:
        """
        Formatiert einen Zeitwert basierend auf der erkannten Zeiteinheit.

        Args:
            days: Zeitwert in Tagen

        Returns:
            Formatierter String (z.B. "120m", "2.5h", "1d")
        """
        if self.time_unit == 'minutes':
            minutes = days * 480  # 8h * 60min
            return f"{minutes:.1f}m"
        elif self.time_unit == 'hours':
            hours = days * 8
            return f"{hours:.1f}h"
        else:
            return f"{days:.1f}d"

    def _format_datetime_value(self, days: float) -> str:
        """
        Formatiert einen Zeitwert als Zeitangabe oder Datum+Uhrzeit.

        Args:
            days: Zeitwert in Tagen

        Returns:
            Formatierter String basierend auf Zeiteinheit
        """
        if self.time_unit == 'minutes':
            minutes = days * 480
            if minutes < 1440:  # < 24h
                hours = minutes / 60
                return f"{hours:.2f}h"
            else:
                # Berechne Datum und Uhrzeit
                dt = self._add_workdays(self.start_date, days)
                return dt.strftime('%Y-%m-%d %H:%M')
        elif self.time_unit == 'hours':
            hours = days * 8
            if hours < 24:
                return f"{hours:.2f}h"
            else:
                dt = self._add_workdays(self.start_date, days)
                return dt.strftime('%Y-%m-%d %H:%M')
        else:
            # Tage-Format: verwende Datum
            dt = self._add_workdays(self.start_date, days)
            return dt.strftime('%Y-%m-%d')

    def _initialize_cpm_data(self) -> None:
        """Initialisiert die CPM-Datenstruktur für alle Tasks."""
        # Erstmal alle Tasks erfassen
        for task in self.tasks:
            task_id = task['id']
            duration_raw = task.get('duration', 0)
            duration = self._parse_duration(duration_raw)

            self.cpm_data[task_id] = {
                'id': task_id,
                'name': task.get('name', f'Task {task_id}'),
                'duration': duration,
                'successors': task.get('dependencies', []),  # Nachfolger
                'predecessors': [],  # Wird unten berechnet
                'faz': 0,  # Frühester Anfangszeitpunkt
                'fez': 0,  # Frühester Endzeitpunkt
                'saz': 0,  # Spätester Anfangszeitpunkt
                'sez': 0,  # Spätester Endzeitpunkt
                'puffer': 0,  # Gesamtpuffer
                'is_critical': False,
            }

        # Berechne Vorgänger aus Nachfolgern
        # Wenn Task A Nachfolger [B, C] hat, dann sind B und C Vorgänger von A
        for task_id, data in self.cpm_data.items():
            for successor_id in data['successors']:
                if successor_id in self.cpm_data:
                    self.cpm_data[successor_id]['predecessors'].append(task_id)

    def _forward_pass(self) -> None:
        """
        Vorwärtsrechnung: Berechnet FAZ und FEZ.
        Verwendet topologische Sortierung für korrekte Reihenfolge.
        """
        # Topologische Sortierung
        sorted_ids = self._topological_sort()

        # Berechne FAZ und FEZ
        for task_id in sorted_ids:
            data = self.cpm_data[task_id]
            predecessors = data['predecessors']

            if not predecessors:
                # Startknoten: FAZ = 0
                data['faz'] = 0
            else:
                # FAZ = Maximum aller FEZ der Vorgänger
                max_fez = 0
                for pred_id in predecessors:
                    if pred_id in self.cpm_data:
                        max_fez = max(max_fez, self.cpm_data[pred_id]['fez'])
                data['faz'] = max_fez

            # FEZ = FAZ + Dauer
            data['fez'] = data['faz'] + data['duration']

    def _backward_pass(self) -> None:
        """
        Rückwärtsrechnung: Berechnet SAZ und SEZ.
        """
        # Finde Endknoten (Tasks ohne Nachfolger)
        end_nodes = [
            task_id for task_id, data in self.cpm_data.items()
            if not data['successors']
        ]

        # Projektende = maximaler FEZ
        project_end = max(data['fez'] for data in self.cpm_data.values())

        # Initialisiere SEZ für Endknoten
        for task_id in end_nodes:
            self.cpm_data[task_id]['sez'] = self.cpm_data[task_id]['fez']

        # Rückwärts-Topologische Sortierung
        reverse_sorted = list(reversed(self._topological_sort()))

        # Berechne SEZ und SAZ rückwärts
        for task_id in reverse_sorted:
            data = self.cpm_data[task_id]
            successors = data['successors']

            if not successors:
                # Endknoten: SEZ bereits gesetzt (= FEZ)
                if data['sez'] == 0:
                    data['sez'] = data['fez']
            else:
                # SEZ = Minimum aller SAZ der Nachfolger
                min_saz = float('inf')
                for succ_id in successors:
                    if succ_id in self.cpm_data:
                        min_saz = min(min_saz, self.cpm_data[succ_id]['saz'])
                data['sez'] = min_saz

            # SAZ = SEZ - Dauer
            data['saz'] = data['sez'] - data['duration']

    def _calculate_slack(self) -> None:
        """Berechnet die Pufferzeiten (Gesamt- und freier Puffer) und markiert kritische Tasks."""
        for task_id, data in self.cpm_data.items():
            # Gesamtpuffer (GP) = SAZ - FAZ (oder SEZ - FEZ)
            data['puffer'] = data['saz'] - data['faz']

            # Freier Puffer (FP) = Min(FAZ der Nachfolger) - FEZ
            # Falls keine Nachfolger: FP = GP
            if data['successors']:
                min_successor_faz = float('inf')
                for succ_id in data['successors']:
                    if succ_id in self.cpm_data:
                        min_successor_faz = min(min_successor_faz, self.cpm_data[succ_id]['faz'])
                data['free_puffer'] = min_successor_faz - data['fez']
            else:
                # Endknoten: freier Puffer = Gesamtpuffer
                data['free_puffer'] = data['puffer']

            # Kritische Tasks haben Gesamtpuffer ≈ 0
            data['is_critical'] = abs(data['puffer']) < 0.001

    def _topological_sort(self) -> list[Union[int, str]]:
        """
        Führt topologische Sortierung durch.

        Returns:
            Liste der Task-IDs in topologischer Reihenfolge
        """
        visited = set()
        result = []

        def visit(task_id: Union[int, str]):
            if task_id in visited or task_id not in self.cpm_data:
                return
            visited.add(task_id)

            # Erst alle Vorgänger besuchen
            for pred_id in self.cpm_data[task_id]['predecessors']:
                visit(pred_id)

            result.append(task_id)

        # Besuche alle Tasks
        for task_id in self.cpm_data.keys():
            visit(task_id)

        return result

    def get_critical_path(self) -> list[Union[int, str]]:
        """
        Gibt die Task-IDs auf dem kritischen Pfad zurück.

        Returns:
            Liste der Task-IDs (sortiert nach FAZ)
        """
        # Verwende Ergebnis aus neuer Implementation wenn verfügbar
        if self._result:
            return self._result.critical_path

        # Fallback auf Legacy-Daten
        critical_tasks = [
            task_id for task_id, data in self.cpm_data.items()
            if data['is_critical']
        ]

        # Sortiere nach FAZ (chronologisch)
        critical_tasks.sort(key=lambda tid: self.cpm_data[tid]['faz'])

        return critical_tasks

    def calculate_dates(self, start_date: Optional[datetime] = None) -> dict:
        """
        Berechnet konkrete Kalenderdaten basierend auf einem Startdatum.

        Args:
            start_date: Projektstartdatum (default: heute)

        Returns:
            Dictionary mit task_id und Datumsinformationen inkl. freier Tage
        """
        if start_date is None:
            start_date = self.start_date

        date_data = {}

        for task_id, data in self.cpm_data.items():
            # Berechne Arbeitstage (ohne Wochenenden)
            faz_date = self._add_workdays(start_date, data['faz'])
            fez_date = self._add_workdays(start_date, data['fez'])
            saz_date = self._add_workdays(start_date, data['saz'])
            sez_date = self._add_workdays(start_date, data['sez'])

            # Zähle freie Tage im Task-Zeitraum (von faz_date bis fez_date)
            free_days = self._count_free_days(faz_date, fez_date)

            date_data[task_id] = {
                'fb_date': faz_date.strftime('%Y-%m-%d'),  # Frühester Beginn
                'fe_date': fez_date.strftime('%Y-%m-%d'),  # Frühestes Ende
                'sb_date': saz_date.strftime('%Y-%m-%d'),  # Spätester Beginn
                'se_date': sez_date.strftime('%Y-%m-%d'),  # Spätestes Ende
                'free_days_info': free_days
            }

        return date_data

    def _add_workdays(self, start_date: datetime, days: float) -> datetime:
        """
        Addiert Arbeitstage zu einem Datum (ohne Wochenenden).

        Args:
            start_date: Startdatum
            days: Anzahl der Arbeitstage

        Returns:
            Neues Datum
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

    def _count_free_days(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Zählt die freien Tage zwischen zwei Daten (Wochenenden, Feiertage, Urlaub).

        Args:
            start_date: Startdatum (inklusiv)
            end_date: Enddatum (exklusiv)

        Returns:
            Dictionary mit num_weekend_days, num_holidays, num_free_days
        """
        if start_date >= end_date:
            return {
                'num_weekend_days': 0,
                'num_holidays': 0,
                'num_free_days': 0
            }

        # Lade Feiertage aus Config
        holidays_set = set()
        if self.config:
            # Hole Feiertage für das Jahr des Projekts
            year = start_date.year
            holidays_set = self.config.get_holidays(year)
            # Falls das Projekt über Jahreswechsel geht, hole auch nächstes Jahr
            if end_date.year > year:
                holidays_set.update(self.config.get_holidays(end_date.year))

        num_weekend_days = 0
        num_holidays = 0
        num_free_days = 0

        current = start_date
        while current < end_date:
            date_str = current.strftime('%Y-%m-%d')
            is_weekend = current.weekday() >= 5

            # Zähle Wochenenden (5=Samstag, 6=Sonntag)
            if is_weekend:
                num_weekend_days += 1
            # Zähle Feiertage (nur wenn nicht bereits Wochenende)
            elif date_str in holidays_set:
                num_holidays += 1

            # TODO: Hier könnte man Urlaub aus Config laden und prüfen
            current += timedelta(days=1)

        return {
            'num_weekend_days': num_weekend_days,
            'num_holidays': num_holidays,
            'num_free_days': num_free_days
        }

    def export_to_json(self, output_path: Path, include_dates: bool = True) -> None:
        """
        Exportiert die Ergebnisse in eine JSON-Datei.

        Args:
            output_path: Ausgabepfad
            include_dates: Ob Kalenderdaten eingeschlossen werden sollen
        """
        # Verwende neue Implementation falls verfügbar
        if self._result:
            output_data = self._result.export_to_dict(include_dates=include_dates)

            # Füge Config-basierte Felder hinzu falls verfügbar
            if self.config:
                default_resource = self.config.get_default_resource()
                if default_resource:
                    output_data['default_resource'] = default_resource

            # Bestimme JSON-Einrückung aus Config
            indent = 2
            if self.config:
                output_settings = self.config.get_output_settings()
                indent = output_settings.get('json_indent', 2)

            # Schreibe JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=indent, ensure_ascii=False)
            return

        # Legacy-Implementation (sollte nicht mehr erreicht werden)
        # Original-Projektdaten laden
        original_tasks = []
        for task in self.tasks:
            task_copy = task.copy()
            task_id = task_copy['id']

            if task_id in self.cpm_data:
                cpm = self.cpm_data[task_id]

                # Füge CPM-Daten hinzu mit deutschen Begriffen
                # Verwende formatierte Werte basierend auf der Zeiteinheit
                task_copy['cpm'] = {
                    'D': self._format_time_value(cpm['duration']),                  # Dauer
                    'FB': self._format_datetime_value(cpm['faz']),                  # Frühester Beginn
                    'FE': self._format_datetime_value(cpm['fez']),                  # Frühestes Ende
                    'SB': self._format_datetime_value(cpm['saz']),                  # Spätester Beginn
                    'SE': self._format_datetime_value(cpm['sez']),                  # Spätestes Ende
                    'GP': self._format_time_value(cpm['puffer']),                   # Gesamtpuffer
                    'FP': self._format_time_value(cpm['free_puffer']),              # Freier Puffer
                    'is_critical': cpm['is_critical'],
                }

                # Füge Kalenderdaten hinzu (optional)
                if include_dates:
                    date_data = self.calculate_dates()
                    if task_id in date_data:
                        task_date_info = date_data[task_id].copy()
                        free_days_info = task_date_info.pop('free_days_info', {})

                        # Basis-Datumsinformationen hinzufügen
                        task_copy['cpm']['dates'] = task_date_info

                        # Freie Tage nur hinzufügen, wenn mindestens einer vorhanden ist
                        total_free = (free_days_info.get('num_weekend_days', 0) +
                                     free_days_info.get('num_holidays', 0) +
                                     free_days_info.get('num_free_days', 0))

                        if total_free > 0:
                            if free_days_info.get('num_weekend_days', 0) > 0:
                                task_copy['cpm']['dates']['num_weekend_days'] = free_days_info['num_weekend_days']
                            if free_days_info.get('num_holidays', 0) > 0:
                                task_copy['cpm']['dates']['num_holidays'] = free_days_info['num_holidays']
                            if free_days_info.get('num_free_days', 0) > 0:
                                task_copy['cpm']['dates']['num_free_days'] = free_days_info['num_free_days']

            original_tasks.append(task_copy)

        # Hole Default-Ressource aus Config
        default_resource = None
        if self.config:
            default_resource = self.config.get_default_resource()

        # Berechne Projektdauer
        max_fez = max(data['fez'] for data in self.cpm_data.values())

        # Erstelle Ausgabe-JSON
        output_data = {
            'project': self.project_name,
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_start': self.start_date.strftime('%Y-%m-%d'),
            'critical_path': self.get_critical_path(),
            'project_duration': self._format_time_value(max_fez),
            'tasks': original_tasks,
        }

        # Füge Default-Ressource hinzu falls verfügbar
        if default_resource:
            output_data['default_resource'] = default_resource

        # Bestimme JSON-Einrückung aus Config
        indent = 2
        if self.config:
            output_settings = self.config.get_output_settings()
            indent = output_settings.get('json_indent', 2)

        # Schreibe JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=indent, ensure_ascii=False)

    def print_summary(self) -> None:
        """Gibt eine Zusammenfassung der CPM-Berechnung aus."""
        from utils import format_time_value_auto

        critical_path = self.get_critical_path()
        project_duration = max(data['fez'] for data in self.cpm_data.values())

        print("=" * 70)
        print(f"Projekt: {self.project_name}")
        print(f"Projektdauer: {format_time_value_auto(project_duration)}")
        print(f"Startdatum: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"Enddatum (geschaetzt): {self._add_workdays(self.start_date, project_duration).strftime('%Y-%m-%d')}")
        print("=" * 70)
        print()
        print("Kritischer Pfad:")
        for task_id in critical_path:
            data = self.cpm_data[task_id]
            duration_str = format_time_value_auto(data['duration'])
            print(f"  [{task_id}] {data['name']:<30} (Dauer: {duration_str})")
        print()
        print("=" * 70)
        print("Alle Tasks:")
        print(f"{'ID':<7} {'Name':<30} {'Dauer':<8} {'FAZ':<6} {'FEZ':<6} {'SAZ':<6} {'SEZ':<6} {'Puffer':<8} {'Krit.'}")
        print("-" * 70)

        for task_id in self._topological_sort():
            data = self.cpm_data[task_id]
            critical_marker = "JA" if data['is_critical'] else ""
            duration_str = format_time_value_auto(data['duration'])
            puffer_str = format_time_value_auto(data['puffer'])

            # Formatiere ID als String für korrekte Breite
            id_str = str(task_id)

            print(
                f"{id_str:<7} {data['name']:<30} {duration_str:<8} "
                f"{data['faz']:<6.1f} {data['fez']:<6.1f} {data['saz']:<6.1f} "
                f"{data['sez']:<6.1f} {puffer_str:<8} {critical_marker}"
            )
        print("=" * 70)


def main():
    """Hauptfunktion für CLI-Verwendung."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Berechnet den kritischen Pfad für Projektdateien"
    )
    parser.add_argument(
        'project_file',
        type=Path,
        help='Pfad zur Projekt-JSON-Datei'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Ausgabedatei für Ergebnisse (default: <projekt>_cpm.json)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Projektstartdatum (YYYY-MM-DD, default: heute)'
    )
    parser.add_argument(
        '--no-dates',
        action='store_true',
        help='Keine Kalenderdaten in Ausgabe einschließen'
    )

    args = parser.parse_args()

    # Lade Projektdatei
    calc = SimpleCPMCalculator.from_file(args.project_file)

    # Setze Startdatum
    if args.start_date:
        calc.start_date = datetime.strptime(args.start_date, '%Y-%m-%d')

    # Berechne CPM
    calc.calculate()

    # Ausgabe auf Konsole
    calc.print_summary()

    # Bestimme Ausgabedatei
    if args.output:
        output_file = args.output
    else:
        # Standard: results Ordner
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        output_file = results_dir / f"{args.project_file.stem}_cpm.json"

    # Exportiere zu JSON
    calc.export_to_json(output_file, include_dates=not args.no_dates)
    print(f"\nErgebnisse gespeichert in: {output_file}")


if __name__ == '__main__':
    main()
