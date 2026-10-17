"""
Base models for sproject
=========================

Contains base classes and shared types for all project models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Iterable, List, Optional

from ..durations import parse_duration_to_days, validate_duration_string
from .dependencies import DepType, Dependency, SUCCESSOR_FIELDS, TaskId


class TaskBase(BaseModel):
    """
    Basis-Klasse für alle Task-Typen.

    Gemeinsame Felder:
    - id: Task-ID (int oder string für Zyklen wie "2-P1")
    - name: Task-Name
    - duration: Dauer als String (z.B. "10d", "5h", "30m")
    - successors: Liste von Nachfolger-Task-IDs (EA - Ende-Anfang / Normalfolge, Standard)
    - successors_aa: Liste von Nachfolger-Task-IDs (AA - Anfang-Anfang / Anfangsfolge)
    - successors_ee: Liste von Nachfolger-Task-IDs (EE - Ende-Ende / Endfolge)
    - successors_ae: Liste von Nachfolger-Task-IDs (AE - Anfang-Ende / Sprungfolge)
    - resources: Liste von Resource-IDs (optional)
    - description: Beschreibung (optional)

    Abhängigkeitstypen:
    - EA (Ende-Anfang): Nachfolger beginnt, wenn Vorgänger endet (Standard)
    - AA (Anfang-Anfang): Nachfolger beginnt, wenn Vorgänger beginnt
    - EE (Ende-Ende): Nachfolger endet, wenn Vorgänger endet
    - AE (Anfang-Ende): Nachfolger endet, wenn Vorgänger beginnt
    """

    id: TaskId
    name: str
    duration: Optional[str] = None
    successors: List[TaskId] = Field(default_factory=list)      # EA (Standard)
    successors_aa: List[TaskId] = Field(default_factory=list)   # Anfang-Anfang
    successors_ee: List[TaskId] = Field(default_factory=list)   # Ende-Ende
    successors_ae: List[TaskId] = Field(default_factory=list)   # Anfang-Ende
    resources: Optional[List[str]] = None
    description: Optional[str] = None
    cost: Optional[float] = None  # Explizite Kosten (0.0 = kostenlos, None = normal berechnen)
    not_before: Optional[str] = None  # Frühester Start, "YYYY-MM-DD[ HH:MM]" (z. B. Materiallieferung)
    deadline: Optional[str] = None    # Spätestes Ende, "YYYY-MM-DD[ HH:MM]" (Datum ohne Uhrzeit = Tagesende)

    @field_validator('not_before', 'deadline')
    @classmethod
    def _validate_date(cls, v: Optional[str]) -> Optional[str]:  # noqa
        if v is not None:
            from .project import parse_start_date
            parse_start_date(v)   # wirft ValueError bei ungültigem Format
        return v

    @field_validator('successors', 'successors_aa', 'successors_ee', 'successors_ae', mode='before')
    @classmethod
    def _none_to_list(cls, v):  # noqa
        return [] if v is None else v

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: Optional[str]) -> Optional[str]:  # noqa
        """Validiert Dauer-Strings wie '10d', '5h', '30m', '2w'; reine Zahlen gelten als Tage."""
        if v is None:
            return v
        v = v.strip()
        if not v or v == "0":
            return "0d"
        if not validate_duration_string(v):
            raise ValueError(f"Invalid duration format: {v}")
        return v if v[-1].isalpha() else f"{v}d"

    @property
    def dependencies(self) -> List[Dependency]:
        """Alle Nachfolger-Beziehungen (EA, AA, EE, AE) als eine Liste."""
        return [
            Dependency(target, dep_type)
            for dep_type, field in SUCCESSOR_FIELDS.items()
            for target in getattr(self, field)
        ]

    def set_dependencies(self, deps: Iterable[Dependency]) -> None:
        """Schreibt Dependencies zurück in die vier JSON-Felder."""
        by_type: Dict[DepType, List[TaskId]] = {dep_type: [] for dep_type in DepType}
        for dep in deps:
            by_type[dep.type].append(dep.target)
        for dep_type, field in SUCCESSOR_FIELDS.items():
            if getattr(self, field) != by_type[dep_type]:   # unveränderte Felder nicht als "gesetzt" markieren
                setattr(self, field, by_type[dep_type])

    def to_days(self) -> float:
        """
        Konvertiert die Dauer dieses Tasks zu Arbeitstagen.

        Examples:
            >>> TaskBase(id=1, name="Test", duration="10d").to_days()
            10.0
        """
        return parse_duration_to_days(self.duration) if self.duration else 0.0

    model_config = {
        'extra': 'allow',  # Erlaube zusätzliche Felder (für Zukunft/Erweiterungen)
    }
