"""
Tracking models (Plan gegen Ist)
================================

- Actual:   Ist-Stand eines Tasks (begonnen, erledigt, Fortschritt)
- Baseline: eingefrorener Plan (Kalenderdaten je Task), gegen den die
            aktuelle Prognose verglichen wird

Beide stehen im Projekt nach Task-ID (als String) – so gelten sie auch für
expandierte Zyklen wie "2-F1.1".
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


def _check_date(v: Optional[str]) -> Optional[str]:
    if v is not None:
        from .project import parse_start_date
        parse_start_date(v)
    return v


class Actual(BaseModel):
    """
    Ist-Stand eines Tasks.

    - start + finish:     erledigt
    - start (ohne finish): läuft; Restarbeit = remaining oder duration × (1 − progress)
    """
    start: Optional[str] = None
    finish: Optional[str] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)   # 0.6 = 60 % erledigt
    remaining: Optional[str] = None                                    # Restarbeit, z. B. "2d"
    note: Optional[str] = None

    _dates = field_validator('start', 'finish')(classmethod(lambda cls, v: _check_date(v)))

    @property
    def is_done(self) -> bool:
        return self.finish is not None

    @property
    def is_started(self) -> bool:
        return self.start is not None or self.finish is not None


class BaselineTask(BaseModel):
    start: str     # "YYYY-MM-DD HH:MM"
    finish: str


class Baseline(BaseModel):
    """Eingefrorener Plan zum Zeitpunkt created."""
    created: str
    project_end: Optional[str] = None
    tasks: Dict[str, BaselineTask] = Field(default_factory=dict)
