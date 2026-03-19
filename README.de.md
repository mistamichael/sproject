# sproject.py – CPM Projektplanung

**sproject.py** berechnet den kritischen Pfad (CPM – Critical Path Method) aus einfachen JSON-Projektdateien und exportiert die Ergebnisse in verschiedene Formate.

## Zweck

- **CPM-Berechnung**: Frühester/spätester Start und Ende, Gesamtpuffer, freier Puffer, kritischer Pfad
- **Kalender-Integration**: Wochenenden und Feiertage werden bei Datumsberechnung übersprungen
- **Ressourcenverwaltung**: Optional Personen, Stundensätze und Kostenübersicht
- **Gantt-Diagramm**: Terminplanung mit Arbeitstagen
- **Mehrere Exportformate**: JSON, TXT, XLSX, Markdown, HTML, SVG-ZIP

## Projektstruktur

```text
sproject/
├── bin/                        # Windows Batch-Skripte
│   ├── setenv.bat              # Umgebungsvariablen setzen
│   ├── activate_venv.bat       # Virtuelle Umgebung aktivieren
│   ├── create_reports.bat      # Reports erzeugen
│   └── run_unittests.bat       # Unit-Tests starten
├── cfg/                        # Konfigurationsdateien
│   ├── defaults.cfg            # Haupt-Konfiguration (Kalender, CPM, Kosten)
│   ├── excel_export.cfg        # XLSX Tab-Reihenfolge und Namen
│   ├── txt_export.cfg          # TXT Ausgabestruktur
│   ├── json_export.cfg         # JSON Export-Einstellungen
│   ├── markdown_export.cfg     # Markdown/Mermaid-Optionen
│   └── holidays_BY_2026.json   # Bayern-Feiertage 2026
├── examples/                   # Beispiel-Projektdateien
│   ├── pizza.json              # Einfaches Beispiel (Minuten)
│   ├── pizzas.json             # Loop-Task Beispiel
│   ├── hausbau.json            # AA/EE-Abhängigkeiten
│   ├── simpleproject.json      # Maschinenmontage (Tage)
│   ├── software_simple.json    # Software-Projekt mit Ressourcen
│   ├── tankdesign.json         # Ingenieurprojekt
│   └── results/                # Vorberechnete Beispiel-Ergebnisse
├── lib/                        # Python-Quellcode
│   ├── sproject.py             # Hauptprogramm (Einstiegspunkt)
│   ├── models/                 # Pydantic-Modelle
│   │   ├── cpm.py              # CPM-Berechnung
│   │   ├── gantt.py            # Gantt-Terminplanung
│   │   ├── tasks.py            # Task-Modelle (inkl. Loop/Cycle)
│   │   ├── resources.py        # Ressourcen und Personen
│   │   ├── project.py          # Projekt-Wurzelmodell
│   │   └── loader.py           # JSON-Loader
│   ├── excel_reports.py        # XLSX-Export
│   ├── json_export.py          # JSON-Export
│   ├── txt_export.py           # TXT-Export
│   ├── markdown_export.py      # Markdown-Export
│   ├── mermaid_export.py       # SVG via Mermaid/kroki
│   ├── utils.py                # Hilfsfunktionen
│   ├── config_loader.py        # Konfiguration lesen
│   ├── test.py                 # Unit-Tests
│   ├── test_models.py          # Modell-Tests
│   └── test_sproject.py        # Integrations-Tests
├── requirements.txt            # Python-Abhängigkeiten
├── log/                        # Logdateien (automatisch erstellt)
├── results/                    # Generierte Reports (automatisch erstellt)
└── README.md
```

## Installation

### Voraussetzungen

- Python 3.10 oder höher

### Abhängigkeiten

```bash
pip install -r requirements.txt
```

Oder einzeln:

```bash
pip install pydantic          # Pflicht
pip install openpyxl          # Für XLSX-Export
pip install requests          # Für SVG/ZIP-Export (via kroki.io)
pip install markdown          # Für HTML-Export
```

Oder mit virtueller Umgebung:

```bash
python -m venv venv
venv\Scripts\activate.bat     # Windows
pip install -r requirements.txt
```

## Verwendung

### Einzelnes Projekt verarbeiten

```bash
python lib/sproject.py --project examples/pizza.json
```

### Exportformat wählen

