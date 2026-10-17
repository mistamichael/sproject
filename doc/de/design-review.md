# Design-Review sproject – Vorschläge für eine einfachere Code-Struktur

Stand: 2026-10-16 · Basis: Commit `abb1bba` · Umfang: `lib/` und `gui/` (~15.000 Zeilen Python)

---

## 0. Umsetzungsstand (Branch `refactor/design-review`)

| Punkt | Stand | Anmerkung |
| --- | --- | --- |
| B1–B8 | ✅ behoben | Tests: `tests/test_gui_headless.py`, `tests/test_task_rows.py`, `tests/test_golden.py` |
| S1 Paket/Imports | ✅ | nur relative Imports; einziger Pfad-Eingriff in den Einstiegspunkten `lib/sproject.py` und `gui/app.py` |
| S2 `build_schedule()` | ✅ | `lib/schedule.py` |
| S3 Kalender/Dauern | ✅ (vereinfacht) | `WorkCalendar` für Arbeitstage/Feiertage; `hours_per_day` bewusst als **eine** Config-Konstante in `lib/durations.py`, statt den Kalender durch alle Formatierer zu reichen |
| S4 `Dependency` | ✅ | JSON-Format unverändert |
| S5 CPM | ✅ | `graphlib`, Regel-Tabellen, O(n)-Lookup im Leveling |
| S6 Expansion | ✅ | `expand_project()`; Verweis-Semantik (Instance → letzte Instanz, Loop → erster Zyklus) unverändert übernommen |
| S7 System-Tasks | ✅ (vereinfacht) | zwei Flags `is_break`/`is_blocker` + `is_system` statt `kind`-Literal; `WE-`-Präfix nur noch an einer Stelle |
| S8 Ressourcen | ✅ | eine Klasse `Resource` |
| S9 `utils.py` | ✅ | aufgeteilt in `durations`, `work_calendar`, `colors`, `paths`, `export_config`, `report_data` |
| S10 Exporte | ✅ teilweise | Registry `lib/exporters.py`; Exporter berechnen Kosten weiterhin selbst (billig, gleiche Eingabe); `excel_reports.py` nicht aufgeteilt |
| S11 GUI | ✅ | `ListSection`, `TaskRow`, `result_panel`, i18n |
| S12 Tests | ✅ | alles unter `tests/` (pytest) |

Zusätzlich gefunden und behoben: `eval()` auf Formeln aus der Projektdatei (Code-Ausführung beim Öffnen einer
Datei) → sicherer Rechen-Auswerter; nicht-deterministische Nachfolger-Reihenfolge (`set`); `--start-date`
stürzte ab; GUI-Feld „Zeiteinheit“ überschrieb die Mengeneinheit `unit`; Speichern schrieb Default-Werte
mit (jetzt `exclude_unset`).

Bewusste Ergebnisänderung: Datumswerte in JSON/TXT/Excel überspringen jetzt dieselben Feiertage wie der
Gantt-Kalender (betrifft `hausbau`, `simpleproject`, `tankdesign`; die CPM-Werte sind unverändert).

Fachliche Korrekturen (zweiter Schritt, Tests in `tests/test_semantics.py`):

1. Ruhepausen werden für alle Projekte mit Personen und `resting_times` eingefügt, nicht nur bei Loop-Projekten
   (betrifft `fassadenbau`).
2. Ein Vorgänger eines Instance-Tasks zeigt nach der Expansion auf die **erste** Instanz (vorher die letzte).
3. Endknoten erhalten SEZ = Projektende (Standard-CPM). Vorher galt SEZ = eigenes FEZ, wodurch jeder Endknoten
   fälschlich kritisch war (z. B. `pizzas`: 51 → 15 kritische Tasks). Projektdauer unverändert.
4. `task.cost` ist ein Festpreis: Die Ressourcenstunden des Tasks zählen nicht als Lohn, der Betrag geht als
   „Feste Task-Kosten“ in die Gesamtkosten ein (`0.0` = kostenlos).

---

## 1. Kurzfazit

Die Kernidee ist sauber: Pydantic-Modell → CPM → Exporte, und die GUI arbeitet auf genau
diesem Modell. Über die Zeit sind aber einige Dinge **mehrfach und leicht unterschiedlich**
entstanden: Rechenweg, Kalenderlogik, Zeit-Umrechnung, Export-Aufrufe und die Tabellen-Logik
der GUI. Daraus kommen die meisten Bugs unten.

