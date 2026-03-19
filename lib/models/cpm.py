"""
CPM (Critical Path Method) calculation with Pydantic models
============================================================

Provides CPM calculation functionality for Project models.
"""

from typing import Dict, List, Literal, Union, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from pathlib import Path

# Import utils - try relative import first, then absolute
try:
    from ..utils import (
        parse_duration_to_days,
        format_time_value,
        format_datetime_value,
        add_workdays,
        count_weekend_days
    )
    from ..config_loader import ConfigLoader
except (ImportError, ValueError):
    from utils import (
        parse_duration_to_days,
        format_time_value,
        format_datetime_value,
        add_workdays,
        count_weekend_days
    )
    from config_loader import ConfigLoader


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
        successors: Nachfolger-IDs (alle Typen kombiniert)
        predecessors: Vorgänger-IDs (alle Typen kombiniert)
        predecessors_ea: Vorgänger mit Ende-Anfang Beziehung
        predecessors_aa: Vorgänger mit Anfang-Anfang Beziehung
        predecessors_ee: Vorgänger mit Ende-Ende Beziehung
        predecessors_ae: Vorgänger mit Anfang-Ende Beziehung
        successors_ea: Nachfolger mit Ende-Anfang Beziehung
        successors_aa: Nachfolger mit Anfang-Anfang Beziehung
        successors_ee: Nachfolger mit Ende-Ende Beziehung
        successors_ae: Nachfolger mit Anfang-Ende Beziehung
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
    # Kombinierte Listen (für Rückwärtskompatibilität)
    successors: List[Union[int, str]] = []
    predecessors: List[Union[int, str]] = []
    # Typisierte Beziehungen
    predecessors_ea: List[Union[int, str]] = []  # Ende-Anfang (Standard)
    predecessors_aa: List[Union[int, str]] = []  # Anfang-Anfang
    predecessors_ee: List[Union[int, str]] = []  # Ende-Ende
    predecessors_ae: List[Union[int, str]] = []  # Anfang-Ende
    successors_ea: List[Union[int, str]] = []    # Ende-Anfang (Standard)
    successors_aa: List[Union[int, str]] = []    # Anfang-Anfang
    successors_ee: List[Union[int, str]] = []    # Ende-Ende
    successors_ae: List[Union[int, str]] = []    # Anfang-Ende


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
        holidays: Set von Feiertagsdaten im Format 'YYYY-MM-DD' (optional)
        skip_weekends: Ob Wochenenden übersprungen werden (optional)
        skip_holidays: Ob Feiertage übersprungen werden (optional)
    """
    project_name: str
    project_duration: str
    critical_path: List[Union[int, str]]
    tasks: Dict[Union[int, str], CPMTaskResult]
    time_unit: Literal['minutes', 'hours', 'days'] = 'days'
    project_start: Optional[datetime] = None
    calculation_date: Optional[datetime] = None
    holidays: Optional[Dict[str, str]] = None
    skip_weekends: bool = True
    skip_holidays: bool = False

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
            'tasks': [],
            'settings': {
                'skip_weekends': self.skip_weekends,
                'skip_holidays': self.skip_holidays,
            }
        }

        if self.calculation_date:
            output_data['calculation_date'] = self.calculation_date.strftime('%Y-%m-%d %H:%M:%S')

        if self.project_start:
            output_data['project_start'] = self.project_start.strftime('%Y-%m-%d')

        # Füge Feiertags-Liste hinzu (falls aktiviert)
        if self.skip_holidays and self.holidays:
            output_data['holidays'] = sorted(list(self.holidays))

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

                # Zähle Feiertage während der Task-Dauer
                if self.skip_holidays and self.holidays:
                    num_holidays = self._count_holidays_in_range(faz_date, fez_date)
                    if num_holidays > 0:
                        task_dict['cpm']['dates']['num_holidays'] = num_holidays

            output_data['tasks'].append(task_dict)

        return output_data

    def _count_holidays_in_range(self, start_date: datetime, end_date: datetime) -> int:
        """
        Zählt die Anzahl der Feiertage in einem Datumsbereich.

        Args:
            start_date: Startdatum (inklusiv)
            end_date: Enddatum (inklusiv)

        Returns:
            Anzahl der Feiertage im Bereich
        """
        if not self.holidays:
            return 0

        count = 0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in self.holidays:
                count += 1
            current_date += timedelta(days=1)

        return count

    def to_network_csv(self) -> str:
        """
        Generiert Netzplan-Daten im CSV-Format.

        Returns:
            CSV-Daten als String
        """
        lines = []
        lines.append("TaskID,Task Name,Duration,FAZ,FEZ,SAZ,SEZ,GP,FP,Successors,IsCritical")

        sorted_tasks = sorted(
            self.tasks.items(),
            key=lambda x: x[1].faz
        )

        for task_id, task in sorted_tasks:
            if isinstance(task_id, str) and task_id.startswith('WE-'):
                continue

            successors = ";".join(str(s) for s in task.successors if not (isinstance(s, str) and s.startswith('WE-')))
            is_critical = "JA" if task.is_critical else "NEIN"

            line = f'"{task_id}","{task.name}",{task.duration:.1f},{task.faz:.1f},{task.fez:.1f},{task.saz:.1f},{task.sez:.1f},{task.puffer:.1f},{task.free_puffer:.1f},"{successors}",{is_critical}'
            lines.append(line)

        return "\n".join(lines)


class CPMCalculator:
    """
    Berechnet CPM für Pydantic Project-Models.

    Arbeitet mit ProjectBase und seinen Unterklassen, anstatt mit Dictionaries.
    """

    def __init__(self, project: 'ProjectBase', start_date: Optional[datetime] = None, cfg_dir: Optional[Path] = None):
        """
        Initialisiert den CPM-Calculator.

        Args:
            project: ProjectBase oder Unterklasse
            start_date: Projektstartdatum (optional)
            cfg_dir: Verzeichnis mit Konfigurationsdateien (optional)
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

        # Lade Konfiguration
        if cfg_dir:
            config_path = cfg_dir / "defaults.cfg"
            self.config = ConfigLoader(config_path if config_path.exists() else None)
        else:
            self.config = ConfigLoader()

        # Lade CPM-Einstellungen
        cpm_settings = self.config.get_cpm_settings()
        self.skip_weekends = cpm_settings.get('skip_weekends', True)
        self.skip_holidays = cpm_settings.get('skip_holidays', False)

        # Lade Feiertage falls aktiviert
        self.holidays: Dict[str, str] = {}
        if self.skip_holidays and self.start_date:
            # Lade Feiertage für das Projektjahr ± 1 Jahr
            self.holidays = self.config.get_holidays(year=self.start_date.year, year_range=1)

        # CPM-Ergebnisse
        self.cpm_tasks: Dict[Union[int, str], CPMTaskResult] = {}

    def calculate(self) -> CPMResult:
        """
        Führt die vollständige CPM-Berechnung durch.

        Returns:
            CPMResult mit berechneten Werten

        Raises:
            ValueError: Bei Selbstreferenz oder zyklischer Abhängigkeit in den Eingabedaten

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

        # Prüfe auf Zyklen und Selbstreferenzen – bricht mit ValueError ab
        self._validate_no_cycles()

        # Vorwärtsrechnung
        self._forward_pass()

        # Rückwärtsrechnung
        self._backward_pass()

        # Pufferzeiten berechnen
        self._calculate_slack()

        # Resource Leveling durchführen (neue Phase mit Ressourcen-Verfügbarkeitsprüfung)
        self._resource_leveling()

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
            calculation_date=datetime.now(),
            holidays=self.holidays if self.skip_holidays else None,
            skip_weekends=self.skip_weekends,
            skip_holidays=self.skip_holidays
        )

    def _initialize_cpm_data(self) -> None:
        """
        Initialisiert die CPM-Datenstruktur für alle Tasks.
        Unterstützt verschiedene Abhängigkeitstypen: EA, AA, EE, AE.
        """
        # Erstelle CPMTaskResult für jeden Task
        for task in self.project.tasks:
            # Parse duration using utils
            duration = parse_duration_to_days(task.duration) if task.duration else 0.0

            # Hole successors (EA - Ende-Anfang, Standard)
            deps_ea = task.successors if hasattr(task, 'successors') and task.successors else []

            # Hole successors_aa (Anfang-Anfang)
            deps_aa = task.successors_aa if hasattr(task, 'successors_aa') and task.successors_aa else []

            # Hole successors_ee (Ende-Ende)
            deps_ee = task.successors_ee if hasattr(task, 'successors_ee') and task.successors_ee else []

            # Hole successors_ae (Anfang-Ende)
            deps_ae = task.successors_ae if hasattr(task, 'successors_ae') and task.successors_ae else []

            # Hole is_break Flag
            is_break = task.is_break if hasattr(task, 'is_break') else False

            # Kombiniere alle dependencies für Rückwärtskompatibilität
            all_deps = list(set(deps_ea + deps_aa + deps_ee + deps_ae))

            self.cpm_tasks[task.id] = CPMTaskResult(
                id=task.id,
                name=task.name,
                duration=duration,
                successors=all_deps,  # Alle dependencies kombiniert
                predecessors=[],      # Wird unten berechnet
                successors_ea=deps_ea,
                successors_aa=deps_aa,
                successors_ee=deps_ee,
                successors_ae=deps_ae,
                predecessors_ea=[],   # Wird unten berechnet
                predecessors_aa=[],   # Wird unten berechnet
                predecessors_ee=[],   # Wird unten berechnet
                predecessors_ae=[],   # Wird unten berechnet
                is_break=is_break
            )

        # Berechne Vorgänger aus Nachfolgern (umgekehrte Beziehungen)
        for task_id, task_result in self.cpm_tasks.items():
            # EA-Beziehungen
            for successor_id in task_result.successors_ea:
                if successor_id in self.cpm_tasks:
                    self.cpm_tasks[successor_id].predecessors_ea.append(task_id)
                    if task_id not in self.cpm_tasks[successor_id].predecessors:
                        self.cpm_tasks[successor_id].predecessors.append(task_id)

            # AA-Beziehungen
            for successor_id in task_result.successors_aa:
                if successor_id in self.cpm_tasks:
                    self.cpm_tasks[successor_id].predecessors_aa.append(task_id)
                    if task_id not in self.cpm_tasks[successor_id].predecessors:
                        self.cpm_tasks[successor_id].predecessors.append(task_id)

            # EE-Beziehungen
            for successor_id in task_result.successors_ee:
                if successor_id in self.cpm_tasks:
                    self.cpm_tasks[successor_id].predecessors_ee.append(task_id)
                    if task_id not in self.cpm_tasks[successor_id].predecessors:
                        self.cpm_tasks[successor_id].predecessors.append(task_id)

            # AE-Beziehungen
            for successor_id in task_result.successors_ae:
                if successor_id in self.cpm_tasks:
                    self.cpm_tasks[successor_id].predecessors_ae.append(task_id)
                    if task_id not in self.cpm_tasks[successor_id].predecessors:
                        self.cpm_tasks[successor_id].predecessors.append(task_id)


    def _validate_no_cycles(self) -> None:
        """
        Prüft den Abhängigkeitsgraph auf Selbstreferenzen und Zyklen.

        Verwendet Tiefensuche (DFS) mit Drei-Farben-Markierung:
        - WHITE: noch nicht besucht
        - GRAY:  aktuell auf dem Rekursions-Stack (offener Pfad)
        - BLACK: vollständig abgearbeitet

        Raises:
            ValueError: Bei Selbstreferenz oder zyklischer Abhängigkeit,
                        mit Angabe der betroffenen Tasks und des Zykluspfads.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {task_id: WHITE for task_id in self.cpm_tasks}
        path: List[Union[int, str]] = []

        def dfs(task_id: Union[int, str]) -> None:
            color[task_id] = GRAY
            path.append(task_id)

            for succ_id in self.cpm_tasks[task_id].successors:
                if succ_id not in self.cpm_tasks:
                    continue

                # Selbstreferenz
                if succ_id == task_id:
                    name = self.cpm_tasks[task_id].name
                    raise ValueError(
                        f"Fehler in Eingabedaten: Task {task_id} ('{name}') "
                        f"referenziert sich selbst als Abhängigkeit (Selbstreferenz)."
                    )

                # Zyklus gefunden: succ_id ist bereits auf dem aktiven Pfad
                if color[succ_id] == GRAY:
                    cycle_start = path.index(succ_id)
                    cycle_ids = path[cycle_start:] + [succ_id]
                    cycle_str = " -> ".join(
                        f"{tid} ('{self.cpm_tasks[tid].name}')"
                        for tid in cycle_ids
                    )
                    raise ValueError(
                        f"Fehler in Eingabedaten: Zyklische Abhängigkeit gefunden:\n"
                        f"  {cycle_str}"
                    )

                if color[succ_id] == WHITE:
                    dfs(succ_id)

            path.pop()
            color[task_id] = BLACK

        for task_id in list(self.cpm_tasks.keys()):
            if color[task_id] == WHITE:
                dfs(task_id)

    def _forward_pass(self) -> None:
        """
        Vorwärtsrechnung: Berechnet FAZ und FEZ (ohne Wochenenden/Feiertage).

        Dies ist Phase 1: Reine Netzplan-Berechnung mit einfacher Zeitarithmetik.
        Wochenenden und Feiertage werden später in Phase 2 (GanttCalculator) berücksichtigt.

        FAZ/FEZ sind reine Arbeitstage seit Projektbeginn (Daten ohne Kalender-Unterbrechungen).
        """
        sorted_ids = self._topological_sort()

        for task_id in sorted_ids:
            task_result = self.cpm_tasks[task_id]

            # Berechne FAZ basierend auf verschiedenen Abhängigkeitstypen
            faz_constraints = [0.0]  # Mindestens 0

            # EA (Ende-Anfang): Nachfolger beginnt wenn Vorgänger endet
            # FAZ(Nachfolger) >= FEZ(Vorgänger)
            for pred_id in task_result.predecessors_ea:
                if pred_id in self.cpm_tasks:
                    pred_fez = self.cpm_tasks[pred_id].fez
                    faz_constraints.append(pred_fez)

            # AA (Anfang-Anfang): Nachfolger beginnt wenn Vorgänger beginnt
            # FAZ(Nachfolger) >= FAZ(Vorgänger)
            for pred_id in task_result.predecessors_aa:
                if pred_id in self.cpm_tasks:
                    pred_faz = self.cpm_tasks[pred_id].faz
                    faz_constraints.append(pred_faz)

            # AE (Anfang-Ende): Nachfolger kann erst enden wenn Vorgänger beginnt
            # FEZ(Nachfolger) >= FAZ(Vorgänger)
            # => FAZ(Nachfolger) >= FAZ(Vorgänger) - Dauer(Nachfolger)
            for pred_id in task_result.predecessors_ae:
                if pred_id in self.cpm_tasks:
                    pred_faz = self.cpm_tasks[pred_id].faz
                    # Nachfolger muss so starten, dass er frühestens endet wenn Vorgänger startet
                    required_faz = pred_faz - task_result.duration
                    faz_constraints.append(required_faz)

            # Setze FAZ auf Maximum aller Constraints (OHNE Wochenenden-Verschiebung)
            task_result.faz = max(faz_constraints)

            # Berechne FEZ: FEZ = FAZ + Dauer (einfache Arithmetik, KEINE Wochenenden)
            task_result.fez = task_result.faz + task_result.duration

            # EE (Ende-Ende): Nachfolger endet wenn Vorgänger endet
            # FEZ(Nachfolger) >= FEZ(Vorgänger)
            # Falls FEZ zu früh ist, verschiebe FAZ nach hinten
            for pred_id in task_result.predecessors_ee:
                if pred_id in self.cpm_tasks:
                    pred_fez = self.cpm_tasks[pred_id].fez
                    if task_result.fez < pred_fez:
                        # Nachfolger muss später enden - verschiebe FAZ
                        task_result.faz = pred_fez - task_result.duration
                        task_result.fez = task_result.faz + task_result.duration

    def _backward_pass(self) -> None:
        """
        Rückwärtsrechnung: Berechnet SAZ und SEZ (ohne Wochenenden/Feiertage).

        Dies ist Phase 1: Reine Netzplan-Berechnung mit einfacher Zeitarithmetik.
        Wochenenden und Feiertage werden später in Phase 2 (GanttCalculator) berücksichtigt.

        SAZ/SEZ sind reine Arbeitstage seit Projektbeginn (Daten ohne Kalender-Unterbrechungen).
        """
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

            # Berechne SEZ basierend auf verschiedenen Abhängigkeitstypen
            sez_constraints = []

            if not task_result.successors:
                # Endknoten: SEZ = FEZ
                sez_constraints.append(task_result.fez)
            else:
                # EA (Ende-Anfang): Vorgänger endet bevor Nachfolger startet
                # SEZ(Vorgänger) <= SAZ(Nachfolger)
                for succ_id in task_result.successors_ea:
                    if succ_id in self.cpm_tasks:
                        succ_saz = self.cpm_tasks[succ_id].saz
                        sez_constraints.append(succ_saz)

                # AA (Anfang-Anfang): Vorgänger startet bevor Nachfolger startet
                # SAZ(Vorgänger) <= SAZ(Nachfolger)
                # => SEZ(Vorgänger) = SAZ(Nachfolger) + Dauer(Vorgänger)
                for succ_id in task_result.successors_aa:
                    if succ_id in self.cpm_tasks:
                        succ_saz = self.cpm_tasks[succ_id].saz
                        # Vorgänger muss so enden, dass er spätestens startet wenn Nachfolger startet
                        required_sez = succ_saz + task_result.duration
                        sez_constraints.append(required_sez)

                # EE (Ende-Ende): Vorgänger endet bevor Nachfolger endet
                # SEZ(Vorgänger) <= SEZ(Nachfolger)
                for succ_id in task_result.successors_ee:
                    if succ_id in self.cpm_tasks:
                        succ_sez = self.cpm_tasks[succ_id].sez
                        sez_constraints.append(succ_sez)

                # AE (Anfang-Ende): Vorgänger startet bevor Nachfolger endet
                # SAZ(Vorgänger) <= SEZ(Nachfolger)
                # => SEZ(Vorgänger) = SEZ(Nachfolger) + Dauer(Vorgänger)
                for succ_id in task_result.successors_ae:
                    if succ_id in self.cpm_tasks:
                        succ_sez = self.cpm_tasks[succ_id].sez
                        # Vorgänger muss so enden, dass er spätestens startet wenn Nachfolger endet
                        required_sez = succ_sez + task_result.duration
                        sez_constraints.append(required_sez)

            # Setze SEZ auf Minimum aller Constraints
            if sez_constraints:
                task_result.sez = min(sez_constraints)
            else:
                # Fallback: SEZ = FEZ (für Tasks ohne Nachfolger)
                task_result.sez = task_result.fez

            # SAZ = SEZ - Dauer (einfache Arithmetik, KEINE Wochenenden)
            task_result.saz = task_result.sez - task_result.duration

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

    def _resource_leveling(self) -> None:
        """
        Resource Leveling: Vergrößert Pufferzeiten wenn Ressourcen-Kapazität überschritten ist.

        Diese Methode prüft für jede Maschinen-/Ofen-Ressource mit Kapazitätslimit:
        - In jedem Zeitintervall: Summe der parallelen Tasks für diese Ressource
        - Falls Kapazität überschritten: Verschiebe Tasks mit Puffer nach vorne/hinten
        - Update FAZ/FEZ/SAZ/SEZ iterativ bis alle Konflikte gelöst sind

        Hinweis: In dieser Phase arbeiten wir mit reinen Arbeitstagen ohne Kalender-Unterbrechungen.
        """
        # Hole Ressourcen aus dem Projekt
        resources = getattr(self.project, 'resources', None) or []

        # Finde Maschinen-Ressourcen mit Kapazitätslimit
        machine_resources = {}
        for resource in resources:
            # Prüfe auf 'capacity' und 'type'
            capacity = getattr(resource, 'capacity', None)
            resource_type = getattr(resource, 'type', None)

            # Berücksichtige Maschinen, Öfen, Lastkraftwagen usw.
            if capacity is not None and resource_type in ['machine', 'oven', 'truck']:
                resource_id = resource.id
                machine_resources[resource_id] = {
                    'capacity': capacity,
                    'name': getattr(resource, 'name', resource_id),
                    'type': resource_type
                }

        # Wenn keine Ressourcen mit Kapazität: Keine Resource-Leveling nötig
        if not machine_resources:
            return

        # Iterative Resource Leveling: Wiederhole bis keine Konflikte mehr
        max_iterations = 10
        for iteration in range(max_iterations):
            conflicts_found = False

            for resource_id, resource_info in machine_resources.items():
                capacity = resource_info['capacity']

                # Prüfe für jeden Task ob diese Ressource benutzt wird
                # Sammle alle Tasks die diese Ressource nutzen
                tasks_using_resource = []
                for task_id, task_result in self.cpm_tasks.items():
                    # Hole Ressourcen aus original Task
                    if hasattr(self.project, 'tasks'):
                        # Finde original Task
                        original_task = None
                        for t in self.project.tasks:
                            if t.id == task_id:
                                original_task = t
                                break

                        if original_task:
                            task_resources = getattr(original_task, 'resources', None) or []
                            if resource_id in task_resources:
                                tasks_using_resource.append((task_id, task_result))

                # Sortiere Tasks nach FAZ (Startzeit)
                tasks_using_resource.sort(key=lambda x: x[1].faz)

                # Prüfe Kapazitätsverletzungen
                # Teile Zeitstrahl in kleine Segmente auf und prüfe Kapazität
                time_segments = set()
                for task_id, task_result in tasks_using_resource:
                    # Sammle alle Zeit-Grenzen
                    time_segments.add(task_result.faz)
                    time_segments.add(task_result.fez)

                time_segments = sorted(time_segments)

                # Für jedes Zeitsegment: Zähle überlappende Tasks
                for i in range(len(time_segments) - 1):
                    segment_start = time_segments[i]
                    segment_end = time_segments[i + 1]
                    segment_mid = (segment_start + segment_end) / 2

                    # Zähle Tasks die zu dieser Zeit laufen
                    active_tasks = [
                        (tid, tr) for tid, tr in tasks_using_resource
                        if tr.faz <= segment_mid < tr.fez
                    ]

                    if len(active_tasks) > capacity:
                        conflicts_found = True

                        # Verschiebe einen Task mit größtem Puffer
                        # Das reduziert die Chance auf Abhängigkeits-Konflikte
                        task_to_move = max(active_tasks, key=lambda x: x[1].puffer)
                        task_id_to_move, task_result_to_move = task_to_move

                        # Verschiebe diesen Task um die Dauer eines anderen Tasks
                        # Suche Lücke nach diesem Zeitsegment
                        new_faz = segment_end

                        # Prüfe Abhängigkeits-Constraints
                        for pred_id in task_result_to_move.predecessors_ea:
                            if pred_id in self.cpm_tasks:
                                pred_fez = self.cpm_tasks[pred_id].fez
                                new_faz = max(new_faz, pred_fez)

                        # Aktualisiere FAZ und FEZ
                        if new_faz > task_result_to_move.faz:
                            old_faz = task_result_to_move.faz
                            shift = new_faz - old_faz

                            task_result_to_move.faz = new_faz
                            task_result_to_move.fez = new_faz + task_result_to_move.duration

                            # Verschiebe auch nachfolgende Tasks bei Bedarf
                            self._update_successor_times(task_id_to_move, shift)

                            # Puffer neu berechnen
                            task_result_to_move.puffer = task_result_to_move.saz - task_result_to_move.faz
                            task_result_to_move.is_critical = abs(task_result_to_move.puffer) < 0.001

            # Wenn keine Konflikte mehr: Fertig
            if not conflicts_found:
                break

    def _update_successor_times(self, task_id: Union[int, str], _shift: float) -> None:
        """
        Aktualisiert die Zeiten von nachfolgenden Tasks wenn ein Task verschoben wird.

        Args:
            task_id: ID des verschobenen Tasks
            shift: Zeitverschiebung (positive Wert = nach vorne schieben)
        """
        task_result = self.cpm_tasks[task_id]

        # Iteriere über alle Nachfolger (EA-Abhängigkeiten)
        for succ_id in task_result.successors_ea:
            if succ_id in self.cpm_tasks:
                succ_result = self.cpm_tasks[succ_id]
                # Nur verschieben wenn der Nachfolger nicht schon später startet
                if succ_result.faz < task_result.fez:
                    new_faz = task_result.fez
                    succ_shift = new_faz - succ_result.faz
                    if succ_shift > 0:
                        succ_result.faz = new_faz
                        succ_result.fez = new_faz + succ_result.duration
                        # Rekursiv Nachfolger aktualisieren
                        self._update_successor_times(succ_id, succ_shift)


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
