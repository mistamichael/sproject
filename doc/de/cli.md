# Kommandozeile (CLI)

> Teil der [sproject-Dokumentation](../../README.de.md#dokumentation). English: [doc/en/cli.md](../en/cli.md)

## Verwendung

### Einzelnes Projekt verarbeiten

Lege deine Projektdatei (z. B. `newproject.json`) in den Ordner `data/` (`$PV_DATA`) und rufe
`bin/create_reports.bat` (`.sh`) auf – es verarbeitet alle Projektdateien dort – oder direkt:

```bash
python lib/sproject.py --project newproject.json

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

# Alle Szenarien mit dem Basisplan vergleichen / ein Szenario statt des Basisplans rechnen
python lib/sproject.py --project examples/software_simple.json --scenarios
python lib/sproject.py --project examples/software_simple.json --scenario "Alice eine Woche krank" --export xlsx

# Monte-Carlo-Simulation mit 500 Läufen (reproduzierbar mit --seed)
python lib/sproject.py --project examples/software_simple.json --simulate 500 --seed 42

# Kleine interaktive HTML-Charts: plotly.js aus dem Internet laden statt einbetten (~4 MB)
python lib/sproject.py --project examples/software_simple.json --export plotly,simulation --plotly-cdn

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
| `plotly` | Interaktive HTML-Charts (Gantt, Ressourcen) |
| `plotly_svg` | Die Plotly-Charts als SVG-Bilder (braucht kaleido und ein lokales Chrome) |
| `scenarios` | Szenario-Vergleich als HTML |
| `simulation` | Monte-Carlo-Simulation als HTML (Histogramm, Kritikalität, Kennzahlen) |

Diagramme von `--export plotly` (interaktives HTML) und `--export plotly_svg` für `examples/software_simple.json`:

![Gantt-Diagramm](../img/gantt_de.svg)

![Ressourcenauslastung](../img/resources_de.svg)

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

## Logging

Logdateien werden automatisch unter `log/` erstellt:

- Format: `sproject_YYYYMMDD_HHMMSS.log`
- Konsole: INFO-Level (wichtige Meldungen)
- Datei: DEBUG-Level (vollständige Details)
