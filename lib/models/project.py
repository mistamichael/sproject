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

# Import utils (relative import from parent package)
from ..utils import detect_time_unit

from .tasks import SimpleTask, InstanceTask, LoopTask
from .resources import Resource, Person


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


class PersonProject(ProjectBase):
    """
    Projekt mit Personen (software_simple.json)

    Zusätzliche Felder:
    - total_hours: Geschätzte Gesamtstunden (optional)
    - unit: Einheit (z.B. "hours")
    - persons: Liste von Personen mit Details
    - resources: Liste von Ressourcen (verweisen auf persons via person_id)
    - tasks: Liste von SimpleTask
    """

    total_hours: Optional[int] = None
    unit: str
    persons: List[Person]
    resources: List[Resource]
    tasks: List[SimpleTask]


# Union-Type für alle Projekt-Varianten
Project = Union[SimpleProject, CycleProject, LoopProject, PersonProject]
