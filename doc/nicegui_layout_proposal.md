# NiceGUI Layout-Vorschlag – sproject Editor

## Überblick

Die GUI ist ein **Wizard-basierter Einzel-Seiten-Editor** für Projektdaten im sproject-Format.
Das Layout besteht aus einer **linken Sidebar** (Navigation/Wizard-Schritte) und einem
**Hauptbereich** (Formular und Aufgabentabelle).

---

## Komplexitätsstufen der JSON-Dateien

Die vier Stufen bauen aufeinander auf. Die GUI schaltet Bereiche frei, sobald der Nutzer
sie explizit aktiviert:

| Stufe | Aktivierte Felder | Beispieldatei |
|-------|-------------------|---------------|
| **1 – Nur Tasks** | `project`, `project_start`, `tasks[]` (id, name, duration, successors) | `tankdesign.json`, `simpleproject.json` |
| **2 – + Ressourcen/Personen** | + `resources[]`, `persons[]`, `total_hours`, `unit` | `software_simple.json` |
| **3 – + Loops/Subtasks** | + `is_loop`, `loop_until`, `subtasks[]`, `total_volume`, `cycle_prefix` | `erdaushub.json` |
| **4 – + Ruhezeiten** | + `resting_times[]`, `rest_intervals` (Verweis oder direkt) | `erdaushub.json` (voll) |

---

## Gesamtlayout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER: [Logo/Titel "sproject Editor"]   [Datei öffnen]  [Speichern]       │
├──────────────────┬──────────────────────────────────────────────────────────┤
│  SIDEBAR         │  HAUPTBEREICH                                             │
│  (Navigation)    │                                                           │
│                  │  ┌─ Projekt-Stammdaten ──────────────────────────────┐   │
│  ① Stammdaten   │  │ Name: [____________________]  Start: [__________] │   │
│  ② Aufgaben     │  │ Einheit: [days▾]  Volumen: [______]               │   │
│                  │  └───────────────────────────────────────────────────┘   │
│  ─────────────── │                                                           │
│  [grau] Ress.   │  ┌─ Aufgabentabelle ─────────────────────────────────┐   │
│  [grau] Personen│  │  (Herzstück – siehe unten)                        │   │
│  [grau] Ruhezeit│  └───────────────────────────────────────────────────┘   │
│                  │                                                           │
│                  │  [+ Ressourcen aktivieren]  [+ Personen aktivieren]       │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

---

## 1. Linke Sidebar – Wizard-Navigation

Die Sidebar zeigt **5 Abschnitte** in der Reihenfolge, die ein sinnvoller Eingabe-Workflow
erfordert. Die letzten drei Abschnitte sind **ausgegraut** bis der Nutzer sie per Toggle/Button
aktiviert.

```
┌──────────────────────┐
│  📋 WIZARD           │
├──────────────────────┤
│  ① Stammdaten       │  ← immer aktiv, grün markiert wenn befüllt
│  ② Aufgaben         │  ← immer aktiv
│  ─────────────────  │
│  ③ Ressourcen  [+]  │  ← ausgegraut / per Toggle einschaltbar
│  ④ Personen    [+]  │  ← ausgegraut / per Toggle einschaltbar
│  ⑤ Ruhezeiten  [+]  │  ← ausgegraut / nur aktiv wenn ④ aktiv
└──────────────────────┘
```

**Verhalten der Sidebar:**
- Aktiver Schritt wird farblich hervorgehoben (z. B. blauer Akzent)
- Abgeschlossene Schritte erhalten ein grünes Häkchen-Icon
- Ausgegrauete Schritte zeigen ein `+`-Icon; Klick darauf aktiviert den Abschnitt und
  scrollt zum entsprechenden Bereich
- Abschnitt "Ruhezeiten" kann nur aktiviert werden, wenn "Personen" bereits aktiv ist
  (logische Abhängigkeit: `resting_times` werden per `rest_intervals`-Verweis an Personen gebunden)

---

## 2. Bereich ① – Projekt-Stammdaten

Einfaches Formular, immer sichtbar am Kopf des Hauptbereichs.

```
┌─ Projekt-Stammdaten ──────────────────────────────────────────────────────┐
│  Projektname:  [_________________________________]                         │
│  Startdatum:   [YYYY-MM-DD HH:MM:SS___]   Einheit: [ days ▾ ]            │
│                                                                            │
│  [Nur bei Loops aktiv]                                                     │
│  Gesamtvolumen: [________]   Einheit-Label: [m3___]                       │
│  Gesamtstunden: [________]   (für Personen-Projekte)                      │
└────────────────────────────────────────────────────────────────────────────┘
```

