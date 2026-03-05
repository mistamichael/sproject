"""
CPM (Critical Path Method) calculation with Pydantic models
============================================================

Provides CPM calculation functionality for Project models.
"""

from typing import Dict, List, Union, Optional, Any
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
except (ImportError, ValueError):
    from utils import (
        parse_duration_to_days,
        detect_time_unit,
        format_time_value,
        format_datetime_value,
        add_workdays,
        count_weekend_days
    )


class CPMTaskResult(BaseModel):
    """
    CPM-Ergebnis für einen einzelnen Task.

    Attributes:
        id: Task-ID
        name: Task-Name
        duration: Dauer in Tagen
        faz: Frühester Anfangszeitpunkt
        fez: Frühester Endzeitpunkt
        saz: Spätester Anfangszeitpunkt
        sez: Spätester Endzeitpunkt
        puffer: Gesamtpuffer
        free_puffer: Freier Puffer
        is_critical: Ob Task kritisch ist
        is_break: Ob Task eine Ruhepause ist (optional)
        successors: Nachfolger-IDs
        predecessors: Vorgänger-IDs
    """
    id: Union[int, str]
    name: str
    duration: float
    faz: float = 0.0
    fez: float = 0.0
    saz: float = 0.0
    sez: float = 0.0
    puffer: float = 0.0
    free_puffer: float = 0.0
    is_critical: bool = False
    is_break: bool = False
    successors: List[Union[int, str]] = []
    predecessors: List[Union[int, str]] = []


class CPMResult(BaseModel):
    """
    Gesamtergebnis der CPM-Berechnung.

    Attributes:
        project_name: Name des Projekts
        project_duration: Projektdauer (formatiert)
        critical_path: Liste der Task-IDs auf dem kritischen Pfad
        tasks: Dictionary mit CPM-Ergebnissen pro Task
        time_unit: Verwendete Zeiteinheit ('minutes', 'hours', 'days')
        project_start: Projektstartdatum
        calculation_date: Zeitpunkt der Berechnung
    """
    project_name: str
    project_duration: str
    critical_path: List[Union[int, str]]
    tasks: Dict[Union[int, str], CPMTaskResult]
    time_unit: str = 'days'
    project_start: Optional[datetime] = None
    calculation_date: Optional[datetime] = None

    def export_to_dict(self, include_dates: bool = True) -> dict:
        """
        Exportiert das Ergebnis als Dictionary (für JSON-Export).

        Args:
            include_dates: Ob Kalenderdaten eingeschlossen werden sollen

        Returns:
            Dictionary mit Projektergebnissen
        """
        output_data = {
            'project': self.project_name,
            'project_duration': self.project_duration,
            'critical_path': self.critical_path,
            'tasks': []
        }

        if self.calculation_date:
            output_data['calculation_date'] = self.calculation_date.strftime('%Y-%m-%d %H:%M:%S')

        if self.project_start:
            output_data['project_start'] = self.project_start.strftime('%Y-%m-%d')

        # Formatiere Tasks für Export
        for task_id, task_result in self.tasks.items():
            task_dict = {
                'id': task_id,
                'name': task_result.name,
                'duration': format_time_value(task_result.duration, self.time_unit),
                'cpm': {
                    'D': format_time_value(task_result.duration, self.time_unit),
                    'FB': format_datetime_value(
                        task_result.faz,
                        self.time_unit,
                        self.project_start
                    ) if self.project_start else format_time_value(task_result.faz, self.time_unit),
                    'FE': format_datetime_value(
                        task_result.fez,
                        self.time_unit,
                        self.project_start
                    ) if self.project_start else format_time_value(task_result.fez, self.time_unit),
                    'SB': format_datetime_value(
                        task_result.saz,
                        self.time_unit,
                        self.project_start
                    ) if self.project_start else format_time_value(task_result.saz, self.time_unit),
                    'SE': format_datetime_value(
                        task_result.sez,
                        self.time_unit,
                        self.project_start
                    ) if self.project_start else format_time_value(task_result.sez, self.time_unit),
                    'GP': format_time_value(task_result.puffer, self.time_unit),
                    'FP': format_time_value(task_result.free_puffer, self.time_unit),
                    'is_critical': task_result.is_critical,
                }
            }

            # Füge Kalenderdaten hinzu (optional)
            if include_dates and self.project_start:
                faz_date = add_workdays(self.project_start, task_result.faz)
                fez_date = add_workdays(self.project_start, task_result.fez)
                saz_date = add_workdays(self.project_start, task_result.saz)
                sez_date = add_workdays(self.project_start, task_result.sez)

                task_dict['cpm']['dates'] = {
                    'fb_date': faz_date.strftime('%Y-%m-%d'),
                    'fe_date': fez_date.strftime('%Y-%m-%d'),
                    'sb_date': saz_date.strftime('%Y-%m-%d'),
                    'se_date': sez_date.strftime('%Y-%m-%d'),
                }

                # Zähle Wochenendtage
                num_weekend_days = count_weekend_days(faz_date, fez_date)
                if num_weekend_days > 0:
                    task_dict['cpm']['dates']['num_weekend_days'] = num_weekend_days

            output_data['tasks'].append(task_dict)

        return output_data


