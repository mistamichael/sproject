"""
Project API
===========

Operationen auf einem Projekt für externe Werkzeuge (MCP-Server, Chatbot,
Skripte) – ohne GUI. Alle Ein- und Ausgaben sind JSON-taugliche dicts/Listen.

    from lib.api import ProjectSession

    s = ProjectSession()
    s.new_project("Garage", project_start="2026-04-01")
    s.add_task({"name": "Fundament", "duration": "3d"})
    s.add_task({"name": "Mauern", "duration": "5d"})
    s.add_dependency(1, 2)
    print(s.calculate()["end"])

Änderungen laufen über das dict des Projekts (exclude_unset) und werden danach
neu validiert: ungültige Eingaben ändern nichts, und save_project() speichert
alle geänderten Felder (keine In-place-Änderungen an Pydantic-Listen).
"""

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from .exporters import EXPORTERS, ExportOptions, export_schedule
from .models import Project, load_project_from_dict, save_project
from .models.dependencies import SUCCESSOR_FIELDS, DepType, parse_task_id
from .paths import get_cfg_dir, get_results_dir
from .report_data import deadline_warning_lines, tracking_summary
from .scenarios import compare_scenarios, comparison_rows
from .schedule import Schedule, build_schedule
from .simulation import simulate, summary_rows, top_critical

TaskId = Union[int, str]
_LIST_FIELDS = ("resources", "persons", "resting_times", "scenarios")


class ApiError(ValueError):
    """Fachlicher Fehler, der dem Aufrufer (z. B. der KI) als Text gemeldet wird."""


def _same_id(a: Any, b: Any) -> bool:
    return str(a) == str(b)


