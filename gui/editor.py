"""
ProjectEditorApp – Zentrale Applikationsklasse (Dear PyGui)
============================================================

Hält das Pydantic-Project-Modell als Single Source of Truth und verbindet
GUI-Events mit lib/. Berechnung und Exporte laufen über dieselben Funktionen
wie die CLI (lib.schedule.build_schedule, lib.exporters).

Datenfluss:
    sync_to_model()  Widgets → Modell   (Stammdaten, Task-Tabelle, Sektionen)
    refresh_all()    Modell  → Widgets
"""

import json
import threading
import webbrowser
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import dearpygui.dearpygui as dpg

from gui.components import result_panel
from gui.components.sections import OptionalSections
from gui.components.sidebar import TOGGLE_TAGS
from gui.components.task_table import rebuild_task_table
from gui.i18n import get_language, t
from gui.task_rows import TaskRow, new_subtask_row, new_task_row, rows_to_tasks, tasks_to_rows
from lib.baseline import create_baseline
from lib.exporters import ExportOptions, export_schedule
from lib.models import Project, load_project, load_project_from_dict, save_project
from lib.paths import get_cfg_dir, get_results_dir, get_work_dir
from lib.charts import build_simulation_figures, write_html
from lib.scenarios import compare_scenarios
from lib.simulation import SimulationResult, has_uncertainty, simulate
from lib.schedule import Schedule, build_schedule

SECTIONS = ("resources", "persons", "resting_times", "uncertainty", "scenarios")

# Report-Formate, die die GUI anbietet (Schlüssel aus lib.exporters.EXPORTERS)
REPORT_FORMATS: Dict[str, str] = {
    "md":   "Markdown",
    "xlsx": "Excel",
    "txt":  "Text",
    "html": "HTML",
    "json": "Netzplan-JSON",
    "plotly": "Charts (HTML)",
    "scenarios": "Szenarien (HTML)",
    "simulation": "Simulation (HTML)",
}

# Stammdaten: Widget-Tag → (Projektfeld, Umwandlung Text → Wert)
_MASTER_FIELDS: Dict[str, tuple] = {
    "inp_project_name":  ("project", str),
    "inp_project_start": ("project_start", str),
    "inp_unit":          ("unit", str),
    "inp_total_volume":  ("total_volume", float),
    "inp_total_hours":   ("total_hours", int),
    "inp_order_volume":  ("order_volume", int),
    "inp_status_date":   ("status_date", str),
}


def _set_value(tag: str, value: Any) -> None:
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)


def _get_value(tag: str) -> str:
    return (dpg.get_value(tag) or "") if dpg.does_item_exist(tag) else ""


