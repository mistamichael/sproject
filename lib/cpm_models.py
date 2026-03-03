"""
cpm_models.py
=============
CPM (Critical Path Method) Berechnungen für Projekt-Tasks.

Enthält:
- CPMCalculationMixin: Mixin für CPM-Berechnungen
- SimpleTaskFile: Einfache Task-Datei für CPM-Berechnungen
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel


class CPMCalculationMixin:
    """
    Mixin-Klasse für CPM-Berechnungen (Critical Path Method).
    Kann für ProjectFile oder einfache Task-Daten verwendet werden.
    """

    def _parse_duration(self, duration_value) -> float:
        """
        Parst Duration-Wert zu Tagen (float).
        Unterstützt: Zahlen (10), Strings mit Einheit ("10d", "2w", "8h")
        """
        if isinstance(duration_value, (int, float)):
            return float(duration_value)

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
            else:
                try:
                    return float(duration_str)
                except ValueError:
                    return 0.0
        return 0.0

    def calculate_cpm(self, tasks_data: list[dict]) -> dict:
        """
        Führt CPM-Berechnung durch.

        Args:
            tasks_data: Liste von Task-Dictionaries mit 'id', 'duration', 'dependencies'

        Returns:
            Dictionary mit task_id als Key und CPM-Daten (faz, fez, saz, sez, puffer, etc.)
        """
        from datetime import datetime, timedelta

        cpm_data = {}

        # Initialisiere CPM-Daten
        for task in tasks_data:
            task_id = task['id']
            duration_raw = task.get('duration', 0)
            duration = self._parse_duration(duration_raw)

            cpm_data[task_id] = {
                'id': task_id,
                'name': task.get('name', f'Task {task_id}'),
                'duration': duration,
                'successors': task.get('dependencies', []),
                'predecessors': [],
                'faz': 0,  # Frühester Anfangszeitpunkt
                'fez': 0,  # Frühester Endzeitpunkt
                'saz': 0,  # Spätester Anfangszeitpunkt
                'sez': 0,  # Spätester Endzeitpunkt
                'puffer': 0,  # Gesamtpuffer
                'free_puffer': 0,  # Freier Puffer
                'is_critical': False,
            }

        # Berechne Vorgänger aus Nachfolgern
        for task_id, data in cpm_data.items():
            for successor_id in data['successors']:
                if successor_id in cpm_data:
                    cpm_data[successor_id]['predecessors'].append(task_id)

        # Vorwärtsrechnung
        self._cpm_forward_pass(cpm_data)

        # Rückwärtsrechnung
        self._cpm_backward_pass(cpm_data)

        # Pufferzeiten berechnen
        self._cpm_calculate_slack(cpm_data)

        return cpm_data

    def _cpm_forward_pass(self, cpm_data: dict) -> None:
        """Vorwärtsrechnung: Berechnet FAZ und FEZ."""
        sorted_ids = self._cpm_topological_sort(cpm_data)

        for task_id in sorted_ids:
            data = cpm_data[task_id]
            predecessors = data['predecessors']

            if not predecessors:
                data['faz'] = 0
            else:
                max_fez = 0
                for pred_id in predecessors:
                    if pred_id in cpm_data:
                        max_fez = max(max_fez, cpm_data[pred_id]['fez'])
                data['faz'] = max_fez

            data['fez'] = data['faz'] + data['duration']

    def _cpm_backward_pass(self, cpm_data: dict) -> None:
        """Rückwärtsrechnung: Berechnet SAZ und SEZ."""
        end_nodes = [tid for tid, data in cpm_data.items() if not data['successors']]
        project_end = max(data['fez'] for data in cpm_data.values())

        for task_id in end_nodes:
            cpm_data[task_id]['sez'] = cpm_data[task_id]['fez']

        reverse_sorted = list(reversed(self._cpm_topological_sort(cpm_data)))

        for task_id in reverse_sorted:
            data = cpm_data[task_id]
            successors = data['successors']

            if not successors:
                if data['sez'] == 0:
                    data['sez'] = data['fez']
            else:
                min_saz = float('inf')
                for succ_id in successors:
                    if succ_id in cpm_data:
                        min_saz = min(min_saz, cpm_data[succ_id]['saz'])
                data['sez'] = min_saz

            data['saz'] = data['sez'] - data['duration']

    def _cpm_calculate_slack(self, cpm_data: dict) -> None:
        """Berechnet Pufferzeiten und markiert kritische Tasks."""
        for task_id, data in cpm_data.items():
            # Gesamtpuffer
            data['puffer'] = data['saz'] - data['faz']

            # Freier Puffer
            if data['successors']:
                min_successor_faz = float('inf')
                for succ_id in data['successors']:
                    if succ_id in cpm_data:
                        min_successor_faz = min(min_successor_faz, cpm_data[succ_id]['faz'])
                data['free_puffer'] = min_successor_faz - data['fez']
            else:
                data['free_puffer'] = data['puffer']

            # Kritisch wenn Puffer ≈ 0
            data['is_critical'] = abs(data['puffer']) < 0.001

    def _cpm_topological_sort(self, cpm_data: dict) -> list:
        """Topologische Sortierung der Tasks."""
        visited = set()
        result = []

        def visit(task_id):
            if task_id in visited or task_id not in cpm_data:
                return
            visited.add(task_id)

            for pred_id in cpm_data[task_id]['predecessors']:
                visit(pred_id)

            result.append(task_id)

        for task_id in cpm_data.keys():
            visit(task_id)

        return result

    def get_critical_path(self, cpm_data: dict) -> list:
        """Ermittelt den kritischen Pfad."""
        critical_tasks = [
            task_id for task_id, data in cpm_data.items()
            if data['is_critical']
        ]
        critical_tasks.sort(key=lambda tid: cpm_data[tid]['faz'])
        return critical_tasks


class SimpleTaskFile(BaseModel, CPMCalculationMixin):
    """
    Einfache Task-Datei ohne vollständige ProjectFile-Struktur.
    Wird für reine CPM-Berechnungen verwendet (z.B. tankdesign.json).
    """
    model_config = {"extra": "ignore"}

    project: Optional[str] = None
    tasks: list[dict] = []

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'SimpleTaskFile':
        """Lädt eine einfache Task-Datei."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def calculate_cpm_for_tasks(self) -> dict:
        """
        Führt CPM-Berechnung für die Tasks durch.

        Returns:
            Dictionary mit CPM-Daten für jeden Task
        """
        return self.calculate_cpm(self.tasks)
