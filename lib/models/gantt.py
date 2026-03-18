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

from typing import Dict, List, Union, Optional, Any, Set
from datetime import datetime, timedelta
from pydantic import BaseModel

# Import utils - try relative import first, then absolute
try:
    from ..utils import (
        parse_duration_to_days,
        detect_time_unit,
        format_time_value,
        format_datetime_value,
        add_workdays,
        count_weekend_days
    )
    from ..config_loader import ConfigLoader
except (ImportError, ValueError):
    from utils import (
        parse_duration_to_days,
        detect_time_unit,
        format_time_value,
        format_datetime_value,
        add_workdays,
        count_weekend_days
    )
    from config_loader import ConfigLoader

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
    holidays: Optional[Set[str]] = None
    skip_weekends: bool = True
    skip_holidays: bool = False
    calculation_date: Optional[datetime] = None


class GanttCalculator:
    """
    Berechnet Gantt-Schedule mit Kalender-Daten und Unterbrechungen.

    Konvertiert CPM-Ergebnisse (Phase 1: reine Arbeitstage) zu realistischen
    Kalender-Daten (Phase 2: mit Wochenenden, Feiertagen, etc.)
    """

    def __init__(
        self,
        cpm_result: CPMResult,
        skip_weekends: bool = True,
        skip_holidays: bool = False,
        holidays: Optional[Set[str]] = None,
        cfg_dir: Optional['Path'] = None
    ):
        """
        Initialisiert den Gantt-Calculator.

        Args:
            cpm_result: Ergebnis der CPM-Berechnung (Phase 1)
            skip_weekends: Ob Wochenenden übersprungen werden
            skip_holidays: Ob Feiertage übersprungen werden
            holidays: Set von Feiertagsdaten im Format 'YYYY-MM-DD'
            cfg_dir: Verzeichnis mit Konfigurationsdateien (optional)
        """
        self.cpm_result = cpm_result
        self.skip_weekends = skip_weekends
        self.skip_holidays = skip_holidays
        self.holidays = holidays or set()
        self.start_date = cpm_result.project_start or datetime.now()
        self.time_unit = cpm_result.time_unit

        # Gantt-Ergebnisse
        self.gantt_tasks: Dict[Union[int, str], GanttTaskResult] = {}

    def calculate(self) -> GanttResult:
        """
        Führt die Gantt-Berechnung durch (Phase 2).

        Konvertiert CPM-Zeiten (reine Arbeitstage) zu Kalender-Daten mit
        Berücksichtigung von Wochenenden, Feiertagen und Pausen.

        Returns:
            GanttResult mit Kalender-Daten
        """
        # Konvertiere jeden CPM-Task zu Gantt-Task
        for task_id, cpm_task in self.cpm_result.tasks.items():
            gantt_task = self._convert_task(task_id, cpm_task)
            self.gantt_tasks[task_id] = gantt_task

        # Berechne Projektdauer
        end_dates = [
            t.calendar_end_date for t in self.gantt_tasks.values()
            if t.calendar_end_date is not None
        ]
        project_end_date = max(end_dates) if end_dates else self.start_date

        # Zähle Arbeitstage und Kalendertage für Projekt
        total_working_days = 0.0
        total_calendar_days = (project_end_date.date() - self.start_date.date()).days

        for gantt_task in self.gantt_tasks.values():
            total_working_days = max(total_working_days, gantt_task.working_days)

        # Formatiere Projektdauer
        project_duration_working = format_time_value(total_working_days, self.time_unit)
        project_duration_calendar = format_time_value(total_calendar_days, 'days')

        return GanttResult(
            project_name=self.cpm_result.project_name,
            project_start_date=self.start_date,
            project_end_date=project_end_date,
            project_duration_calendar_days=project_duration_calendar,
            project_duration_working_days=project_duration_working,
            tasks=self.gantt_tasks,
            time_unit=self.time_unit,
            critical_path=self.cpm_result.critical_path,
            holidays=self.cpm_result.holidays,
            skip_weekends=self.skip_weekends,
            skip_holidays=self.skip_holidays,
            calculation_date=datetime.now()
        )

    def _convert_task(self, task_id: Union[int, str], cpm_task: CPMTaskResult) -> GanttTaskResult:
        """
        Konvertiert einen CPM-Task zu einem Gantt-Task mit Kalender-Daten.

        Args:
            task_id: Task-ID
            cpm_task: CPM-Ergebnis für diesen Task

        Returns:
            GanttTaskResult mit Kalender-Daten
        """
        # Berechne Startdatum aus CPM FAZ (in Arbeitstagen)
        start_date = self._calculate_date_from_days(cpm_task.faz)

        # Berechne Enddatum mit Berücksichtigung von Unterbrechungen
        end_date, working_days, interruptions = self._calculate_end_date(
            start_date,
            cpm_task.duration
        )

        # Zähle tatsächliche Kalendertage
        calendar_days = (end_date.date() - start_date.date()).days + 1

        return GanttTaskResult(
            id=task_id,
            name=cpm_task.name,
            network_duration_days=cpm_task.duration,
            calendar_start_date=start_date,
            calendar_end_date=end_date,
            working_days=working_days,
            calendar_days=calendar_days,
            interruptions=interruptions,
            is_critical=cpm_task.is_critical,
            puffer_days=cpm_task.puffer
        )

    def _calculate_date_from_days(self, days: float) -> datetime:
        """
        Konvertiert Arbeitstage (seit Projektbeginn) zu Kalender-Datum.

        Args:
            days: Anzahl Arbeitstage seit Projektbeginn

        Returns:
            Kalender-Datum
        """
        # Verwende add_workdays aus utils (berücksichtigt bereits Wochenenden)
        # Diese Funktion nimmt die CPM-Zeiten (reine Arbeitstage) und konvertiert sie zu Kalender-Daten
        return add_workdays(self.start_date, days)

    def _calculate_end_date(
        self,
        start_date: datetime,
        working_days: float
    ) -> tuple:
        """
        Berechnet Enddatum mit Berücksichtigung von Unterbrechungen.

        Args:
            start_date: Startdatum
            working_days: Anzahl Arbeitstage für diese Task

        Returns:
            Tuple: (end_date, actual_working_days, interruptions_list)
        """
        interruptions = []
        current_date = start_date
        remaining_work = working_days
        actual_working = 0.0

        # Addiere Tage bis arbeitszeit aufgebraucht ist
        max_iterations = int(working_days * 10) + 100  # Safety limit
        iteration = 0

        while remaining_work > 0 and iteration < max_iterations:
            iteration += 1

            # Prüfe ob current_date ein Arbeitstag ist
            is_working_day = self._is_working_day(current_date)

            if is_working_day:
                # Einen Tag Arbeit verbrauchen
                actual_working += 1.0
                remaining_work -= 1.0
            else:
                # Dokumentiere Unterbrechung
                reason = self._get_interruption_reason(current_date)
                interruptions.append({
                    'date': current_date,
                    'type': reason,
                    'description': f'Unterbrechung: {reason}'
                })

            # Zum nächsten Tag
            current_date += timedelta(days=1)

        # Gehe einen Tag zurück (wir sind einen Tag zu weit gegangen)
        end_date = current_date - timedelta(days=1)

        return end_date, actual_working, interruptions

    def _is_working_day(self, date: datetime) -> bool:
        """
        Prüft ob ein Datum ein Arbeitstag ist.

        Args:
            date: Zu prüfendes Datum

        Returns:
            True wenn Arbeitstag, False wenn Wochenende/Feiertag
        """
        # Prüfe Wochenende
        if self.skip_weekends and date.weekday() >= 5:  # 5=Samstag, 6=Sonntag
            return False

        # Prüfe Feiertag
        if self.skip_holidays:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.holidays:
                return False

        return True

    def _get_interruption_reason(self, date: datetime) -> str:
        """
        Ermittelt den Grund für eine Unterbrechung.

        Args:
            date: Datum

        Returns:
            Grund als String ('weekend', 'holiday', etc.)
        """
        if self.skip_weekends and date.weekday() >= 5:
            return 'weekend'

        if self.skip_holidays:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.holidays:
                return 'holiday'

        return 'unknown'

    def export_to_dict(self) -> dict:
        """
        Exportiert Gantt-Ergebnis zu Dictionary.

        Returns:
            Dictionary mit Gantt-Daten
        """
        result = {
            'project_name': self.cpm_result.project_name,
            'project_start_date': self.start_date.isoformat() if self.start_date else None,
            'time_unit': self.time_unit,
            'skip_weekends': self.skip_weekends,
            'skip_holidays': self.skip_holidays,
            'tasks': {}
        }

        for task_id, gantt_task in self.gantt_tasks.items():
            result['tasks'][str(task_id)] = {
                'id': str(task_id),
                'name': gantt_task.name,
                'network_duration_days': round(gantt_task.network_duration_days, 3),
                'calendar_start_date': gantt_task.calendar_start_date.isoformat() if gantt_task.calendar_start_date else None,
                'calendar_end_date': gantt_task.calendar_end_date.isoformat() if gantt_task.calendar_end_date else None,
                'working_days': round(gantt_task.working_days, 2),
                'calendar_days': gantt_task.calendar_days,
                'is_critical': gantt_task.is_critical,
                'puffer_days': round(gantt_task.puffer_days, 3)
            }

        return result
