# CLAUDE.md – Projektanweisungen für Claude Code

## Projektübersicht

**sproject** ist ein Projektplanungstool mit CPM-Berechnung (Critical Path Method).
Projekte werden als JSON-Dateien gespeichert und können über eine GUI (dieses Repo) oder die CLI/den MCP-Server des Pakets **moncapro** bearbeitet werden. sproject ist der Desktop-Editor.

## Projektstruktur

```text
sproject/
├── bin/              # Start-Skripte (.bat/.sh): setenv, install_py, activate_venv, gui, mcp_server
├── cfg/              # GUI-Konfiguration: gui.cfg, themes/ (Berechnungs-cfg liegt im Paket moncapro)
├── doc/              # Dokumentation
├── gui/              # Dear PyGui GUI-Anwendung
│   ├── app.py        # Hauptlayout, Menüs, Toolbar, Dialoge, Viewport-Aufbau
│   ├── editor.py     # ProjectEditorApp – State, Datei-Ops, sync/refresh, Exporte
│   ├── task_rows.py  # TaskRow: verlustfreie Umwandlung Tasks ↔ Tabellenzeilen (ohne DPG)
│   ├── analysis_rows.py # Text ↔ Modell für Unsicherheiten und Szenarien (ohne DPG)
│   ├── colors.py     # Ressourcen-Farbzuordnung (eigene Farbe vor Palette)
│   ├── i18n.py       # Internationalisierung (de/en), t()-Funktion
│   ├── gui_config.py # Konfigurationslader (gui.cfg → Farben, Größen, Themes)
│   ├── server_link.py # Explizite Verbindung zum moncapro-Server (MCP-Client), Abgleich im DPG-Hauptthread
│   └── components/   # UI-Komponenten
│       ├── list_section.py # Generische bearbeitbare Tabelle (Column, ListSection), Formular-Dialog, Farbwähler
│       ├── sections.py     # Ressourcen, Personen, Ruhezeiten, Urlaub, Teilzeit, Unsicherheiten, Szenarien
│       ├── task_table.py   # Aufgaben-Tabelle
│       ├── result_panel.py # Ergebnis-Tab
│       ├── sidebar.py      # Wizard-Navigation + Beispielliste
│       └── file_browser.py # Datei-Öffnen-Dialog
├── results/          # Export-Ausgaben (in .gitignore)
├── tests/            # pytest: GUI-Tests ohne Fenster (Rechenkern-Tests liegen in moncapro)
└── work/             # Arbeitsdateien, Default-Speicherort für neue Projekte (PV_WORK)
```