**Felder:**
- `project` – Textfeld, Pflichtfeld
- `project_start` – Datetimepicker (Format `YYYY-MM-DD HH:MM:SS`)
- `unit` – Dropdown: `days`, `hours`, `minutes`
- `total_volume` – Zahl, nur sichtbar wenn Loop-Tasks vorhanden
- `total_hours` – Zahl, nur sichtbar wenn Personen aktiv
- `order_volume` – Zahl, nur sichtbar wenn InstanceTasks vorhanden (Zyklus-Modus)

---

## 3. Bereich ② – Aufgabentabelle (Herzstück)

Die Tabelle ist das zentrale Element. Sie zeigt alle Tasks und unterstützt Inline-Bearbeitung.

### Spalten der Tabelle

| Spalte | Breite | Inhalt |
|--------|--------|--------|
| **#** | 50px | Task-ID (int oder string), editierbar |
| **Name** | ~30% | Taskname, editierbar; bei Subtasks eingerückt |
| **Dauer** | 90px | z. B. `10d`, `4h`, `30m` – mit Einheit-Tooltip |
| **Nachfolger** | ~20% | Liste der Abhängigkeiten mit Typ-Auswahl (s.u.) |
| **Ressourcen** | ~15% | Kurzform (IDs), Klick öffnet Ressourcen-Picker |
| **Kosten** | 80px | Optional: direkte Kostenangabe (`cost`-Feld) |
| **Aktionen** | 90px | Icons: Bearbeiten / Löschen / Loop hinzufügen |

### Zeilentypen und visuelle Unterscheidung

```
┌────┬──────────────────────────────┬────────┬────────────────┬──────────────┐
│ #  │ Name                         │ Dauer  │ Nachfolger     │ Ressourcen   │
├────┼──────────────────────────────┼────────┼────────────────┼──────────────┤
│ 1  │ Initialisierung              │ 15m    │ 2 [EA]         │ R_P1, B1, L1 │
├────┼──────────────────────────────┼────────┼────────────────┼──────────────┤
│    │ ████████████████ LOOP-TASK ████████████████████████████████████████  │
│ 2  │ 🔁 Belade-Zyklus            │ –      │ –              │ –            │
│    │   ╰─ • Beladen               │ formel │ –              │ R_P3&B1 …    │
│    │   ╰─ • Transport-Umlauf      │ formel │ –              │ R_P1&L1 …    │
└────┴──────────────────────────────┴────────┴────────────────┴──────────────┘
```

**Loop-Zeilen** (`is_loop: true`):
- Hintergrund: `amber-100` / `bg-amber-50` (NiceGUI: `classes='bg-amber-100'`)
- Icon: 🔁 vor dem Namen
- Zusatzfelder unterhalb der Zeile (aufklappbar): `loop_until`, `cycle_prefix`, `loop_count`,
  `volume_per_cycle`
- Subtasks als **eingerückte Kindzeilen** direkt unter der Loop-Zeile

**Subtask-Zeilen** (Kinder eines LoopTask):
- Einrückung: 32px Abstand links (CSS `pl-8`)
- Gestrichelter linker Rahmen: `border-l-2 border-dashed border-amber-400`
- Kein `id`-Feld sichtbar (wird auto-generiert)
- Spalte "Dauer": zeigt entweder `duration` oder `duration_formula` (Tooltip mit Formel)

**Break-Zeilen** (`is_break: true`) – nur lesend, werden vom System generiert:
- Hintergrund: `gray-100`, kursiver Text, kein Bearbeiten-Button

### Nachfolger-Eingabe mit Typ-Auswahl

Jeder Nachfolger-Eintrag ist ein Chip mit Typ-Dropdown:

```
Nachfolger: [  3 [EA▾]  ×  ]  [  7 [AA▾]  ×  ]  [ + Nachfolger ]
```

- **EA** = Ende-Anfang (Standard, `successors[]`)
- **AA** = Anfang-Anfang (`successors_aa[]`)
- **EE** = Ende-Ende (`successors_ee[]`)
- **AE** = Anfang-Ende (`successors_ae[]`)

