# Excel-Reports: Gantt Chart und Resource List

Dokumentation für die Excel-Export-Funktionen mit Gantt-Diagrammen und Ressourcenlisten.

## Übersicht

Das sproject-System kann Excel-Dateien mit folgenden Reports generieren:

1. **CPM Analyse** - Immer enthalten bei `--export xlsx`
2. **Gantt Chart** - Mit `--gantt` Flag
3. **Resource List** - Mit `--resource` Flag

## Verwendung

### Basis-Export (nur CPM)

```batch
python lib\sproject.py --project examples\software_simple.json --calculate-cpm --export xlsx
```

Erstellt: `results\software_simple_cpm.xlsx` mit einem Sheet "CPM Analyse"

### Mit Gantt Chart

```batch
python lib\sproject.py --project examples\erdaushub.json --calculate-cpm --export xlsx --gantt
```

Erstellt Excel mit:
- CPM Analyse
- Gantt Chart

### Mit Resource List

```batch
python lib\sproject.py --project examples\software_simple.json --calculate-cpm --export xlsx --resource
```

Erstellt Excel mit:
- CPM Analyse
- Resource List

### Mit beiden Reports

```batch
python lib\sproject.py --project examples\erdaushub.json --calculate-cpm --export xlsx --gantt --resource
```

Erstellt Excel mit:
- CPM Analyse
- Gantt Chart
- Resource List

## Gantt Chart Features

### Zeitstrahl
- **Automatische Granularität**: Stunden, Tage oder Wochen je nach Projektdauer
- **Bei > 7 Tagen**:
  - Zeile 1: Monat
  - Zeile 2: Tage des Monats
  - Zeile 3: Kalenderwochen (KW)

### Spalten
Konfigurierbar via `reports` in der JSON oder Standard:
- **Vorgang**: Task-ID
- **name**: Task-Name (z.B. "Projektinitialisierung")
- **start**: Startdatum (leer wenn nicht angegeben)
- **end**: Enddatum (leer wenn nicht angegeben)
- **effort**: Aufwand (z.B. "4.0h", "2.5d")
- **chart**: Balkendiagramm

### Sortierung
Tasks werden nach **FAZ (Frühester Anfangszeitpunkt)** sortiert:
- **Aufsteigend**: Tasks die früh starten erscheinen oben
- **Bei gleichem FAZ**: Sortierung nach Task-ID

**Beispiel (tankdesign.json):**
```
Zeile | ID | Name                           | FAZ
------+----+-------------------------------+------
  1   | 1  | design tank projekt           |  0.0
  2   | 2  | Select Tank supplyer          | 10.0  <- gleiche FAZ
  3   | 3  | construct tank foundation     | 10.0  <- wie Task 2
  4   | 4  | manufacture tank components   | 18.0
  ...
```

### Balken-Darstellung

Jeder Task hat **zwei Rechtecke**:

1. **Transparentes Rechteck** (Puffer)
   - Von FAZ (Frühester Anfangszeitpunkt) bis SEZ (Spätester Endzeitpunkt)
   - Zeigt die gesamte verfügbare Zeitspanne

2. **Gefülltes Rechteck** (Dauer)
   - Von FAZ bis FAZ + Dauer
   - Zeigt die tatsächliche Arbeitszeit

### Farbverlauf

