"""
Resource and Person models
===========================

Modelle für Ressourcen (Maschinen, Personen, LKWs) und Personen-Details.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union


class ResourceBase(BaseModel):
    """
    Basis-Klasse für alle Ressourcen.

    Felder:
    - id: Resource-ID
    - name: Name der Ressource
    - type: Typ (person, machine, truck, etc.) - optional für Legacy-Dateien
    - color: Hex-Farbcode für Visualisierung (optional, z.B. "4472C4")
    """

    id: str
    name: str
    type: Optional[str] = None  # Optional für Legacy-JSON ohne type
    color: Optional[str] = None  # Optional: Hex-Farbcode ohne #

    model_config = {
        'extra': 'allow',
    }


class MachineResource(ResourceBase):
    """
    Maschinen-Ressource (z.B. Bagger, Ofen)

    Zusätzliche Felder:
    - capacity: Kapazität (optional)
    - loading_speed_per_min: Ladegeschwindigkeit (optional)
    - count: Anzahl (optional)
    - unit: Einheit (optional)
    """

    type: Literal["machine"]
    capacity: Optional[Union[int, float]] = None
    count: Optional[int] = None
    unit: Optional[str] = None


class TruckResource(ResourceBase):
    """
    LKW-Ressource für erdaushub.json

    Zusätzliche Felder:
    - capacity: Ladekapazität
    - transport_cycle_fixed: Feste Transportzeit
    """

    type: Literal["truck"]
    capacity: Union[int, float]


class OvenResource(ResourceBase):
    """
    Ofen-Ressource für pizzas.json

    Zusätzliche Felder:
    - capacity: Ladekapazität
    """

    type: Literal["oven"]
    capacity: Union[int, float]

class PersonResource(ResourceBase):
    """
    Personen-Ressource

    Zusätzliche Felder:
    - person_id: Verweis auf Person in persons-Sektion (optional)
    - role: Rolle (optional, wenn kein person_id)
    - count: Anzahl (optional)
    - name: Optional (wird aus Person abgeleitet wenn person_id vorhanden)
    - type: Optional (default "person")
    """

    name: Optional[str] = None  # type: ignore[assignment]
    type: Literal["person"] = "person"  # type: ignore[assignment]
    person_id: Optional[str] = None
    role: Optional[str] = None
    count: Optional[int] = None


class TimeRange(BaseModel):
    """Zeitbereich für Arbeitszeiten"""

    from_: str = Field(alias="from")
    to: str

    model_config = {
        'populate_by_name': True,  # Erlaubt from_ und from
    }


class WorkHoursOverride(BaseModel):
    """
    Spezielle Arbeitszeiten für eine Person (z.B. Teilzeit)

    Felder:
    - description: Beschreibung
    - days: Arbeitstage
    - hours: Arbeitszeiten
    """

    description: str
    days: List[str]
    hours: List[TimeRange]


class VacationEntry(BaseModel):
    """
    Urlaubs-/Abwesenheitseintrag

    Felder:
    - from_: Startdatum (optional, für Zeiträume)
    - to: Enddatum (optional, für Zeiträume)
    - date: Einzeldatum (optional, für einzelne Tage)
    - description: Beschreibung
    """

    from_: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    date: Optional[str] = None
    description: str

    model_config = {
        'populate_by_name': True,
    }


class RestInterval(BaseModel):
    """
    Ruhepausen-Regel

    Felder:
    - after_hours: Nach wie vielen Stunden Arbeit eine Pause erforderlich ist
    - duration: Dauer der Pause (z.B. "45m", "30m")
    - note: Beschreibung/Begründung (optional)
    """

    after_hours: float
    duration: str
    note: Optional[str] = None


class Person(BaseModel):
    """
    Person mit Arbeitszeiten und Urlaub (software_simple.json, erdaushub.json)

    Felder:
    - id: Personen-ID
    - name: Name
    - email: E-Mail
    - role: Rolle
    - hourly_rate: Stundensatz
    - workinghours_override: Spezielle Arbeitszeiten (optional)
    - vacation: Urlaubseinträge (optional)
    - rest_intervals: Verweis auf Ruhepausen-Regeln oder direkte Angabe (optional)
    """

    id: str
    name: str
    email: Optional[str] = None
    role: str
    hourly_rate: float
    workinghours_override: Optional[WorkHoursOverride] = None
    vacation: Optional[List[VacationEntry]] = None
    rest_intervals: Optional[Union[str, List[RestInterval]]] = None  # Kann Verweis ("resting_times") oder direkte Liste sein


# Union-Type für alle Resource-Varianten
# Union-Type für alle Resource-Varianten
# WICHTIG: PersonResource zuerst, da es die flexibelsten Regeln hat (name optional)
Resource = Union[PersonResource, TruckResource, OvenResource, MachineResource, ResourceBase]