class ProjectSession:
    """
    Hält ein Projekt und bietet kleine, prüfbare Operationen darauf.

    on_change wird nach jeder erfolgreichen Änderung mit dem neuen Projekt
    aufgerufen (z. B. damit die GUI neu zeichnet).
    """

    def __init__(self, project: Optional[Project] = None, path: Optional[Path] = None,
                 cfg_dir: Optional[Path] = None,
                 on_change: Optional[Callable[[Project], None]] = None):
        self.project = project
        self.path = path
        self.cfg_dir = cfg_dir or get_cfg_dir()
        self.on_change = on_change

    # ------------------------------------------------------------------
    # Projekt anlegen, laden, speichern
    # ------------------------------------------------------------------

    def new_project(self, name: str, project_start: Optional[str] = None,
                    unit: Optional[str] = None) -> Dict[str, Any]:
        """Neues, leeres Projekt (ersetzt das aktuelle)."""
        data: Dict[str, Any] = {"project": name, "tasks": []}
        if project_start:
            data["project_start"] = project_start
        if unit:
            data["unit"] = unit
        self.path = None
        self._commit(data)
        return self.overview()

    def load(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Lädt eine Projekt-JSON-Datei."""
        file_path = Path(path)
        if not file_path.exists():
            raise ApiError(f"Datei nicht gefunden: {file_path}")
        self._commit(json.loads(file_path.read_text(encoding="utf-8")))
        self.path = file_path
        return self.overview()

    def save(self, path: Union[str, Path, None] = None) -> str:
        """Speichert als sproject-JSON; ohne Pfad unter dem zuletzt verwendeten."""
        target = Path(path) if path else self.path
        if target is None:
            raise ApiError("Kein Speicherpfad bekannt – bitte einen Pfad angeben")
        save_project(self._require(), target)
        self.path = target
        return str(target)

    def get_project(self) -> Dict[str, Any]:
        """Projekt als JSON-dict (so wie es gespeichert würde)."""
        return self._data()

    def replace_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ersetzt das ganze Projekt durch data (Format wie die JSON-Datei)."""
        self._commit(dict(data))
        return self.overview()

    def patch_project(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setzt Felder auf oberster Ebene (project, project_start, unit, tasks, resources …).
        Der Wert None entfernt ein Feld.
        """
        data = self._data()
        for key, value in fields.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        self._commit(data)
        return self.overview()

    @staticmethod
    def schema() -> Dict[str, Any]:
        """JSON-Schema des Projektformats."""
        return Project.model_json_schema(by_alias=True)

    def overview(self) -> Dict[str, Any]:
        """Kurzfassung: Stammdaten, Tasks (ID, Name, Dauer, Nachfolger), Anzahl Ressourcen/Personen."""
        project = self._require()
        data = self._data()
        info: Dict[str, Any] = {k: data[k] for k in ("project", "project_start", "unit", "total_volume",
                                                     "order_volume", "status_date") if k in data}
        info["tasks"] = self.list_tasks()
        for key in _LIST_FIELDS:
            info[f"{key}_count"] = len(getattr(project, key) or [])
        if self.path:
            info["path"] = str(self.path)
        return info

    # ------------------------------------------------------------------
    # Tasks und Abhängigkeiten
    # ------------------------------------------------------------------

    def list_tasks(self) -> List[Dict[str, Any]]:
        rows = []
        for task in self._require().tasks:
            row: Dict[str, Any] = {"id": task.id, "name": task.name}
            if task.duration:
                row["duration"] = task.duration
            for field in SUCCESSOR_FIELDS.values():
                if getattr(task, field):
                    row[field] = getattr(task, field)
            if task.resources:
                row["resources"] = task.resources
            if getattr(task, "is_loop", False):
                row["is_loop"] = True
            rows.append(row)
        return rows

    def add_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fügt einen Task hinzu. Ohne "id" wird die nächste freie Zahl vergeben.
        Felder wie in der JSON-Datei: name, duration ("3d", "4h", "30m"), successors,
        resources, not_before, deadline, delay, cost, description, subtasks (Loop) …
        """
        data = self._data()
        tasks = list(data.get("tasks", []))
        task = dict(task)
        if "id" not in task or task["id"] in (None, ""):
            task["id"] = self._next_id(t["id"] for t in tasks)
        else:
            task["id"] = parse_task_id(str(task["id"]))
        if any(_same_id(t["id"], task["id"]) for t in tasks):
            raise ApiError(f"Task-ID {task['id']} existiert bereits")
        data["tasks"] = tasks + [task]
        self._commit(data)
        return task

    def update_task(self, task_id: TaskId, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Ändert Felder eines Tasks; None entfernt ein Feld."""
        data = self._data()
        tasks = list(data.get("tasks", []))
        index = self._task_index(tasks, task_id)
        task = dict(tasks[index])
        for key, value in fields.items():
            if key == "id":
                raise ApiError("Die Task-ID kann nicht geändert werden – Task löschen und neu anlegen")
            if value is None:
                task.pop(key, None)
            else:
                task[key] = value
        tasks[index] = task
        data["tasks"] = tasks
        self._commit(data)
        return task

    def remove_task(self, task_id: TaskId) -> List[TaskId]:
        """Löscht einen Task und entfernt ihn aus allen Nachfolgerlisten. Gibt die übrigen IDs zurück."""
        data = self._data()
        tasks = list(data.get("tasks", []))
        del tasks[self._task_index(tasks, task_id)]
        cleaned = []
        for task in tasks:
            task = dict(task)
            for field in SUCCESSOR_FIELDS.values():
                if field in task:
                    task[field] = [s for s in task[field] if not _same_id(s, task_id)]
            cleaned.append(task)
        data["tasks"] = cleaned
        self._commit(data)
        return [t["id"] for t in cleaned]

    def add_dependency(self, predecessor: TaskId, successor: TaskId, dep_type: str = "EA") -> Dict[str, Any]:
        """
        Abhängigkeit predecessor → successor. dep_type: EA (Ende-Anfang, Standard),
        AA (Anfang-Anfang), EE (Ende-Ende), AE (Anfang-Ende).
        """
        try:
            field = SUCCESSOR_FIELDS[DepType(dep_type.upper())]
        except ValueError:
            raise ApiError(f"Unbekannter Abhängigkeitstyp {dep_type!r} (erlaubt: EA, AA, EE, AE)") from None
        if _same_id(predecessor, successor):
            raise ApiError("Ein Task kann nicht von sich selbst abhängen")
        data = self._data()
        tasks = list(data.get("tasks", []))
        self._task_index(tasks, successor)          # Nachfolger muss existieren
        index = self._task_index(tasks, predecessor)
        task = dict(tasks[index])
        targets = list(task.get(field, []))
        if not any(_same_id(s, successor) for s in targets):
            targets.append(parse_task_id(str(successor)))
        task[field] = targets
        tasks[index] = task
        data["tasks"] = tasks
        self._commit(data)
        return task

    def remove_dependency(self, predecessor: TaskId, successor: TaskId) -> Dict[str, Any]:
        """Entfernt alle Abhängigkeiten predecessor → successor (alle Typen)."""
        data = self._data()
        tasks = list(data.get("tasks", []))
        index = self._task_index(tasks, predecessor)
        task = dict(tasks[index])
        for field in SUCCESSOR_FIELDS.values():
            if field in task:
                task[field] = [s for s in task[field] if not _same_id(s, successor)]
        tasks[index] = task
        data["tasks"] = tasks
        self._commit(data)
        return task

    def set_uncertainty(self, task_id: TaskId, duration_range: Optional[List[str]] = None,
                        risk: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Unsicherheit für die Monte-Carlo-Simulation: duration_range = [min, max],
        risk = {"probability": 0.2, "delay": "3d", "note": "..."}. None entfernt den Eintrag.
        """
        return self.update_task(task_id, {"duration_range": duration_range, "risk": risk})

    # ------------------------------------------------------------------
    # Ressourcen, Personen, Ruhezeiten, Szenarien
    # ------------------------------------------------------------------

    def set_list(self, field: str, items: List[Dict[str, Any]]) -> int:
        """Ersetzt resources, persons, resting_times oder scenarios komplett."""
        self._check_list_field(field)
        data = self._data()
        if items:
            data[field] = list(items)
        else:
            data.pop(field, None)
        self._commit(data)
        return len(items)

    def upsert_item(self, field: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fügt eine Ressource/Person (Schlüssel "id") bzw. ein Szenario (Schlüssel "name")
        hinzu oder ersetzt den vorhandenen Eintrag.
        """
        key = self._item_key(field)
        if key not in item:
            raise ApiError(f"{field}: Eintrag braucht das Feld {key!r}")
        data = self._data()
        items = [x for x in data.get(field, []) if not _same_id(x.get(key), item[key])]
        data[field] = items + [dict(item)]
        self._commit(data)
        return item

    def remove_item(self, field: str, key_value: str) -> int:
        """Entfernt eine Ressource/Person (per id) oder ein Szenario (per name)."""
        key = self._item_key(field)
        data = self._data()
        items = data.get(field, [])
        remaining = [x for x in items if not _same_id(x.get(key), key_value)]
        if len(remaining) == len(items):
            raise ApiError(f"{field}: Eintrag {key_value!r} nicht gefunden")
        data[field] = remaining
        self._commit(data)
        return len(remaining)

    # ------------------------------------------------------------------
    # Prüfen und Rechnen
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """Fachliche Prüfung: unbekannte Nachfolger/Ressourcen, Zyklen, Rechenfehler. Leer = in Ordnung."""
        project = self._require()
        issues: List[str] = []
        try:
            expanded = project.expand()
        except Exception as e:
            return [f"Expansion fehlgeschlagen: {e}"]
        ids = {str(t.id) for t in expanded.tasks} | {str(t.id) for t in project.tasks}
        resource_ids = {r.id for r in project.resources or []}
        for task in project.tasks:
            for dep in task.dependencies:
                if str(dep.target) not in ids:
                    issues.append(f"Task {task.id}: unbekannter Nachfolger {dep.target}")
            for rid in task.resources or []:
                if rid not in resource_ids:
                    issues.append(f"Task {task.id}: unbekannte Ressource {rid}")
        person_ids = {p.id for p in project.persons or []}
        for res in project.resources or []:
            if res.person_id and res.person_id not in person_ids:
                issues.append(f"Ressource {res.id}: unbekannte Person {res.person_id}")
        if not issues:
            try:
                self._schedule()
            except Exception as e:
                issues.append(str(e))
        return issues

    def calculate(self, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Berechnet den Plan (Expansion, CPM, Ressourcen, Kalender, Kosten) und gibt eine Kurzfassung zurück."""
        return schedule_summary(self._schedule(start_date))

    def export(self, formats: Iterable[str], out_dir: Union[str, Path, None] = None,
               lang: str = "de") -> List[str]:
        """Exportiert Reports. Formate: siehe lib.exporters.EXPORTERS."""
        formats = [f.strip().lower() for f in formats if f.strip()]
        unknown = [f for f in formats if f not in EXPORTERS]
        if unknown:
            raise ApiError(f"Unbekannte Formate: {', '.join(unknown)}. Erlaubt: {', '.join(EXPORTERS)}")
        options = ExportOptions(out_dir=Path(out_dir) if out_dir else get_results_dir(),
                                file_stem=self._file_stem(), cfg_dir=self.cfg_dir, lang=lang)
        return [str(p) for p in export_schedule(self._schedule(), formats, options)]

    def compare_scenarios(self) -> List[List[str]]:
        """Basisplan gegen alle Szenarien (Tabelle, erste Zeile = Kopf)."""
        return comparison_rows(compare_scenarios(self._require(), cfg_dir=self.cfg_dir))

    def simulate(self, runs: int = 300, seed: Optional[int] = None) -> Dict[str, Any]:
        """Monte-Carlo-Simulation: Kennzahlen und die am häufigsten kritischen Tasks."""
        sim = simulate(self._require(), runs=runs, seed=seed, cfg_dir=self.cfg_dir)
        return {"summary": summary_rows(sim), "top_critical": top_critical(sim)}

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _require(self) -> Project:
        if self.project is None:
            raise ApiError("Kein Projekt geöffnet – zuerst new_project oder load aufrufen")
        return self.project

    def _data(self) -> Dict[str, Any]:
        return self._require().model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)

    def _commit(self, data: Dict[str, Any]) -> None:
        """Validiert data als Projekt und übernimmt es – bei Fehlern bleibt alles unverändert."""
        try:
            project = load_project_from_dict(data)
        except Exception as e:
            raise ApiError(f"Ungültige Projektdaten: {e}") from None
        self.project = project
        if self.on_change:
            self.on_change(project)

    def _schedule(self, start_date: Optional[str] = None) -> Schedule:
        return build_schedule(self._require(), start_date=start_date, cfg_dir=self.cfg_dir)

    def _file_stem(self) -> str:
        if self.path:
            return self.path.stem
        return re.sub(r"[^A-Za-z0-9_-]+", "_", self._require().project).strip("_") or "projekt"

    @staticmethod
    def _task_index(tasks: List[Dict[str, Any]], task_id: TaskId) -> int:
        for i, task in enumerate(tasks):
            if _same_id(task.get("id"), task_id):
                return i
        raise ApiError(f"Task {task_id} nicht gefunden")

    @staticmethod
    def _next_id(ids: Iterable[Any]) -> int:
        numbers = [i for i in ids if isinstance(i, int)]
        return max(numbers, default=0) + 1

    @staticmethod
    def _check_list_field(field: str) -> None:
        if field not in _LIST_FIELDS:
            raise ApiError(f"Unbekannte Liste {field!r} (erlaubt: {', '.join(_LIST_FIELDS)})")

    def _item_key(self, field: str) -> str:
        self._check_list_field(field)
        if field == "resting_times":
            raise ApiError("resting_times haben keine ID – mit set_list komplett setzen")
        return "name" if field == "scenarios" else "id"


def schedule_summary(schedule: Schedule) -> Dict[str, Any]:
    """Kurzfassung eines Rechenlaufs als JSON-taugliches dict."""
    result = schedule.cpm
    has_dates = result.project_start is not None
    fmt = '%Y-%m-%d %H:%M' if result.time_unit != 'days' else '%Y-%m-%d'

    def when(days: float, is_end: bool) -> Optional[str]:
        return result.date_at(days, is_end=is_end).strftime(fmt) if has_dates else None

    tasks = []
    for task_id in sorted(result.tasks, key=lambda x: result.tasks[x].faz):
        task = result.tasks[task_id]
        tasks.append({
            "id": task_id, "name": task.name, "duration_days": round(task.duration, 4),
            "start": when(task.faz, False), "end": when(task.fez, True),
            "slack_days": round(task.puffer, 4), "critical": task.is_critical,
        })
    return {
        "project": schedule.name,
        "time_unit": result.time_unit,
        "start": result.project_start.strftime(fmt) if result.project_start else None,
        "end": when(result.project_end_days, True),
        "duration_days": round(result.project_end_days, 4),
        "critical_path": [{"id": tid, "name": result.tasks[tid].name} for tid in result.critical_path],
        "total_costs": schedule.costs.total_costs if schedule.costs else None,
        "deadline_warnings": deadline_warning_lines(result),
        "tracking": dict(tracking_summary(result)),
        "tasks": tasks,
    }