Die Balkenfarben ändern sich **von Zeile zu Zeile** (nicht innerhalb eines Balkens):
- **Erste Zeile**: Violet (#8B7AB8)
- **Letzte Zeile**: Blau (#4472C4)
- **Dazwischen**: Gradueller Übergang

Konfigurierbar in [cfg/defaults.cfg](../cfg/defaults.cfg):
```ini
[GanttChart]
color_start = 8B7AB8  # Violet
color_end = 4472C4    # Blau
```

### Kritischer Pfad

Tasks auf dem kritischen Pfad haben:
- **Rote Umrandung** (Medium-Dicke)
- **Gleiche Farbverlauf-Farbe** wie andere Tasks in ihrer Position

Konfigurierbar:
```ini
critical_border_color = FF0000  # Rot
```

## Resource List Features

### Spalten
- **User**: Person-Name
- **Rolle**: Person-Rolle
- **start**: Startdatum (leer)
- **end**: Enddatum (leer)
- **chart**: Balken für zugewiesene Tasks

### Zeitstrahl
Gleiche Logik wie Gantt Chart (Stunden/Tage/KW)

### Balken
- Zeigt **alle Tasks** einer Person in ihrer Zeile
- **Gleiche Farben** wie im Gantt Chart für denselben Task
- Keine Transparenz (nur Dauer, kein Puffer)

## Default-Ressourcen

Für Projekte **ohne** `persons`-Sektion (z.B. erdaushub.json):

Das System verwendet automatisch **Max Mustermann** aus [cfg/defaults.cfg](../cfg/defaults.cfg):

```ini
[Resource]
name = Max Mustermann
email = max@mustermann.com
id = default_resource
hourly_rate = 100.00
```

### Beispiel: erdaushub.json

```batch
python lib\sproject.py --project examples\erdaushub.json --calculate-cpm --export xlsx --gantt --resource
```

**Ergebnis:**
- ✅ Gantt Chart mit allen 68 Tasks (nach Loop-Expansion)
- ✅ Resource List mit "Max Mustermann (Default Resource)"
- ✅ Alle Tasks werden "Max Mustermann" zugewiesen

## Konfiguration

### defaults.cfg

```ini
[GanttChart]
# Farbverlauf für Gantt-Balken
color_start = 8B7AB8          # Startfarbe (Violet)
color_end = 4472C4            # Zielfarbe (Blau)

# Kritischer Pfad
critical_border_color = FF0000  # Rote Umrandung

# Transparenz für Puffer-Balken (0-255)
slack_bar_transparency = 180   # 70% transparent

# Höhen
bar_height = 20                # Balken-Höhe
timeline_header_height = 25    # Zeitstrahl-Header-Höhe
```

### In JSON (software_simple.json)

```json
{
  "reports": [
    {
      "id": "gantt_chart",
      "type": "gantt",
      "name": "Gantt Chart",
      "headline": "Projekt Zeitplan",
      "columns": ["Vorgang", "name", "start", "end", "effort", "chart"],
      "timeformat": "%Y-%m-%d",
      "loadunit": "days"
    },
    {
      "id": "resource_view",
      "type": "resource_list",
      "name": "StatusUpdate",
      "headline": "Resourcendiagramm",
      "columns": ["User", "Rolle", "start", "end", "chart"],
      "timeformat": "%Y-%m-%d",
      "loadunit": "days"
    }
  ]
}
```

**Hinweis:** Mit `--gantt` und `--resource` Flags werden die Reports aus der JSON **überschrieben**.

## Kombination mit anderen Projekt-Typen

### SimpleProject (tankdesign.json)
```batch
python lib\sproject.py --project examples\tankdesign.json --calculate-cpm --export xlsx --gantt --resource
```
- ✅ Funktioniert mit Default-Person

### LoopProject (erdaushub.json)
```batch
python lib\sproject.py --project examples\erdaushub.json --calculate-cpm --export xlsx --gantt --resource
```
- ✅ Loop wird expandiert (68 Tasks)
- ✅ Default-Person wird verwendet

### CycleProject (pizzas.json)
```batch
python lib\sproject.py --project examples\pizzas.json --calculate-cpm --export xlsx --gantt --resource
```
- ✅ Cycles werden expandiert
- ✅ Default-Person wird verwendet

### PersonProject (software_simple.json)
```batch
python lib\sproject.py --project examples\software_simple.json --calculate-cpm --export xlsx --gantt --resource
```
- ✅ Verwendet echte Personen (Alice, Bob, Charlie, Diana)
- ✅ Reports aus JSON werden überschrieben

## Technische Details

### Module
- **lib/excel_reports.py**: Hauptmodul für Excel-Generierung
- **lib/sproject.py**: Integration und Argument-Parsing
- **lib/models/reports.py**: Pydantic-Modelle für Reports
- **cfg/defaults.cfg**: Konfiguration

### Funktionen
- `create_gantt_chart()`: Erstellt Gantt-Chart-Sheet
- `create_resource_list()`: Erstellt Resource-List-Sheet
- `add_dynamic_reports()`: Fügt Reports dynamisch hinzu
- `create_default_person_from_config()`: Lädt Default-Person aus Config

### Abhängigkeiten
```bash
pip install openpyxl pydantic
```

## Fehlerbehandlung

### Fehlende openpyxl
```
XLSX-Export übersprungen: openpyxl ist nicht installiert
```
**Lösung:** `pip install openpyxl`

### Keine Reports bei JSON-Export
Die Flags `--gantt` und `--resource` funktionieren **nur** mit `--export xlsx`.

Bei `--export json` oder `--export txt` werden sie ignoriert.

## Beispiel-Ausgaben

### erdaushub_cpm.xlsx
- **CPM Analyse**: 68 Tasks mit FAZ, FEZ, SAZ, SEZ, Puffer
- **Gantt Chart**: Zeitstrahl + 68 Balken (Violet → Blau)
- **Resource List**: "Max Mustermann" mit allen 68 Tasks

### software_simple_cpm.xlsx
- **CPM Analyse**: 8 Tasks
- **Gantt Chart**: Zeitstrahl + 8 Balken, kritischer Pfad rot umrandet
- **Resource List**: 4 Personen (Alice, Bob, Charlie, Diana) mit zugewiesenen Tasks

## Siehe auch

- [tests/README.md](../tests/README.md) - Unit-Tests für Excel-Export
- [cfg/defaults.cfg](../cfg/defaults.cfg) - Konfiguration
- [examples/software_simple.json](../examples/software_simple.json) - Beispiel mit Reports
