"""
Task models for different project types
========================================

Spezialisierte Task-Modelle für verschiedene Projekt-Typen:
- SimpleTask: Einfache Tasks (tankdesign, pizza)
- InstanceTask: Tasks mit Instanzen/Zyklen (pizzas)
- LoopTask: Loop-Tasks mit Subtasks (erdaushub)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from .base import TaskBase


class SimpleTask(TaskBase):
    """
    Einfache Tasks für tankdesign.json, pizza.json

    Zusätzliche Felder:
    - is_break:    Markiert diesen Task als Ruhepause (optional, default False)
    - is_blocker:  Markiert diesen Task als Kalender-Blocker (Wochenende/Feiertag),
                   GP=0, keine Ressourcen, keine Kosten (optional, default False)
    """
    is_break: bool = False
    is_blocker: bool = False


class ExpandableTask(TaskBase):
    """
    Basis-Klasse für Tasks die expandiert werden können (InstanceTask, LoopTask).

    Diese Klasse sammelt gemeinsame Felder für alle expandierbaren Task-Typen.

    Gemeinsame Felder:
    - cycle_prefix: Präfix für Zyklusnummern (z.B. "P" für "2-P1", "F" für "2-F1")
    """
    cycle_prefix: str = "C"  # Default "C" für Cycle


class InstanceTask(ExpandableTask):
    """
    Tasks mit Instanzen für pizzas.json

    Zusätzliche Felder:
    - instances: Anzahl der Instanzen (int) oder Referenz (str wie "order_volume")
    - cycle_prefix: Präfix für Zyklusnummern (Standard: "P" für "2-P1", "2-P2")
    """

    instances: Union[int, str]  # z.B. "order_volume" oder 12
    cycle_prefix: str = "P"  # Override default


class SubTask(BaseModel):
    """
    Subtask für Loop-Tasks (erdaushub.json)

    Felder:
    - name: Name des Subtasks
    - required_resources: Liste von Resource-IDs (optional)
    - duration: Feste Dauer oder Resource-Referenz (optional)
    - duration_formula: Formel zur Berechnung (optional)
    """

    name: str
    required_resources: Optional[List[str]] = None
    duration: Optional[str] = None
    duration_formula: Optional[str] = None

    model_config = {
        'extra': 'allow',
    }


class LoopTask(ExpandableTask):
    """
    Loop-Tasks für erdaushub.json

    Zusätzliche Felder:
    - is_loop: Muss True sein (Marker)
    - loop_until: Bedingung für Loop-Ende (z.B. "total_volume <= 0")
    - cycle_prefix: Präfix für Zyklusnummern (Standard: "F" für "2-F1", "2-F2")
    - subtasks: Liste von Subtasks
    - loop_count: Anzahl der Loop-Iterationen (optional, alternativ zu automatischer Berechnung)
    - volume_per_cycle: Volumen pro Zyklus (optional, für Berechnung von loop_count)
    """

    is_loop: Literal[True] = True
    loop_until: str
    cycle_prefix: str = "F"  # Override default
    subtasks: List[SubTask] = Field(default_factory=list)
    loop_count: Optional[int] = None  # Explizite Anzahl Iterationen
    volume_per_cycle: Optional[Union[int, float]] = None  # Volumen pro Zyklus


# Union-Type für alle Task-Varianten
Task = Union[LoopTask, InstanceTask, SimpleTask]
