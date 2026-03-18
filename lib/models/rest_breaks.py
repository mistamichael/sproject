"""
Rest Break Management for Person Resources
===========================================

Verwaltet Ruhepausen für Personen basierend auf Arbeitszeit-Regeln.
"""

from typing import List, Optional
from .resources import Person, RestInterval


def resolve_rest_intervals(person: Person, project_resting_times: Optional[List[RestInterval]] = None) -> List[RestInterval]:
    """
    Löst rest_intervals Verweise auf und gibt die tatsächlichen RestInterval-Objekte zurück.

    Args:
        person: Person mit rest_intervals (kann Verweis oder direkte Liste sein)
        project_resting_times: Globale resting_times aus dem Projekt

    Returns:
        Liste von RestInterval-Objekten
    """
    if not person.rest_intervals:
        return []

    # Fall 1: Direkter Verweis auf project resting_times
    if isinstance(person.rest_intervals, str):
        if person.rest_intervals == "resting_times" and project_resting_times:
            return project_resting_times
        # Unbekannter Verweis
        return []

    # Fall 2: Direkte Liste von RestInterval
    return person.rest_intervals



class PersonWorkTracker:
    """
    Verfolgt Arbeitszeiten und Pausen für eine Person.
    """

    def __init__(self, person_id: str, rest_intervals: List[RestInterval]):
        self.person_id = person_id
        self.rest_intervals = sorted(rest_intervals, key=lambda x: x.after_hours)
        self.worked_hours = 0.0
        self.taken_breaks: List[float] = []  # Schwellenwerte der genommenen Pausen
        self.last_break_at = 0.0  # Arbeitszeit bei letzter Pause

    def add_work_time(self, hours: float) -> Optional[RestInterval]:
        """
        Fügt Arbeitszeit hinzu und prüft ob eine Pause erforderlich ist.

        Args:
            hours: Hinzuzufügende Arbeitsstunden

        Returns:
            RestInterval falls Pause erforderlich, sonst None
        """
        self.worked_hours += hours

        # Prüfe alle Pausenregeln
        for interval in self.rest_intervals:
            threshold = interval.after_hours
            if threshold in self.taken_breaks:
                continue  # Diese Pause wurde bereits genommen

            if self.worked_hours >= threshold:
                # Pause ist erforderlich
                return interval

        return None

    def take_break(self, interval: RestInterval):
        """
        Markiert eine Pause als genommen.

        Args:
            interval: Die genommene Pause
        """
        if interval.after_hours not in self.taken_breaks:
            self.taken_breaks.append(interval.after_hours)
            self.last_break_at = self.worked_hours

