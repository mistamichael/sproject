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
import math

from .resources import Person, VacationEntry, RestInterval
from .cpm import CPMResult, CPMTaskResult


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

    def get_hours_for_date(self, date: datetime) -> float:
        """Gibt Arbeitsstunden für einen Datum zurück"""
        if not self.is_working_day(date):
            return 0.0

        weekday_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        weekday = weekday_names[date.weekday()]

        if weekday not in self.working_hours:
            return 0.0  # Kein Working Hours definiert für diesen Tag

        hours_list = self.working_hours[weekday]
        return sum(h.total_hours() for h in hours_list)


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

    def calculate_task_dates(
        self,
        task_id: Union[int, str],
        resource_ids: Optional[List[str]] = None,
        earliest_start: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """
        Berechnet Start- und Enddatum für einen Task basierend auf:
        - CPM FAZ/FEZ (in Arbeitstagen)
        - Verfügbarkeit der Ressourcen (Urlaub, Arbeitszeiten)

        Args:
            task_id: Task-ID
            resource_ids: IDs der zugeordneten Ressourcen
            earliest_start: Frühestmöglicher Startdatum (optional)

        Returns:
            (start_date, end_date) als datetime
        """
        cpm_task = self.cpm_result.tasks.get(task_id)
        if not cpm_task:
            raise ValueError(f"Task {task_id} nicht in CPM-Ergebnis gefunden")

        # FAZ in Tage seit Projektstart
        faz_days = cpm_task.faz

        # Berechne Startdatum unter Berücksichtigung von Ressourcen-Verfügbarkeit
        start_date = self._calculate_start_date(
            faz_days,
            resource_ids or [],
            earliest_start
        )

        # Berechne Enddatum basierend auf Dauer und Ressourcen-Verfügbarkeit
        end_date = self._calculate_end_date(
            start_date,
            cpm_task.duration,
            resource_ids or []
        )

        self.task_dates[task_id] = (start_date, end_date)
        return start_date, end_date

    def _calculate_start_date(
        self,
        faz_days: float,
        resource_ids: List[str],
        earliest_start: Optional[datetime] = None
    ) -> datetime:
        """
        Berechnet Startdatum basierend auf FAZ und Ressourcen-Verfügbarkeit
        """
        # Basis-Startdatum von FAZ
        base_start = self.project_start + timedelta(days=faz_days)

        # Wenn keine Ressourcen oder earliest_start definiert, nutze base_start
        if not resource_ids and not earliest_start:
            return base_start

        # Verschiebe zu nächstem Arbeitstag für alle Ressourcen
        current = max(base_start, earliest_start) if earliest_start else base_start

        while True:
            # Prüfe ob alle Ressourcen verfügbar sind
            all_available = True
            for resource_id in resource_ids:
                person_cal = self._get_person_calendar(resource_id)
                if person_cal and not person_cal.is_working_day(current):
                    all_available = False
                    break

            if all_available:
                return current

            current += timedelta(days=1)

            # Sicherheit: Max 365 Tage nach base_start
            if (current - base_start).days > 365:
                return base_start

    def _calculate_end_date(
        self,
        start_date: datetime,
        duration_days: float,
        resource_ids: List[str]
    ) -> datetime:
        """
        Berechnet Enddatum basierend auf Dauer und Ressourcen-Verfügbarkeit.
        Zählt nur Arbeitstage für die verfügbaren Ressourcen.
        """
        current = start_date
        remaining_days = duration_days

        while remaining_days > 0:
            # Prüfe ob alle Ressourcen heute verfügbar sind
            all_available = True
            for resource_id in resource_ids:
                person_cal = self._get_person_calendar(resource_id)
                if person_cal and not person_cal.is_working_day(current):
                    all_available = False
                    break

            if all_available:
                remaining_days -= 1.0

            if remaining_days > 0:
                current += timedelta(days=1)

        return current

    def _get_person_calendar(self, resource_id: str) -> Optional[PersonCalendar]:
        """Gibt PersonCalendar für eine Ressourcen-ID zurück"""
        # Suche in person_calendars
        if resource_id in self.person_calendars:
            return self.person_calendars[resource_id]

        # Suche in Person-IDs
        for person_id, cal in self.person_calendars.items():
            if person_id == resource_id:
                return cal

        return None

    def get_all_task_dates(self) -> Dict[Union[int, str], Tuple[datetime, datetime]]:
        """Berechnet alle Task-Datumsangaben"""
        for task_id in self.cpm_result.tasks.keys():
            if task_id not in self.task_dates:
                # TODO: Hole resource_ids aus original project
                self.calculate_task_dates(task_id)

        return self.task_dates