```bash
# Nur JSON (Standard)
python lib/sproject.py --project examples/tankdesign.json

# Mehrere Formate gleichzeitig
python lib/sproject.py --project examples/hausbau.json --export txt,json,xlsx,md,html,zip

# Alle verfügbaren Formate
python lib/sproject.py --project examples/software_simple.json --export txt,json,xlsx,md,html,zip
```

### Alle Projekte im Verzeichnis verarbeiten

```bash
python lib/sproject.py --data-dir examples --export json
```

### Weitere Optionen

```bash
# Ausgabeverzeichnis angeben
python lib/sproject.py --project examples/pizza.json --output-dir ./meine_ergebnisse

# Startdatum überschreiben
python lib/sproject.py --project examples/simpleproject.json --start-date 2026-06-01

# Konfigurationsverzeichnis
python lib/sproject.py --project examples/pizza.json --cfg-dir ./cfg

# Ausführliche Ausgabe
python lib/sproject.py --project examples/pizza.json --verbose

# Hilfe
python lib/sproject.py --help
```

### Exportformate

| Format | Beschreibung |
| ------ | ------------ |
| `json` | Netzplan + Gantt als JSON (Standard) |
| `txt` | Strukturierte ASCII-Textdatei |
| `xlsx` | Excel mit konfigurierbaren Tabs (via `cfg/excel_export.cfg`) |
| `md` | Markdown-Report mit eingebetteten Mermaid-Diagrammen |
| `html` | HTML-Report, Mermaid-Diagramme werden im Browser gerendert |
| `zip` | Alle Diagramme als SVG in einem ZIP-Archiv (via Mermaid/kroki.io) |

## Projektdatei-Format (JSON)

### Minimales Beispiel

```json
{
  "project": "Mein Projekt",
  "project_start": "2026-04-01 08:00:00",
  "tasks": [
    {
      "id": 1,
      "name": "Planung",
      "duration": "3d",
      "successors": [2]
    },
    {
      "id": 2,
      "name": "Umsetzung",
      "duration": "10d",
      "successors": [3]
    },
    {
      "id": 3,
      "name": "Abnahme",
      "duration": "2d",
      "successors": []
    }
  ]
}
```

### Dauerformate

| Angabe  | Bedeutung                 |
| ------- | ------------------------- |
| `"10d"` | 10 Arbeitstage            |
| `"2w"`  | 2 Wochen = 10 Arbeitstage |
| `"8h"`  | 8 Stunden = 1 Arbeitstag  |
| `"30m"` | 30 Minuten                |
| `10`    | 10 Tage (Zahl)            |

### Abhängigkeitstypen

| Feld | Typ | Bedeutung |
| ---- | --- | --------- |
| `successors` | EA | Ende→Anfang: Nachfolger startet nach Ende des Vorgängers (Standard) |
| `successors_aa` | AA | Anfang→Anfang: Nachfolger startet gleichzeitig mit Vorgänger |
| `successors_ee` | EE | Ende→Ende: Nachfolger endet gleichzeitig mit Vorgänger |

Beispiel (aus `hausbau.json`):

```json
{
  "id": 5,
  "name": "Mauerwerk errichten",
  "duration": "10d",
  "successors": [10],
  "successors_aa": [6, 7],
  "note": "AA: Elektrik und Sanitär beginnen sobald Mauern beginnen"
}
```

### Projekt mit Ressourcen und Kosten

```json
{
  "project": "Software Projekt",
  "project_start": "2026-04-01 09:00:00",
  "persons": [
    {
      "id": "DEV1",
      "name": "Alice",
      "email": "alice@example.com",
      "role": "Senior Developer",
      "hourly_rate": 85.0,
      "vacation": [
        {"from": "2026-04-14", "to": "2026-04-18", "description": "Urlaub"}
      ]
    }
  ],
  "resources": [
    {
      "id": "R_DEV1",
      "name": "Senior Developer",
      "type": "person",
      "person_id": "DEV1"
    }
  ],
  "tasks": [
    {
      "id": 1,
      "name": "Backend Entwicklung",
      "duration": "40h",
      "resources": ["R_DEV1"],
      "successors": [2]
    },
    {
      "id": 2,
      "name": "Deployment",
      "duration": "8h",
      "resources": ["R_DEV1"],
      "successors": []
    }
  ]
}
```