Beim Speichern wird der Nachfolger automatisch in die richtige `successors_xx`-Liste
des JSON-Modells geschrieben.

### Ressourcen-Picker

Klick auf die Ressourcen-Zelle öffnet ein **Dialog-Overlay**:

```
┌─ Ressourcen zuweisen ──────────────────────────────────────────────────┐
│  Verfügbare Ressourcen:                                                  │
│                                                                          │
│  [✓] R_PERS1  LKW-Fahrer Max    (person)   ● #5B9BD5                  │
│  [✓] R_PERS2  LKW-Fahrer Heinz  (person)   ● #4472C4                  │
│  [ ] R_PERS3  Baggerführer Bodo (person)   ● #2F5597                  │
│  [✓] B1       Kettenbagger      (machine)  ● #C9A400                  │
│  [ ] L1       LKW 1             (truck)    ● #C19A6B                  │
│                                                                          │
│  Auswahl:  R_PERS1, R_PERS2, B1                [Übernehmen] [Abbrechen]│
└────────────────────────────────────────────────────────────────────────┘
```

- Ressourcen werden mit Farbpunkt (`color`-Feld) angezeigt
- Filter nach Typ: Dropdown `Alle | person | machine | truck | oven`
- In der Tabellenzelle erscheint die Kurzform als komma-getrennte ID-Liste

### Tabellenaktionen

- **Zeile hinzufügen**: Button `+ Aufgabe` unterhalb der Tabelle
- **Loop-Zeile hinzufügen**: Button `+ Loop-Task` (erscheint nur wenn Stufe 3 aktiv)
- **Subtask hinzufügen**: `+`-Icon in der Loop-Zeile
- **Reihenfolge**: Drag-and-Drop via Handle-Icon (erste Spalte)
- **Löschen**: Bestätigungs-Dialog vor dem Löschen

---

## 4. Bereich ③ – Ressourcen (optional)

Wird aktiviert wenn der Nutzer in Sidebar auf `③ Ressourcen [+]` klickt oder
eine Ressource in einer Task-Zeile hinzufügt.

```
┌─ Ressourcen ──────────────────────────────────────────────────────────────┐
│  [ + Ressource hinzufügen ]                                               │
│                                                                            │
│  ID       Name              Typ        Farbe    Kapazität  Stundensatz    │
│  ─────────────────────────────────────────────────────────────────────── │
│  R_PERS1  LKW-Fahrer Max    person  ●  5B9BD5   –          –             │
│  B1       Kettenbagger      machine ●  C9A400   –          140 €/h       │
│  L1       LKW 1             truck   ●  C19A6B   12 m3      120 €/h       │
└────────────────────────────────────────────────────────────────────────────┘
```

- Typ-spezifische Felder erscheinen kontextabhängig:
  - `machine`: `capacity`, `loading_speed_per_min`, `count`, `unit`
  - `truck`: `capacity`, `transport_cycle_fixed`
  - `oven`: `capacity`
  - `person`: `person_id` (Verweis auf Personen-Abschnitt), `role`, `count`
- Farbauswahl per Colorpicker (Hex ohne `#`)

---

## 5. Bereich ④ – Personen (optional)

```
┌─ Personen ────────────────────────────────────────────────────────────────┐
│  [ + Person hinzufügen ]                                                  │
│                                                                            │
│  ▶ DEV1  Alice         Senior Dev    85 €/h   [Urlaub: 1 Eintrag]        │
│  ▶ DEV2  Bob           Junior Dev    55 €/h   [Teilzeit]                 │
│  ▶ DES1  Charlie       UI/UX         70 €/h   [Abwesenheit: 1 Eintrag]   │
└────────────────────────────────────────────────────────────────────────────┘
```

- Aufklappbare Zeilen (Akkordeon) für Details
- Aufgeklappter Bereich zeigt:
  - `email`, `role`, `hourly_rate`
  - `workinghours_override`: Wochentage + Uhrzeitbereiche
  - `vacation`: Liste mit `from`/`to` oder `date` + `description`
  - `rest_intervals`: Dropdown `– keine –` / `resting_times (global)` / `eigene Regeln`

---

## 6. Bereich ⑤ – Ruhezeiten (optional, nur mit Personen)

