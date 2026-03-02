#!/usr/bin/env python3
"""
cpm_calculator.py
=================
Berechnet den kritischen Pfad (Critical Path Method) für einfache Projektdateien.
Unterstützt JSON-Dateien mit vereinfachter Struktur (wie tankdesign.json).
"""

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta

try:
    from config_loader import get_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class SimpleCPMCalculator:
    """
    Berechnet CPM für einfache Projektdateien ohne vollständige TJP-Struktur.
    """

    def __init__(self, project_data: dict):
        """
        Initialisiert den Calculator mit Projektdaten.

        Args:
            project_data: Dictionary mit 'project' und 'tasks' Keys
        """
        self.project_name = project_data.get('project', 'Unbekanntes Projekt')
        self.tasks = project_data.get('tasks', [])

        # Lade Defaults aus Config
        if HAS_CONFIG:
            config = get_config()
            self.start_date = config.get_project_start_date()
            self.config = config
        else:
            self.start_date = datetime.now()
            self.config = None

        self.cpm_data = {}

    @classmethod
    def from_file(cls, file_path: Path) -> 'SimpleCPMCalculator':
        """Lädt Projektdaten aus JSON-Datei."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def calculate(self) -> dict[int, dict[str, Any]]:
        """
        Führt die vollständige CPM-Berechnung durch.

        Returns:
            Dictionary mit task_id als Key und CPM-Daten
        """
        # Initialisiere CPM-Daten
        self._initialize_cpm_data()

        # Vorwärtsrechnung
        self._forward_pass()

        # Rückwärtsrechnung
        self._backward_pass()

        # Pufferzeiten berechnen
        self._calculate_slack()

        return self.cpm_data

    def _initialize_cpm_data(self) -> None:
        """Initialisiert die CPM-Datenstruktur für alle Tasks."""
        # Erstmal alle Tasks erfassen
        for task in self.tasks:
            task_id = task['id']
            duration = task.get('duration', 0)

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

    def _topological_sort(self) -> list[int]:
        """
        Führt topologische Sortierung durch.

        Returns:
            Liste der Task-IDs in topologischer Reihenfolge
        """
        visited = set()
        result = []

        def visit(task_id: int):
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

    def get_critical_path(self) -> list[int]:
        """
        Gibt die Task-IDs auf dem kritischen Pfad zurück.

        Returns:
            Liste der Task-IDs (sortiert nach FAZ)
        """
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
        # Original-Projektdaten laden
        original_tasks = []
        for task in self.tasks:
            task_copy = task.copy()
            task_id = task_copy['id']

            if task_id in self.cpm_data:
                cpm = self.cpm_data[task_id]

                # Füge CPM-Daten hinzu mit deutschen Begriffen
                task_copy['cpm'] = {
                    'D': cpm['duration'],                  # Dauer
                    'FB': cpm['faz'],                      # Frühester Beginn
                    'FE': cpm['fez'],                      # Frühestes Ende
                    'SB': cpm['saz'],                      # Spätester Beginn
                    'SE': cpm['sez'],                      # Spätestes Ende
                    'GP': round(cpm['puffer'], 2),         # Gesamtpuffer
                    'FP': round(cpm['free_puffer'], 2),    # Freier Puffer
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

        # Erstelle Ausgabe-JSON
        output_data = {
            'project': self.project_name,
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_start': self.start_date.strftime('%Y-%m-%d'),
            'critical_path': self.get_critical_path(),
            'project_duration': max(
                data['fez'] for data in self.cpm_data.values()
            ),
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
        critical_path = self.get_critical_path()
        project_duration = max(data['fez'] for data in self.cpm_data.values())

        print("=" * 70)
        print(f"Projekt: {self.project_name}")
        print(f"Projektdauer: {project_duration} Tage")
        print(f"Startdatum: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"Enddatum (geschätzt): {self._add_workdays(self.start_date, project_duration).strftime('%Y-%m-%d')}")
        print("=" * 70)
        print()
        print("Kritischer Pfad:")
        for task_id in critical_path:
            data = self.cpm_data[task_id]
            print(f"  [{task_id}] {data['name']:<30} (Dauer: {data['duration']} Tage)")
        print()
        print("=" * 70)
        print("Alle Tasks:")
        print(f"{'ID':<4} {'Name':<30} {'Dauer':<6} {'FAZ':<6} {'FEZ':<6} {'SAZ':<6} {'SEZ':<6} {'Puffer':<6} {'Krit.'}")
        print("-" * 70)

        for task_id in self._topological_sort():
            data = self.cpm_data[task_id]
            critical_marker = "JA" if data['is_critical'] else ""
            print(
                f"{task_id:<4} {data['name']:<30} {data['duration']:<6} "
                f"{data['faz']:<6.1f} {data['fez']:<6.1f} {data['saz']:<6.1f} "
                f"{data['sez']:<6.1f} {data['puffer']:<6.1f} {critical_marker}"
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
