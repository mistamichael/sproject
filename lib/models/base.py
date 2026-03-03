"""
Base models for sproject
=========================

Contains base classes and shared types for all project models.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List
from datetime import datetime

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
    - dependencies: Liste von Task-IDs, von denen dieser Task abhängt
    - resources: Liste von Resource-IDs (optional)
    - description: Beschreibung (optional)
    """

    id: Union[int, str]
    name: str
    duration: Optional[str] = None
    dependencies: List[Union[int, str]] = Field(default_factory=list)
    resources: Optional[List[str]] = None
    description: Optional[str] = None

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: Optional[str]) -> Optional[str]:
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