```
┌─ Ruhezeiten (globale Regeln) ─────────────────────────────────────────────┐
│  [ + Regel hinzufügen ]                                                   │
│                                                                            │
│  Nach  [4.5] h  →  Pause  [45m]  Hinweis: [Lenkzeitunterbrechung …]  [×] │
│  Nach  [6.0] h  →  Pause  [30m]  Hinweis: [Arbeitszeitgesetz …]      [×] │
└────────────────────────────────────────────────────────────────────────────┘
```

- Felder: `after_hours` (Zahl), `duration` (Dauer-String), `note` (optional)
- Personen können im Personen-Bereich auf `resting_times` (global) verweisen oder
  eigene Regeln inline definieren

---

## NiceGUI-Komponenten-Mapping

| UI-Element | NiceGUI-Komponente |
|------------|-------------------|
| Sidebar Navigation | `ui.left_drawer` + `ui.list` mit `ui.item` |
| Akkordeon-Abschnitte | `ui.expansion` |
| Aufgabentabelle | `ui.aggrid` (empfohlen) oder `ui.table` |
| Inline-Bearbeitung | `ui.input`, `ui.select` direkt in Tabellenzeilen |
| Nachfolger-Chips | `ui.chip` + `ui.select` (Typ) |
| Ressourcen-Picker | `ui.dialog` + `ui.checkbox` pro Ressource |
| Farbauswahl | `ui.color_input` |
| Datetimepicker | `ui.input` mit `type='datetime-local'` |
| Drag & Drop Tabelle | `ui.aggrid` mit `rowDragManaged: True` |
| Loop-Hintergrund | `classes='bg-amber-100'` auf `ui.row` / aggrid `rowClassRules` |
| Subtask-Einrückung | `classes='pl-8 border-l-2 border-dashed border-amber-400'` |
| Toggle für opt. Bereiche | `ui.switch` oder `ui.button` in Sidebar |
| Header-Toolbar | `ui.header` mit `ui.button` |

---

## Zustandsmodell (reaktive Daten)

```python
# Zentrales reaktives State-Objekt
project_state = {
    "data": Project,          # Pydantic-Modell direkt
    "active_sections": {      # Welche optionalen Abschnitte sind aktiv?
        "resources": False,
        "persons": False,
        "resting_times": False,
    },
    "selected_task_id": None, # Aktuell bearbeiteter Task
    "dirty": False,           # Ungespeicherte Änderungen
}
```

Änderungen in der GUI aktualisieren `project_state["data"]` direkt.
`ui.refreshable`-Dekoratoren sorgen für reaktive Neudarstellung.

---

## Dateioperationen

- **Öffnen**: `ui.upload` oder Datei-Picker → `json.load` → `Project.model_validate()`
- **Speichern**: `project.model_dump(exclude_none=True)` → `json.dump` → Download-Link
- **Validierung**: Pydantic-Fehler werden als `ui.notify(..., type='negative')` angezeigt

---

## Hinweise zur Implementierung

1. **aggrid ist erste Wahl** für die Aufgabentabelle – unterstützt Inline-Editing,
   RowDrag, RowClassRules (amber für Loops) und Custom Cell Renderers nativ.
2. **Subtasks als separate Zeilen** in aggrid mit `treeData`-Modus oder als
   gruppierte Daten mit `rowGrouping` – alternativ als separates `ui.table` direkt
   unter der Loop-Zeile (in einem aggrid Full-Row-Expand-Panel).
3. **Nachfolger-Typ** wird beim Laden aus den vier `successors_xx`-Listen geflacht
   zu einer einheitlichen Liste `[{id, type}]` und beim Speichern wieder
   in die korrekten Felder aufgeteilt.
4. **Ressourcen-Picker** braucht Zugriff auf `project.resources` – nur definierte
   Resource-IDs sind wählbar.
5. **Stufenweise Freischaltung**: Die GUI prüft beim Laden automatisch welche
   Komplexitätsstufe die JSON-Datei hat und schaltet die Abschnitte entsprechend frei.
6. **`_sync_to_model()` ist der kritische Schritt** vor jedem Speichern und vor jeder
   Berechnung – er übersetzt den aggrid-State (Zeilen-Dicts) zurück in das Pydantic-Modell.

---

## Architektur – Modulstruktur

