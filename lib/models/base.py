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
    - dependencies: Liste von Task-IDs (EA - Ende-Anfang / Normalfolge, Standard)
    - dependencies_aa: Liste von Task-IDs (AA - Anfang-Anfang / Anfangsfolge)
    - dependencies_ee: Liste von Task-IDs (EE - Ende-Ende / Endfolge)
    - dependencies_ae: Liste von Task-IDs (AE - Anfang-Ende / Sprungfolge)
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
    dependencies: List[Union[int, str]] = Field(default_factory=list)  # EA (Standard)
    dependencies_aa: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Anfang-Anfang
    dependencies_ee: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Ende-Ende
    dependencies_ae: Optional[List[Union[int, str]]] = Field(default_factory=list)  # Anfang-Ende
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
