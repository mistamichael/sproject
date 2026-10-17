"""
Optionale Sektionen: Ressourcen, Personen, Ruhezeiten, Urlaub, Teilzeit
=======================================================================

Jede Sektion ist eine ListSection mit Spaltenbeschreibung plus ein
"Hinzufügen"-Dialog. IDs sind nur Anzeige, weil andere Objekte auf sie
verweisen (Tasks → Ressourcen, Ressourcen → Personen).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from gui.colors import next_resource_color, resource_color_map
from gui.components.list_section import (
    Column, FormField, ListSection, float_setter, open_form_dialog, show_error,
)
from gui.i18n import t
from lib.models.resources import (
    RESOURCE_TYPES, Person, Resource, RestInterval, TimeRange, VacationEntry, WorkHoursOverride,
)

_RANGE_SEPARATORS = (" – ", " - ")


# ---------------------------------------------------------------------------
# Zeilen-Adapter für verschachtelte Daten (Urlaub/Teilzeit hängen an Personen)
# ---------------------------------------------------------------------------

@dataclass
class VacationRow:
    person: Person
    entry: VacationEntry


@dataclass
class WorkHoursRow:
    person: Person
    override: WorkHoursOverride


def format_vacation_date(entry: VacationEntry) -> str:
    if entry.date:
        return entry.date
    return f"{entry.from_} – {entry.to or ''}" if entry.from_ else ""


def parse_vacation_date(text: str) -> Dict[str, Optional[str]]:
    """'2026-05-01' → Einzeltag, '2026-05-01 – 2026-05-05' → Zeitraum."""
    for sep in _RANGE_SEPARATORS:
        if sep in text:
            start, end = text.split(sep, 1)
            return {"date": None, "from_": start.strip(), "to": end.strip()}
    return {"date": text.strip(), "from_": None, "to": None}


def parse_time_ranges(text: str) -> List[TimeRange]:
    """'08:00-12:00, 13:00-17:00' → [TimeRange, TimeRange]."""
    ranges = []
    for part in text.split(","):
        if "-" in part:
            start, end = part.split("-", 1)
            ranges.append(TimeRange.model_validate({"from": start.strip(), "to": end.strip()}))
    return ranges


def _split_list(text: str) -> List[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _required(key: str):
    """Setter für Pflicht-Textfelder: leere Eingaben werden ignoriert."""
    def _set(obj, text: str) -> None:
        if text:
            setattr(obj, key, text)
    return _set


def _set_vacation_date(row: VacationRow, text: str) -> None:
    if text:
        for key, value in parse_vacation_date(text).items():
            setattr(row.entry, key, value)


def _set_days(row: WorkHoursRow, text: str) -> None:
    if _split_list(text):
        row.override.days = _split_list(text)


def _set_hours(row: WorkHoursRow, text: str) -> None:
    if parse_time_ranges(text):
        row.override.hours = parse_time_ranges(text)


# ---------------------------------------------------------------------------
# Sektionen
# ---------------------------------------------------------------------------

class OptionalSections:
    """Hält alle optionalen Sektionen eines Editors und verbindet sie mit dessen Projekt."""

    def __init__(self, app):
        self.app = app
        self.resources = ListSection(
            "resources_content", [
                Column("id", "col.id", width=100, editable=False),
                Column("name", "col.name"),
                Column("type", "col.type", width=90, items=RESOURCE_TYPES),
                Column("color", "col.color", width=80),
            ],
            get_rows=lambda: self._project_list("resources"),
            on_remove=lambda i: self._remove("resources", i),
            empty_text="task.no_resources",
            text_color=lambda r: resource_color_map(self.app.project).get(r.id),
        )
        self.persons = ListSection(
            "persons_content", [
                Column("id", "col.id", width=90, editable=False),
                Column("name", "col.name", set=_required("name")),
                Column("role", "col.role", set=_required("role")),
                Column("hourly_rate", "col.rate", width=70, set=float_setter("hourly_rate")),
                Column("info", "col.info", editable=False, get=self._person_info),
            ],
            get_rows=lambda: self._project_list("persons"),
            on_remove=lambda i: self._remove("persons", i),
            empty_text="task.no_persons",
        )
        self.resting_times = ListSection(
            "resting_times_content", [
                Column("after_hours", "col.after_hours", width=90, set=float_setter("after_hours")),
                Column("duration", "col.pause", width=80, set=_required("duration")),
                Column("note", "col.note"),
            ],
            get_rows=lambda: self._project_list("resting_times"),
            on_remove=lambda i: self._remove("resting_times", i),
            empty_text="task.no_resting",
        )
        self.vacation = ListSection(
            "vacation_content", [
                Column("person", "col.person_id", width=100, editable=False, get=lambda r: r.person.id),
                Column("date", "col.date", width=180, get=lambda r: format_vacation_date(r.entry),
                       set=_set_vacation_date),
                Column("description", "col.description", get=lambda r: r.entry.description or "",
                       set=lambda r, v: setattr(r.entry, "description", v)),
            ],
            get_rows=self._vacation_rows,
            on_remove=self._remove_vacation,
            empty_text="list.no_vacation",
        )
        self.workinghours = ListSection(
            "workinghours_content", [
                Column("person", "col.person_id", width=100, editable=False, get=lambda r: r.person.id),
                Column("description", "col.description", get=lambda r: r.override.description or "",
                       set=lambda r, v: setattr(r.override, "description", v)),
                Column("days", "col.days", width=180, get=lambda r: ", ".join(r.override.days),
                       set=_set_days),
                Column("hours", "col.hours", width=150,
                       get=lambda r: ", ".join(f"{h.from_}-{h.to}" for h in r.override.hours),
                       set=_set_hours),
            ],
            get_rows=self._workinghours_rows,
            on_remove=self._remove_workinghours,
            empty_text="list.no_workinghours",
        )
        self.all = [self.resources, self.persons, self.resting_times, self.vacation, self.workinghours]

    # -- gemeinsame Helfer ----------------------------------------------------

    @property
    def project(self):
        return self.app.project

    def _project_list(self, attr: str) -> list:
        return (getattr(self.project, attr) or []) if self.project else []

    def _changed(self) -> None:
        self.app.dirty = True
        self.refresh()

    def _remove(self, attr: str, index: int) -> None:
        self.sync()
        items = self._project_list(attr)
        if 0 <= index < len(items):
            items.pop(index)
            self._changed()

    def refresh(self) -> None:
        for section in self.all:
            section.refresh()

    def sync(self) -> bool:
        """Liest alle Tabellen ins Modell zurück; True wenn sich etwas geändert hat."""
        return any([section.sync() for section in self.all])

    @staticmethod
    def _person_info(person: Person) -> str:
        info = []
        if person.vacation:
            info.append(t("info.vacation", count=len(person.vacation)))
        if person.workinghours_override:
            info.append(t("info.part_time"))
        return ", ".join(info)

    def _vacation_rows(self) -> List[VacationRow]:
        return [VacationRow(p, v) for p in self._project_list("persons") for v in (p.vacation or [])]

    def _workinghours_rows(self) -> List[WorkHoursRow]:
        return [WorkHoursRow(p, p.workinghours_override)
                for p in self._project_list("persons") if p.workinghours_override]

    def _remove_vacation(self, index: int) -> None:
        self.sync()
        rows = self._vacation_rows()
        if 0 <= index < len(rows):
            (rows[index].person.vacation or []).remove(rows[index].entry)
            self._changed()

    def _remove_workinghours(self, index: int) -> None:
        self.sync()
        rows = self._workinghours_rows()
        if 0 <= index < len(rows):
            rows[index].person.workinghours_override = None
            self._changed()

    def _person_ids(self, only_without_override: bool = False) -> List[str]:
        return [p.id for p in self._project_list("persons")
                if not (only_without_override and p.workinghours_override)]

    # -- Hinzufügen-Dialoge ---------------------------------------------------

    def add_resource(self) -> None:
        open_form_dialog("add_resource_dialog", "dlg.add_resource", [
            FormField("id", "col.id", default="R_NEW", no_spaces=True),
            FormField("name", "col.name", hint=t("hint.resource_name")),
            FormField("type", "col.type", default="person", items=RESOURCE_TYPES),
            FormField("color", "col.color", default=next_resource_color(self.project), hint=t("hint.color")),
        ], self._confirm_resource, width=360)

    def _confirm_resource(self, v: Dict[str, str]) -> None:
        if not v.get("id") or not self.project:
            return
        if v["id"] in {r.id for r in self._project_list("resources")}:
            show_error("resources_content", t("error.duplicate_id", id=v["id"]))
            return
        self.sync()
        resource = Resource.model_validate({"id": v["id"], "name": v.get("name") or None,
                                            "type": v.get("type") or "person", "color": v.get("color") or None})
        if resource.type == "person":
            resource.person_id = self._ensure_person_for(resource)
        elif resource.type == "truck":
            resource.capacity = 12
        if self.project.resources is None:
            self.project.resources = []
        self.project.resources.append(resource)
        self._changed()

    def _ensure_person_for(self, resource: Resource) -> str:
        """Legt zur Personen-Ressource eine Person an (falls noch nicht vorhanden)."""
        person_id = resource.id[2:] if resource.id.startswith("R_") else f"P_{resource.id}"
        if self.project.persons is None:
            self.project.persons = []
        if person_id not in self._person_ids():
            self.project.persons.append(Person(
                id=person_id, name=resource.name or t("default.person_name"),
                role=t("default.person_role"), hourly_rate=50.0,
            ))
        return person_id

    def add_person(self) -> None:
        open_form_dialog("add_person_dialog", "dlg.add_person", [
            FormField("id", "col.id", default="PERS1", no_spaces=True),
            FormField("name", "col.name", default=t("default.person_name")),
            FormField("role", "col.role", default=t("default.person_role")),
            FormField("rate", "col.rate", default="50"),
        ], self._confirm_person, width=360)

    def _confirm_person(self, v: Dict[str, str]) -> None:
        if not v.get("id") or not self.project:
            return
        if v["id"] in self._person_ids():
            show_error("persons_content", t("error.duplicate_id", id=v["id"]))
            return
        try:
            rate = float(v.get("rate", ""))
        except ValueError:
            rate = 50.0
        self.sync()
        if self.project.persons is None:
            self.project.persons = []
        self.project.persons.append(Person(
            id=v["id"], name=v.get("name") or t("default.person_name"),
            role=v.get("role") or t("default.person_role"), hourly_rate=rate,
        ))
        self._changed()

    def add_resting_time(self) -> None:
        open_form_dialog("add_resting_time_dialog", "dlg.add_resting_time", [
            FormField("after_hours", "col.after_hours", default="4.5"),
            FormField("duration", "col.pause", default="45m"),
            FormField("note", "col.note"),
        ], self._confirm_resting_time, width=360)

    def _confirm_resting_time(self, v: Dict[str, str]) -> None:
        if not self.project:
            return
        try:
            after_hours = float(v.get("after_hours", ""))
        except ValueError:
            after_hours = 4.5
        self.sync()
        if self.project.resting_times is None:
            self.project.resting_times = []
        self.project.resting_times.append(RestInterval(
            after_hours=after_hours, duration=v.get("duration") or "45m", note=v.get("note") or None,
        ))
        self._changed()

    def add_vacation(self) -> None:
        ids = self._person_ids()
        open_form_dialog("add_vacation_dialog", "dlg.add_vacation", [
            FormField("person_id", "col.person_id", default=ids[0] if ids else "", items=ids),
            FormField("date", "col.date", default="2026-01-01", hint=t("hint.vacation_date")),
            FormField("description", "col.description", hint=t("hint.vacation_desc")),
        ], self._confirm_vacation)

    def _confirm_vacation(self, v: Dict[str, str]) -> None:
        person = next((p for p in self._project_list("persons") if p.id == v.get("person_id")), None)
        if not person or not v.get("date"):
            return
        self.sync()
        entry = VacationEntry(description=v.get("description") or t("default.vacation"),
                              **parse_vacation_date(v["date"]))
        person.vacation = (person.vacation or []) + [entry]
        self._changed()

    def add_workinghours(self) -> None:
        ids = self._person_ids(only_without_override=True)
        open_form_dialog("add_workinghours_dialog", "dlg.add_workinghours", [
            FormField("person_id", "col.person_id", default=ids[0] if ids else "", items=ids),
            FormField("description", "col.description", default=t("default.part_time")),
            FormField("days", "col.days", default="mon, tue, wed, thu, fri",
                      hint="mon, tue, wed, thu, fri, sat, sun"),
            FormField("hours", "col.hours", default="08:00-12:00", hint="08:00-12:00, 13:00-17:00"),
        ], self._confirm_workinghours, width=420)

    def _confirm_workinghours(self, v: Dict[str, str]) -> None:
        person = next((p for p in self._project_list("persons") if p.id == v.get("person_id")), None)
        days, hours = _split_list(v.get("days", "")), parse_time_ranges(v.get("hours", ""))
        if not person or not days or not hours:
            return
        self.sync()
        person.workinghours_override = WorkHoursOverride(
            description=v.get("description") or t("default.part_time"), days=days, hours=hours,
        )
        self._changed()