```
sproject/
├── lib/                   ← vorhandene Bibliothek (unverändert)
│   ├── models/            ← Pydantic-Modelle, CPM-Logik, Exporter
│   │   ├── __init__.py
│   │   ├── project.py     ← Project, calculate_cpm()
│   │   ├── tasks.py
│   │   ├── resources.py
│   │   ├── base.py
│   │   ├── cpm.py
│   │   └── loader.py      ← load_project(), save_project()
│   ├── excel_reports.py
│   ├── markdown_export.py
│   └── gantt.py
│
└── gui/                   ← neue GUI-Schicht (NiceGUI)
    ├── app.py             ← Einstiegspunkt: ui.run()
    ├── editor.py          ← class ProjectEditorApp
    └── components/        ← wiederverwendbare UI-Bausteine
        ├── task_table.py
        ├── resource_picker.py
        └── sidebar.py
```

**Abhängigkeitsrichtung:** `gui/` → `lib/` (einseitig). Die Bibliothek importiert
nichts aus dem GUI-Layer. Kein Code aus `lib/` wird dupliziert oder verändert.

---

## Klasse `ProjectEditorApp`

Die gesamte GUI-Logik ist in einer Klasse gebündelt. Sie hält das Pydantic-Modell
als Single Source of Truth und verbindet GUI-Events mit der Bibliothek.

```python
# gui/editor.py
from pathlib import Path
from nicegui import ui
from lib.models import (
    load_project, load_project_from_dict, save_project,
    Project, CPMResult
)


class ProjectEditorApp:
    """Kapselt den gesamten GUI-State und alle Event-Handler."""

    def __init__(self):
        self.project: Project | None = None
        self.active_sections = {
            "resources": False,
            "persons": False,
            "resting_times": False,
        }
        self.last_cpm_result: CPMResult | None = None
        self.dirty: bool = False

    # ------------------------------------------------------------------
    # Datei-Operationen
    # ------------------------------------------------------------------

    def load_from_file(self, file_path: Path) -> None:
        """Lädt ein Projekt aus einer lokalen Datei (CLI / Entwicklung)."""
        self.project = load_project(file_path)
        self._detect_active_sections()
        self.refresh_all()

    def load_from_upload(self, content: bytes) -> None:
        """Callback für ui.upload – parst den Byte-Inhalt."""
        import json
        data = json.loads(content.decode("utf-8"))
        self.project = load_project_from_dict(data)
        self._detect_active_sections()
        self.refresh_all()

    def write2json(self, file_path: Path | None = None) -> Path:
        """
        Serialisiert den aktuellen GUI-State als sproject-JSON.

        Ablauf:
          1. _sync_to_model()  – aggrid-Rows → Pydantic-Felder aktualisieren
          2. save_project()    – model_dump(by_alias=True, exclude_none=True) + json.dump
          3. Rückgabe des Zielpfads (für Download-Link)

        Args:
            file_path: Zielpfad; wenn None → temporäre Datei in /tmp/

        Returns:
            Absoluter Pfad der geschriebenen JSON-Datei.
        """
        self._sync_to_model()
        if file_path is None:
            import tempfile
            file_path = Path(tempfile.mktemp(suffix=".json"))
        save_project(self.project, file_path)
        self.dirty = False
        return file_path

    # ------------------------------------------------------------------
    # Berechnung
    # ------------------------------------------------------------------

    def run_calculation(self) -> None:
        """
        Führt die CPM-Berechnung aus und zeigt das Ergebnis-Panel.

        Ablauf:
          1. _sync_to_model()
          2. project.calculate_cpm()  – liefert CPMResult
          3. _show_result(result)     – baut das Ergebnis-Panel auf
        """
        if self.project is None:
            ui.notify("Kein Projekt geladen.", type="warning")
            return
        self._sync_to_model()
        try:
            result = self.project.calculate_cpm()
            self.last_cpm_result = result
            self._show_result(result)
        except Exception as e:
            ui.notify(f"Fehler bei der Berechnung: {e}", type="negative")

    # ------------------------------------------------------------------
    # Interne Hilfsmethoden
    # ------------------------------------------------------------------

    def _detect_active_sections(self) -> None:
        """Schaltet optionale Abschnitte basierend auf geladenen Daten frei."""
        if self.project is None:
            return
        self.active_sections["resources"] = bool(self.project.resources)
        self.active_sections["persons"] = bool(self.project.persons)
        self.active_sections["resting_times"] = bool(self.project.resting_times)

    def _sync_to_model(self) -> None:
        """
        KRITISCHER SCHRITT: Überträgt den aktuellen aggrid-State in das
        Pydantic-Modell, bevor gespeichert oder berechnet wird.

        Konkret:
        - Liest Zeilen aus dem aggrid (task_rows)
        - Baut SimpleTask / LoopTask / SubTask-Objekte
        - Verteilt Nachfolger nach Typ in successors / successors_aa / …
        - Aktualisiert self.project.tasks
        - Liest Felder aus Stammdaten-Inputs
        - Aktualisiert self.project.resources und .persons falls aktiv
        """
        # Implementierung greift auf self._task_grid.run_grid_method(...)
        # und self._header_inputs (ui.input-Objekte) zu.
        raise NotImplementedError("In editor.py zu implementieren")

    @ui.refreshable
    def refresh_all(self) -> None:
        """Zeichnet alle refreshable-Komponenten neu (nach Laden/Reset)."""
        pass

    def _show_result(self, result: CPMResult) -> None:
        """
        Baut das Ergebnis-Panel unterhalb der Tabelle auf:
        - CPM-Tabelle: ES / EF / LS / LF / Puffer / krit.
        - Export-Buttons: Markdown, Excel, Gantt SVG, JSON
        """
        pass
```

