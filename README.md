# sproject.py - Einfaches Projektmanagement

## Zweck des Programms

**sproject.py** ist ein Tool für einfaches Projektmanagement durch die Kombination von:

- **Ressourcenverwaltung**: Verwaltung von Personen, Teams und deren Verfügbarkeit
- **Kalender**: Arbeitszeiten, Feiertage und Abwesenheiten
- **Projektangaben**: Tasks, Meilensteine, Abhängigkeiten und Aufwände
- **Reportbeschreibung**: Konfigurierbare Reports für verschiedene Projektansichten

Das Programm basiert auf [Pydantic](https://docs.pydantic.dev/)-Modellen und lädt Projektdaten aus JSON-Dateien, um Reports, Ressourcenpläne, Gantt-Diagramme und Kostenpläne zu erstellen.

## Features

- **JSON-basierte Konfiguration**: Alle Projektdaten werden in strukturierten JSON-Dateien gespeichert
- **Validierung**: Automatische Validierung der Eingabedaten durch Pydantic
- **Querverweise**: Automatisches Auflösen von Referenzen zwischen Personen, Tasks und Arbeitszeiten
- **Flexibles Logging**: Detailliertes Logging in Dateien und Konsole
- **Batch-Verarbeitung**: Verarbeitung mehrerer Projekte in einem Durchlauf

## Projektstruktur

```
sproject/
├── bin/                      # Batch-Skripte für Windows
│   ├── setenv.bat           # Umgebungsvariablen Setup
│   ├── activate_venv.bat    # Virtuelle Umgebung aktivieren
│   ├── create_reports.bat   # Reports erstellen
│   └── ...
├── cfg/                      # Konfigurationsdateien (global)
│   ├── persons.json         # Personen/Ressourcen-Definitionen
│   ├── workinghours_absences.json  # Arbeitszeiten & Abwesenheiten
│   └── reports.json         # Report-Definitionen
├── data/                     # Projektdateien
│   └── project_example.json # Projekt-Definitionen
├── lib/                      # Python-Module
│   ├── sproject.py          # Hauptprogramm
│   ├── tjp_models.py        # Pydantic-Modelle
│   └── test.py              # Unit-Tests
├── log/                      # Logdateien (automatisch erstellt)
├── results/                  # Generierte Reports (automatisch erstellt)
└── README.md                 # Diese Datei
```

## Installation

### Voraussetzungen

- Python 3.10 oder höher
- pip für Paketinstallation

### Abhängigkeiten installieren

```bash
pip install pydantic
```

Oder mit einer virtuellen Umgebung:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate.bat  # Windows

pip install pydantic
```

## Verwendung

### Umgebungsvariablen setzen

Vor der ersten Verwendung die Umgebungsvariablen mit `setenv.bat` setzen:

```cmd
cd bin
setenv.bat
```

Dies setzt folgende Variablen:
- `PROJECT`: Projekt-Wurzelverzeichnis
- `PV_BIN`: bin-Verzeichnis
- `PV_LIB`: lib-Verzeichnis
- `PV_DATA`: data-Verzeichnis
- `PV_CFG`: cfg-Verzeichnis
- `PV_LOG`: log-Verzeichnis
- `PV_RESULTS`: results-Verzeichnis

### Projekt verarbeiten

#### Einzelnes Projekt

```bash
python lib/sproject.py --project data/project_example.json
```

#### Alle Projekte im data-Ordner

```bash
python lib/sproject.py
```

#### Mit ausführlicher Ausgabe

```bash
python lib/sproject.py --project data/project_example.json --verbose
```

#### Benutzerdefiniertes Log-Verzeichnis

```bash
python lib/sproject.py --log-dir ./custom_logs
```

### Hilfe anzeigen

```bash
python lib/sproject.py --help
```

## Konfigurationsdateien

### 1. persons.json

Definiert Ressourcen-Gruppen und Personen:

```json
{
  "resource_groups": [
    {
      "id": "dev",
      "name": "Developers",
      "rate": 100.0,
      "members": [
        {
          "id": "alice",
          "name": "Alice Smith",
          "email": "alice@example.com"
        }
      ]
    }
  ]
}
```

### 2. workinghours_absences.json

Definiert Arbeitszeiten und Abwesenheiten:

```json
{
  "global_workinghours": {
    "id": "standard",
    "description": "Standard 40h/week",
    "schedules": [
      {
        "days": ["mon", "tue", "wed", "thu", "fri"],
        "hours": [{"from": "09:00", "to": "17:00"}]
      }
    ]
  },
  "global_leaves": [
    {
      "type": "holiday",
      "name": "Neujahr",
      "date": "2025-01-01",
      "applies_to": "all"
    }
  ]
}
```

### 3. project.json

Definiert Projektdetails und Tasks:

```json
{
  "project": {
    "id": "my_project",
    "name": "My Project",
    "version": "1.0",
    "start": "2025-01-01",
    "duration": "90d",
    "timezone": "Europe/Berlin",
    "currency": "EUR"
  },
  "tasks": [
    {
      "id": "coding",
      "name": "Coding Phase",
      "effort": "20d",
      "allocate": ["alice"]
    }
  ]
}
```

### 4. reports.json

Definiert Report-Konfigurationen:

```json
{
  "reports": [
    {
      "id": "overview",
      "type": "taskreport",
      "name": "Project Overview",
      "columns": ["name", "start", "end", "effort"]
    }
  ]
}
```

## Tests

Unit-Tests ausführen:

```bash
cd lib
python -m unittest test.py
```

Oder einzelne Testklassen:

```bash
python -m unittest test.TestWorkingHours
python -m unittest test.TestTJPRegistry
```

## Logging

Logdateien werden automatisch im `log/`-Verzeichnis erstellt:

- Format: `sproject_YYYYMMDD_HHMMSS.log`
- Enthält Debug-Informationen, Fehler und Warnungen
- Konsolenausgabe zeigt nur wichtige Informationen (INFO-Level)

## Entwicklung

### Neue Features hinzufügen

1. Modelle in [tjp_models.py](lib/tjp_models.py) erweitern
2. Logik in [sproject.py](lib/sproject.py) implementieren
3. Tests in [test.py](lib/test.py) hinzufügen

### Code-Qualität

- Alle Modelle basieren auf Pydantic für automatische Validierung
- Type Hints für bessere IDE-Unterstützung
- Docstrings für alle wichtigen Funktionen

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Logdateien in `log/`
2. Validieren Sie Ihre JSON-Dateien mit `--verbose`
3. Führen Sie die Tests aus, um die Grundfunktionalität zu prüfen
