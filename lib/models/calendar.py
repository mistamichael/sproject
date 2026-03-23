"""
Calendar and Resource-Aware Date Calculation
==============================================

Berechnet echte Datumsangaben unter Berücksichtigung von:
- Arbeitszeiten (working_days, hours_per_day)
- Urlauben und Abwesenheiten
- Pausen und Ruhezeiten pro Mitarbeiter
- Verfügbarkeit von Ressourcen
"""

from typing import Dict, List, Set
from dataclasses import dataclass, field

from .resources import RestInterval


@dataclass
class WorkingHours:
    """Arbeitszeiten für einen Tag"""
    start: str  # Format: "HH:MM"
    end: str    # Format: "HH:MM"

    def total_hours(self) -> float:
        """Berechnet Gesamtstunden des Tages"""
        start_h, start_m = map(int, self.start.split(':'))
        end_h, end_m = map(int, self.end.split(':'))

        start_mins = start_h * 60 + start_m
        end_mins = end_h * 60 + end_m

        return (end_mins - start_mins) / 60.0

    def __repr__(self) -> str:
        return f"{self.start}-{self.end}"
