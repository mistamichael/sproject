"""
Optionale Sektionen: Ressourcen, Personen, Ruhezeiten, Urlaub, Teilzeit,
Unsicherheiten, Szenarien
=======================================================================

Jede Sektion ist eine ListSection mit Spaltenbeschreibung plus ein
"Hinzufügen"-Dialog. IDs sind nur Anzeige, weil andere Objekte auf sie
verweisen (Tasks → Ressourcen, Ressourcen → Personen).

Unsicherheiten hängen an den Task-Objekten der Aufgaben-Tabelle
(app.task_rows[i].source). Weil sync_to_model() die Tasks neu aufbaut,
hängt der Editor die Zeilen danach mit retarget_tasks() um.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from gui.analysis_rows import (
    TARGETS, ChangeRow, UncertaintyRow, accepts_uncertainty, build_change, change_target,
    format_change, format_percent, format_vacation_date, has_uncertainty, parse_percent,
    parse_range, parse_risk, parse_vacation_date, range_bound, set_change_target, set_change_text,
    set_range, set_risk_delay, set_risk_note, set_risk_probability,
)
from gui.colors import next_resource_color, resource_color_map
from gui.components.list_section import (
    Column, FormField, ListSection, float_setter, open_form_dialog, show_error,
)
from gui.gui_config import load_gui_config
from gui.i18n import t
from lib.simulation import planned_outside_range
from lib.models.resources import (
    RESOURCE_TYPES, Person, Resource, RestInterval, TimeRange, VacationEntry, WorkHoursOverride,
)
from lib.models.scenario import Scenario

_COLORS = load_gui_config().section("colors")


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


def _set_scenario_probability(scenario: Scenario, text: str) -> None:
    try:
        scenario.probability = parse_percent(text)
    except ValueError:
        pass


def _target_label(row: ChangeRow) -> str:
    return t(f"target.{change_target(row.change)[0]}")


def _range_color(row: UncertaintyRow) -> Optional[Tuple[int, int, int]]:
    """Rot, wenn die geplante Dauer außerhalb von Min–Max liegt (die Simulation nimmt dann den Rand)."""
    return tuple(_COLORS.get("error_text", (255, 80, 80))[:3]) if planned_outside_range(row.task) else None


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
                Column("color", "col.color", width=110, color=True),
            ],
            get_rows=lambda: self._project_list("resources"),
            on_remove=lambda i: self._remove("resources", i),
            empty_text="task.no_resources",
            text_color=lambda r: resource_color_map(self.app.project).get(r.id),
            on_change=self._color_picked,
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
        self.uncertainty = ListSection(
            "uncertainty_content", [
                Column("task", "col.task", width=70, editable=False, get=lambda r: str(r.task.id)),
                Column("name", "col.name", editable=False, get=lambda r: r.task.name),
                Column("planned", "col.planned", width=70, editable=False,
                       get=lambda r: r.task.duration or "", text_color=_range_color),
                Column("range_min", "col.range_min", width=70, get=lambda r: range_bound(r.task, 0),
                       set=lambda r, v: set_range(r.task, low=v), text_color=_range_color),
                Column("range_max", "col.range_max", width=70, get=lambda r: range_bound(r.task, 1),
                       set=lambda r, v: set_range(r.task, high=v), text_color=_range_color),
                Column("risk_probability", "col.risk_probability", width=80,
                       get=lambda r: format_percent(r.task.risk.probability) if r.task.risk else "",
                       set=lambda r, v: set_risk_probability(r.task, v)),
                Column("risk_delay", "col.risk_delay", width=90,
                       get=lambda r: r.task.risk.delay if r.task.risk else "",
                       set=lambda r, v: set_risk_delay(r.task, v)),
                Column("risk_note", "col.note",
                       get=lambda r: (r.task.risk.note or "") if r.task.risk else "",
                       set=lambda r, v: set_risk_note(r.task, v)),
            ],
            get_rows=self._uncertainty_rows,
            on_remove=self._remove_uncertainty,
            empty_text="list.no_uncertainty",
            on_double_click=self.edit_uncertainty,
            warning=self._range_warning,
        )
        self.scenarios = ListSection(
            "scenarios_content", [
                Column("name", "col.name", set=_required("name")),
                Column("description", "col.description",
                       set=lambda s, v: setattr(s, "description", v or None)),
                Column("probability", "col.probability", width=90,
                       get=lambda s: format_percent(s.probability), set=_set_scenario_probability),
                Column("changes", "col.changes", width=90, editable=False,
                       get=lambda s: str(len(s.changes))),
            ],
            get_rows=lambda: self._project_list("scenarios"),
            on_remove=lambda i: self._remove("scenarios", i),
            empty_text="list.no_scenarios",
            on_double_click=self.edit_scenario,
        )
        self.scenario_changes = ListSection(
            "scenario_changes_content", [
                Column("scenario", "col.scenario", editable=False, get=lambda r: r.scenario.name),
                Column("target", "col.target", width=80, editable=False, get=_target_label),
                Column("target_id", "col.target_id", width=110, get=lambda r: change_target(r.change)[1],
                       set=lambda r, v: set_change_target(r, v, t("default.absence"))),
                Column("change", "col.change", get=lambda r: format_change(r.change),
                       set=lambda r, v: set_change_text(r, v, t("default.absence"))),
            ],
            get_rows=self._change_rows,
            on_remove=self._remove_change,
            empty_text="list.no_changes",
            on_double_click=self.edit_change,
        )
        self.all = [self.resources, self.persons, self.resting_times, self.vacation, self.workinghours,
                    self.uncertainty, self.scenarios, self.scenario_changes]

    # -- gemeinsame Helfer ----------------------------------------------------

    @property
    def project(self):
        return self.app.project

    def _project_list(self, attr: str) -> list:
        return (getattr(self.project, attr) or []) if self.project else []

    def _changed(self) -> None:
        self.app.dirty = True
        self.refresh()

    def _color_picked(self) -> None:
        """Neue Ressourcenfarbe: alles ins Modell, dann neu aufbauen (Textfarben, Task-Tabelle)."""
        self.app.sync_to_model()
        self.app.dirty = True
        self.app.refresh_all()

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

    def _uncertainty_tasks(self) -> list:
        return [row.source for row in self.app.task_rows
                if not row.is_subtask and accepts_uncertainty(row.source)]

    def _uncertainty_rows(self) -> List[UncertaintyRow]:
        return [UncertaintyRow(task) for task in self._uncertainty_tasks() if has_uncertainty(task)]

    def _range_warning(self) -> Optional[str]:
        ids = [str(row.task.id) for row in self.uncertainty.shown_rows if planned_outside_range(row.task)]
        return t("warn.range_outside", tasks=", ".join(ids)) if ids else None

    def retarget_tasks(self, new_by_old: Dict[int, object]) -> None:
        """Nach dem Neuaufbau der Tasks (sync_to_model): Zeilen auf die neuen Objekte umhängen."""
        for row in self.uncertainty.shown_rows:
            row.task = new_by_old.get(id(row.task), row.task)

    def _remove_uncertainty(self, index: int) -> None:
        self.sync()
        rows = self.uncertainty.shown_rows
        if 0 <= index < len(rows):
            rows[index].task.duration_range = None
            rows[index].task.risk = None
            self._changed()

    def _change_rows(self) -> List[ChangeRow]:
        return [ChangeRow(s, c) for s in self._project_list("scenarios") for c in s.changes]

    def _remove_change(self, index: int) -> None:
        self.sync()
        rows = self._change_rows()
        if 0 <= index < len(rows):
            scenario, change = rows[index].scenario, rows[index].change
            scenario.changes = [c for c in scenario.changes if c is not change]
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

    # -- Unsicherheiten und Szenarien: ein Formular für Hinzufügen und Bearbeiten (Doppelklick) --

    @staticmethod
    def _task_label(task) -> str:
        return f"{task.id}: {task.name}"

    @staticmethod
    def _uncertainty_fields(labels: List[str], task=None) -> List[FormField]:
        risk = task.risk if task is not None else None
        return [
            FormField("task", "col.task", default=labels[0], items=labels),
            FormField("range_min", "col.range_min", default=range_bound(task, 0) if task else "",
                      hint=t("hint.range")),
            FormField("range_max", "col.range_max", default=range_bound(task, 1) if task else "",
                      hint=t("hint.range")),
            FormField("risk_probability", "col.risk_probability",
                      default=format_percent(risk.probability) if risk else "", hint="0–100"),
            FormField("risk_delay", "col.risk_delay", default=risk.delay if risk else "1d"),
            FormField("risk_note", "col.note", default=(risk.note or "") if risk else ""),
        ]

    def add_uncertainty(self) -> None:
        self.app.sync_to_model()   # neue Zeilen der Aufgaben-Tabelle bekommen erst so ein Task-Objekt
        labels = [self._task_label(task) for task in self._uncertainty_tasks() if not has_uncertainty(task)]
        if not labels:
            show_error("uncertainty_content", t("error.no_task_for_uncertainty"))
            return
        open_form_dialog("add_uncertainty_dialog", "dlg.add_uncertainty", self._uncertainty_fields(labels),
                         self._confirm_uncertainty, width=420)

    def _confirm_uncertainty(self, v: Dict[str, str]) -> None:
        task_id = v.get("task", "").split(":", 1)[0]
        task = next((x for x in self._uncertainty_tasks() if str(x.id) == task_id), None)
        if task is not None:
            self._apply_uncertainty(task, v, adding=True)

    def edit_uncertainty(self, index: int) -> None:
        self.sync()
        rows = self.uncertainty.shown_rows
        if not 0 <= index < len(rows):
            return
        task = rows[index].task
        open_form_dialog("edit_uncertainty_dialog", "dlg.edit_uncertainty",
                         self._uncertainty_fields([self._task_label(task)], task),
                         lambda v: self._apply_uncertainty(task, v, adding=False),
                         width=420, confirm_label="button.apply")

    def _apply_uncertainty(self, task, v: Dict[str, str], adding: bool) -> None:
        """Dialogwerte übernehmen; beim Bearbeiten entfernen leere Felder die Unsicherheit."""
        try:
            duration_range = parse_range(task.duration or "", v.get("range_min", ""), v.get("range_max", ""))
            risk = parse_risk(v.get("risk_probability", ""), v.get("risk_delay", ""), v.get("risk_note", ""))
        except ValueError as e:
            show_error("uncertainty_content", t("error.invalid_input", error=e))
            return
        if adding and duration_range is None and risk is None:
            show_error("uncertainty_content", t("error.no_uncertainty_given"))
            return
        self.sync()
        task.duration_range = duration_range
        task.risk = risk
        self._changed()

    @staticmethod
    def _scenario_fields(scenario: Optional[Scenario] = None) -> List[FormField]:
        return [
            FormField("name", "col.name", default=scenario.name if scenario else t("default.scenario_name")),
            FormField("description", "col.description",
                      default=(scenario.description or "") if scenario else ""),
            FormField("probability", "col.probability", hint=t("hint.scenario_probability"),
                      default=format_percent(scenario.probability) if scenario else ""),
        ]

    def add_scenario(self) -> None:
        open_form_dialog("add_scenario_dialog", "dlg.add_scenario", self._scenario_fields(),
                         self._confirm_scenario, width=420)

    def _confirm_scenario(self, v: Dict[str, str]) -> None:
        self._apply_scenario(None, v)

    def edit_scenario(self, index: int) -> None:
        self.sync()
        scenarios = self._project_list("scenarios")
        if not 0 <= index < len(scenarios):
            return
        scenario = scenarios[index]
        open_form_dialog("edit_scenario_dialog", "dlg.edit_scenario", self._scenario_fields(scenario),
                         lambda v: self._apply_scenario(scenario, v), width=420, confirm_label="button.apply")

    def _apply_scenario(self, scenario: Optional[Scenario], v: Dict[str, str]) -> None:
        """scenario None → neu anlegen, sonst die Werte übernehmen."""
        if not v.get("name") or not self.project:
            return
        if v["name"] in {s.name for s in self._project_list("scenarios") if s is not scenario}:
            show_error("scenarios_content", t("error.duplicate_id", id=v["name"]))
            return
        try:
            probability = parse_percent(v.get("probability", ""))
        except ValueError as e:
            show_error("scenarios_content", t("error.invalid_input", error=e))
            return
        self.sync()
        if scenario is None:
            self.project.scenarios = self._project_list("scenarios") + [
                Scenario(name=v["name"], description=v.get("description") or None, probability=probability)]
        else:
            scenario.name = v["name"]
            scenario.description = v.get("description") or None
            scenario.probability = probability
        self._changed()

    @staticmethod
    def _change_fields(names: List[str], row: Optional[ChangeRow] = None) -> List[FormField]:
        kind, target = change_target(row.change) if row else ("task", "")
        return [
            FormField("scenario", "col.scenario", default=row.scenario.name if row else names[-1], items=names),
            FormField("target", "col.target", default=t(f"target.{kind}"),
                      items=[t(f"target.{k}") for k in TARGETS]),
            FormField("target_id", "col.target_id", default=target, hint=t("hint.target_id")),
            FormField("change", "col.change", hint=t("hint.change"),
                      default=format_change(row.change) if row else "duration_factor=1.5"),
        ]

    def add_change(self) -> None:
        names = [s.name for s in self._project_list("scenarios")]
        if not names:
            show_error("scenario_changes_content", t("error.no_scenario"))
            return
        open_form_dialog("add_change_dialog", "dlg.add_change", self._change_fields(names),
                         self._confirm_change, width=520)

    def _confirm_change(self, v: Dict[str, str]) -> None:
        self._apply_change(None, v)

    def edit_change(self, index: int) -> None:
        self.sync()
        rows = self._change_rows()
        if not 0 <= index < len(rows):
            return
        names = [s.name for s in self._project_list("scenarios")]
        row = rows[index]
        open_form_dialog("edit_change_dialog", "dlg.edit_change", self._change_fields(names, row),
                         lambda v: self._apply_change(row, v), width=520, confirm_label="button.apply")

    def _apply_change(self, row: Optional[ChangeRow], v: Dict[str, str]) -> None:
        """row None → neue Änderung, sonst ersetzen (ggf. in ein anderes Szenario verschieben)."""
        scenario = next((s for s in self._project_list("scenarios") if s.name == v.get("scenario")), None)
        kind = next((k for k in TARGETS if t(f"target.{k}") == v.get("target")), None)
        if scenario is None or kind is None:
            return
        try:
            change = build_change(kind, v.get("target_id", ""), v.get("change", ""), t("default.absence"))
        except ValueError as e:
            show_error("scenario_changes_content", t("error.invalid_input", error=e))
            return
        self.sync()
        # Listen neu zuweisen statt in place ändern: das Feld gilt dann als gesetzt (Speichern)
        if row is not None and row.scenario is scenario:
            scenario.changes = [change if c is row.change else c for c in scenario.changes]
        else:
            if row is not None:
                row.scenario.changes = [c for c in row.scenario.changes if c is not row.change]
            scenario.changes = scenario.changes + [change]
        self._changed()
