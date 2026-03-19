"""
Base models for sproject
=========================

Contains base classes and shared types for all project models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List

# Import utils - try relative import first, then absolute
try:
    from ..utils import parse_duration_to_days, validate_duration_string
except (ImportError, ValueError):
    from utils import parse_duration_to_days, validate_duration_string


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

    id: Union[int, str]
    name: str
    duration: Optional[str] = None
    successors: List[Union[int, str]] = Field(default_factory=list)  # EA (Standard)
    successors_aa: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Anfang-Anfang
    successors_ee: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Ende-Ende
    successors_ae: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Anfang-Ende
    resources: Optional[List[str]] = None
    description: Optional[str] = None
    cost: Optional[float] = None  # Explizite Kosten (0.0 = kostenlos, None = normal berechnen)

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: Optional[str]) -> Optional[str]:  # noqa
        """Validiert Dauer-Strings wie '10d', '5h', '30m', '2w'"""
        if v is None:
            return v

        v = v.strip()
        if not v or v == "0":
            return "0d"

        # Nutze utils-Funktion
        if validate_duration_string(v):
            return v

        # Fallback: interpretiere als Tage
        try:
            float(v)
            return f"{v}d"
        except ValueError:
            raise ValueError(f"Invalid duration format: {v}")

    def to_days(self) -> float:
        """
        Konvertiert die Dauer dieses Tasks zu Tagen.

        Returns:
            Dauer in Tagen

        Examples:
            >>> task = TaskBase(id=1, name="Test", duration="10d")
            >>> task.to_days()
            10.0
        """
        if self.duration is None:
            return 0.0
        return parse_duration_to_days(self.duration)

    model_config = {
        'extra': 'allow',  # Erlaube zusätzliche Felder (für Zukunft/Erweiterungen)
    }
