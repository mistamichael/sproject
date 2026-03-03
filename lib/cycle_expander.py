#!/usr/bin/env python3
"""
cycle_expander.py
==================
Erweitert Tasks mit Zyklen/Instanzen und Loop-Tasks in separate Aufgaben.
Unterstützt:
- Tasks mit "instances": "order_volume" (Pizzas)
- Tasks mit "is_loop": true (Erdaushub)

DEPRECATED: Diese Klasse wird in Zukunft durch Project.expand_cycles() / expand_loops() ersetzt.
Verwenden Sie stattdessen:
    from models import load_project
    project = load_project("file.json")
    if hasattr(project, 'expand_cycles'):
        expanded = project.expand_cycles()
    elif hasattr(project, 'expand_loops'):
        expanded = project.expand_loops()
"""

import json
import warnings
from pathlib import Path
from typing import Any, Optional, Union
import math


class CycleExpander:
    """
    Expandiert Tasks mit mehreren Instanzen oder Loops in separate Task-Einträge.

    DEPRECATED: Verwenden Sie stattdessen CycleProject.expand_cycles() oder
    LoopProject.expand_loops() aus dem models Package.
    Diese Klasse wird für Rückwärtskompatibilität beibehalten, delegiert aber
    an die neue Pydantic-basierte Implementierung.
    """

    def __init__(self, project_data: Union[dict, 'ProjectBase']):
        """
        Initialisiert den Expander mit Projektdaten.

        Args:
            project_data: Dictionary mit Projektdaten ODER ProjectBase-Instanz
        """
        # Konvertiere dict zu Project falls nötig
        if isinstance(project_data, dict):
            try:
                from models import load_project_from_dict
            except ImportError:
                from .models import load_project_from_dict
            self.project = load_project_from_dict(project_data)
            self._is_legacy = True
            # Behalte original data für Rückwärtskompatibilität
            self.project_data = project_data.copy()
        else:
            # Bereits ein Pydantic-Project
            self.project = project_data
            self._is_legacy = False
            # Erstelle dict-Repräsentation
            self.project_data = self.project.model_dump(by_alias=True, exclude_none=True)

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

        # Hole Ressourcen falls verfügbar
        if hasattr(self.project, 'resources'):
            self.resources = [r.model_dump(by_alias=True) for r in self.project.resources]
        else:
            self.resources = []

        # Hole globale Parameter
        self.order_volume = getattr(self.project, 'order_volume', 1)
        self.total_volume = getattr(self.project, 'total_volume', 0)

        self.expanded_tasks = []
        self._expanded_project = None

    @classmethod
    def from_file(cls, file_path: Path) -> 'CycleExpander':
        """Lädt Projektdaten aus JSON-Datei."""
        try:
            from models import load_project
        except ImportError:
            from .models import load_project
        project = load_project(file_path)
        return cls(project)

    def expand(self) -> dict:
        """
        Führt die Zyklus-Erweiterung durch.

        Returns:
            Dictionary mit erweiterten Tasks
        """
        # Delegiere an neue Implementation
        try:
            from models.project import CycleProject, LoopProject
        except ImportError:
            from .models.project import CycleProject, LoopProject

        if isinstance(self.project, CycleProject):
            self._expanded_project = self.project.expand_cycles()
        elif isinstance(self.project, LoopProject):
            self._expanded_project = self.project.expand_loops()
        else:
            # Kein expandierbares Projekt - gebe Original zurück
            self._expanded_project = self.project

        # Konvertiere zu dict für Rückwärtskompatibilität
        result = self._expanded_project.model_dump(by_alias=True, exclude_none=True)

        # Update expanded_tasks für Legacy-Code
        self.expanded_tasks = [
            {
                'id': task.id,
                'name': task.name,
                'duration': task.duration,
                'dependencies': task.dependencies or []
            }
            for task in self._expanded_project.tasks
        ]

        return result

    def _expand_instances(self, task: dict, num_instances: int, prefix: str) -> None:
        """
        Expandiert einen Task mit mehreren Instanzen.

        Args:
            task: Original-Task
            num_instances: Anzahl der Instanzen
            prefix: Präfix für Zyklusnummer (z.B. 'P' für Pizza)
        """
        task_id = task['id']
        dependencies = task.get('dependencies', [])

        for cycle in range(1, num_instances + 1):
            expanded_task = task.copy()

            # Neue ID: z.B. "2-P1", "2-P2", etc.
            expanded_task['id'] = f"{task_id}-{prefix}{cycle}"

            # Original-ID als Referenz speichern
            expanded_task['original_id'] = task_id
            expanded_task['cycle_number'] = cycle
            expanded_task['cycle_prefix'] = prefix

            # Entferne "instances" aus expandiertem Task
            if 'instances' in expanded_task:
                del expanded_task['instances']

            # Aktualisiere Dependencies
            # - Wenn Abhängigkeit zu einem Task besteht, der auch expandiert wird,
            #   muss die Dependency auf den entsprechenden Zyklus zeigen
            new_dependencies = []
            for dep_id in dependencies:
                # Suche ob dep_id auch ein instances-Task ist
                dep_task = self._find_task_by_id(dep_id)
                if dep_task and 'instances' in dep_task:
                    # Verknüpfe mit dem gleichen Zyklus des Vorgängers
                    dep_prefix = dep_task.get('cycle_prefix', 'P')
                    new_dependencies.append(f"{dep_id}-{dep_prefix}{cycle}")
                else:
                    # Normale Abhängigkeit bleibt
                    new_dependencies.append(dep_id)

            expanded_task['dependencies'] = new_dependencies

            # Verkette Zyklen: Jeder Zyklus hängt vom vorherigen ab (außer der erste)
            if cycle > 1:
                # Hänge vom gleichen Task des vorherigen Zyklus ab
                prev_cycle_id = f"{task_id}-{prefix}{cycle-1}"
                if prev_cycle_id not in expanded_task['dependencies']:
                    expanded_task['dependencies'].append(prev_cycle_id)

            self.expanded_tasks.append(expanded_task)

    def _expand_loop(self, task: dict, num_loops: int, prefix: str) -> None:
        """
        Expandiert einen Loop-Task in mehrere Iterationen.

        Args:
            task: Original-Task mit "is_loop": true
            num_loops: Anzahl der Loop-Iterationen
            prefix: Präfix für Zyklusnummer (z.B. 'F' für Fahrt)
        """
        task_id = task['id']
        dependencies = task.get('dependencies', [])

        # Berechne Dauer pro Loop basierend auf Subtasks
        loop_duration = self._calculate_loop_duration(task)

        for cycle in range(1, num_loops + 1):
            expanded_task = {
                'id': f"{task_id}-{prefix}{cycle}",
                'name': f"{task.get('name', 'Loop')} #{cycle}",
                'duration': loop_duration,
                'original_id': task_id,
                'cycle_number': cycle,
                'cycle_prefix': prefix,
                'dependencies': dependencies.copy() if cycle == 1 else [f"{task_id}-{prefix}{cycle-1}"]
            }

            # Übernehme weitere Felder falls vorhanden
            for key in ['resources', 'description']:
                if key in task:
                    expanded_task[key] = task[key]

            self.expanded_tasks.append(expanded_task)

    def _calculate_loop_count(self, task: dict) -> int:
        """
        Berechnet die Anzahl der Loop-Iterationen basierend auf loop_until Bedingung.

        Args:
            task: Task mit "is_loop": true

        Returns:
            Anzahl der Iterationen
        """
        loop_until = task.get('loop_until', '')

        # Parse "total_volume <= 0" Bedingung
        if 'total_volume' in loop_until:
            # Berechne wie viele Zyklen nötig sind um total_volume auf 0 zu bringen
            # Hole LKW-Ressourcen
            trucks = [r for r in self.resources if r.get('type') == 'truck']

            if not trucks:
                return 1  # Fallback

            # Nimm capacity des ersten LKWs (oder Durchschnitt)
            truck_capacity = trucks[0].get('capacity', 15)

            # Anzahl Zyklen = total_volume / truck_capacity (aufgerundet)
            num_cycles = math.ceil(self.total_volume / truck_capacity)

            return max(1, num_cycles)

        # Fallback: Default-Wert
        return task.get('loop_count', 10)

    def _calculate_loop_duration(self, task: dict) -> str:
        """
        Berechnet die Dauer eines Loop-Zyklus basierend auf Subtasks.

        Args:
            task: Task mit Subtasks

        Returns:
            Dauer als String (z.B. "50m")
        """
        subtasks = task.get('subtasks', [])

        if not subtasks:
            return task.get('duration', '0m')

        # Summiere Subtask-Dauern oder verwende Formeln
        total_minutes = 0.0

        for subtask in subtasks:
            # Prüfe auf duration_formula
            if 'duration_formula' in subtask:
                # Versuche Formel auszuwerten (vereinfacht)
                # z.B. "resource.truck.capacity / resource.B1.loading_speed_per_min"
                duration = self._evaluate_duration_formula(subtask['duration_formula'])
                total_minutes += duration
            elif 'duration' in subtask:
                # Parse feste Dauer
                duration_str = subtask['duration']
                # Falls es auf resource verweist
                if isinstance(duration_str, str) and 'resource.' in duration_str:
                    duration = self._evaluate_duration_formula(duration_str)
                else:
                    duration = self._parse_duration_to_minutes(duration_str)
                total_minutes += duration

        return f"{total_minutes:.1f}m"

    def _evaluate_duration_formula(self, formula: str) -> float:
        """
        Wertet eine Dauer-Formel oder resource-Referenz aus (vereinfacht).

        Args:
            formula: String wie "resource.truck.capacity / resource.B1.loading_speed_per_min"
                     oder "resource.truck.transport_cycle_fixed"

        Returns:
            Dauer in Minuten
        """
        # Falls es eine einfache resource.XXX.YYY Referenz ist (ohne Operatoren)
        import re

        # Prüfe auf einfache Referenz ohne Operatoren
        simple_pattern = r'^resource\.(\w+)\.(\w+)$'
        simple_match = re.match(simple_pattern, formula.strip())

        if simple_match:
            resource_id, attr = simple_match.groups()
            # Hole Ressource
            if resource_id in ['truck', 'current_truck', 'any_truck']:
                trucks = [r for r in self.resources if r.get('type') == 'truck']
                if trucks:
                    value = trucks[0].get(attr, 0)
                    # Falls Wert ein String ist (z.B. "40m"), parse ihn
                    return self._parse_duration_to_minutes(value)
            else:
                resource = self._find_resource_by_id(resource_id)
                if resource:
                    value = resource.get(attr, 0)
                    return self._parse_duration_to_minutes(value)
            return 0.0

        # Extrahiere Werte aus resources für komplexe Formeln
        # z.B. "resource.truck.capacity / resource.B1.loading_speed_per_min"
        pattern = r'resource\.(\w+)\.(\w+)'
        matches = re.findall(pattern, formula)

        # Ersetze durch tatsächliche Werte
        formula_eval = formula
        for resource_id, attr in matches:
            # Suche Ressource
            if resource_id in ['truck', 'current_truck', 'any_truck']:
                # Hole ersten LKW
                trucks = [r for r in self.resources if r.get('type') == 'truck']
                if trucks:
                    value = trucks[0].get(attr, 0)
                    formula_eval = formula_eval.replace(f'resource.{resource_id}.{attr}', str(value))
            else:
                # Suche nach ID
                resource = self._find_resource_by_id(resource_id)
                if resource:
                    value = resource.get(attr, 0)
                    formula_eval = formula_eval.replace(f'resource.{resource_id}.{attr}', str(value))

        # Evaluiere Formel
        try:
            result = eval(formula_eval)
            return float(result)
        except:
            return 0.0

    def _parse_duration_to_minutes(self, duration_str: str) -> float:
        """
        Parst Dauer-String zu Minuten.

        Args:
            duration_str: String wie "40m", "1h", "2d"

        Returns:
            Dauer in Minuten
        """
        if isinstance(duration_str, (int, float)):
            return float(duration_str)

        duration_str = str(duration_str).strip()

        if duration_str.endswith('m'):
            return float(duration_str[:-1])
        elif duration_str.endswith('h'):
            return float(duration_str[:-1]) * 60
        elif duration_str.endswith('d'):
            return float(duration_str[:-1]) * 8 * 60  # 8h Arbeitstag
        else:
            try:
                return float(duration_str)
            except:
                return 0.0

    def _find_task_by_id(self, task_id: int) -> Optional[dict]:
        """Findet einen Task anhand seiner ID."""
        for task in self.tasks:
            if task.get('id') == task_id:
                return task
        return None

    def _find_resource_by_id(self, resource_id: str) -> Optional[dict]:
        """Findet eine Ressource anhand ihrer ID."""
        for resource in self.resources:
            if resource.get('id') == resource_id:
                return resource
        return None

    def export_to_json(self, output_path: Path) -> None:
        """
        Exportiert das erweiterte Projekt in eine JSON-Datei.

        Args:
            output_path: Ausgabepfad
        """
        # Verwende neue Implementation falls verfügbar
        if self._expanded_project is None:
            # Expandiere erst falls noch nicht geschehen
            self.expand()

        try:
            from models import save_project
        except ImportError:
            from .models import save_project

        # Nutze save_project für konsistente Ausgabe
        save_project(self._expanded_project, output_path, indent=2)


def main():
    """Hauptfunktion für CLI-Verwendung."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Expandiert Tasks mit Zyklen/Instanzen"
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Pfad zur Projekt-JSON-Datei'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Ausgabedatei für expandiertes Projekt (default: <projekt>_expanded.json)'
    )

    args = parser.parse_args()

    # Lade und expandiere Projektdatei
    expander = CycleExpander.from_file(args.input_file)

    # Bestimme Ausgabedatei
    if args.output:
        output_file = args.output
    else:
        output_file = args.input_file.parent / f"{args.input_file.stem}_expanded.json"

    # Exportiere expandiertes Projekt
    expander.export_to_json(output_file)
    print(f"Expandiertes Projekt gespeichert in: {output_file}")


if __name__ == '__main__':
    main()
