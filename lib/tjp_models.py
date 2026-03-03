"""
tjp_models.py
=============
Pydantic-Modelle für die TaskJuggler JSON-Dateien:
  - workinghours_absences.json
  - persons.json
  - project.json
  - reports.json

Lädt alle Dateien über TJPRegistry und löst ID-Querverweise auf.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

# Import CPM-Klassen aus separatem Modul
from cpm_models import CPMCalculationMixin, SimpleTaskFile


# ─────────────────────────────────────────────────────────────────────────────
# Basis-Hilfsmethoden
# ─────────────────────────────────────────────────────────────────────────────

class TJPBase(BaseModel):
    """Gemeinsame Basisfunktionen für alle TJP-Modelle."""

    model_config = {"extra": "ignore"}  # _schema, _refs, _comment ignorieren

    def to_json(self, indent: int = 2) -> str:
        """Serialisiert das Objekt zurück nach JSON."""
        return self.model_dump_json(indent=indent, exclude_none=True)

    def __str__(self) -> str:
        name = getattr(self, "name", None) or getattr(self, "id", None) or ""
        cls  = self.__class__.__name__
        return f"<{cls} '{name}'>" if name else f"<{cls}>"

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{k}={v!r}"
            for k, v in self.model_dump(exclude_none=True).items()
            if k not in ("_schema", "_refs")
        )
        return f"{self.__class__.__name__}({fields})"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Arbeitszeiten & Abwesenheiten
# ─────────────────────────────────────────────────────────────────────────────

VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

class TimeSlot(TJPBase):
    """Einzelnes Zeitfenster z.B. 09:00–12:00."""
    from_time: str  = Field(alias="from")
    to_time:   str  = Field(alias="to")

    model_config = {"populate_by_name": True}

    @field_validator("from_time", "to_time")
    @classmethod
    def valid_time(cls, v: str) -> str:
        h, m = v.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59, f"Ungültige Uhrzeit: {v}"
        return v


class DaySchedule(TJPBase):
    """Tagesplan: Wochentage → Zeitfenster oder 'off'."""
    days:  list[str]
    hours: Union[list[TimeSlot], Literal["off"]]

    @field_validator("days")
    @classmethod
    def valid_days(cls, v: list[str]) -> list[str]:
        bad = set(v) - VALID_DAYS
        assert not bad, f"Unbekannte Wochentage: {bad}"
        return v


class WorkingHours(TJPBase):
    """Arbeitszeit-Definition (global oder Override)."""
    id:          str
    description: Optional[str] = None
    resource_id: Optional[str] = None   # Nur bei Overrides
    schedules:   list[DaySchedule]

    def is_working_day(self, day: str) -> bool:
        """Prüft ob ein Wochentag ein Arbeitstag ist."""
        day = day.lower()
        for s in self.schedules:
            if day in s.days:
                return s.hours != "off"
        return False

    def hours_per_day(self, day: str) -> float:
        """Berechnet die täglichen Arbeitsstunden für einen Wochentag."""
        day = day.lower()
        for s in self.schedules:
            if day in s.days and isinstance(s.hours, list):
                total = 0.0
                for slot in s.hours:
                    h1, m1 = map(int, slot.from_time.split(":"))
                    h2, m2 = map(int, slot.to_time.split(":"))
                    total += (h2 + m2 / 60) - (h1 + m1 / 60)
                return total
        return 0.0


class Absence(TJPBase):
    """Abwesenheit: Feiertag, Urlaub oder Sondertag."""
    type:        Literal["holiday", "vacation", "special"]
    name:        str
    resource_id: Optional[str] = None          # None → gilt für alle
    applies_to:  Optional[Literal["all"]] = None
    date:        Optional[str] = None          # Einzeltag
    from_date:   Optional[str] = Field(None, alias="from")
    to_date:     Optional[str] = Field(None, alias="to")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def date_or_range(self) -> Absence:
        has_single = self.date is not None
        has_range  = self.from_date is not None and self.to_date is not None
        assert has_single or has_range, \
            f"Abwesenheit '{self.name}' benötigt 'date' oder 'from'+'to'"
        return self

    def is_global(self) -> bool:
        return self.applies_to == "all" or self.resource_id is None


class WorkingHoursFile(TJPBase):
    """Komplette workinghours_absences.json."""
    global_workinghours:    WorkingHours
    workinghours_overrides: list[WorkingHours]     = []
    global_leaves:          list[Absence]          = []
    personal_absences:      list[Absence]          = []

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> WorkingHoursFile:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def get_override(self, override_id: str) -> Optional[WorkingHours]:
        return next((o for o in self.workinghours_overrides if o.id == override_id), None)

    def absences_for(self, resource_id: str) -> list[Absence]:
        """Gibt alle Abwesenheiten zurück, die für eine Person gelten."""
        return [
            a for a in self.global_leaves + self.personal_absences
            if a.is_global() or a.resource_id == resource_id
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Personen / Ressourcen
# ─────────────────────────────────────────────────────────────────────────────

class Person(TJPBase):
    """Einzelne Person / Ressource."""
    id:                       str
    name:                     str
    email:                    Optional[str] = None
    workinghours_override_ref:Optional[str] = None

    # Wird durch TJPRegistry befüllt (aufgelöste Querverweise)
    _resolved_workinghours: Optional[WorkingHours] = None

    @property
    def workinghours(self) -> Optional[WorkingHours]:
        return self._resolved_workinghours

    def resolve_workinghours(self, wh: WorkingHours) -> None:
        """Setzt die aufgelöste WorkingHours-Instanz."""
        self._resolved_workinghours = wh


class ResourceGroup(TJPBase):
    """Gruppe von Personen mit gemeinsamen Eigenschaften."""
    id:                       str
    name:                     str
    rate:                     float
    workinghours_override_ref:Optional[str] = None
    members:                  list[Person]  = []

    @field_validator("rate")
    @classmethod
    def positive_rate(cls, v: float) -> float:
        assert v > 0, f"Stundensatz muss positiv sein, war: {v}"
        return v


class PersonsFile(TJPBase):
    """Komplette persons.json."""
    resource_groups: list[ResourceGroup]

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> PersonsFile:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def all_persons(self) -> list[Person]:
        """Gibt alle Personen über alle Gruppen zurück."""
        return [m for g in self.resource_groups for m in g.members]

    def get_person(self, person_id: str) -> Optional[Person]:
        return next((p for p in self.all_persons() if p.id == person_id), None)

    def get_group(self, group_id: str) -> Optional[ResourceGroup]:
        return next((g for g in self.resource_groups if g.id == group_id), None)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Projekt
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMeta(TJPBase):
    """Projektmetadaten."""
    id:                  str
    name:                str
    version:             str
    start:               str
    duration:            str
    timezone:            str
    timeformat:          str
    currency:            str
    now:                 str
    workinghours_ref:    str  # → WorkingHours.id

    def calculate_cpm(self, tasks: list['Task']) -> dict[str, dict[str, Any]]:
        """
        Berechnet den kritischen Pfad mittels Vorwärts- und Rückwärtsrechnung.

        Args:
            tasks: Liste aller Tasks

        Returns:
            Dictionary mit task_id als Key und CPM-Daten (FB, FE, SB, SE, GP)
        """
        from datetime import datetime, timedelta

        # Baue Abhängigkeiten-Graph auf
        task_dict = {t.id: t for t in tasks}
        cpm_data = {}

        # Initialisiere CPM-Daten
        for task in tasks:
            duration = self._parse_duration(task.duration or task.effort or "0d")
            cpm_data[task.id] = {
                'duration': duration,
                'FB': 0,  # Frühester Beginn
                'FE': 0,  # Frühestes Ende
                'SB': 0,  # Spätester Beginn
                'SE': 0,  # Spätestes Ende
                'GP': 0,  # Gesamtpuffer
            }

        # Vorwärtsrechnung (FB, FE)
        self._forward_pass(tasks, task_dict, cpm_data)

        # Rückwärtsrechnung (SB, SE)
        self._backward_pass(tasks, task_dict, cpm_data)

        # Pufferzeiten berechnen
        for task_id, data in cpm_data.items():
            data['GP'] = data['SB'] - data['FB']

        return cpm_data

    def _parse_duration(self, duration_str: str) -> float:
        """
        Parst Duration-String zu Tagen (float).
        Unterstützt: 10d, 2w, 8h, etc.
        """
        duration_str = duration_str.strip()
        if not duration_str or duration_str == "0":
            return 0.0

        if duration_str.endswith('d'):
            return float(duration_str[:-1])
        elif duration_str.endswith('w'):
            return float(duration_str[:-1]) * 5  # 5 Arbeitstage
        elif duration_str.endswith('h'):
            return float(duration_str[:-1]) / 8  # 8h Arbeitstag
        else:
            # Fallback: versuche als Zahl zu parsen (Tage)
            try:
                return float(duration_str)
            except ValueError:
                return 0.0

    def _forward_pass(self, tasks: list['Task'], task_dict: dict, cpm_data: dict) -> None:
        """Vorwärtsrechnung: Berechnet FAZ und FEZ für alle Tasks."""
        # Topologische Sortierung für korrekte Reihenfolge
        visited = set()
        sorted_tasks = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            task = task_dict.get(task_id)
            if task:
                # Erst alle Abhängigkeiten besuchen
                for dep in task.depends:
                    visit(dep.task_id)
                sorted_tasks.append(task_id)

        for task in tasks:
            visit(task.id)

        # Berechne FB und FE
        for task_id in sorted_tasks:
            task = task_dict[task_id]
            data = cpm_data[task_id]

            # FB ist Maximum aller FE der Vorgänger
            if task.depends:
                max_fe = 0
                for dep in task.depends:
                    pred_data = cpm_data.get(dep.task_id)
                    if pred_data:
                        gap = dep.gap_days() or 0
                        max_fe = max(max_fe, pred_data['FE'] + gap)
                data['FB'] = max_fe
            else:
                data['FB'] = 0

            # FE = FB + Duration
            data['FE'] = data['FB'] + data['duration']

    def _backward_pass(self, tasks: list['Task'], task_dict: dict, cpm_data: dict) -> None:
        """Rückwärtsrechnung: Berechnet SB und SE für alle Tasks."""
        # Finde maximales FE (Projektende)
        max_fe = max(data['FE'] for data in cpm_data.values())

        # Topologische Sortierung rückwärts
        visited = set()
        sorted_tasks = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            sorted_tasks.append(task_id)
            task = task_dict.get(task_id)
            if task:
                # Besuche alle Tasks, die von diesem abhängen
                for other_task in tasks:
                    for dep in other_task.depends:
                        if dep.task_id == task_id:
                            visit(other_task.id)

        # Starte mit Tasks ohne Nachfolger
        tasks_with_successors = set()
        for task in tasks:
            for dep in task.depends:
                tasks_with_successors.add(dep.task_id)

        for task in tasks:
            if task.id not in tasks_with_successors:
                visit(task.id)

        # Initialisiere SE für Tasks ohne Nachfolger
        for task_id in cpm_data:
            if task_id not in tasks_with_successors:
                cpm_data[task_id]['SE'] = cpm_data[task_id]['FE']

        # Berechne SE und SB rückwärts
        for task_id in sorted_tasks:
            task = task_dict[task_id]
            data = cpm_data[task_id]

            # Finde Nachfolger
            successors = []
            for other_task in tasks:
                for dep in other_task.depends:
                    if dep.task_id == task_id:
                        successors.append((other_task.id, dep))

            # SE ist Minimum aller SB der Nachfolger
            if successors:
                min_sb = float('inf')
                for succ_id, dep in successors:
                    succ_data = cpm_data[succ_id]
                    gap = dep.gap_days() or 0
                    min_sb = min(min_sb, succ_data['SB'] - gap)
                data['SE'] = min_sb
            elif 'SE' not in data or data['SE'] == 0:
                # Endknoten: SE = FE
                data['SE'] = data['FE']

            # SB = SE - Duration
            data['SB'] = data['SE'] - data['duration']

    def get_critical_path(self, tasks: list['Task']) -> list[str]:
        """
        Ermittelt den kritischen Pfad.

        Args:
            tasks: Liste aller Tasks

        Returns:
            Liste der Task-IDs auf dem kritischen Pfad
        """
        cpm_data = self.calculate_cpm(tasks)

        # Kritische Tasks haben Gesamtpuffer (GP) = 0
        critical_tasks = [
            task_id for task_id, data in cpm_data.items()
            if abs(data['GP']) < 0.001  # Floating-point Vergleich
        ]

        return critical_tasks


class Account(TJPBase):
    """Buchführungskonto, optional mit Unterkonten."""
    id:       str
    name:     str
    accounts: list[Account] = []

Account.model_rebuild()  # Rekursives Modell


class Balance(TJPBase):
    cost_account: str
    rev_account:  str


class Dependency(TJPBase):
    """Aufgaben-Abhängigkeit mit optionalem Gap/Lead."""
    task_id:     str
    gapduration: Optional[str] = None   # positiv = Gap, negativ = Lead

    def is_lead(self) -> bool:
        return self.gapduration is not None and self.gapduration.startswith("-")

    def gap_days(self) -> Optional[float]:
        """Gibt den Gap-Wert in Tagen zurück (negativ = Lead)."""
        if self.gapduration is None:
            return None
        val = self.gapduration.strip().lstrip("-")
        sign = -1 if self.gapduration.startswith("-") else 1
        if val.endswith("d"):
            return sign * float(val[:-1])
        if val.endswith("w"):
            return sign * float(val[:-1]) * 5  # 5 Arbeitstage pro Woche
        return None


class Charge(TJPBase):
    amount: float
    event:  Literal["onstart", "onend"]


class Task(TJPBase):
    """Projektaufgabe oder Meilenstein, optional mit Unteraufgaben."""
    id:        str
    name:      str
    milestone: bool             = False
    start:     Optional[str]    = None
    depends:   list[Dependency] = []
    effort:    Optional[str]    = None
    duration:  Optional[str]    = None
    allocate:  list[str]        = []    # Person-IDs
    charge:    list[Charge]     = []
    chargeset: list[str]        = []    # Account-IDs
    tasks:     list[Task]       = []    # Unteraufgaben

    # Wird durch TJPRegistry befüllt
    _resolved_persons: list[Person] = []

    @model_validator(mode="after")
    def milestone_has_no_effort(self) -> Task:
        if self.milestone:
            assert not self.effort, \
                f"Meilenstein '{self.id}' darf kein 'effort' haben"
        return self

    @property
    def persons(self) -> list[Person]:
        return self._resolved_persons

    def resolve_persons(self, person_list: list[Person]) -> None:
        self._resolved_persons = person_list

    def all_subtasks(self) -> list[Task]:
        """Gibt rekursiv alle Unteraufgaben zurück."""
        result = []
        for t in self.tasks:
            result.append(t)
            result.extend(t.all_subtasks())
        return result

Task.model_rebuild()


# CPMCalculationMixin und SimpleTaskFile werden aus cpm_models.py importiert


class ProjectFile(TJPBase, CPMCalculationMixin):
    """Komplette project.json."""
    project:  ProjectMeta
    accounts: list[Account] = []
    balance:  Optional[Balance] = None
    tasks:    list[Task]    = []

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> ProjectFile:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def get_account(self, account_id: str) -> Optional[Account]:
        def search(accounts: list[Account]) -> Optional[Account]:
            for a in accounts:
                if a.id == account_id:
                    return a
                found = search(a.accounts)
                if found:
                    return found
            return None
        return search(self.accounts)

    def all_tasks(self) -> list[Task]:
        """Gibt alle Tasks rekursiv zurück."""
        result = []
        for t in self.tasks:
            result.append(t)
            result.extend(t.all_subtasks())
        return result

    def get_task(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.all_tasks() if t.id == task_id), None)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Reports
# ─────────────────────────────────────────────────────────────────────────────

class ReportFilter(TJPBase):
    """Filterbedingung in einem Report."""
    directive:  str           # z.B. "hidetask"
    expression: str           # z.B. "complete == 100"

    def description(self) -> str:
        return f"{self.directive}({self.expression})"


class Report(TJPBase):
    """Ein Report beliebigen Typs."""
    id:         str
    type:       Literal["taskreport", "accountreport", "textreport"]
    name:       str
    headline:   Optional[str]       = None
    header:     Optional[str]       = None
    columns:    list[str]           = []
    timeformat: Optional[str]       = None
    loadunit:   Optional[str]       = None
    hideresource:Optional[int]      = None
    directives: list[str]           = []
    filters:    list[ReportFilter]  = []

    @model_validator(mode="after")
    def textreport_needs_no_columns(self) -> Report:
        if self.type == "textreport" and self.columns:
            raise ValueError(f"textreport '{self.id}' sollte keine columns haben")
        return self

    def active_filters(self) -> list[str]:
        return [f.description() for f in self.filters]


class ReportsFile(TJPBase):
    """Komplette reports.json."""
    reports: list[Report]

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> ReportsFile:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def get_report(self, report_id: str) -> Optional[Report]:
        return next((r for r in self.reports if r.id == report_id), None)

    def by_type(self, report_type: str) -> list[Report]:
        return [r for r in self.reports if r.type == report_type]


# ─────────────────────────────────────────────────────────────────────────────
# Konsolidierte Konfigurationsdatei
# ─────────────────────────────────────────────────────────────────────────────

class ConsolidatedConfigFile(TJPBase):
    """
    Konsolidierte Konfigurationsdatei, die persons, workinghours_absences
    und reports in einer Datei vereint.
    """
    persons: dict                     # enthält resource_groups
    workinghours_absences: dict       # enthält global_workinghours, etc.
    reports: list[Report]

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> ConsolidatedConfigFile:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def to_persons_file(self) -> PersonsFile:
        """Extrahiert PersonsFile aus der konsolidierten Struktur."""
        return PersonsFile.model_validate(self.persons)

    def to_workinghours_file(self) -> WorkingHoursFile:
        """Extrahiert WorkingHoursFile aus der konsolidierten Struktur."""
        return WorkingHoursFile.model_validate(self.workinghours_absences)

    def to_reports_file(self) -> ReportsFile:
        """Extrahiert ReportsFile aus der konsolidierten Struktur."""
        return ReportsFile(reports=self.reports)


# ─────────────────────────────────────────────────────────────────────────────
# 5. TJPRegistry – lädt alles und löst Querverweise auf
# ─────────────────────────────────────────────────────────────────────────────

class TJPRegistry:
    """
    Zentrales Lade- und Verknüpfungs-Objekt.

    Verwendung:
        registry = TJPRegistry.load(
            persons_path    = "persons.json",
            wh_path         = "workinghours_absences.json",
            project_path    = "project.json",
            reports_path    = "reports.json",
        )
        alice  = registry.get_person("alice")
        coding = registry.get_task("coding_phase")
        print(coding.persons)        # → aufgelöste Person-Objekte
        print(alice.workinghours)    # → aufgelöstes WorkingHours-Objekt
    """

    def __init__(
        self,
        persons:  PersonsFile,
        wh:       WorkingHoursFile,
        project:  ProjectFile,
        reports:  ReportsFile,
    ) -> None:
        self.persons  = persons
        self.wh       = wh
        self.project  = project
        self.reports  = reports
        self._resolve_all()

    @classmethod
    def load(
        cls,
        persons_path: Union[str, Path],
        wh_path:      Union[str, Path],
        project_path: Union[str, Path],
        reports_path: Union[str, Path],
    ) -> TJPRegistry:
        return cls(
            persons = PersonsFile.from_json(persons_path),
            wh      = WorkingHoursFile.from_json(wh_path),
            project = ProjectFile.from_json(project_path),
            reports = ReportsFile.from_json(reports_path),
        )

    @classmethod
    def load_consolidated(
        cls,
        config_path: Union[str, Path],
        project_path: Union[str, Path],
    ) -> TJPRegistry:
        """
        Lädt eine konsolidierte Konfigurationsdatei (persons + workinghours + reports)
        zusammen mit einer separaten project.json.

        Args:
            config_path: Pfad zur konsolidierten Config-Datei
            project_path: Pfad zur project.json

        Returns:
            TJPRegistry-Instanz mit allen geladenen Daten
        """
        config = ConsolidatedConfigFile.from_json(config_path)
        return cls(
            persons = config.to_persons_file(),
            wh      = config.to_workinghours_file(),
            project = ProjectFile.from_json(project_path),
            reports = config.to_reports_file(),
        )

    # ── Querverweise auflösen ────────────────────────────────────────────────

    def _resolve_all(self) -> None:
        self._resolve_person_workinghours()
        self._resolve_task_persons()

    def _resolve_person_workinghours(self) -> None:
        """Weist jeder Person ihr WorkingHours-Objekt zu."""
        global_wh = self.wh.global_workinghours
        for person in self.persons.all_persons():
            ref = person.workinghours_override_ref
            if ref:
                override = self.wh.get_override(ref)
                person.resolve_workinghours(override or global_wh)
            else:
                # Gruppen-Override prüfen
                group = next(
                    (g for g in self.persons.resource_groups if person in g.members),
                    None
                )
                if group and group.workinghours_override_ref:
                    override = self.wh.get_override(group.workinghours_override_ref)
                    person.resolve_workinghours(override or global_wh)
                else:
                    person.resolve_workinghours(global_wh)

    def _resolve_task_persons(self) -> None:
        """Weist jedem Task seine Person-Objekte aus allocate[] zu."""
        for task in self.project.all_tasks():
            resolved = [
                p for pid in task.allocate
                if (p := self.persons.get_person(pid)) is not None
            ]
            task.resolve_persons(resolved)

    # ── Convenience-Zugriff ─────────────────────────────────────────────────

    def get_person(self, person_id: str) -> Optional[Person]:
        return self.persons.get_person(person_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.project.get_task(task_id)

    def get_report(self, report_id: str) -> Optional[Report]:
        return self.reports.get_report(report_id)

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.project.get_account(account_id)

    def absences_for(self, person_id: str) -> list[Absence]:
        return self.wh.absences_for(person_id)

    def summary(self) -> str:
        """Gibt eine lesbare Übersicht der geladenen Daten aus."""
        p = self.project.project
        persons = self.persons.all_persons()
        tasks   = self.project.all_tasks()
        lines = [
            f"{'='*55}",
            f"  TJP-Projekt: {p.name} v{p.version}",
            f"  Zeitraum:    {p.start} ({p.duration})",
            f"  Währung:     {p.currency}  |  Zeitzone: {p.timezone}",
            f"{'='*55}",
            f"  Ressourcen:  {len(persons)} Personen in "
            f"{len(self.persons.resource_groups)} Gruppen",
            f"  Aufgaben:    {len(tasks)} (inkl. Unteraufgaben)",
            f"  Reports:     {len(self.reports.reports)}",
            f"  Feiertage:   {len(self.wh.global_leaves)} global",
            f"{'='*55}",
        ]
        for person in persons:
            wh   = person.workinghours
            absc = self.absences_for(person.id)
            wday = wh.hours_per_day("mon") if wh else 0
            lines.append(
                f"  👤 {person.name:<12} ({person.id})"
                f"  {wday:.1f}h/Tag"
                f"  Abwesenheiten: {len(absc)}"
            )
        return "\n".join(lines)
