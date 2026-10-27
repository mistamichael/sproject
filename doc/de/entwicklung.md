# Entwicklung

> Teil der [sproject-Dokumentation](../../README.de.md#dokumentation). English: [doc/en/development.md](../en/development.md)

## Tests

Alle Tests ausführen (Unit-Tests, Golden-File-Vergleich aller Beispiele, GUI-Tests ohne Fenster):

```bash
python -m pytest
```

Nach einer gewollten Ergebnisänderung die Referenzdateien in `tests/golden/` neu erzeugen:

```bash
UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py
```

Nur die KI-Schnittstelle (API, MCP-Werkzeuge, GUI-Anbindung über HTTP):

```bash
python -m pytest tests/test_api.py
python -m pytest tests/test_gui_headless.py -k server_link
```

Oder über das Batch-Skript (Windows):

```cmd
bin\run_unittests.bat
```

## Entwicklung

### Code-Qualität prüfen

```bash
make lint           # Alle Tools
make lint-dead      # Nur Dead Code (vulture + skylos)
make lint-types     # Nur Type Checks (pyright + mypy)
```

Einzelne Tools:

```bash
make vulture        # Dead Code (80% Konfidenz)
make skylos         # Dead Code (ML-gestützt)
make pyright        # Typprüfung (schnell)
make mypy           # Typprüfung (streng)
```

### Neue Projekte hinzufügen

1. JSON-Datei in `examples/` anlegen (Struktur wie oben)
2. Verarbeiten: `python lib/sproject.py --project examples/meinprojekt.json`
3. Ergebnisse im `results/`-Verzeichnis prüfen

### Modelle erweitern

- Task-Modelle: [lib/models/tasks.py](../../lib/models/tasks.py)
- Ressourcen: [lib/models/resources.py](../../lib/models/resources.py)
- CPM-Berechnung: [lib/models/cpm.py](../../lib/models/cpm.py)
- Gantt: [lib/models/gantt.py](../../lib/models/gantt.py)
- Export-Module: `lib/*_export.py`

## Projektstruktur

```text
sproject/
├── bin/                        # Start-Skripte, jeweils als .bat (Windows) und .sh (Linux/macOS)
│   ├── install_py.bat          # Installation: .venv anlegen und pip install (Doppelklick)
│   ├── setenv.bat              # Umgebungsvariablen setzen
│   ├── activate_venv.bat       # Virtuelle Umgebung aktivieren
│   ├── create_reports.bat      # Reports erzeugen
│   ├── gui.bat                 # GUI-Editor starten
│   ├── mcp_server.bat          # sproject-Server (KI-Schnittstelle) starten: --port [N] | --claude
│   └── run_unittests.bat       # Unit-Tests starten
├── cfg/                        # Konfigurationsdateien
│   ├── defaults.cfg            # Haupt-Konfiguration (Kalender, CPM, Kosten)
│   ├── excel_export.cfg        # XLSX Tab-Reihenfolge und Namen
│   ├── txt_export.cfg          # TXT Ausgabestruktur
│   ├── json_export.cfg         # JSON Export-Einstellungen
│   └── markdown_export.cfg     # Markdown/Mermaid-Optionen
├── examples/                   # Beispiel-Projektdateien
│   ├── pizza.json              # Einfaches Beispiel (Minuten)
│   ├── pizzas.json             # Loop-Task Beispiel
│   ├── hausbau.json            # AA/EE-Abhängigkeiten
│   ├── simpleproject.json      # Maschinenmontage (Tage)
│   ├── software_simple.json    # Software-Projekt mit Ressourcen
│   ├── tankdesign.json         # Ingenieurprojekt
│   └── results/                # Vorberechnete Beispiel-Ergebnisse
├── gui/                        # GUI-Editor (Dear PyGui)
│   ├── app.py                  # Layout, Menüs, Toolbar, Dialoge
│   ├── editor.py               # Editor-State, Datei-Operationen, Berechnung, Exporte
│   ├── task_rows.py            # Verlustfreie Umwandlung Tasks ↔ Tabellenzeilen
│   ├── analysis_rows.py        # Text ↔ Modell für Unsicherheiten und Szenarien
│   ├── server_link.py          # Verbindung der GUI zum sproject-Server (Menü Server)
│   └── components/             # Sektionen, Tabellen, Ergebnis-Panel, Sidebar
├── lib/                        # Python-Quellcode (Paket "lib")
│   ├── sproject.py             # CLI-Einstiegspunkt
│   ├── api.py                  # ProjectSession: Projekt-Operationen für KI-Werkzeuge und Skripte
│   ├── schedule.py             # build_schedule(): Expansion → CPM → Gantt → Kosten
│   ├── scenarios.py            # Szenarien anwenden und vergleichen
│   ├── simulation.py           # Monte-Carlo-Simulation
│   ├── charts.py               # Plotly-Charts (Gantt, Ressourcen, Simulation)
│   ├── exporters.py            # Export-Registry (gemeinsam für CLI und GUI)
│   ├── models/                 # Pydantic-Modelle
│   │   ├── project.py          # Projekt-Wurzelmodell (Daten + Validierung)
│   │   ├── tasks.py            # Task-Modelle (inkl. Loop/Cycle)
│   │   ├── dependencies.py     # Abhängigkeitstypen EA/AA/EE/AE
│   │   ├── resources.py        # Ressourcen und Personen
│   │   ├── expander.py         # Expansion von Instance-/Loop-Tasks
│   │   ├── rest_breaks.py      # Ruhepausen für Personen
│   │   ├── cpm.py              # CPM-Berechnung
│   │   ├── gantt.py            # Gantt-Terminplanung (Kalenderdaten)
│   │   └── loader.py           # JSON-Loader
│   ├── durations.py            # Dauer-Parsing/-Formatierung (hours_per_day aus defaults.cfg)
│   ├── work_calendar.py        # Arbeitstage, Wochenenden, Feiertage
│   ├── cost_calculator.py      # Kostenrechnung
│   ├── report_data.py          # Gemeinsame Datenaufbereitung der Exporte
│   ├── excel_reports.py        # XLSX-Export
│   ├── json_export.py          # JSON-Export
│   ├── txt_export.py           # TXT-Export
│   ├── markdown_export.py      # Markdown/HTML/ZIP-Export
│   ├── mermaid_export.py       # SVG via Mermaid/kroki
│   ├── colors.py, paths.py, export_config.py, config_loader.py
├── mcp_server/                 # MCP-Server (KI-Schnittstelle): Werkzeuge auf Basis von lib/api.py
├── tests/                      # pytest (inkl. Golden-File-Tests in tests/golden/)
├── data/                       # Eigene Projektdateien für die CLI (Beispiel: simple_software_project.xlsx)
├── .mcp.json                   # meldet den MCP-Server bei Claude Code an
├── requirements.txt            # Python-Abhängigkeiten
├── log/                        # Logdateien (automatisch erstellt)
├── results/                    # Generierte Reports (automatisch erstellt)
└── README.md
```