Die Vorschläge folgen drei Regeln:

1. **Ein Weg pro Aufgabe** (DRY / Single Source of Truth): ein Rechenweg, ein Kalender,
   eine Dauer-Umrechnung.
2. **Klare Schichten**: `lib/` hat keine Kenntnis von GUI oder CLI, GUI und CLI rufen dieselbe
   Fassade auf.
3. **KISS statt Framework**: keine Plugin-Systeme, keine DI-Container. Dataclasses, ein paar
   kleine Klassen, Dictionaries als Registry.

---

## 2. Befunde, die schon heute zu falschen Ergebnissen führen

Diese Punkte sind **Bugs, die aus der Struktur entstehen**. Sie sollten vor bzw. mit dem
Refactoring behoben werden.

| # | Befund | Ort | Folge |
| --- | --- | --- | --- |
| B1 | GUI rechnet **ohne Expansion** von Loop-/Instance-Tasks; die CLI expandiert vorher | [gui/editor.py:329](../../gui/editor.py#L329) vs. [lib/sproject.py:404-416](../../lib/sproject.py#L404-L416) | `erdaushub.json`/`pizzas.json` liefern in der GUI andere (falsche) Dauern als die CLI |
| B2 | `expand_cycles()` gibt ein neues `Project` **nur mit `project`, `project_start`, `tasks`** zurück | [lib/models/project.py:176-180](../../lib/models/project.py#L176-L180) | Ressourcen, Personen, Ruhezeiten gehen verloren → keine Kosten, kein Resource-Leveling |
| B3 | CLI expandiert mit `if … elif` | [lib/sproject.py:409-416](../../lib/sproject.py#L409-L416) | Projekt mit Instance- **und** Loop-Tasks wird nur halb expandiert |
| B4 | GUI-Round-Trip ist **verlustbehaftet**: `tasks_to_rows`/`rows_to_tasks` kennen nur 3 Typen und wenige Felder | [gui/editor.py:88-206](../../gui/editor.py#L88-L206) | Laden + Speichern in der GUI löscht `InstanceTask.instances` (wird zu SimpleTask), `description`, `is_break`, `is_blocker`, `duration_formula`, `required_resources`, `cost`/`resources` von LoopTasks |
| B5 | Inline-Bearbeitung von Ressourcen, Personen und Ruhezeiten wird **nie zurückgelesen** – `_sync_to_model()` liest nur Stammdaten + Tasks | [gui/editor.py:362-403](../../gui/editor.py#L362-L403), Tags `res_{i}_*`, `pers_{i}_*`, `rest_{i}_*` | Änderungen in diesen Tabellen gehen beim Speichern/Berechnen verloren |
| B6 | Stunden pro Arbeitstag an **drei Stellen**: `parse_duration_to_days` fest `8`/`480`, `HOURS_PER_WORKDAY` aus `defaults.cfg`, `cost_calculator.HOURS_PER_DAY = 8.0` | [lib/utils.py:233-318](../../lib/utils.py#L233-L318), [lib/utils.py:77](../../lib/utils.py#L77), [lib/cost_calculator.py:12](../../lib/cost_calculator.py#L12) | Wer `hours_per_day = 7.5` konfiguriert, bekommt inkonsistente Dauern und Kosten |
| B7 | Kalenderlogik dreifach: `add_workdays()` ignoriert Feiertage **und** `skip_weekends`; `GanttCalculator._is_working_day()` beachtet beides; `excel_reports.is_working_day()` nutzt eine eigene Tagesliste | [lib/utils.py:546](../../lib/utils.py#L546), [lib/models/gantt.py:279](../../lib/models/gantt.py#L279), [lib/excel_reports.py:168](../../lib/excel_reports.py#L168) | Datumswerte in JSON/MD/Excel/Gantt können voneinander abweichen |
| B8 | GUI-TXT- und GUI-Excel-Export sind **eigene Implementierungen** (TXT handgeschrieben, Excel nur Gantt-Sheet) statt `lib.txt_export`/`sproject.export_cpm_to_xlsx` | [gui/editor.py:1818-1871](../../gui/editor.py#L1818-L1871) | GUI-Exporte sehen anders aus als CLI-Exporte, fehlende Sheets/Abschnitte |

---

## 3. Strukturvorschläge

### S1 – `lib` als echtes Paket, keine Import-Fallbacks

**Ist:** 30× `try: from ..utils import … except (ImportError, ValueError): from utils import …`,
dazu `sys.path.insert` in 5 Dateien. `lib/sproject.py` importiert absolut (`from models import …`),
die GUI importiert `lib.models`. Von den 128 mypy-Fehlern sind **46 `[no-redef]`**, die nur aus
diesem Muster kommen.

**Soll:**

- `pyproject.toml` mit Paket `sproject` (oder `lib` behalten) und `pip install -e .` im
  `install_py`-Skript.
- Überall nur relative Imports innerhalb des Pakets: `from .utils import …`.
- CLI-Start über `python -m sproject.cli` bzw. einen `[project.scripts]`-Eintrag.
- Alle `sys.path.insert` entfernen.

**Nutzen:** -60 Zeilen Boilerplate, mypy/pyright werden aussagekräftig, eine Import-Art.

---

### S2 – Eine Fassade für den gesamten Rechenweg

**Ist:** Die Reihenfolge *expand → CPM → Gantt → Kosten* steht nur in `sproject.main()`
(und dort mit `elif`). Die GUI ruft nur `calculate_cpm()`. Jeder Exporter ruft
`calculate_project_costs()` erneut selbst auf (4×), JSON berechnet zusätzlich Gantt.

**Soll:** Ein Modul `lib/schedule.py` mit genau einer öffentlichen Funktion:

```python
@dataclass(frozen=True)
class Schedule:
    project: Project            # bereits expandiert
    cpm: CPMResult
    gantt: GanttResult
    costs: CostBreakdown | None
    calendar: WorkCalendar


def build_schedule(project: Project, settings: Settings) -> Schedule:
    expanded = expand(project)                    # S6: alle Typen, verlustfrei
    cpm = CPMCalculator(expanded).calculate()     # rein, ohne Config-I/O
    gantt = GanttCalculator(cpm, settings.calendar).calculate()
    costs = calculate_project_costs(expanded, cpm, settings.calendar)
    return Schedule(expanded, cpm, gantt, costs, settings.calendar)
```

- CLI und GUI rufen **nur** `build_schedule()` → B1, B3 behoben, GUI = CLI.
- `Project.calculate_cpm()` kann als dünner Wrapper bleiben oder entfallen.
- `CPMCalculator.__init__` liest heute selbst `defaults.cfg` und Feiertage – das wandert in
  `Settings` (geladen einmal am Programmstart). Der Calculator wird dadurch eine reine
  Funktion und trivial testbar.

---

### S3 – Ein Kalender- und Zeitmodell (`WorkCalendar`)

**Ist:** Siehe B6/B7. Zusätzlich `_parse_duration_to_minutes` als Kopie in
[lib/models/expander.py:442](../../lib/models/expander.py#L442) (ohne `w`-Einheit),
`HOURS_PER_WORKDAY` wird beim **Import** von `utils.py` aus einer Datei gelesen
(Seiteneffekt beim Import), und [lib/models/calendar.py](../../lib/models/calendar.py)
enthält eine ungenutzte `WorkingHours`-Dataclass.

**Soll:** Eine kleine Klasse, die alle Kalenderfragen beantwortet:

```python
@dataclass(frozen=True)
class WorkCalendar:
    hours_per_day: float = 8.0
    days_per_week: int = 5
    skip_weekends: bool = True
    holidays: frozenset[date] = frozenset()

    def is_working_day(self, d: date) -> bool: ...
    def add_workdays(self, start: datetime, days: float) -> datetime: ...
    def to_days(self, duration: str) -> float: ...        # "40h" -> 5.0
    def to_minutes(self, duration: str) -> float: ...
    def interruption_reason(self, d: date) -> str | None: ...  # 'weekend' | 'holiday'
```

- Ersetzt `parse_duration_to_days`, `parse_duration_to_minutes`, `add_workdays`,
  `count_weekend_days`, `GanttCalculator._is_working_day/_get_interruption_reason`,
  `excel_reports.is_working_day`, `cost_calculator.HOURS_PER_DAY`, `utils.HOURS_PER_WORKDAY`.
- Die Dauer-Parser teilen sich **eine** Tabelle `{'m': 1, 'h': 60, 'd': hpd*60, 'w': dpw*hpd*60}`
  statt vier `if/elif`-Ketten.
- `lib/models/calendar.py` (nur ungenutzte `WorkingHours`) wird durch dieses Modul ersetzt.

**Hinweis Pydantic:** `TaskBase.to_days()` kennt den Kalender nicht. Entweder entfällt die
Methode, oder der Kalender wird übergeben (`task.to_days(cal)`). Keine globale Variable.

---

### S4 – Abhängigkeiten als ein Typ statt vier Listen

**Ist:** `successors`, `successors_aa`, `successors_ee`, `successors_ae` auf `TaskBase`;
in `CPMTaskResult` sogar **10 Listen** (4× successors, 4× predecessors, 2× kombiniert).
Dadurch ist fast jede CPM-Phase viermal fast identisch ausgeschrieben
([lib/models/cpm.py:415-443](../../lib/models/cpm.py#L415-L443), Forward/Backward-Pass),
ebenso `_successors_to_str`/`_str_to_successors` in der GUI und `_parse_successors` in
`task_table.py`.

**Soll:** Intern ein Typ, das JSON-Format bleibt unverändert:

```python
class DepType(StrEnum):
    EA = "EA"; AA = "AA"; EE = "EE"; AE = "AE"

@dataclass(frozen=True)
class Dependency:
    target: TaskId
    type: DepType = DepType.EA
```

- In `TaskBase` eine Property `dependencies -> list[Dependency]`, die aus den vier
  JSON-Feldern gebaut wird (Lesen). Schreiben über eine Hilfsfunktion
  `set_dependencies(task, deps)`. Das JSON-Schema bleibt kompatibel.
- CPM nutzt eine kleine Regel-Tabelle statt vier Schleifen:

```python
# FAZ-Constraint für Nachfolger s aus Vorgänger p
FORWARD = {
    DepType.EA: lambda p, s: p.fez,
    DepType.AA: lambda p, s: p.faz,
    DepType.AE: lambda p, s: p.faz - s.duration,
    DepType.EE: lambda p, s: p.fez - s.duration,
}
```

- `CPMTaskResult` hält nur noch `successors: list[Dependency]` und
  `predecessors: list[Dependency]`. Exporte, die die typisierten Listen brauchen, filtern.
- Ein gemeinsamer Parser/Formatter `"3, 5[AA]" <-> list[Dependency]` in `lib/` statt
  zwei Varianten in der GUI.

**Nutzen:** CPM-Modul geschätzt -150 Zeilen, ein neuer Abhängigkeitstyp (z. B. mit Lag)
ist eine Zeile in der Tabelle statt vier Stellen.

---

### S5 – CPM-Algorithmus verschlanken

| Ist | Soll |
| --- | --- |
| Eigene DFS-Zyklusprüfung (`_validate_no_cycles`, ~55 Zeilen) + eigene rekursive Topo-Sortierung, die bei jedem Pass neu läuft | `graphlib.TopologicalSorter` (Standardbibliothek ab 3.9): sortiert und wirft `CycleError` mit dem Zykluspfad. Einmal sortieren, Ergebnis wiederverwenden |
| `_resource_leveling` sucht für **jeden** CPM-Task linear den Original-Task in `project.tasks` (O(n²) pro Ressource und Iteration) | Einmal `tasks_by_id = {t.id: t for t in project.tasks}` |
| Kapazitätsressourcen werden über `getattr(resource, 'capacity')` und `type in ['machine','oven','truck']` erkannt | Siehe S8: `resource.capacity is not None` reicht |
| `_update_successor_times(task_id, _shift)` – Parameter ungenutzt | Parameter entfernen |
| Kritikalität `abs(puffer) < 0.001` an mehreren Stellen | Konstante `EPS` + Property `is_critical` |
| `WE-`-Präfix als Erkennung für Blocker-Tasks (8 Stellen) | Siehe S7 |

---

### S6 – Expansion: eine Funktion, verlustfrei

**Ist:** `expand_cycles()` und `expand_loops()` sind fast identisch (Mapping bauen →
Nachfolger umbiegen → neues Project), unterscheiden sich nur in `[-1]` vs. `[0]` und darin,
welche Felder in das neue `Project` kopiert werden (→ B2).

**Soll:**

```python
def expand(project: Project) -> Project:
    """Expandiert alle Instance- und Loop-Tasks; alle anderen Felder bleiben erhalten."""
    tasks, mapping = [], {}
    for task in project.tasks:
        parts = expand_task(task, project)    # SimpleTask -> [task]
        tasks.extend(parts)
        mapping[task.id] = parts
    _remap_successors(tasks, mapping)
    if project.persons and project.resting_times:
        tasks = insert_rest_breaks(tasks, project)
    return project.model_copy(update={"tasks": tasks})   # nichts geht verloren
```

- `expand_task` dispatcht über den Typ (`match task: case LoopTask(): …`).
- `_insert_rest_breaks` wandert aus dem Modell in `rest_breaks.py` (dort liegt bereits der
  `PersonWorkTracker`). Die Variable `break_counter` ist ungenutzt.
- Das Pydantic-Modell `Project` enthält danach **nur Daten + Validierung**, keine
  Algorithmen (Single Responsibility).
- Die vier Aliase `SimpleProject = CycleProject = LoopProject = PersonProject = Project`
  nach einer Übergangszeit entfernen; `ProjectBase` mit `Project` zusammenführen
  (es gibt nur eine Unterklasse).

---

### S7 – System-Tasks explizit statt über Magic Strings

**Ist:** Pausen über `is_break`, Wochenend-Blocker über `is_blocker` **und** über den
ID-Präfix `'WE-'` (u. a. [lib/models/cpm.py:609-611](../../lib/models/cpm.py#L609-L611),
`utils.is_system_task`, `to_network_csv`). `getattr(task_result, '_is_blocker', False)` greift
auf ein Feld zu, das es auf `CPMTaskResult` nie gibt.

**Soll:** Ein Feld `kind: Literal["work", "break", "blocker"] = "work"` auf `SimpleTask`
und `CPMTaskResult`. `is_break`/`is_blocker` bleiben als JSON-Eingabe per Validator
kompatibel. Alle Prüfungen werden zu `task.kind != "work"`.

---

### S8 – Ressourcen-Modell vereinfachen

**Ist:**

- 5 Ressourcen-Klassen (`ResourceBase`, `PersonResource`, `MachineResource`,
  `TruckResource`, `OvenResource`), die sich nur in `type` und `capacity` unterscheiden.
- Die Union `Resource` ist nicht diskriminiert; die Reihenfolge entscheidet, welche Klasse
  greift.
- `hourly_rate` und `provisioning_costs` auf Ressourcen werden in `cost_calculator.py`
  per `getattr` gelesen, sind aber **nicht deklariert** (nur über `extra='allow'` vorhanden).
- Die GUI bietet den Typ `"material"` an, den kein Modell kennt.

**Soll (KISS):** Eine Klasse, der Typ ist nur ein Wert:

```python
class Resource(BaseModel):
    id: str
    name: str | None = None
    type: Literal["person", "machine", "truck", "oven", "material"] = "person"
    color: str | None = None
    capacity: float | None = None      # gesetzt => Resource-Leveling aktiv
    count: int | None = None
    unit: str | None = None
    person_id: str | None = None       # nur bei type == "person"
    hourly_rate: float | None = None
    provisioning_costs: float = 0.0
```

- Ein `model_validator` prüft typabhängige Pflichtfelder (z. B. `truck` braucht `capacity`).
- Die GUI liest die Typliste aus dem `Literal` statt aus `_RES_TYPES`.
- `cost_calculator.py` kommt ohne `hasattr`/`getattr` aus (heute 87 solcher Aufrufe in `lib/`,
  die meisten nur, weil die Typen nicht klar sind).

---

### S9 – `utils.py` aufteilen (933 Zeilen Sammelbecken)

`utils.py` enthält heute Farben, Konfiguration, Dauer-Parsing, Datumsrechnung, ID-Erzeugung,
Personen-/Ressourcen-Aufbereitung für Reports und Formatierung. Vorschlag:

| Neu | Inhalt aus `utils.py` |
| --- | --- |
| `calendar.py` | `WorkCalendar` (S3): Dauern, Arbeitstage, Feiertage |
| `formatting.py` | `format_time_value*`, `format_datetime_value`, `format_task_field`, `get_time_unit_label` |
| `colors.py` | `hex_to_rgb`, `rgb_to_hex`, `interpolate_color` (+ die Kopie `_interpolate_palette` aus `task_table.py`) |
| `config.py` | `get_cfg_dir`, `load_labels`, `load_export_config` + `ConfigLoader` |
| `reports/data.py` | `PersonEntry`, `ResourceDetailEntry`, `ResourceData`, `collect_*` |

`generate_cycle_id`/`parse_cycle_id` gehören zu `expander.py`.

---

### S10 – Exporte: eine Signatur, eine Registry

**Ist:**

- Jeder Exporter hat eine eigene Signatur (`result, output_path, project_name, project,
  cfg_dir, lang, gantt_data …`) und lädt seine Config auf eigene Art
  (`_load_txt_config`, `_load_md_config`, `_load_json_config`, `load_excel_export_config`).
- `sproject.main()` hat eine `if/elif`-Kette über 6 Formate mit jeweils eigenem
  `try/except`, `project.project if hasattr(project, 'project') else …` steht 4× darin.
- Kosten werden in jedem Exporter neu berechnet.
- GUI-Exporte sind teilweise eigene Implementierungen (B8).

**Soll:**

```python
# lib/export/__init__.py
Exporter = Callable[[Schedule, Path, ExportOptions], Path]

EXPORTERS: dict[str, Exporter] = {
    "json": json_export.export,
    "txt":  txt_export.export,
    "md":   markdown_export.export_md,
    "html": markdown_export.export_html,
    "xlsx": excel_export.export,
    "zip":  markdown_export.export_svg_zip,
}

def export_all(schedule: Schedule, formats: list[str], out_dir: Path, opts: ExportOptions) -> list[Path]:
    return [EXPORTERS[f](schedule, out_dir, opts) for f in formats]
```

- `ExportOptions` (Dataclass): `lang`, `cfg_dir`, `file_stem`.
- Alle Exporter lesen Kosten, Gantt, Kalender aus dem `Schedule` (S2) – nichts wird doppelt
  berechnet.
- CLI und GUI rufen beide `export_all()` → identische Dateien.
- `export_cpm_to_xlsx` aus `sproject.py` nach `lib/export/excel_export.py` verschieben;
  `excel_reports.py` (1.400 Zeilen) dabei in *Sheets* (`summary`, `tasks`, `gantt`,
  `resources`, `costs`) aufteilen.
- `CPMResult.export_to_dict()` und `to_network_csv()` gehören ebenfalls in die Exporter,
  nicht ins Ergebnis-Modell.

---

### S11 – GUI: `ProjectEditorApp` aufteilen

**Ist:** `editor.py` hat 1.900 Zeilen, eine Klasse mit ~60 Methoden. Für jede Sektion
wiederholt sich dasselbe Muster:

```
_refresh_X()  _cb_add_X()  _confirm_add_X()  _cb_remove_X()
```

für Ressourcen, Personen, Ruhezeiten, Urlaub, Teilzeit (5×), plus Ergebnis-Panel und Exporte.
Inline-Edits werden nicht zurückgelesen (B5).

**Soll:** Ein **generischer Tabellen-Baustein** + schlanke Sektionen.

```python
@dataclass
class Column:
    key: str                  # Feldname im Pydantic-Objekt
    label_key: str            # i18n-Key
    width: int | None = None
    widget: Literal["text", "combo", "float"] = "text"
    items: list[str] | None = None


class ListSection:
    """Bearbeitbare Tabelle für eine Liste von Pydantic-Objekten."""

    def __init__(self, tag: str, columns: list[Column],
                 get_items: Callable[[], list[BaseModel]],
                 new_item: Callable[[dict], BaseModel]): ...

    def build(self, parent: str) -> None: ...      # Tabelle + "Hinzufügen"-Dialog
    def refresh(self) -> None: ...                 # Modell -> Widgets
    def sync(self) -> None: ...                    # Widgets -> Modell  (behebt B5)
```

- `ResourcesSection`, `PersonsSection`, `RestingTimesSection`, `VacationSection`,
  `WorkingHoursSection` werden zu je ~30 Zeilen Spaltenkonfiguration.
- `ProjectEditorApp` behält nur: State (`project`, `dirty`, `schedule`), Datei-Operationen,
  `sync_to_model()` = Schleife über `section.sync()`, `refresh_all()` = Schleife über
  `section.refresh()`.
- `ResultPanel` (heute `_show_result*`, ~270 Zeilen) als eigene Klasse in
  `gui/components/result_panel.py`.
- Datei-/Export-Aktionen nutzen `build_schedule()` und `export_all()` (S2, S10).

**Kleinere GUI-Punkte:**

| Ist | Soll |
| --- | --- |
| Tabellenzeilen als `dict` mit 12 String-Keys (`row_type`, `parent_id`, …) | `@dataclass TaskRow` mit **Referenz auf das Original-Task-Objekt**; beim Zurückschreiben nur editierte Felder per `model_copy(update=…)` ändern → behebt B4 |
| `import dearpygui.dearpygui as dpg` in fast jeder Methode | einmal oben im Modul |
| 10× `except Exception: pass` um DPG-Aufrufe | entfernen bzw. nur `does_item_exist` prüfen – versteckt sonst echte Fehler |
| Statusmeldungen hart auf Deutsch (`"Gespeichert: …"`, `"Kein Projekt geladen."`, `"Keine Ressourcen definiert."`) | `t("status.saved", path=…)` – laut CLAUDE.md Pflicht |
| `get_json_bytes()` schreibt über `tempfile.mktemp` (veraltet, unsicher) in eine Temp-Datei | `project.model_dump_json(by_alias=True, exclude_none=True, indent=2).encode()` |
| `editor.py` importiert private Helfer aus `task_table` (`_build_resource_color_map`, `_interpolate_palette`, `_DEFAULT_PALETTE`) | in `gui/colors.py` öffentlich machen |
| `load_from_file` und `load_from_bytes` sind fast gleich | `load_from_bytes` ruft `_set_project(project, path)` wie `load_from_file` |
| Export-Verzeichnis: `PV_RESULTS` wird in `_get_export_dir` und in `sproject.main` unterschiedlich aufgelöst | eine Funktion `paths.results_dir()` in `lib/config.py` |

---

### S12 – Tests an einem Ort

Testcode liegt heute an drei Stellen: `lib/test_models.py`, `tests/`, `bin/test_examples.py`.
Vorschlag: alles nach `tests/` (pytest), `bin/` enthält gemäß Projekt-Template nur
Umgebungs-Skripte.

Vor dem Refactoring als **Sicherheitsnetz**: Golden-File-Tests über alle Dateien in
`examples/` (JSON-Export vergleichen mit `examples/results/`). Damit ist jedes Refactoring
in S3–S7 gegen unbeabsichtigte Ergebnisänderungen abgesichert. Bewusste Änderungen
(B1, B6, B7) aktualisieren die Golden Files einmal mit Begründung im Commit.

---

## 4. Zielstruktur

```text
lib/                         # Paket (pyproject.toml, pip install -e .)
├── models/
│   ├── tasks.py             # TaskBase, SimpleTask(kind), InstanceTask, LoopTask, SubTask
│   ├── dependencies.py      # DepType, Dependency, Parser/Formatter "3, 5[AA]"
│   ├── resources.py         # Resource (eine Klasse), Person, VacationEntry, RestInterval …
│   ├── project.py           # Project – nur Daten + Validierung
│   └── io.py                # load_project, save_project (heute loader.py)
├── calendar.py              # WorkCalendar
├── config.py                # Settings, ConfigLoader, Pfade (PV_*)
├── expand.py                # expand(), expand_task(), insert_rest_breaks()
├── cpm.py                   # CPMCalculator, CPMResult (rein, ohne I/O)
├── gantt.py                 # GanttCalculator, GanttResult
├── costs.py                 # calculate_project_costs
├── schedule.py              # Schedule, build_schedule()   ← einziger Einstieg
├── formatting.py
├── colors.py
├── export/
│   ├── __init__.py          # EXPORTERS, export_all(), ExportOptions
│   ├── json_export.py
│   ├── txt_export.py
│   ├── markdown_export.py   # md, html, svg-zip
│   ├── mermaid.py
│   ├── report_data.py       # collect_person_entries, collect_resource_data …
│   └── excel/               # summary.py, tasks.py, gantt.py, resources.py, costs.py
└── cli.py                   # argparse → build_schedule → export_all  (heute sproject.py)

gui/
├── app.py                   # Layout, Menüs, Theme
├── editor.py                # ProjectEditorApp: State, Datei-Ops, sync/refresh-Schleifen
├── i18n.py
├── gui_config.py
├── colors.py                # Ressourcen-Farbzuordnung (öffentlich)
└── components/
    ├── list_section.py      # Column, ListSection  (generisch)
    ├── sections.py          # Resources-/Persons-/RestingTimes-/Vacation-/WorkingHoursSection
    ├── task_table.py        # TaskRow-Dataclass + Tabelle
    ├── result_panel.py
    ├── gantt_chart.py
    ├── sidebar.py
    ├── file_browser.py
    └── resource_picker.py
```

---

## 5. Vorgehen in Schritten

Jeder Schritt ist einzeln mergebar und hält das JSON-Format kompatibel.

| Schritt | Inhalt | Aufwand | Risiko |
| --- | --- | --- | --- |
| 0 | Golden-File-Tests über `examples/` (S12) | klein | – |
| 1 | Paket + Imports bereinigen (S1); mypy-Lauf danach neu bewerten | klein | gering |
| 2 | `expand()` verlustfrei + `build_schedule()`; GUI und CLI darauf umstellen (S2, S6) → **B1–B3** | mittel | gering |
| 3 | `WorkCalendar` einführen, Dauer-/Datumsfunktionen ersetzen (S3) → **B6, B7** | mittel | mittel (Ergebnisse ändern sich bewusst) |
| 4 | GUI: `ListSection` + `sync()` je Sektion; `TaskRow` mit Original-Referenz (S11) → **B4, B5** | mittel–groß | mittel |
| 5 | Export-Registry + `ExportOptions`; GUI-Exporte auf `export_all()` (S10) → **B8** | mittel | gering |
| 6 | `Dependency`-Typ, CPM mit Regel-Tabelle und `graphlib` (S4, S5) | mittel | mittel (Golden Files!) |
| 7 | `kind` statt `WE-`/Flags, ein `Resource`-Modell (S7, S8) | klein–mittel | gering |
| 8 | `utils.py` und `excel_reports.py` aufteilen (S9, S10) | mittel | gering (reines Verschieben) |

---

## 6. Was bewusst **nicht** geändert werden sollte

- **Pydantic und Dear PyGui** bleiben – beide passen gut.
- **Funktionsbasierte Exporter** sind in Ordnung; eine Klassenhierarchie `BaseExporter` wäre
  hier mehr Aufwand als Nutzen. Ein Dict als Registry reicht.
- **Kein Event-Bus / MVC-Framework** für die GUI: `sync()`/`refresh()` pro Sektion ist
  einfach und reicht für die Größe der Anwendung.
- **Das JSON-Dateiformat** bleibt unverändert. Neue interne Typen (`Dependency`, `kind`) werden
  per Validator aus den bestehenden Feldern erzeugt.

---

## Anhang: Messwerte (Stand dieses Reviews)

| Metrik | Wert |
| --- | --- |
| Größte Dateien | `gui/editor.py` 1.902 · `lib/excel_reports.py` 1.406 · `lib/utils.py` 933 · `lib/markdown_export.py` 906 · `lib/models/cpm.py` 862 |
| `try/except ImportError`-Fallbacks | 30 |
| `sys.path.insert` | 5 Dateien |
| `hasattr`/`getattr` in `lib/` | 87 |
| `'WE-'`-Prüfungen | 8 |
| mypy (`lib/`) | 128 Fehler, davon 46 `[no-redef]` (Import-Fallbacks) |
| pyright (`lib/`) | 176 Fehler |
| vulture (80 %) | 1 Fund: unbenutzter Import `Set` in `lib/models/calendar.py` |

`make` war in der Review-Umgebung nicht verfügbar; die Tools wurden direkt über `.venv`
aufgerufen (gleiche Parameter wie im Makefile, ohne skylos).
