"""
Gantt Schedule Calculation with calendar-aware dates and interruptions
========================================================================

Phase 2: Konvertiert reine CPM-Zeiten (in Arbeitstagen) zu Kalender-Daten mit Unterbrechungen.

Diese Komponente berücksichtigt:
- Wochenenden (Samstag/Sonntag)
- Feiertage
- Ferien/Pausen
- Arbeitszeiten pro Person/Ressource
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from ..durations import TimeUnit, format_time_value
from ..work_calendar import WorkCalendar
from .cpm import CPMResult, CPMTaskResult


class GanttTaskResult(BaseModel):
    """
    Gantt-Ergebnis für einen einzelnen Task mit Kalender-Daten.

    Attributes:
        id: Task-ID
        name: Task-Name
        network_duration_days: Reine Arbeits-Dauer in Tagen (aus CPM Phase 1)
        calendar_start_date: Kalender-Startdatum (mit Unterbrechungen berücksichtigt)
        calendar_end_date: Kalender-Enddatum (mit Unterbrechungen berücksichtigt)
        working_days: Anzahl echter Arbeitstage (ohne Wochenenden/Feiertage)
        calendar_days: Anzahl Kalendertage (inclusive Wochenenden/Feiertage)
        interruptions: Liste von Unterbrechungen (Wochenenden, Feiertage, Ferien)
        is_critical: Ob Task kritisch ist
        puffer_days: Gesamtpuffer in Tagen
    """
    id: Union[int, str]
    name: str
    network_duration_days: float  # Aus CPM Phase 1
    calendar_start_date: Optional[datetime] = None
    calendar_end_date: Optional[datetime] = None
    working_days: float = 0.0  # Echte Arbeitstage
    calendar_days: int = 0  # Kalendertage
    interruptions: List[Dict[str, Any]] = []  # Liste von Unterbrechungen
    is_critical: bool = False
    puffer_days: float = 0.0



class GanttResult(BaseModel):
    """
    Gesamtergebnis der Gantt-Berechnung (Phase 2).

    Attributes:
        project_name: Name des Projekts
        project_start_date: Projektstartdatum
        project_end_date: Projektendatum (mit Kalender-Unterbrechungen)
        project_duration_calendar_days: Projektdauer in Kalendertagen
        project_duration_working_days: Projektdauer in Arbeitstagen (keine Wochenenden/Feiertage)
        tasks: Dictionary mit Gantt-Ergebnissen pro Task
        time_unit: Verwendete Zeiteinheit ('minutes', 'hours', 'days')
        critical_path: Liste der Task-IDs auf dem kritischen Pfad
        holidays: Set von Feiertagsdaten im Format 'YYYY-MM-DD' (optional)
        skip_weekends: Ob Wochenenden übersprungen werden
        skip_holidays: Ob Feiertage übersprungen werden
        calculation_date: Zeitpunkt der Berechnung
    """
    project_name: str
    project_start_date: Optional[datetime] = None
    project_end_date: Optional[datetime] = None
    project_duration_calendar_days: Optional[str] = None  # Formatiert mit Einheit
    project_duration_working_days: Optional[str] = None  # Formatiert mit Einheit
    tasks: Dict[Union[int, str], GanttTaskResult] = {}
    time_unit: str = 'days'  # 'minutes', 'hours', 'days'
    critical_path: List[Union[int, str]] = []
    holidays: Optional[Dict[str, str]] = None
    skip_weekends: bool = True
    skip_holidays: bool = False
    calculation_date: Optional[datetime] = None

    def export_to_dict(self) -> dict:
        """Gantt-Schedule als Dictionary (für den JSON-Export)."""
        return {
            'project_name': self.project_name,
            'project_start_date': self.project_start_date.isoformat() if self.project_start_date else None,
            'time_unit': self.time_unit,
            'skip_weekends': self.skip_weekends,
            'skip_holidays': self.skip_holidays,
            'tasks': {
                str(task_id): {
                    'id': str(task_id),
                    'name': task.name,
                    'network_duration_days': round(task.network_duration_days, 3),
                    'calendar_start_date': task.calendar_start_date.isoformat() if task.calendar_start_date else None,
                    'calendar_end_date': task.calendar_end_date.isoformat() if task.calendar_end_date else None,
                    'working_days': round(task.working_days, 2),
                    'calendar_days': task.calendar_days,
                    'is_critical': task.is_critical,
                    'puffer_days': round(task.puffer_days, 3),
                }
                for task_id, task in self.tasks.items()
            },
        }


class GanttCalculator:
    """
    Rechnet CPM-Ergebnisse (Phase 1, Arbeitstage) in Kalenderdaten um (Phase 2).

    Wochenenden und Feiertage kommen aus dem Kalender des CPM-Ergebnisses.
    """

    def __init__(self, cpm_result: CPMResult, calendar: Optional[WorkCalendar] = None):
        self.cpm_result = cpm_result
        self.calendar = calendar or cpm_result.calendar
        self.start_date = cpm_result.project_start or datetime.now()
        self.time_unit: TimeUnit = cpm_result.time_unit

    def calculate(self) -> GanttResult:
        """Kalenderdaten für alle Tasks und das Projekt."""
        tasks = {tid: self._convert_task(tid, t) for tid, t in self.cpm_result.tasks.items()}

        end_dates = [t.calendar_end_date for t in tasks.values() if t.calendar_end_date]
        project_end_date = max(end_dates) if end_dates else self.start_date
        total_working_days = max((t.working_days for t in tasks.values()), default=0.0)
        total_calendar_days = (project_end_date.date() - self.start_date.date()).days

        return GanttResult(
            project_name=self.cpm_result.project_name,
            project_start_date=self.start_date,
            project_end_date=project_end_date,
            project_duration_calendar_days=format_time_value(total_calendar_days, 'days'),
            project_duration_working_days=format_time_value(total_working_days, self.time_unit),
            tasks=tasks,
            time_unit=self.time_unit,
            critical_path=self.cpm_result.critical_path,
            holidays=self.cpm_result.holidays,
            skip_weekends=self.cpm_result.skip_weekends,
            skip_holidays=self.cpm_result.skip_holidays,
            calculation_date=datetime.now(),
        )

    def _convert_task(self, task_id: Union[int, str], cpm_task: CPMTaskResult) -> GanttTaskResult:
        start_date = self.calendar.add_workdays(self.start_date, cpm_task.faz)
        end_date, working_days, interruptions = self._calculate_end_date(start_date, cpm_task.duration)
        return GanttTaskResult(
            id=task_id,
            name=cpm_task.name,
            network_duration_days=cpm_task.duration,
            calendar_start_date=start_date,
            calendar_end_date=end_date,
            working_days=working_days,
            calendar_days=(end_date.date() - start_date.date()).days + 1,
            interruptions=interruptions,
            is_critical=cpm_task.is_critical,
            puffer_days=cpm_task.puffer,
        )

    def _calculate_end_date(self, start_date: datetime,
                            working_days: float) -> Tuple[datetime, float, List[Dict[str, Any]]]:
        """
        Zählt ab start_date ganze Arbeitstage ab, bis working_days aufgebraucht sind
        (angefangene Tage zählen voll), und protokolliert übersprungene Tage.

        Returns:
            (Enddatum, gezählte Arbeitstage, Unterbrechungen)
        """
        interruptions: List[Dict[str, Any]] = []
        current = start_date
        remaining = working_days
        counted = 0.0
        for _ in range(int(working_days * 10) + 100):   # Sicherheitslimit
            if remaining <= 0:
                break
            reason = self.calendar.interruption_reason(current)
            if reason is None:
                counted += 1.0
                remaining -= 1.0
            else:
                interruptions.append({
                    'date': current, 'type': reason, 'description': f'Unterbrechung: {reason}',
                })
            current += timedelta(days=1)
        return current - timedelta(days=1), counted, interruptions
