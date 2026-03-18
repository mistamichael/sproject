"""
Project model (unified)
========================

Einheitliches Projekt-Modell für alle JSON-Strukturen.
Ein einzelnes `Project`-Modell ersetzt SimpleProject, CycleProject,
LoopProject und PersonProject.  Backward-Compat-Aliase bleiben erhalten.
"""

from pydantic import BaseModel
from typing import Optional, List, Union

# Import utils - try relative import first, then absolute
try:
    from ..utils import detect_time_unit
except (ImportError, ValueError):
    from utils import detect_time_unit

from .tasks import SimpleTask, InstanceTask, LoopTask
from .resources import Resource, Person, RestInterval


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

    def calculate_cpm(self, start_date: Optional[str] = None, cfg_dir: Optional['Path'] = None) -> 'CPMResult':
        """
        Berechnet Critical Path Method für dieses Projekt.

        Args:
            start_date: Projektstartdatum (optional, überschreibt project_start)
            cfg_dir: Verzeichnis mit Konfigurationsdateien (optional, für Feiertage)

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

        calculator = CPMCalculator(self, start_dt, cfg_dir=cfg_dir)
        return calculator.calculate()

    model_config = {
        'extra': 'allow',
    }


class Project(ProjectBase):
    """
    Einheitliches Projekt-Modell (ersetzt SimpleProject, CycleProject,
    LoopProject und PersonProject).

    Alle Felder sind optional — vorhandene Felder bestimmen das Verhalten:
    - order_volume + InstanceTask → expand_cycles() anwenden
    - total_volume + LoopTask    → expand_loops() anwenden
    - persons                    → Ressourcen/Personenauswertung aktiv
    """

    # Felder für Zyklus-Projekte (ehemals CycleProject)
    order_volume: Optional[int] = None

    # Felder für Loop- und Personen-Projekte (ehemals LoopProject / PersonProject)
    total_volume: Optional[Union[int, float]] = None
    total_hours: Optional[int] = None
    unit: Optional[str] = None

    # Ressourcen und Personen (ehemals PersonProject / CycleProject / LoopProject)
    resources: Optional[List[Resource]] = None
    persons: Optional[List[Person]] = None
    resting_times: Optional[List['RestInterval']] = None

    # Alle Task-Typen in einem Union (spezifischere zuerst)
    tasks: List[Union[LoopTask, InstanceTask, SimpleTask]] = []

    # ------------------------------------------------------------------
    # Expansion
    # ------------------------------------------------------------------

    def expand_cycles(self) -> 'Project':
        """
        Expandiert InstanceTasks in einzelne Zyklen.

        Gibt `self` unverändert zurück, wenn keine InstanceTasks vorhanden sind.

        Returns:
            Neues Project mit expandierten Tasks
        """
        from .expander import expand_instance_task

        if not any(isinstance(t, InstanceTask) for t in self.tasks):
            return self  # Keine InstanceTasks → nichts zu tun

        if self.order_volume is None:
            raise ValueError("order_volume muss für Cycle-Expansion gesetzt sein")

        expanded_tasks = []
        instance_task_mapping: dict = {}

        for task in self.tasks:
            if isinstance(task, InstanceTask):
                expanded = expand_instance_task(task, self.order_volume, self.tasks)
                expanded_tasks.extend(expanded)
                instance_task_mapping[task.id] = [t.id for t in expanded]
            else:
                expanded_tasks.append(task)

        for task in expanded_tasks:
            if task.dependencies:
                updated_deps = []
                for dep_id in task.dependencies:
                    if dep_id in instance_task_mapping:
                        updated_deps.append(instance_task_mapping[dep_id][-1])
                    else:
                        updated_deps.append(dep_id)
                task.dependencies = updated_deps

        return Project(
            project=self.project,
            project_start=self.project_start,
            tasks=expanded_tasks,
        )

    def expand_loops(self) -> 'Project':
        """
        Expandiert LoopTasks basierend auf loop_until-Bedingung.

        Gibt `self` unverändert zurück, wenn keine LoopTasks vorhanden sind.
        Personen, Ressourcen und Ruhepausen-Regeln werden im Ergebnis beibehalten.

        Returns:
            Neues Project mit expandierten Tasks
        """
        from .expander import expand_loop_task

        if not any(isinstance(t, LoopTask) for t in self.tasks):
            return self  # Keine LoopTasks → nichts zu tun

        if self.total_volume is None:
            raise ValueError("total_volume muss für Loop-Expansion gesetzt sein")

        expanded_tasks = []
        loop_task_mapping: dict = {}

        for task in self.tasks:
            if isinstance(task, LoopTask):
                expanded = expand_loop_task(task, self.total_volume, self.resources or [])
                expanded_tasks.extend(expanded)
                loop_task_mapping[task.id] = [t.id for t in expanded]
            else:
                expanded_tasks.append(task)

        for task in expanded_tasks:
            if task.dependencies:
                updated_deps = []
                for dep_id in task.dependencies:
                    if dep_id in loop_task_mapping:
                        updated_deps.append(loop_task_mapping[dep_id][0])
                    else:
                        updated_deps.append(dep_id)
                task.dependencies = updated_deps

        if self.persons and self.resting_times:
            expanded_tasks = self._insert_rest_breaks(expanded_tasks)

        return Project(
            project=self.project,
            project_start=self.project_start,
            total_hours=self.total_hours,
            total_volume=self.total_volume,
            unit=self.unit,
            persons=self.persons,
            resources=self.resources,
            tasks=expanded_tasks,
            resting_times=self.resting_times,
        )

    def _insert_rest_breaks(self, tasks: List[SimpleTask]) -> List[SimpleTask]:
        """
        Fügt Ruhepausen-Tasks basierend auf Arbeitszeit-Regeln ein.
        """
        try:
            from .rest_breaks import resolve_rest_intervals, PersonWorkTracker
        except ImportError:
            from rest_breaks import resolve_rest_intervals, PersonWorkTracker

        try:
            from ..utils import parse_duration_to_minutes
        except (ImportError, ValueError):
            from utils import parse_duration_to_minutes

        trackers = {}
        for person in self.persons:
            intervals = resolve_rest_intervals(person, self.resting_times)
            if intervals:
                trackers[person.id] = PersonWorkTracker(person.id, intervals)

        if not trackers:
            return tasks

        res_to_person = {}
        for res in (self.resources or []):
            if hasattr(res, 'person_id') and res.person_id:
                res_to_person[res.id] = res.person_id

        tasks_with_breaks = []
        break_counter = 1

        for task in tasks:
            if task.resources and not task.is_break:
                task_minutes = parse_duration_to_minutes(task.duration)
                task_hours = task_minutes / 60.0

                working_persons = set()
                for res_id in task.resources:
                    person_id = res_to_person.get(res_id)
                    if person_id and person_id in trackers:
                        working_persons.add(person_id)

                required_breaks = {}
                for person_id in working_persons:
                    tracker = trackers[person_id]
                    required_break = tracker.add_work_time(task_hours)
                    if required_break:
                        required_breaks[person_id] = required_break

                tasks_with_breaks.append(task)

                for person_id, rest_interval in required_breaks.items():
                    person = next((p for p in self.persons if p.id == person_id), None)

                    if person:
                        person_id_short = person_id.replace('PERS', 'P')
                        break_id = f"{task.id}-BRK-{person_id_short}"

                        break_task = SimpleTask(
                            id=break_id,
                            name=f"Pause: {person.name} ({rest_interval.note or rest_interval.duration})",
                            duration=rest_interval.duration,
                            resources=None,
                            cost=0.0,
                            dependencies=[],
                            is_break=True
                        )

                        task.dependencies.append(break_id)
                        tasks_with_breaks.append(break_task)
                        trackers[person_id].take_break(rest_interval)
                        break_counter += 1
            else:
                tasks_with_breaks.append(task)

        return tasks_with_breaks


# ---------------------------------------------------------------------------
# Backward-Compat-Aliase
# Alle vier ehemaligen Klassen zeigen auf Project.
# isinstance(project, PersonProject) etc. funktionieren weiterhin, weil
# alle Projects Instanzen von Project sind.
# ---------------------------------------------------------------------------
SimpleProject = Project
CycleProject = Project
LoopProject = Project
PersonProject = Project