- Rechenkern: eigenes Paket **moncapro** ([github.com/mistamichael/moncapro](https://github.com/mistamichael/moncapro), `pip install moncapro`) mit CPM, Leveling, Szenarien, Simulation, Exporten, CLI und MCP-Server – dort steht auch dessen `CLAUDE.md` mit der Kern-Architektur. Änderungen daran gehören in dieses Repo, nicht hierher.
- Quellcode hier: `gui/` (GUI-Schicht)
- Sprache: Python
- GUI-Framework: **Dear PyGui** (dearpygui)
- Datenmodelle: **Pydantic** (BaseModel)

## Architektur

### Datenfluss

1. **JSON-Datei** → `moncapro.models.load_project()` → **Pydantic `Project`-Modell**
2. **GUI** liest/schreibt über `ProjectEditorApp` (Single Source of Truth = `self.project`)
3. **UI → Modell:** `sync_to_model()` liest Stammdaten, Task-Tabelle (`TaskRow`) und alle `ListSection`s
4. **Modell → UI:** `refresh_all()` aktualisiert alle DPG-Widgets aus dem Pydantic-Objekt
5. **Berechnung:** `moncapro.schedule.build_schedule(project)` → `Schedule` (expandiertes Projekt, CPM, Gantt, Kosten) – GUI und CLI identisch
   - Zeitumrechnung CPM-Arbeitstage → Kalender **nur** über `CPMResult.date_at(workdays, is_end)` (Bruchteile = Arbeitsstunden, Enden = Ende des letzten Arbeitstags; Datum ohne Uhrzeit = Arbeitsbeginn aus `morning_shift`).
   - CPM rechnet in Arbeitstagen; danach plant `moncapro/models/leveling.py` mit Ressourcen (eine Person/ein LKW = eine Aufgabe zugleich, `Resource.slots`), Urlaub und Teilzeit (strecken Tasks) sowie `not_before`/`deadline`. Mehrere Prioritätsregeln, der kürzeste Plan gewinnt.
   - Ruhepausen werden nach dem berechneten Zeitplan eingefügt (zweiter CPM-Lauf).
   - Plan gegen Ist: `status_date`, `actuals`, `baseline` im Projekt (`moncapro/models/tracking.py`, `moncapro/baseline.py`); Doku: `doc/de/termine-und-ist.md`.
   - Szenarien: `scenarios` im Projekt (`moncapro/models/scenario.py`), angewendet und verglichen in `moncapro/scenarios.py`.
   - Monte-Carlo: `duration_range`/`risk` am Task, `probability` am Szenario → `moncapro/simulation.py` (nutzt die im Basisplan gewählte Leveling-Regel). Liegt die geplante Dauer außerhalb von `duration_range`, nimmt die Simulation den Rand und meldet den Task (`planned_outside_range()`, `SimulationResult.clamped`); die GUI markiert ihn in Sektion 6.
6. **Export:** `moncapro.exporters.export_schedule()` – JSON, Markdown, HTML, Excel (.xlsx), TXT, SVG-ZIP
7. **KI-Schnittstelle:** `moncapro/api.py` (`ProjectSession`) → `moncapro/mcp/server.py` (`build_server(session)`); Doku: `doc/de/ki-schnittstelle.md`
   - **Genau ein moncapro-Server** (HTTP, `bin/mcp_server.* --port` = `moncapro-mcp --http`, Standard 8765) hält das Projekt. Claude Code (`.mcp.json`, HTTP) und GUI sind nur Clients. Ein zweiter Start auf demselben Port bricht ab (`port_in_use`). Nie wieder einen Server im GUI-Prozess starten – das ergibt zwei Projekte.
   - Änderungen laufen über das Projekt-dict und werden neu validiert (`_commit`, zählt `revision` hoch) – ungültige Eingaben ändern nichts.
   - GUI: `gui/server_link.py` (`ServerLink`) verbindet sich nur explizit (Menü *Server*), MCP-Client im Hintergrund-Thread; `process()` läuft pro Frame in der Render-Schleife von `gui/app.py`. Abgleich ca. 1 s: GUI → `replace_project(data, base_revision)`, Server → `get_revision()`/`get_state()` → `editor.apply_external_project()`. Konflikt: Server gewinnt. Nicht synchronisieren, solange ein Eingabefeld aktiv ist.
   - **Projektwechsel** (`new_project`, `load`, `replace_project` ohne `base_revision` → `ProjectSession._switch`): vorher `write_backup()` nach `$MONCAPRO_WORK/backup`, `generation` + `last_switch` setzen, Antwort mit `warning`. Der Server merkt sich je MCP-Sitzung den gesehenen `generation`-Stand (`run()` in `build_server`) und lehnt den nächsten Aufruf eines Clients ab, wenn ein *anderer* Client gewechselt hat. Die GUI meldet fremde Wechsel per Hinweis-Dialog, eigene (`editor.project_generation`) sendet sie ohne `base_revision`; verlorene GUI-Eingaben sichert `ServerLink._backup_local()`.
   - Tests mit Projektwechsel müssen `backup_dir` auf ein Temp-Verzeichnis setzen – sonst landen Sicherungen in `work/backup`.
   - Im stdio-Modus nichts auf stdout schreiben – `print()` der Bibliothek wird im Server nach stderr umgeleitet.
   - Beispiel-Eingabe für den Projektaufbau per KI: `data/simple_software_project.xlsx` (per Ausnahme in `.gitignore` versioniert).
8. **Speichern:** `save_project()` schreibt nur explizit gesetzte Felder (`exclude_unset`) → Laden/Speichern ist verlustfrei

### GUI-Layout (Dear PyGui)

```text
Viewport
├── Menüleiste (Datei, Analyse, Einstellungen, Server, Hilfe)
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
        ├── 6. Unsicherheiten: duration_range, risk je Task (optional, togglebar)
        ├── 7. Szenarien + Szenario-Änderungen (optional, togglebar)
        └── Ergebnis-Panel (nach Berechnung)
```

### Umgebungsvariablen (gesetzt durch `bin/setenv.*`)

`MONCAPRO_CFG` bleibt bewusst ungesetzt: die Berechnungs-Konfiguration kommt aus dem Paket (ein eigenes Verzeichnis ersetzt sie vollständig). `PV_CFG` gilt nur für `gui.cfg` und Themes.

| Variable             | Pfad                | Verwendung                        |
|----------------------|---------------------|-----------------------------------|
| `PROJECT`            | Projekt-Root        | Basispfad                         |
| `PV_BIN`             | `bin/`              | Skripte                           |
| `PV_CFG`             | `cfg/`              | GUI-Konfiguration (nur gui.cfg)   |
| `PV_THEMES`          | `cfg/themes/`       | Theme-Dateien                     |
| `PV_DATA`            | `data/`             | Eingabe-JSON (CLI)                |
| `PV_LOG`             | `log/`              | Logdateien                        |
| `PV_RESULTS`         | `results/`          | Export-Ausgaben                   |
| `PV_WORK`            | `work/`             | Arbeitsdateien, Default für "Neu" |
| `PV_TESTS`           | `tests/`            | Tests                             |
| `MONCAPRO_DATA/LOG/RESULTS/WORK` | wie `PV_DATA/LOG/RESULTS/WORK` | für den Rechenkern, gesetzt durch `setenv` |

### Wichtige Klassen und Dateien

(`moncapro/…` = Paket moncapro, nicht in diesem Repo)

| Klasse/Datei                       | Zweck                                    |
|------------------------------------|------------------------------------------|
| `gui/editor.py: ProjectEditorApp`  | Zentraler GUI-State, Datei-Ops, Exporte  |
| `moncapro/schedule.py: build_schedule`  | Kompletter Rechenweg (CLI + GUI)         |
| `moncapro/models/leveling.py`           | Ressourcenplanung, Urlaub, Teilzeit      |
| `moncapro/time_axis.py`, `moncapro/charts.py`| Zeitachse (Kalender) und Plotly-Charts   |
| `moncapro/models/project.py: Project`   | Pydantic-Modell (Daten + Validierung)    |
| `moncapro/models/tasks.py`              | SimpleTask, LoopTask, SubTask            |
| `moncapro/models/resources.py`          | Resource, Person, VacationEntry, etc.    |
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

- **Neue Tabellen-Sektion:** `ListSection` mit `Column`-Liste in `gui/components/sections.py` – nicht von Hand bauen
  - Neue optionale Sektion zusätzlich eintragen in: `SECTIONS` (`gui/editor.py`), `_detect_active_sections()`, `SECTIONS`/`TOGGLE_TAGS` (`gui/components/sidebar.py`), `_build_*_section()` + `_label_map` (`gui/app.py`)
  - Optionen: `Column(color=True)` = Farbfeld + Farbwähler, `Column(text_color=…)` = Warnfarbe je Spalte, `ListSection(on_double_click=…)` = Zeile im Formular bearbeiten, `ListSection(warning=…)` = Hinweis unter der Tabelle
  - Hinzufügen und Bearbeiten nutzen dasselbe `open_form_dialog()` (`confirm_label="button.apply"` beim Bearbeiten)
- **IDs** in Sektionstabellen sind nur Anzeige (andere Objekte verweisen darauf)
- **Text ↔ Modell** ohne DPG in eigene Module (`task_rows.py`, `analysis_rows.py`), damit testbar

- **i18n:** Jeder sichtbare Text nutzt `t("key")` aus `gui/i18n.py` – immer de + en pflegen
- **Tags:** DPG-Items erhalten sprechende Tags (z.B. `mi_new`, `inp_project_name`)
- **Shortcuts:** Werden als `shortcut=`-Label am Menüeintrag deklariert (nur Display)
- **State:** Änderungen am Projekt setzen `self.dirty = True`
- **Refresh:** Nach Modelländerungen `refresh_all()` oder spezifische `_refresh_*()` aufrufen

### Fallstricke (GUI und Modell)

- **Tasks werden bei jedem `sync_to_model()` neu aufgebaut** (`rows_to_tasks`). Was an Task-Objekten hängt (Unsicherheiten), wird vorher übernommen und danach per `sections.retarget_tasks()` auf die neuen Objekte umgehängt – sonst gehen Eingaben nach dem ersten Berechnen verloren.
- **`save_project()` nutzt `exclude_unset`:** Listen in Modellen nicht in place ändern (`append`, `remove`), sondern neu zuweisen (`x.changes = x.changes + [c]`) – sonst gilt das Feld als ungesetzt und wird nicht gespeichert.
- **Dear PyGui: kein zweites modales Fenster über einem offenen modalen Dialog** – es bleibt unsichtbar. In Formular-Dialogen deshalb Inhalte aufklappen (`add_color_input(inline=True)`).
- **Dear PyGui-Tabellen:** Jedes Kind einer `table_row` ist eine eigene Spalte – mehrere Widgets für eine Zelle in eine `dpg.group()` packen.
- **Dear PyGui-Tabellen mit `mvTable_SizingStretchProp`:** Dehnbare Spalten brauchen ein festes Gewicht (`init_width_or_weight=1.0`), sonst wandert bei jeder Größenänderung Breite in die letzte Spalte.
- **Dear PyGui nie aus einem Fremd-Thread ändern:** Der MCP-Client in `ServerLink` läuft im Hintergrund-Thread und liefert nur Futures; DPG-Zugriffe (`sync_to_model`, `apply_external_project`) passieren ausschließlich in `ServerLink.process()` im Hauptthread.
- **Lokalisierte Windows-Ausgaben:** `netstat` schreibt auf deutschem Windows „ABHÖREN“ statt „LISTEN“ – Ports nicht per `netstat`-Text prüfen, sondern mit `port_in_use()` bzw. `Get-NetTCPConnection`.
- **Headless-Tests rendern nicht:** Ob etwas sichtbar ist (Modals, Layout), nur per Screenshot prüfbar (`dpg.output_frame_buffer()` mit Viewport).

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