### Loop-Tasks (wiederkehrende Vorgänge)

Für sich wiederholende Zyklen (z. B. Produktionsschleifen) können `is_loop`-Tasks verwendet werden:

```json
{
  "id": 2,
  "name": "Produktionszyklus",
  "is_loop": true,
  "loop_until": "total_volume <= 0",
  "cycle_prefix": "P",
  "volume_per_cycle": 1,
  "subtasks": [
    {"name": "Bearbeitung", "duration": "5m", "resources": ["R_WORKER"]},
    {"name": "Qualitätsprüfung", "duration": "2m", "resources": ["R_QA"]}
  ]
}
```

Das Programm expandiert Loop-Tasks automatisch vor der CPM-Berechnung.

## Konfiguration

Alle Standardwerte werden aus `cfg/defaults.cfg` gelesen:

```ini
[CPM]
skip_weekends  = true     # Wochenenden überspringen
skip_holidays  = true     # Feiertage überspringen (Bayern 2026)

[WorkingHours]
hours_per_day  = 8        # Arbeitsstunden pro Tag
days_per_week  = 5        # Arbeitstage pro Woche

[Resource]
hourly_rate    = 100.00   # Standard-Stundensatz (EUR)

[Costs]
overhead_factor = 1.5     # Overhead-Multiplikator

[Output]
results_dir    = results  # Ausgabeverzeichnis
```

Der XLSX-Export konfiguriert die Tabellenblätter über `cfg/excel_export.cfg`.

## Ausgabestruktur (CPM-Tabelle)

```text
ID      Name                           Dauer    FAZ    FEZ    SAZ    SEZ    GP     FP     Krit.
─────────────────────────────────────────────────────────────────────────────────────────────
1       Planung                        3d       0.0    3.0    0.0    3.0    0.0    0.0    JA
2       Umsetzung                      10d      3.0    13.0   3.0    13.0   0.0    0.0    JA
3       Abnahme                        2d       13.0   15.0   13.0   15.0   0.0    0.0    JA
```

| Kürzel | Bedeutung                  |
| ------ | -------------------------- |
| FAZ    | Frühester Anfangszeitpunkt |
| FEZ    | Frühester Endzeitpunkt     |
| SAZ    | Spätester Anfangszeitpunkt |
| SEZ    | Spätester Endzeitpunkt     |
| GP     | Gesamtpuffer               |
| FP     | Freier Puffer              |

## Beispielprojekte

| Datei                  | Beschreibung               | Besonderheiten                    |
| ---------------------- | -------------------------- | --------------------------------- |
| `pizza.json`           | Pizza zubereiten (Minuten) | Kurze Dauern in `m`               |
| `pizzas.json`          | Pizza-Service mit Volumen  | Loop-Tasks, Ressourcen, Maschinen |
| `simpleproject.json`   | Maschinenmontage           | Klassisches CPM-Beispiel          |
| `tankdesign.json`      | Tank-Design Projekt        | Einfaches Ingenieurprojekt        |
| `hausbau.json`         | Einfamilienhaus-Bau        | AA/EE-Abhängigkeiten              |
| `erdaushub.json`       | Erdaushub                  | Parallel laufende Tätigkeiten     |
| `fassadenbau.json`     | Fassadenbau                | Abschnittweise Montage            |
| `software_simple.json` | Software-Entwicklung       | Personen, Ressourcen, Kosten      |

## Tests

Unit-Tests ausführen:

```bash
cd lib
python -m unittest test.py
python -m unittest test_models.py
python -m unittest test_sproject.py
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

- Task-Modelle: [lib/models/tasks.py](lib/models/tasks.py)
- Ressourcen: [lib/models/resources.py](lib/models/resources.py)
- CPM-Berechnung: [lib/models/cpm.py](lib/models/cpm.py)
- Gantt: [lib/models/gantt.py](lib/models/gantt.py)
- Export-Module: `lib/*_export.py`

## Logging

Logdateien werden automatisch unter `log/` erstellt:

- Format: `sproject_YYYYMMDD_HHMMSS.log`
- Konsole: INFO-Level (wichtige Meldungen)
- Datei: DEBUG-Level (vollständige Details)

## Lizenz

Dieses Projekt ist unter der [MIT-Lizenz](LICENSE) lizenziert.
