"""
tjp_models.py
=============
Pydantic-Modelle für die TaskJuggler JSON-Dateien:
  - workinghours_absences.json
  - persons.json
  - project.json
  - reports.json

Legacy-Modelle für alte TJP-basierte Konfigurationsdateien.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

# Import CPM-Klassen aus separatem Modul
from cpm_models import CPMCalculationMixin


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


# ─────────────────────────────────────────────────────────────────────────────
# 2. Personen / Ressourcen
# ─────────────────────────────────────────────────────────────────────────────

class Person(TJPBase):
    """Einzelne Person / Ressource."""
    id:                       str
    name:                     str
    email:                    Optional[str] = None
    workinghours_override_ref:Optional[str] = None

    # Aufgelöste Querverweise
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


# ─────────────────────────────────────────────────────────────────────────────
# 3. Projekt
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMeta(TJPBase):
    """Projektmetadaten."""
    id:                  str
    name:                str
    start:               str
    duration:            str
    timeformat:          str
    now:                 str

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
        Unterstützt: 10d, 2w, 8h, 30m, etc.
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
        elif duration_str.endswith('m'):
            # Minuten: 60m = 1h, 8h = 1 Arbeitstag
            return float(duration_str[:-1]) / (8 * 60)
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



class Account(TJPBase):
    """Buchführungskonto, optional mit Unterkonten."""
    id:       str
    name:     str
    accounts: list[Account] = []

Account.model_rebuild()  # Rekursives Modell


class Dependency(TJPBase):
    """Aufgaben-Abhängigkeit mit optionalem Gap/Lead."""
    task_id:     int | str
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


class Task(TJPBase):
    """Projektaufgabe oder Meilenstein, optional mit Unteraufgaben."""
    id:        int | str
    name:      str
    milestone: bool             = False
    start:     Optional[str]    = None
    depends:   list[Dependency] = []
    effort:    Optional[str]    = None
    duration:  Optional[str]    = None
    tasks:     list[Task]       = []    # Unteraufgaben

    @model_validator(mode="after")
    def milestone_has_no_effort(self) -> Task:
        if self.milestone:
            assert not self.effort, \
                f"Meilenstein '{self.id}' darf kein 'effort' haben"
        return self

    def all_subtasks(self) -> list[Task]:
        """Gibt rekursiv alle Unteraufgaben zurück."""
        result = []
        for t in self.tasks:
            result.append(t)
            result.extend(t.all_subtasks())
        return result

Task.model_rebuild()


# CPMCalculationMixin wird aus cpm_models.py importiert


class ProjectFile(TJPBase, CPMCalculationMixin):
    """Komplette project.json."""
    project:  ProjectMeta
    accounts: list[Account] = []
    tasks:    list[Task]    = []

    def all_tasks(self) -> list[Task]:
        """Gibt alle Tasks rekursiv zurück."""
        result = []
        for t in self.tasks:
            result.append(t)
            result.extend(t.all_subtasks())
        return result



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
    filters:    list[ReportFilter]  = []

    @model_validator(mode="after")
    def textreport_needs_no_columns(self) -> Report:
        if self.type == "textreport" and self.columns:
            raise ValueError(f"textreport '{self.id}' sollte keine columns haben")
        return self


