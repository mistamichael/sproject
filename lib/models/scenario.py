"""
Scenario models
===============

Ein Szenario ist eine benannte Liste von Änderungen am Basisplan.
Angewendet wird es von lib/scenarios.py.
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from .resources import VacationEntry

TaskRef = Union[int, str]


class ScenarioChange(BaseModel):
    """
    Eine Änderung – genau eines von task, resource oder person:

    - task:     Task-ID oder Muster ("2-F*.2"). duration_factor multipliziert die Dauer,
                alle weiteren Felder (duration, delay, resources, deadline …) werden gesetzt.
    - resource: unavailable = zusätzliche Ausfallzeiten
    - person:   vacation = zusätzliche Abwesenheiten
    """
    task: Optional[TaskRef] = None
    resource: Optional[str] = None
    person: Optional[str] = None
    duration_factor: Optional[float] = Field(default=None, gt=0)
    unavailable: Optional[List[VacationEntry]] = None
    vacation: Optional[List[VacationEntry]] = None

    model_config = {'extra': 'allow'}

    @model_validator(mode='after')
    def _one_target(self) -> 'ScenarioChange':
        targets = [x for x in (self.task, self.resource, self.person) if x is not None]
        if len(targets) != 1:
            raise ValueError("Eine Szenario-Änderung braucht genau eines von 'task', 'resource', 'person'")
        return self

    @property
    def task_fields(self) -> dict:
        """Task-Felder, die direkt gesetzt werden (alles außer den Steuerfeldern)."""
        return dict(self.model_extra or {})


class Scenario(BaseModel):
    name: str
    description: Optional[str] = None
    changes: List[ScenarioChange] = Field(default_factory=list)