class CPMCalculator:
    """
    Berechnet CPM für Pydantic Project-Models.

    Arbeitet mit ProjectBase und seinen Unterklassen, anstatt mit Dictionaries.
    """

    def __init__(self, project: 'ProjectBase', start_date: Optional[datetime] = None):
        """
        Initialisiert den CPM-Calculator.

        Args:
            project: ProjectBase oder Unterklasse
            start_date: Projektstartdatum (optional)
        """
        self.project = project
        self.start_date = start_date

        # Wenn kein Startdatum übergeben wurde, versuche es aus project_start zu holen
        if self.start_date is None:
            if project.project_start:
                try:
                    self.start_date = datetime.strptime(project.project_start, '%Y-%m-%d')
                except ValueError:
                    self.start_date = datetime.now()
            else:
                self.start_date = datetime.now()

        # Erkenne Zeiteinheit
        self.time_unit = project.get_time_unit()

        # CPM-Ergebnisse
        self.cpm_tasks: Dict[Union[int, str], CPMTaskResult] = {}

    def calculate(self) -> CPMResult:
        """
        Führt die vollständige CPM-Berechnung durch.

        Returns:
            CPMResult mit berechneten Werten

        Examples:
            >>> from models import load_project
            >>> project = load_project("examples/tankdesign.json")
            >>> calculator = CPMCalculator(project)
            >>> result = calculator.calculate()
            >>> result.project_duration
            '50.0d'
            >>> result.critical_path
            [1, 3, 7, 8]
        """
        # Initialisiere CPM-Daten
        self._initialize_cpm_data()

        # Vorwärtsrechnung
        self._forward_pass()

        # Rückwärtsrechnung
        self._backward_pass()

        # Pufferzeiten berechnen
        self._calculate_slack()

        # Erstelle Ergebnis
        project_duration_days = max(task.fez for task in self.cpm_tasks.values())
        project_duration_str = format_time_value(project_duration_days, self.time_unit)

        critical_path = self._get_critical_path()

        return CPMResult(
            project_name=self.project.project,
            project_duration=project_duration_str,
            critical_path=critical_path,
            tasks=self.cpm_tasks,
            time_unit=self.time_unit,
            project_start=self.start_date,
            calculation_date=datetime.now()
        )

    def _initialize_cpm_data(self) -> None:
        """Initialisiert die CPM-Datenstruktur für alle Tasks."""
        # Erstelle CPMTaskResult für jeden Task
        for task in self.project.tasks:
            # Parse duration using utils
            duration = parse_duration_to_days(task.duration) if task.duration else 0.0

            # Hole dependencies
            dependencies = task.dependencies if hasattr(task, 'dependencies') and task.dependencies else []

            # Hole is_break Flag
            is_break = task.is_break if hasattr(task, 'is_break') else False

            self.cpm_tasks[task.id] = CPMTaskResult(
                id=task.id,
                name=task.name,
                duration=duration,
                successors=dependencies,  # dependencies sind Nachfolger
                predecessors=[],  # Wird unten berechnet
                is_break=is_break
            )

        # Berechne Vorgänger aus Nachfolgern
        for task_id, task_result in self.cpm_tasks.items():
            for successor_id in task_result.successors:
                if successor_id in self.cpm_tasks:
                    self.cpm_tasks[successor_id].predecessors.append(task_id)

    def _insert_weekend_blocker(
        self,
        fez_of_predecessor: float,
        predecessor_id: Union[int, str],
        successor_id: Union[int, str]
    ) -> Optional[str]:
        """
        Prüft ob zwischen Vorgänger-Ende und Nachfolger-Start ein Wochenende liegt.
        Falls ja, wird ein Wochenend-Blocker-Task als CPMTaskResult eingefügt.

        Der Blocker hat:
        - Puffer = 0 (FAZ = SAZ, FEZ = SEZ)
        - Keine Ressourcen
        - is_blocker = True

        Args:
            fez_of_predecessor: FEZ des Vorgänger-Tasks (Tage seit Projektstart)
            predecessor_id:     ID des Vorgänger-Tasks
            successor_id:       ID des Task der nach dem Wochenende kommt

        Returns:
            ID des eingefügten Blocker-Tasks, oder None wenn kein Wochenende
        """
        start_dt = self.start_date + timedelta(days=fez_of_predecessor)
        weekday = start_dt.weekday()  # 0=Mo, 5=Sa, 6=So

        if weekday < 5:  # Kein Wochenende
            return None

        # Berechne Wochenend-Dauer zum nächsten Montag
        if weekday == 5:  # Samstag -> 2 Tage bis Montag
            weekend_days = 2
        else:  # Sonntag -> 1 Tag bis Montag
            weekend_days = 1

        blocker_id = f"WE-{predecessor_id}-{successor_id}"

        # Nicht doppelt einfügen
        if blocker_id in self.cpm_tasks:
            return blocker_id

        blocker_faz = fez_of_predecessor
        blocker_fez = blocker_faz + weekend_days  # Kalender-Tage, kein add_workdays

        blocker = CPMTaskResult(
            id=blocker_id,
            name=f"Wochenende",
            duration=float(weekend_days),
            faz=blocker_faz,
            fez=blocker_fez,
            saz=blocker_faz,   # GP = 0: SAZ = FAZ
            sez=blocker_fez,   # GP = 0: SEZ = FEZ
            puffer=0.0,
            free_puffer=0.0,
            is_critical=True,
            is_break=False,
            successors=[successor_id],
            predecessors=[predecessor_id]
        )
        self.cpm_tasks[blocker_id] = blocker
        return blocker_id

    def _forward_pass(self) -> None:
        """
        Vorwärtsrechnung: Berechnet FAZ und FEZ.
        Verwendet topologische Sortierung für korrekte Reihenfolge.
        Berücksichtigt Wochenenden durch Einfügen von Blocker-Tasks.
        """
        sorted_ids = self._topological_sort()

        for task_id in sorted_ids:
            task_result = self.cpm_tasks[task_id]

            if not task_result.predecessors:
                # Startknoten: FAZ = 0
                task_result.faz = 0.0
            else:
                # FAZ = Maximum aller FEZ der Vorgänger
                max_fez = 0.0
                max_pred_id = None
                for pred_id in task_result.predecessors:
                    if pred_id in self.cpm_tasks:
                        pred_fez = self.cpm_tasks[pred_id].fez
                        if pred_fez > max_fez:
                            max_fez = pred_fez
                            max_pred_id = pred_id
                task_result.faz = max_fez

                # Prüfe ob FAZ auf ein Wochenende fällt -> Blocker-Task einfügen
                if max_pred_id is not None and self.start_date:
                    blocker_id = self._insert_weekend_blocker(max_fez, max_pred_id, task_id)
                    if blocker_id:
                        # FAZ des aktuellen Tasks = FEZ des Blockers
                        task_result.faz = self.cpm_tasks[blocker_id].fez
                        # Vorgänger des aktuellen Tasks: ersetze max_pred durch blocker
                        if max_pred_id in task_result.predecessors:
                            idx = task_result.predecessors.index(max_pred_id)
                            task_result.predecessors[idx] = blocker_id
                        # Nachfolger des Vorgänger-Tasks: ersetze task_id durch blocker
                        pred_task = self.cpm_tasks[max_pred_id]
                        if task_id in pred_task.successors:
                            idx = pred_task.successors.index(task_id)
                            pred_task.successors[idx] = blocker_id

            # FEZ = FAZ + Dauer (mit Wochenenden für normale Tasks)
            if hasattr(self.project.tasks[0] if self.project.tasks else None, 'is_blocker'):
                pass  # Skip – wird weiter unten behandelt
            task_result.fez = self._add_duration_with_weekends(task_result.faz, task_result.duration)

    def _backward_pass(self) -> None:
        """Rückwärtsrechnung: Berechnet SAZ und SEZ."""
        # Finde Endknoten (Tasks ohne Nachfolger)
        end_nodes = [
            task_id for task_id, task_result in self.cpm_tasks.items()
            if not task_result.successors
        ]

        # Projektende = maximaler FEZ
        project_end = max(task.fez for task in self.cpm_tasks.values())

        # Initialisiere SEZ für Endknoten
        for task_id in end_nodes:
            self.cpm_tasks[task_id].sez = self.cpm_tasks[task_id].fez

        # Rückwärts-Topologische Sortierung
        reverse_sorted = list(reversed(self._topological_sort()))

        # Berechne SEZ und SAZ rückwärts
        for task_id in reverse_sorted:
            task_result = self.cpm_tasks[task_id]

            if not task_result.successors:
                # Endknoten: SEZ bereits gesetzt (= FEZ)
                if task_result.sez == 0:
                    task_result.sez = task_result.fez
            else:
                # SEZ = Minimum aller SAZ der Nachfolger
                min_saz = float('inf')
                for succ_id in task_result.successors:
                    if succ_id in self.cpm_tasks:
                        min_saz = min(min_saz, self.cpm_tasks[succ_id].saz)
                task_result.sez = min_saz

            # SAZ = SEZ - Dauer (mit Wochenenden rückwärts)
            task_result.saz = self._subtract_duration_with_weekends(task_result.sez, task_result.duration)

    def _calculate_slack(self) -> None:
        """Berechnet die Pufferzeiten und markiert kritische Tasks."""
        for task_id, task_result in self.cpm_tasks.items():
            # Pausen und Wochenend-Blocker: GP=0, FAZ=SAZ, FEZ=SEZ erzwingen
            is_fixed = task_result.is_break or getattr(task_result, '_is_blocker', False)
            # is_blocker erkennen anhand des ID-Präfix (WE-) für Blocker-Tasks
            is_fixed = is_fixed or (isinstance(task_id, str) and task_id.startswith('WE-'))

            if is_fixed:
                task_result.saz = task_result.faz
                task_result.sez = task_result.fez
                task_result.puffer = 0.0
                task_result.free_puffer = 0.0
                task_result.is_critical = True
                continue

            # Gesamtpuffer (GP) = SAZ - FAZ
            task_result.puffer = task_result.saz - task_result.faz

            # Freier Puffer (FP) = Min(FAZ der Nachfolger) - FEZ
            if task_result.successors:
                min_successor_faz = float('inf')
                for succ_id in task_result.successors:
                    if succ_id in self.cpm_tasks:
                        min_successor_faz = min(min_successor_faz, self.cpm_tasks[succ_id].faz)
                task_result.free_puffer = min_successor_faz - task_result.fez
            else:
                # Endknoten: freier Puffer = Gesamtpuffer
                task_result.free_puffer = task_result.puffer

            # Kritische Tasks haben Gesamtpuffer ≈ 0
            task_result.is_critical = abs(task_result.puffer) < 0.001

    def _add_duration_with_weekends(self, start_days: float, duration_days: float) -> float:
        """
        Addiert Dauer zu Startzeit unter Berücksichtigung von Wochenenden.

        Args:
            start_days: Start in Tagen seit Projektbeginn
            duration_days: Dauer in Arbeitstagen

        Returns:
            Endzeit in Tagen seit Projektbeginn (inkl. Wochenenden)
        """
        # Handle infinity values
        if start_days == float('inf') or duration_days == float('inf'):
            return float('inf')

        # Konvertiere Tage zu datetime
        start_datetime = self.start_date + timedelta(days=start_days)

        # Addiere Arbeitstage (überspringt Wochenenden)
        end_datetime = add_workdays(start_datetime, duration_days)

        # Konvertiere zurück zu Tagen
        days_diff = (end_datetime - self.start_date).total_seconds() / 86400
        return days_diff

    def _subtract_duration_with_weekends(self, end_days: float, duration_days: float) -> float:
        """
        Subtrahiert Dauer von Endzeit unter Berücksichtigung von Wochenenden.

        Args:
            end_days: Ende in Tagen seit Projektbeginn
            duration_days: Dauer in Arbeitstagen

        Returns:
            Startzeit in Tagen seit Projektbeginn (inkl. Wochenenden)
        """
        # Handle infinity values
        if end_days == float('inf') or duration_days == float('inf'):
            return float('inf')

        # Konvertiere Tage zu datetime
        end_datetime = self.start_date + timedelta(days=end_days)

        # Subtrahiere Arbeitstage (negative Dauer = rückwärts)
        start_datetime = add_workdays(end_datetime, -duration_days)

        # Konvertiere zurück zu Tagen
        days_diff = (start_datetime - self.start_date).total_seconds() / 86400
        return days_diff

    def _topological_sort(self) -> List[Union[int, str]]:
        """
        Führt topologische Sortierung durch.

        Returns:
            Liste der Task-IDs in topologischer Reihenfolge
        """
        visited = set()
        result = []

        def visit(task_id: Union[int, str]):
            if task_id in visited or task_id not in self.cpm_tasks:
                return
            visited.add(task_id)

            # Erst alle Vorgänger besuchen
            for pred_id in self.cpm_tasks[task_id].predecessors:
                visit(pred_id)

            result.append(task_id)

        # Besuche alle Tasks
        for task_id in self.cpm_tasks.keys():
            visit(task_id)

        return result

    def _get_critical_path(self) -> List[Union[int, str]]:
        """
        Gibt die Task-IDs auf dem kritischen Pfad zurück.

        Returns:
            Liste der Task-IDs (sortiert nach FAZ)
        """
        critical_tasks = [
            task_id for task_id, task_result in self.cpm_tasks.items()
            if task_result.is_critical
        ]

        # Sortiere nach FAZ (chronologisch)
        critical_tasks.sort(key=lambda tid: self.cpm_tasks[tid].faz)

        return critical_tasks
