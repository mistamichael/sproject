# CLAUDE.md – Projektanweisungen für Claude Code

## Projektübersicht

**sproject** ist ein Projektplanungstool mit CPM-Berechnung (Critical Path Method).
Projekte werden als JSON-Dateien gespeichert und können über eine GUI oder CLI bearbeitet werden.

## Projektstruktur

```text
sproject/
├── bin/              # Start-Skripte (.bat/.sh): setenv, install_py, activate_venv, gui
├── cfg/              # Konfiguration: gui.cfg, defaults.cfg, themes/
├── doc/              # Dokumentation
├── examples/         # Beispiel-JSON-Projektdateien
├── gui/              # Dear PyGui GUI-Anwendung
│   ├── app.py        # Hauptlayout, Menüs, Toolbar, Viewport-Aufbau
│   ├── editor.py     # ProjectEditorApp – zentraler State + Event-Handler
│   ├── i18n.py       # Internationalisierung (de/en), t()-Funktion
│   ├── gui_config.py # Konfigurationslader (gui.cfg → Farben, Größen, Themes)
│   └── components/   # UI-Komponenten
│       ├── sidebar.py      # Wizard-Navigation + Beispielliste
│       ├── task_table.py   # Aufgaben-Tabelle mit Zeilen-Management
│       ├── file_browser.py # Datei-Öffnen-Dialog
│       └── icon_font.py    # Icon-Rendering
├── lib/              # Kernlogik (kein GUI-Code)
│   ├── models/       # Pydantic-Modelle: Project, Tasks, Resources, CPMResult
│   ├── cpm.py        # CPM-Algorithmus
│   ├── markdown_export.py
│   └── excel_reports.py
├── results/          # Export-Ausgaben (in .gitignore)
├── tests/            # Tests
└── work/             # Arbeitsdateien, Default-Speicherort für neue Projekte (PV_WORK)
```

- Quellcode: `lib/` (Kernlogik), `gui/` (GUI-Schicht)
- Sprache: Python
- GUI-Framework: **Dear PyGui** (dearpygui)
- Datenmodelle: **Pydantic** (BaseModel)

## Architektur

### Datenfluss

1. **JSON-Datei** → `lib.models.load_project()` → **Pydantic `Project`-Modell**
2. **GUI** liest/schreibt über `ProjectEditorApp` (Single Source of Truth = `self.project`)
3. **UI → Modell:** `_sync_to_model()` liest DPG-Widgets → aktualisiert Pydantic-Objekt
4. **Modell → UI:** `refresh_all()` aktualisiert alle DPG-Widgets aus dem Pydantic-Objekt
5. **Berechnung:** `project.calculate_cpm()` → `CPMResult`
6. **Export:** JSON, Markdown, Excel (.xlsx), TXT

### GUI-Layout (Dear PyGui)

```text
Viewport
├── Menüleiste (Datei, Einstellungen, Hilfe)
├── Icon-Toolbar (Öffnen, Speichern, Speichern unter, Export, Berechnen)
├── Statuszeile
└── Hauptbereich (2-spaltig)
    ├── Links: Sidebar (Wizard-Navigation + Beispieldateien)
    └── Rechts: Inhaltsbereiche
        ├── 1. Stammdaten (Projektname, Start, Einheit, etc.)
        ├── 2. Aufgaben-Tabelle (SimpleTask, LoopTask, SubTask)
        ├── 3. Ressourcen (optional, togglebar)
        ├── 4. Personen (optional, togglebar)
        ├── 5. Ruhezeiten/Urlaub/Teilzeit (optional, togglebar)
        └── Ergebnis-Panel (nach Berechnung)
```

### Umgebungsvariablen (gesetzt durch `bin/setenv.*`)

| Variable             | Pfad                | Verwendung                        |
|----------------------|---------------------|-----------------------------------|
| `PROJECT`            | Projekt-Root        | Basispfad                         |
| `PV_BIN`             | `bin/`              | Skripte                           |
| `PV_LIB`             | `lib/`              | PYTHONPATH                        |
| `PV_CFG`             | `cfg/`              | GUI-Konfiguration laden           |
| `PV_THEMES`          | `cfg/themes/`       | Theme-Dateien                     |
| `PV_DATA`            | `data/`             | Eingabe-JSON (CLI)                |
| `PV_LOG`             | `log/`              | Logdateien                        |
| `PV_RESULTS`         | `results/`          | Export-Ausgaben                   |
| `PV_EXAMPLES`        | `examples/`         | Beispieldateien                   |
| `PV_EXAMPLE_RESULTS` | `examples/results/` | Beispiel-Exporte                  |
| `PV_WORK`            | `work/`             | Arbeitsdateien, Default für "Neu" |
| `PV_TESTS`           | `tests/`            | Tests                             |

### Wichtige Klassen und Dateien

| Klasse/Datei                       | Zweck                                    |
|------------------------------------|------------------------------------------|
| `gui/editor.py: ProjectEditorApp`  | Zentraler GUI-State, alle Event-Handler  |
| `lib/models/project.py: Project`   | Pydantic-Modell, `calculate_cpm()`       |
| `lib/models/tasks.py`              | SimpleTask, LoopTask, SubTask            |
| `lib/models/resources.py`          | Resource, Person, VacationEntry, etc.    |
| `gui/i18n.py`                      | `t(key, **kwargs)` – Übersetzungen de/en |
| `gui/app.py`                       | `build_gui(editor)` – DPG-Layout         |

### Menüstruktur (Datei-Menü)

```text
Datei
├── Neu            (Ctrl+N)  → editor.new_project()
├── Öffnen …       (Ctrl+O)  → Datei-Browser
├── Speichern      (Ctrl+S)  → editor.save_quick()
├── Speichern unter… (Ctrl+Shift+S)
├── Export …
└── Schließen
```

### Konventionen für GUI-Erweiterungen

- **i18n:** Jeder sichtbare Text nutzt `t("key")` aus `gui/i18n.py` – immer de + en pflegen
- **Tags:** DPG-Items erhalten sprechende Tags (z.B. `mi_new`, `inp_project_name`)
- **Shortcuts:** Werden als `shortcut=`-Label am Menüeintrag deklariert (nur Display)
- **State:** Änderungen am Projekt setzen `self.dirty = True`
- **Refresh:** Nach Modelländerungen `refresh_all()` oder spezifische `_refresh_*()` aufrufen

## Code-Qualität / Linting

Vor Code-Reviews, Refactorings oder nach größeren Änderungen immer den Lint-Lauf starten:

```bash
make lint
```

### Einzelne Tools

| Befehl            | Zweck                          |
|-------------------|-------------------------------|
| `make vulture`    | Dead Code (konservativ, 80%)  |
| `make skylos`     | Dead Code (ML-gestützt)       |
| `make pyright`    | Type Checking (schnell)       |
| `make mypy`       | Type Checking (streng)        |
| `make lint-dead`  | Nur Dead Code (beide Tools)   |
| `make lint-types` | Nur Type Checks (beide Tools) |

## Arbeitshinweise für Claude Code

- Vor dem Vorschlag von Refactorings: `make lint` ausführen und Ergebnisse berücksichtigen.
- Als toten Code markierte Symbole (vulture/skylos) nur entfernen, wenn der Nutzer dies explizit bestätigt.
- Typ-Fehler (pyright/mypy) bei neu generiertem Code direkt beheben, bevor der Code vorgeschlagen wird.
- `--ignore-missing-imports` bei mypy ist gesetzt – fehlende Stubs sind kein Blocker.