---

## `write2json` – Datenfluss

```
GUI-State (aggrid rows, ui.input-Werte)
         │
         ▼
  _sync_to_model()
         │  übersetzt Zeilen-Dicts → Pydantic-Objekte
         │  verteilt Nachfolger-Typen in successors / successors_aa / …
         ▼
  self.project  (Pydantic-Modell, vollständig aktuell)
         │
         ▼
  save_project(project, file_path)          ← aus lib/models/loader.py
         │  model_dump(by_alias=True, exclude_none=True)
         │  behandelt "from_" → "from" Alias automatisch
         ▼
  output.json   (sproject-konformes JSON)
```

---

## Header – „Berechnen & Anzeigen"-Button

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  sproject Editor  │  [📂 Öffnen]  [▾ Speichern]  [▶ Berechnen & Anzeigen]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Speichern-Dropdown** (gesplitteter Button):

- `Speichern als JSON` → `write2json()` + `ui.download`
- `Kopie exportieren...` → Dateiname-Dialog → `write2json(custom_path)`

**Berechnen & Anzeigen**:

- Ruft `app.run_calculation()` auf
- Bei Erfolg: Ergebnis-Panel erscheint unterhalb der Aufgabentabelle (kein
  separates Fenster – bleibt im Scroll-Kontext der Seite)
- Bei Fehler: `ui.notify(..., type='negative')` mit Pydantic-Fehlermeldung

NiceGUI-Umsetzung:

```python
with ui.header().classes("items-center gap-4"):
    ui.label("sproject Editor").classes("text-lg font-bold")
    ui.space()
    ui.button("📂 Öffnen", on_click=open_dialog.open)
    with ui.button_group():
        ui.button("💾 Speichern", on_click=lambda: _save_and_download())
        ui.button("▾").props("flat").on("click", save_menu.open)
    ui.button(
        "▶ Berechnen & Anzeigen",
        on_click=app.run_calculation,
    ).props("color=primary")
```

---

## Ergebnis-Panel (nach Berechnung)

```text
┌─ CPM-Ergebnis ────────────────────────────────────────────────────────────┐
│  Gesamtdauer: 47 Arbeitstage   Projektende: 2026-05-12                    │
│                                                                            │
│  #   Name                    ES      EF      LS      LF    Puffer  Krit.  │
│  ──────────────────────────────────────────────────────────────────────── │
│  1   Initialisierung         0       15m     0       15m   0       ★      │
│  2   Belade-Zyklus           15m     –       …       …     …       ★      │
│  3   …                       …       …       …       …     2d             │
│                                                                            │
│  [↓ Markdown]  [↓ Excel]  [↓ Gantt SVG]  [↓ JSON speichern]              │
└────────────────────────────────────────────────────────────────────────────┘
```

**Export-Buttons** verwenden die bestehenden Exporter aus `lib/`:

| Button | Aufruf |
| --- | --- |
| `↓ Markdown` | `from lib.markdown_export import ...` |
| `↓ Excel` | `from lib.excel_reports import ...` |
| `↓ Gantt SVG` | `from lib.models.gantt import ...` |
| `↓ JSON` | `app.write2json()` + `ui.download(...)` |

Kritische Tasks (`slack == 0`) werden in der Tabelle **rot** hervorgehoben
(`classes='text-red-600 font-bold'`).
