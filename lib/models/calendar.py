"""
Calendar and Resource-Aware Date Calculation
==============================================

Berechnet echte Datumsangaben unter Berücksichtigung von:
- Arbeitszeiten (working_days, hours_per_day)
- Urlauben und Abwesenheiten
- Pausen und Ruhezeiten pro Mitarbeiter
- Verfügbarkeit von Ressourcen
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

from .resources import Person, RestInterval
from .cpm import CPMResult


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


@dataclass
class PersonCalendar:
    """Kalender für eine Person mit Urlaub, Pausen und Arbeitszeiten"""
    person_id: str
    person_name: str
    working_days: Set[str] = field(default_factory=lambda: {'mon', 'tue', 'wed', 'thu', 'fri'})
    working_hours: Dict[str, List[WorkingHours]] = field(default_factory=dict)  # {weekday: [hours]}
    vacation_dates: Set[str] = field(default_factory=set)  # {YYYY-MM-DD}
    rest_intervals: List[RestInterval] = field(default_factory=list)

    def is_working_day(self, date: datetime) -> bool:
        """Prüft ob ein Datum ein Arbeitstag ist"""
        weekday_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        weekday = weekday_names[date.weekday()]

        return weekday in self.working_days and date.strftime('%Y-%m-%d') not in self.vacation_dates



class CalendarCalculator:
    """
    Berechnet echte Datumsangaben basierend auf CPM-Ergebnissen
    und Ressourcen/Kalender-Constraints.
    """

    def __init__(
        self,
        cpm_result: CPMResult,
        persons: Optional[Dict[str, Person]] = None,
        working_days: Optional[Set[str]] = None,
        hours_per_day: float = 8.0,
        project_start: Optional[datetime] = None
    ):
        """
        Args:
            cpm_result: CPM-Berechnungsergebnis
            persons: Dictionary von Personen {person_id: Person}
            working_days: Arbeitstage (default: mon-fri)
            hours_per_day: Standard-Arbeitsstunden pro Tag
            project_start: Projektstartdatum (default: aus cpm_result)
        """
        self.cpm_result = cpm_result
        self.persons = persons or {}
        self.working_days = working_days or {'mon', 'tue', 'wed', 'thu', 'fri'}
        self.hours_per_day = hours_per_day
        self.project_start = project_start or cpm_result.project_start or datetime.now()

        # Erstelle PersonCalendars
        self.person_calendars: Dict[str, PersonCalendar] = {}
        self._initialize_calendars()

        # Ergebnisse: Task-ID -> (start_date, end_date)
        self.task_dates: Dict[Union[int, str], Tuple[datetime, datetime]] = {}

    def _initialize_calendars(self) -> None:
        """Initialisiert PersonCalendars aus Personen-Daten"""
        for person_id, person in self.persons.items():
            # Erstelle Kalender
            cal = PersonCalendar(
                person_id=person_id,
                person_name=person.name,
                working_days=self.working_days.copy()
            )

            # Setze Working Hours
            if person.workinghours_override:
                # Spezielle Arbeitszeiten für diese Person
                for day in person.workinghours_override.days:
                    cal.working_hours[day] = [
                        WorkingHours(h.from_, h.to)
                        for h in person.workinghours_override.hours
                    ]
            else:
                # Standard Working Hours für alle Arbeitstage
                default_hours = [WorkingHours("09:00", "17:00")]  # 8 Stunden
                for day in self.working_days:
                    cal.working_hours[day] = default_hours

            # Setze Urlaub
            if person.vacation:
                for entry in person.vacation:
                    if entry.date:
                        # Einzelner Tag
                        cal.vacation_dates.add(entry.date)
                    elif entry.from_ and entry.to:
                        # Zeitraum
                        start = datetime.strptime(entry.from_, '%Y-%m-%d')
                        end = datetime.strptime(entry.to, '%Y-%m-%d')
                        current = start
                        while current <= end:
                            cal.vacation_dates.add(current.strftime('%Y-%m-%d'))
                            current += timedelta(days=1)

            # Setze Rest Intervals
            if person.rest_intervals:
                if isinstance(person.rest_intervals, list):
                    cal.rest_intervals = person.rest_intervals

            self.person_calendars[person_id] = cal

