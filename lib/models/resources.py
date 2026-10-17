"""
Resource and Person models
===========================

Modelle für Ressourcen (Maschinen, Personen, LKWs) und Personen-Details.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union, get_args


ResourceType = Literal["person", "machine", "truck", "oven", "material"]
RESOURCE_TYPES: List[str] = list(get_args(ResourceType))

# Typen, bei denen capacity die Zahl gleichzeitiger Aufträge ist (siehe Resource.slots)
_PARALLEL_CAPACITY_TYPES = {"machine", "oven"}


class Resource(BaseModel):
    """
    Ressource (Person, Maschine, LKW, Ofen, Material).

    Felder:
    - id, name, type, color (Hex ohne #)
    - capacity:           Kapazität; bei machine/truck/oven aktiviert sie Resource-Leveling
    - count, unit:        Anzahl / Einheit (optional)
    - person_id:          Verweis auf Person (nur type == "person"; Name/Stundensatz kommen von dort)
    - role:               Rolle, wenn keine Person verknüpft ist
    - hourly_rate:        Stundensatz für Nicht-Personen-Ressourcen
    - provisioning_costs: einmalige Bereitstellungskosten

    Weitere Felder (z. B. loading_speed_per_min) sind erlaubt und in
    duration_formula über resource.<id>.<feld> nutzbar.
    """

    id: str
    name: Optional[str] = None
    type: ResourceType = "person"
    color: Optional[str] = None
    capacity: Optional[Union[int, float]] = None
    count: Optional[int] = None
    unit: Optional[str] = None
    person_id: Optional[str] = None
    role: Optional[str] = None
    hourly_rate: Optional[float] = None
    provisioning_costs: Optional[float] = None
    unavailable: Optional[List["VacationEntry"]] = None   # Ausfallzeiten (Wartung, Defekt)

    model_config = {
        'extra': 'allow',
    }

    @property
    def slots(self) -> Optional[int]:
        """
        Wie viele Tasks die Ressource gleichzeitig bearbeiten kann (None = unbegrenzt).

        count, wenn gesetzt; sonst capacity bei Maschinen/Öfen (z. B. Ofen mit 4 Plätzen);
        Material ist unbegrenzt; alles andere (Personen, LKW, Bagger) kann eine Aufgabe zugleich.
        Bei LKW ist capacity die Ladekapazität, nicht die Zahl paralleler Fahrten.
        """
        if self.count:
            return int(self.count)
        if self.type in _PARALLEL_CAPACITY_TYPES and self.capacity:
            return max(int(self.capacity), 1)
        if self.type == "material":
            return None
        return 1


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


Resource.model_rebuild()