class ProjectEditorApp:
    """GUI-State, Datei-Operationen, Berechnung und Exporte."""

    def __init__(self):
        self.project: Optional[Project] = None
        self.task_rows: List[TaskRow] = []
        self.active_sections: Dict[str, bool] = dict.fromkeys(SECTIONS, False)
        self.schedule: Optional[Schedule] = None
        self.scenario_outcomes: list = []
        self.simulation: Optional[SimulationResult] = None
        self._simulation_running = False
        self.sections = OptionalSections(self)
        self._dirty = False
        self._last_save_path: Optional[Path] = None
        # Zählt, wie oft in der GUI ein anderes Projekt geöffnet/angelegt wurde (gui/server_link.py)
        self.project_generation = 0

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._dirty = value
        if value and self.schedule is not None:
            self.schedule = None
            result_panel.hide_result()

    @property
    def last_cpm_result(self):
        return self.schedule.cpm if self.schedule else None

    def _file_stem(self) -> str:
        return ((self.project.project if self.project else "") or "project").replace(" ", "_")

    def _require_project(self) -> Project:
        if self.project is None:
            raise RuntimeError(t("status.no_project"))
        return self.project

    def _set_project(self, project: Project, path: Optional[Path]) -> None:
        self.project_generation += 1
        self.project = project
        self.task_rows = tasks_to_rows(project.tasks)
        self._detect_active_sections()
        self._last_save_path = path
        self.schedule = None
        self._dirty = False
        self.refresh_all()

    # ------------------------------------------------------------------
    # Änderungen vom sproject-Server (gui/server_link.py)
    # ------------------------------------------------------------------

    def apply_external_project(self, project: Project, path: Optional[Path]) -> None:
        """Übernimmt den Projektstand des Servers; eingeblendete Sektionen bleiben sichtbar."""
        shown = dict(self.active_sections)
        self.project = project
        self.task_rows = tasks_to_rows(project.tasks)
        self._detect_active_sections()
        self.active_sections = {k: v or shown.get(k, False) for k, v in self.active_sections.items()}
        if path is not None:
            self._last_save_path = path
        self.refresh_all()
        self.dirty = True
        self._set_status(t("status.server_changed", name=project.project))

    # ------------------------------------------------------------------
    # Datei-Operationen
    # ------------------------------------------------------------------

    def new_project(self) -> None:
        """Neues, leeres Projekt; Speicherort ist $PV_WORK/<datum>-projekt.json."""
        path = get_work_dir() / f"{date.today().isoformat()}-projekt.json"
        self._set_project(Project(project=t("default.project_name"), tasks=[]), path)
        self._set_status(t("status.new_project", name=path.name))

    def load_from_file(self, file_path: Path) -> None:
        try:
            project = load_project(file_path)
            self._set_project(project, file_path)
            self._set_status(t("status.loaded", name=project.project))
        except Exception as e:
            self._set_status(t("status.load_error", error=e))

    def load_from_bytes(self, content: bytes, filename: str = "") -> None:
        try:
            project = load_project_from_dict(json.loads(content.decode("utf-8")))
            self._set_project(project, None)
            self._set_status(t("status.loaded", name=project.project))
        except Exception as e:
            self._set_status(t("status.load_error", error=e))

    def save_to_file(self, file_path: Optional[Path] = None) -> Path:
        """Speichert das Projekt als sproject-JSON."""
        self.sync_to_model()
        file_path = file_path or Path.cwd() / f"{self._file_stem()}.json"
        save_project(self._require_project(), file_path)
        self._last_save_path = file_path
        self._dirty = False
        self._set_status(t("status.saved", path=file_path))
        return file_path

    def save_quick(self) -> None:
        """Speichert ohne Dialog unter dem zuletzt verwendeten Pfad."""
        if self.project is None:
            self._set_status(t("status.no_project"))
            return
        self.save_to_file(self._last_save_path)

    def get_json_bytes(self) -> bytes:
        self.sync_to_model()
        return self._require_project().model_dump_json(by_alias=True, exclude_none=True, exclude_unset=True, indent=2).encode("utf-8")

    # ------------------------------------------------------------------
    # Berechnung
    # ------------------------------------------------------------------

    def run_calculation(self) -> None:
        if self.project is None:
            self._set_status(t("status.no_project"))
            return
        try:
            self.sync_to_model()
            self.schedule = build_schedule(self.project, cfg_dir=get_cfg_dir())
            self.scenario_outcomes = (compare_scenarios(self.project, cfg_dir=get_cfg_dir())
                                      if self.project.scenarios else [])
            self.simulation = None
            result_panel.show_result(self.schedule, self._quick_export_actions(), self.scenario_outcomes)
            self._set_status(t("status.calc_done", duration=self.schedule.cpm.project_duration))
        except Exception as e:
            self._set_status(t("status.calc_error", error=e))

    # ------------------------------------------------------------------
    # Widgets ↔ Modell
    # ------------------------------------------------------------------

    def _read_task_rows_from_ui(self) -> None:
        for i, row in enumerate(self.task_rows):
            for field in ("id", "name", "duration", "successors_str", "cost"):
                tag = f"task_{i}_{field}"
                if dpg.does_item_exist(tag):
                    setattr(row, field, dpg.get_value(tag) or "")

    def sync_to_model(self) -> None:
        """Überträgt alle Eingaben ins Pydantic-Modell."""
        if self.project is None:
            return
        for tag, (field, convert) in _MASTER_FIELDS.items():
            text = _get_value(tag).strip()
            if not text:
                continue
            try:
                setattr(self.project, field, convert(text))
            except ValueError:
                pass
        self._read_task_rows_from_ui()
        # Unsicherheiten stehen in den Task-Objekten der Zeilen – vor dem Neuaufbau übernehmen
        self.sections.uncertainty.sync()
        sources = [row.source for row in self.task_rows if not row.is_subtask]
        self.project.tasks = rows_to_tasks(self.task_rows)
        self.task_rows = tasks_to_rows(self.project.tasks)
        self.sections.retarget_tasks({id(old): new for old, new in zip(sources, self.project.tasks)
                                      if old is not None})
        self.sections.sync()
        # Geplante Dauer kann sich in der Aufgaben-Tabelle geändert haben → Min/Max-Warnung neu prüfen
        self.sections.uncertainty.refresh()

    # Name aus früheren Versionen
    _sync_to_model = sync_to_model

    def refresh_all(self) -> None:
        """Aktualisiert alle Widgets aus dem Modell."""
        if self.project is None:
            return
        for tag, (field, _) in _MASTER_FIELDS.items():
            value = getattr(self.project, field)
            _set_value(tag, "" if value is None else str(value))
        rebuild_task_table(self)
        self.sections.refresh()
        self._update_section_visibility()
        self._update_sidebar()
        result_panel.hide_result()

    def _detect_active_sections(self) -> None:
        p = self._require_project()
        persons = p.persons or []
        self.active_sections = {
            "resources": bool(p.resources),
            "persons": bool(persons),
            "resting_times": bool(p.resting_times)
                             or any(x.vacation or x.workinghours_override for x in persons),
            "uncertainty": any(task.duration_range or task.risk for task in p.tasks),
            "scenarios": bool(p.scenarios),
        }

    def _update_section_visibility(self) -> None:
        for section in SECTIONS:
            if dpg.does_item_exist(f"section_{section}"):
                dpg.configure_item(f"section_{section}", show=self.active_sections[section])

    def _update_sidebar(self) -> None:
        for section, tag in TOGGLE_TAGS.items():
            _set_value(tag, self.active_sections[section])

    def toggle_section(self, section: str) -> None:
        self.active_sections[section] = not self.active_sections.get(section, False)
        self._update_section_visibility()
        self._update_sidebar()

    # ------------------------------------------------------------------
    # Task-Tabelle
    # ------------------------------------------------------------------

    def _rows_changed(self) -> None:
        self.dirty = True
        rebuild_task_table(self)

    def add_task_row(self, is_loop: bool = False) -> None:
        self._read_task_rows_from_ui()
        name = t("task.new_loop") if is_loop else t("task.new")
        self.task_rows.append(new_task_row(self.task_rows, is_loop, name))
        self._rows_changed()

    def delete_task_row(self, row_idx: int) -> None:
        """Löscht eine Zeile – bei Loop-Tasks samt Subtasks."""
        self._read_task_rows_from_ui()
        if row_idx >= len(self.task_rows):
            return
        row = self.task_rows[row_idx]
        self.task_rows = [
            r for i, r in enumerate(self.task_rows)
            if i != row_idx and not (row.is_loop and r.is_subtask and r.parent_id == row.id)
        ]
        self._rows_changed()

    def add_subtask_to_loop(self, loop_row_idx: int) -> None:
        self._read_task_rows_from_ui()
        if loop_row_idx >= len(self.task_rows):
            return
        loop_id = self.task_rows[loop_row_idx].id
        insert_pos = loop_row_idx + 1
        while insert_pos < len(self.task_rows) and self.task_rows[insert_pos].parent_id == loop_id:
            insert_pos += 1
        self.task_rows.insert(insert_pos, new_subtask_row(loop_id, t("task.new_subtask")))
        self._rows_changed()

    # ------------------------------------------------------------------
    # Exporte
    # ------------------------------------------------------------------

    def export_project_json(self, target_dir: Optional[Path] = None) -> Path:
        """Kopie der Projektdatei (Eingabeformat) in target_dir."""
        if self.project is None:
            raise RuntimeError(t("status.no_project"))
        return self.save_to_file((target_dir or Path.cwd()) / f"{self._file_stem()}.json")

    def export_report(self, fmt: str, target_dir: Optional[Path] = None) -> Path:
        """Report im Format fmt (siehe REPORT_FORMATS) – identisch zum CLI-Export."""
        if self.schedule is None:
            raise RuntimeError(t("error.no_result"))
        options = ExportOptions(out_dir=target_dir or get_results_dir(), file_stem=self._file_stem(),
                                cfg_dir=get_cfg_dir(), lang=get_language())
        return export_schedule(self.schedule, [fmt], options)[0]

    def _quick_export_actions(self) -> Dict[str, Callable[[], None]]:
        """Buttons im Ergebnis-Tab: Export nach $PV_RESULTS."""
        def report(fmt: str) -> Callable[[], None]:
            return lambda: self._wrap_export(lambda: self.export_report(fmt))

        actions = {f"↓ {REPORT_FORMATS[fmt]}": report(fmt) for fmt in ("md", "xlsx", "txt")}
        actions["↓ JSON"] = lambda: self._wrap_export(lambda: self.export_project_json(get_results_dir()))
        actions[f"↗ {t('result.open_charts')}"] = self.open_charts_in_browser
        actions[t("result.save_baseline")] = self.save_baseline
        return actions

    # ------------------------------------------------------------------
    # Analyse: Szenarien und Monte-Carlo
    # ------------------------------------------------------------------

    def run_scenarios(self) -> None:
        """Basisplan und Szenarien rechnen, Vergleich im Ergebnis-Tab und im Browser zeigen."""
        if self.project is None:
            self._set_status(t("status.no_project"))
            return
        self.sync_to_model()
        if not self.project.scenarios:
            self._set_status(t("status.no_scenarios"))
            return
        self.run_calculation()
        if self.schedule is not None:
            self._open_in_browser(lambda: self.export_report("scenarios"))

    def run_simulation(self, runs: int, seed: Optional[int] = None) -> None:
        """Monte-Carlo-Simulation im Hintergrund; Ergebnis im Ergebnis-Tab und als HTML im Browser."""
        if self.project is None:
            self._set_status(t("status.no_project"))
            return
        self.sync_to_model()
        if not has_uncertainty(self.project):
            self._set_status(t("status.no_uncertainty"))
            return
        if self._simulation_running:
            return
        self.run_calculation()
        if self.schedule is None:
            return
        project, schedule = self.project, self.schedule
        self._simulation_running = True
        self._set_status(t("status.simulation_running", runs=runs))

        def work() -> None:
            try:
                sim = simulate(project, runs=runs, seed=seed, cfg_dir=get_cfg_dir())
                self.simulation = sim
                path = write_html(build_simulation_figures(sim, schedule.name, get_language()),
                                  get_results_dir() / f"{self._file_stem()}_simulation.html", schedule.name)
                result_panel.show_result(schedule, self._quick_export_actions(), self.scenario_outcomes, sim)
                p80 = sim.date(sim.percentile(80))
                self._set_status(t("status.simulation_done", p80=f"{p80:%Y-%m-%d %H:%M}" if p80 else "–"))
                webbrowser.open(path.resolve().as_uri())
            except Exception as e:
                self._set_status(t("status.calc_error", error=e))
            finally:
                self._simulation_running = False

        threading.Thread(target=work, daemon=True).start()

    def _open_in_browser(self, export: Callable[[], Path]) -> None:
        try:
            path = export()
            webbrowser.open(path.resolve().as_uri())
            self._set_status(t("status.saved", path=path))
        except Exception as e:
            self._set_status(t("status.export_failed", error=e))

    def save_baseline(self) -> None:
        """Aktuellen Plan als Baseline ins Projekt übernehmen (wird mit dem Projekt gespeichert)."""
        if self.schedule is None or self.project is None:
            self._set_status(t("error.no_result"))
            return
        try:
            self.project.baseline = create_baseline(self.schedule)
            self._dirty = True
            self._set_status(t("status.baseline_saved", end=self.project.baseline.project_end))
        except Exception as e:
            self._set_status(t("status.export_failed", error=e))

    def open_charts_in_browser(self) -> None:
        """Interaktive Plotly-Charts erzeugen und im Standardbrowser öffnen."""
        self._open_in_browser(lambda: self.export_report("plotly"))

    def _wrap_export(self, export: Callable[[], Path]) -> None:
        try:
            self._set_status(t("status.saved", path=export()))
        except Exception as e:
            self._set_status(t("status.export_failed", error=e))

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @staticmethod
    def _set_status(msg: str) -> None:
        _set_value("statusbar_text", msg)


