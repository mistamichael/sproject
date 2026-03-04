"""
Project models for different types
===================================

Projekt-Modelle für verschiedene JSON-Strukturen:
- SimpleProject: Einfache Projekte (tankdesign, pizza)
- CycleProject: Projekte mit Instanzen (pizzas)
- LoopProject: Projekte mit Loops (erdaushub)
- PersonProject: Projekte mit Personen (software_simple)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Union

# Import utils - try relative import first, then absolute
try:
    from ..utils import detect_time_unit
except (ImportError, ValueError):
    from utils import detect_time_unit

from .tasks import SimpleTask, InstanceTask, LoopTask
from .resources import Resource, Person
from .reports import Report


class ProjectBase(BaseModel):
    """
    Basis-Klasse für alle Projekt-Typen.

    Gemeinsame Felder:
    - project: Projektname
    - project_start: Projektstartdatum (optional)
    - tasks: Liste von Tasks
    """

    project: str
    project_start: Optional[str] = None

    def get_time_unit(self) -> str:
        """
        Erkennt die dominante Zeiteinheit in den Projekt-Tasks.

        Returns:
            'minutes', 'hours' oder 'days'

        Examples:
            >>> project = load_project("examples/pizzas.json")
            >>> project.get_time_unit()
            'minutes'
        """
        durations = [task.duration for task in self.tasks if task.duration]
        if not durations:
            return 'days'
        return detect_time_unit(durations)

    def get_all_task_ids(self) -> List[Union[int, str]]:
        """
        Gibt alle Task-IDs im Projekt zurück.

        Returns:
            Liste von Task-IDs
        """
        return [task.id for task in self.tasks]

    def calculate_cpm(self, start_date: Optional[str] = None) -> 'CPMResult':
        """
        Berechnet Critical Path Method für dieses Projekt.

        Args:
            start_date: Projektstartdatum (optional, überschreibt project_start)

        Returns:
            CPMResult mit berechneten Werten

        Examples:
            >>> from models import load_project
            >>> project = load_project("examples/tankdesign.json")
            >>> result = project.calculate_cpm()
            >>> result.project_duration
            '50.0d'
            >>> result.critical_path
            [1, 3, 7, 8]
        """
        from .cpm import CPMCalculator
        from datetime import datetime

        # Verwende übergebenes Startdatum oder project_start
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        elif self.project_start:
            try:
                start_dt = datetime.strptime(self.project_start, '%Y-%m-%d')
            except ValueError:
                start_dt = datetime.strptime(self.project_start, '%Y-%m-%d %H:%M:%S')
        else:
            start_dt = None

        calculator = CPMCalculator(self, start_dt)
        return calculator.calculate()

    model_config = {
        'extra': 'allow',
    }


class SimpleProject(ProjectBase):
    """
    Einfaches Projekt (tankdesign.json, pizza.json)

    Nur Basis-Felder, keine speziellen Ressourcen oder Personen.
    """

    tasks: List[SimpleTask]


class CycleProject(ProjectBase):
    """
    Projekt mit Zyklen/Instanzen (pizzas.json)

    Zusätzliche Felder:
    - order_volume: Anzahl der zu produzierenden Einheiten
    - unit: Einheit (z.B. "Pizzen")
    - resources: Liste von Ressourcen
    - tasks: Kann SimpleTask oder InstanceTask enthalten
    """

    order_volume: int
    unit: str
    resources: List[Resource]
    tasks: List[Union[SimpleTask, InstanceTask]]

    def expand_cycles(self) -> 'SimpleProject':
        """
        Expandiert InstanceTasks in einzelne Zyklen.

        Returns:
            Neues SimpleProject mit expandierten Tasks

        Examples:
            >>> project = load_project("examples/pizzas.json")
            >>> expanded = project.expand_cycles()
            >>> len(expanded.tasks)  # 1 + (3 * 12) = 37 tasks
            37
        """
        from .expander import expand_instance_task

        expanded_tasks = []
        instance_task_mapping = {}  # Mapping: original_id -> [expanded_task_ids]

        for task in self.tasks:
            if isinstance(task, InstanceTask):
                # Expandiere InstanceTask
                expanded = expand_instance_task(task, self.order_volume, self.tasks)
                expanded_tasks.extend(expanded)
                # Speichere Mapping
                instance_task_mapping[task.id] = [t.id for t in expanded]
            else:
                # SimpleTask bleibt unverändert
                expanded_tasks.append(task)

        # Aktualisiere Dependencies: Ersetze Referenzen auf expandierte Tasks
        for task in expanded_tasks:
            if task.dependencies:
                updated_deps = []
                for dep_id in task.dependencies:
                    if dep_id in instance_task_mapping:
                        # Referenziert einen expandierten InstanceTask
                        # Verweise auf den LETZTEN expandierten Task (letzte Instanz)
                        updated_deps.append(instance_task_mapping[dep_id][-1])
                    else:
                        # Normale Dependency
                        updated_deps.append(dep_id)
                # Aktualisiere dependencies
                task.dependencies = updated_deps

        # Erstelle neues SimpleProject
        return SimpleProject(
            project=self.project,
            project_start=self.project_start,
            tasks=expanded_tasks
        )


class LoopProject(ProjectBase):
    """
    Projekt mit Loops (erdaushub.json)

    Zusätzliche Felder:
    - total_volume: Gesamtvolumen
    - unit: Einheit (z.B. "m3")
    - resources: Liste von Ressourcen (Maschinen, LKWs)
    - tasks: Kann SimpleTask oder LoopTask enthalten
    """

    total_volume: Union[int, float]
    unit: str
    resources: List[Resource]
    tasks: List[Union[SimpleTask, LoopTask]]

    def expand_loops(self) -> 'SimpleProject':
        """
        Expandiert LoopTasks basierend auf loop_until Bedingung.

        Returns:
            Neues SimpleProject mit expandierten Tasks

        Examples:
            >>> project = load_project("examples/erdaushub.json")
            >>> expanded = project.expand_loops()
            >>> # Tasks werden basierend auf total_volume expandiert
        """
        from .expander import expand_loop_task

        expanded_tasks = []
        loop_task_mapping = {}  # Mapping: original_id -> [expanded_task_ids]

        for task in self.tasks:
            if isinstance(task, LoopTask):
                # Expandiere LoopTask
                expanded = expand_loop_task(task, self.total_volume, self.resources)
                expanded_tasks.extend(expanded)
                # Speichere Mapping
                loop_task_mapping[task.id] = [t.id for t in expanded]
            else:
                # SimpleTask bleibt unverändert
                expanded_tasks.append(task)

        # Aktualisiere Dependencies: Ersetze Referenzen auf expandierte Tasks
        for task in expanded_tasks:
            if task.dependencies:
                updated_deps = []
                for dep_id in task.dependencies:
                    if dep_id in loop_task_mapping:
                        # Referenziert einen expandierten LoopTask
                        # Verweise auf den LETZTEN expandierten Task (letzte Iteration)
                        updated_deps.append(loop_task_mapping[dep_id][-1])
                    else:
                        # Normale Dependency
                        updated_deps.append(dep_id)
                # Aktualisiere dependencies
                task.dependencies = updated_deps

        # Erstelle neues SimpleProject
        return SimpleProject(
            project=self.project,
            project_start=self.project_start,
            tasks=expanded_tasks
        )


class PersonProject(ProjectBase):
    """
    Projekt mit Personen (software_simple.json, erdaushub.json mit Personen)

    Zusätzliche Felder:
    - total_hours: Geschätzte Gesamtstunden (optional)
    - total_volume: Gesamtvolumen für Loop-Tasks (optional)
    - unit: Einheit (z.B. "hours", "m3")
    - persons: Liste von Personen mit Details
    - resources: Liste von Ressourcen (verweisen auf persons via person_id)
    - tasks: Liste von SimpleTask oder LoopTask
    - reports: Liste von Reports (Gantt Chart, Resource List, etc.)
    """

    total_hours: Optional[int] = None
    total_volume: Optional[Union[int, float]] = None
    unit: str
    persons: List[Person]
    resources: List[Resource]
    tasks: List[Union[SimpleTask, LoopTask]]
    reports: Optional[List[Report]] = None

    def expand_loops(self) -> 'PersonProject':
        """
        Expandiert LoopTasks basierend auf loop_until Bedingung.

        Returns:
            Neues PersonProject mit expandierten Tasks

        Examples:
            >>> project = load_project("examples/erdaushub.json")
            >>> expanded = project.expand_loops()
            >>> # Tasks werden basierend auf total_volume expandiert
        """
        from .expander import expand_loop_task

        expanded_tasks = []
        loop_task_mapping = {}  # Mapping: original_id -> [expanded_task_ids]

        for task in self.tasks:
            if isinstance(task, LoopTask):
                # Expandiere LoopTask
                if self.total_volume is None:
                    raise ValueError(f"total_volume muss für Loop-Task '{task.name}' gesetzt sein")
                expanded = expand_loop_task(task, self.total_volume, self.resources)
                expanded_tasks.extend(expanded)
                # Speichere Mapping
                loop_task_mapping[task.id] = [t.id for t in expanded]
            else:
                # SimpleTask bleibt unverändert
                expanded_tasks.append(task)

        # Aktualisiere Dependencies: Ersetze Referenzen auf expandierte Tasks
        for task in expanded_tasks:
            if task.dependencies:
                updated_deps = []
                for dep_id in task.dependencies:
                    if dep_id in loop_task_mapping:
                        # Referenziert einen expandierten LoopTask
                        # Verweise auf den LETZTEN expandierten Task (letzte Iteration)
                        updated_deps.append(loop_task_mapping[dep_id][-1])
                    else:
                        # Normale Dependency
                        updated_deps.append(dep_id)
                # Aktualisiere dependencies
                task.dependencies = updated_deps

        # Erstelle neues PersonProject mit expandierten Tasks
        return PersonProject(
            project=self.project,
            project_start=self.project_start,
            total_hours=self.total_hours,
            total_volume=self.total_volume,
            unit=self.unit,
            persons=self.persons,
            resources=self.resources,
            tasks=expanded_tasks,
            reports=self.reports
        )


# Union-Type für alle Projekt-Varianten
Project = Union[SimpleProject, CycleProject, LoopProject, PersonProject]
