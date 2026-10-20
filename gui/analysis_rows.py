"""
Zeilen-Adapter für Unsicherheiten und Szenarien
===============================================

Text ↔ Modell für die Sektionen "Unsicherheiten" (Task.duration_range,
Task.risk) und "Szenarien" (Project.scenarios). Ungültige Eingaben lassen den
alten Wert stehen, wie bei den übrigen Sektionstabellen.

Kein Dear-PyGui-Code – die Umwandlung ist ohne GUI testbar.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from lib.durations import parse_duration_to_days, validate_duration_string
from lib.models.base import TaskBase, TaskRisk
from lib.models.dependencies import parse_task_id
from lib.models.resources import VacationEntry
from lib.models.scenario import Scenario, ScenarioChange
from lib.models.tasks import InstanceTask, SimpleTask

_RANGE_SEPARATORS = (" – ", " - ")

# Ziel einer Szenario-Änderung → Feld mit den Zeiträumen (None = Task-Felder)
TARGETS: Dict[str, Optional[str]] = {"task": None, "resource": "unavailable", "person": "vacation"}

# Task-Felder, deren Text in Szenario-Änderungen keine Zeichenkette ist
_FLOAT_FIELDS = ("duration_factor", "cost")
_LIST_FIELDS = ("resources",)


# ---------------------------------------------------------------------------
# Zeiträume (Urlaub, Ausfallzeiten)
# ---------------------------------------------------------------------------

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


def format_entries(entries: Optional[List[VacationEntry]]) -> str:
    """'2026-03-09 – 2026-03-13 (krank); 2026-04-01'"""
    return "; ".join(format_vacation_date(e) + (f" ({e.description})" if e.description else "")
                     for e in entries or [])


def parse_entries(text: str, default_description: str) -> List[VacationEntry]:
    entries = []
    for part in (p.strip() for p in text.split(";")):
        if not part:
            continue
        description = default_description
        if part.endswith(")") and "(" in part:
            part, description = part[:-1].split("(", 1)
            part, description = part.strip(), description.strip()
        entries.append(VacationEntry(description=description, **parse_vacation_date(part)))
    if not entries:
        raise ValueError("Zeitraum fehlt, z. B. 2026-03-09 – 2026-03-13 (krank)")
    return entries


# ---------------------------------------------------------------------------
# Wahrscheinlichkeiten (Anzeige in Prozent, Modell 0..1)
# ---------------------------------------------------------------------------

def format_percent(probability: Optional[float]) -> str:
    return "" if probability is None else f"{probability * 100:g}"


def parse_percent(text: str) -> Optional[float]:
    """'20', '20 %', '12,5' → 0.2 / 0.2 / 0.125; leer → None. ValueError außerhalb 0–100."""
    text = text.replace("%", "").replace(",", ".").strip()
    if not text:
        return None
    value = float(text)
    if not 0 <= value <= 100:
        raise ValueError(f"Wahrscheinlichkeit {value:g} % liegt nicht zwischen 0 und 100")
    return value / 100


# ---------------------------------------------------------------------------
# Unsicherheiten
# ---------------------------------------------------------------------------

@dataclass
class UncertaintyRow:
    """Eine Zeile je Task. task wird nach jedem Neuaufbau der Tasks umgehängt."""
    task: TaskBase


def accepts_uncertainty(task: Any) -> bool:
    """Loop-Tasks haben keine eigene Dauer – ihre Unsicherheit steckt in den Subtasks/Szenarien."""
    return isinstance(task, (SimpleTask, InstanceTask))


def has_uncertainty(task: TaskBase) -> bool:
    return bool(task.duration_range or task.risk)


def range_bound(task: TaskBase, index: int) -> str:
    return task.duration_range[index] if task.duration_range else ""


def parse_range(planned: str, low: str, high: str) -> Optional[List[str]]:
    """
    Min/Max-Texte → duration_range. Eine leere Grenze ist die geplante Dauer,
    beide leer → None. ValueError bei ungültiger Dauer oder Min > Max.
    """
    low, high = low.strip(), high.strip()
    if not low and not high:
        return None
    low, high = low or planned, high or planned
    for value in (low, high):
        if not validate_duration_string(value):
            raise ValueError(f"Ungültige Dauer '{value}'")
    if parse_duration_to_days(low) > parse_duration_to_days(high):
        raise ValueError("Minimum ist größer als Maximum")
    return [low, high]


def set_range(task: TaskBase, low: Optional[str] = None, high: Optional[str] = None) -> None:
    """Setzt eine Grenze von duration_range, die andere bleibt. Ungültig → unverändert."""
    current = task.duration_range or ["", ""]
    try:
        task.duration_range = parse_range(task.duration or "", current[0] if low is None else low,
                                          current[1] if high is None else high)
    except ValueError:
        pass


def parse_risk(probability: str, delay: str, note: str) -> Optional[TaskRisk]:
    """Dialog-Texte → TaskRisk; leere Wahrscheinlichkeit → kein Risiko. ValueError bei Fehlern."""
    value = parse_percent(probability)
    if value is None:
        return None
    return TaskRisk(probability=value, delay=delay.strip() or "0d", note=note.strip() or None)


def _risk(task: TaskBase) -> TaskRisk:
    if task.risk is None:
        task.risk = TaskRisk(probability=0.0, delay="0d")
    return task.risk


def set_risk_probability(task: TaskBase, text: str) -> None:
    """Prozent; leer entfernt das Risiko."""
    try:
        probability = parse_percent(text)
    except ValueError:
        return
    if probability is None:
        task.risk = None
    else:
        _risk(task).probability = probability


def set_risk_delay(task: TaskBase, text: str) -> None:
    if validate_duration_string(text):
        _risk(task).delay = text


def set_risk_note(task: TaskBase, text: str) -> None:
    if text or task.risk:
        _risk(task).note = text or None


# ---------------------------------------------------------------------------
# Szenario-Änderungen
# ---------------------------------------------------------------------------

@dataclass
class ChangeRow:
    scenario: Scenario
    change: ScenarioChange


def change_target(change: ScenarioChange) -> Tuple[str, str]:
    """→ (Art, ID/Muster), Art ∈ TARGETS"""
    for kind in TARGETS:
        value = getattr(change, kind)
        if value is not None:
            return kind, str(value)
    raise ValueError("Szenario-Änderung ohne Ziel")


def _format_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def format_change(change: ScenarioChange) -> str:
    """Task: 'duration_factor=1.5; deadline=2026-03-27', sonst die Zeiträume."""
    kind, _ = change_target(change)
    entries_field = TARGETS[kind]
    if entries_field:
        return format_entries(getattr(change, entries_field))
    fields = dict(change.task_fields)
    if change.duration_factor is not None:
        fields = {"duration_factor": change.duration_factor, **fields}
    return "; ".join(f"{key}={_format_value(value)}" for key, value in fields.items())


def _parse_task_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    for part in (p.strip() for p in text.split(";")):
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"'{part}': erwartet Feld=Wert, z. B. duration_factor=1.5")
        key, value = (x.strip() for x in part.split("=", 1))
        if key != "duration_factor" and key not in SimpleTask.model_fields:
            raise ValueError(f"Unbekanntes Task-Feld '{key}'")
        if key in _FLOAT_FIELDS:
            fields[key] = float(value.replace(",", "."))
        elif key in _LIST_FIELDS:
            fields[key] = [v.strip() for v in value.split(",") if v.strip()]
        else:
            fields[key] = value
    if not fields:
        raise ValueError("Keine Änderung angegeben, z. B. duration_factor=1.5")
    return fields


def build_change(kind: str, target: str, text: str, default_description: str = "") -> ScenarioChange:
    """Neue Szenario-Änderung aus den Texten der Tabelle bzw. des Dialogs (ValueError bei Fehlern)."""
    if kind not in TARGETS:
        raise ValueError(f"Unbekanntes Ziel '{kind}'")
    target = target.strip()
    if not target:
        raise ValueError("ID bzw. Muster fehlt")
    entries_field = TARGETS[kind]
    if entries_field:
        data: Dict[str, Any] = {kind: target, entries_field: parse_entries(text, default_description)}
    else:
        data = {"task": parse_task_id(target), **_parse_task_fields(text)}
    return ScenarioChange.model_validate(data)


def _replace_change(row: ChangeRow, new: ScenarioChange) -> None:
    # neue Liste zuweisen, damit das Feld als gesetzt gilt (save_project: exclude_unset)
    row.scenario.changes = [new if c is row.change else c for c in row.scenario.changes]
    row.change = new


def set_change_target(row: ChangeRow, text: str, default_description: str = "") -> None:
    kind, _ = change_target(row.change)
    try:
        _replace_change(row, build_change(kind, text, format_change(row.change), default_description))
    except ValueError:
        pass


def set_change_text(row: ChangeRow, text: str, default_description: str = "") -> None:
    kind, target = change_target(row.change)
    try:
        _replace_change(row, build_change(kind, target, text, default_description))
    except ValueError:
        pass
