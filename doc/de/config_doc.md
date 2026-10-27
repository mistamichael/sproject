# Konfigurationsdateien

Das `cfg/`-Verzeichnis enthält alle Konfigurationsdateien für sproject. Jede Export-Funktion hat eine eigene Config-Datei — so lassen sich Inhalt, Reihenfolge und Bezeichnungen der Ausgaben ohne Code-Änderungen anpassen.

---

## defaults.cfg

Globale Standardwerte für Kalender, CPM-Berechnung, Arbeitszeiten, Ressourcen und Ausgabe.

### [Project]

- `start_date`: Standard-Projektstartdatum (Format: YYYY-MM-DD oder "today")
- `timezone`: Zeitzone (z.B. Europe/Berlin)
- `currency`: Währung (z.B. EUR, USD)
- `timeformat`: Zeitformat für Ausgaben

### [Resource]

- `name`: Name des Standard-Mitarbeiters
- `email`: E-Mail-Adresse
- `id`: Eindeutige ID
- `hourly_rate`: Stundensatz in der definierten Währung

### [WorkingHours]

- `hours_per_day`: Arbeitsstunden pro Tag
- `days_per_week`: Arbeitstage pro Woche
- `working_days`: Arbeitswochentage (kommasepariert)
- `morning_shift`: Vormittagsarbeitszeit (Format: HH:MM-HH:MM)
- `afternoon_shift`: Nachmittagsarbeitszeit (Format: HH:MM-HH:MM)
- `lunch_break`: Mittagspause in Minuten

### [CPM]

- `round_slack`: Pufferzeiten auf ganze Tage runden (true/false)
- `critical_tolerance`: Toleranz für Puffer=0 Erkennung (Float)
- `skip_weekends`: Wochenenden bei Datumsberechnung überspringen (true/false)
- `skip_holidays`: Feiertage bei Datumsberechnung überspringen (true/false)

### [Duration]

- `week_to_days`: Anzahl Arbeitstage pro Woche
- `day_to_hours`: Anzahl Arbeitsstunden pro Tag
- `month_to_days`: Durchschnittliche Arbeitstage pro Monat

### [Output]

- `results_dir`: Verzeichnis für Berechnungsergebnisse
- `graphs_dir`: Verzeichnis für Graphen
- `json_indent`: Einrückung in JSON-Dateien
- `include_dates`: Kalenderdaten in Ausgabe einschließen (true/false)
- `verbose_output`: Detaillierte Ausgabe (true/false)

### [Costs]

- `overhead_factor`: Overhead-Faktor (Multiplikator)
- `risk_buffer_percent`: Risikopuffer in Prozent
- `vat_percent`: Mehrwertsteuer in Prozent

### [Logging]

- `log_level`: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_dir`: Verzeichnis für Log-Dateien
- `log_file_format`: Format für Log-Dateinamen
- `max_log_size`: Maximale Größe einer Log-Datei in MB
- `log_retention`: Anzahl aufzubewahrende Log-Dateien

---

## Export-Konfigurationen

Für jeden Exporttyp gibt es eine eigene `.cfg`-Datei. Diese steuern Inhalt, Reihenfolge und Bezeichnungen der Ausgaben — ohne Code-Änderungen.

### excel_export.cfg

Konfiguriert den Excel-Export (`--export xlsx`).

**Zweck:** Welche Tabellenblätter erzeugt werden und in welcher Reihenfolge, wird ausschließlich über `section_order` gesteuert. Wer z.B. keinen Gantt-Tab möchte, entfernt `gantt_chart` aus der Liste.

```ini
[sections]
# Reihenfolge der Tabellenblätter im Excel
section_order = summary, critical_path, tasklist, gantt_chart, resource_list, cost_overview
```

Verfügbare Sektionen:

| Sektion          | Inhalt                              |
|------------------|-------------------------------------|
| `summary`        | Projektzusammenfassung              |
| `critical_path`  | Kritischer Pfad (CPM-Tabelle)       |
| `tasklist`       | Alle Vorgänge mit Terminen          |
| `gantt_chart`    | Gantt-Diagramm (Tage/Stunden)       |
| `resource_list`  | Ressourcenauslastung je Person      |
| `cost_overview`  | Kostenübersicht                     |

Tab-Bezeichnungen werden je Sprache in `[de]` und `[en]` definiert:

```ini
[de]
summary       = Projektzusammenfassung
critical_path = Kritischer Pfad
tasklist      = Alle Tasks
resource_list = Auslastung
cost_overview = Kosten
puffer        = Puffer
kritisch      = Kritisch

[en]
summary       = Project Summary
critical_path = Critical Path
tasklist      = All Tasks
resource_list = Resources
cost_overview = Costs
puffer        = Float
kritisch      = Critical
```

Die aktive Sprache wird über `--lang de` bzw. `--lang en` beim Aufruf gewählt (Standard: `de`).

---

### markdown_export.cfg

Konfiguriert sowohl den Markdown-Export (`--export md`) als auch den HTML-Export (`--export html`).

**Zweck:** Steuert welche Sektionen (Zusammenfassung, CPM-Tabelle, Mermaid-Diagramme) in der Ausgabe erscheinen und in welcher Reihenfolge. Beide Formate — `.md` und `.html` — nutzen dieselbe Config, da HTML aus dem Markdown generiert wird.

```ini
[sections]
section_order = summary, critical_path, netplan, tasklist, gantt_chart, resource_list, cost_overview
```

Abschnittsbezeichnungen ebenfalls zweisprachig:

```ini
[de]
summary       = Projektzusammenfassung
critical_path = Kritischer Pfad
netplan       = Netzplan
tasklist      = Alle Tasks
gantt_chart   = Gantt Chart (mit Wochenenden)
resource_list = Resource List
cost_overview = Kostenübersicht

[en]
summary       = Project Summary
critical_path = Critical Path
netplan       = Network Plan
tasklist      = All Tasks
gantt_chart   = Gantt Chart (with weekends)
resource_list = Resource List
cost_overview = Cost Overview
```

---

### txt_export.cfg

Konfiguriert den Text-Export (`--export txt`).

**Zweck:** Steuert welche Abschnitte in der ASCII-Textdatei erscheinen (Kopfzeile, CPM-Tabelle, Ressourcen, Zusammenfassung) und deren Formatierung (Trennlinien, Spaltenbreiten).

---

### json_export.cfg

Konfiguriert den JSON-Export (`--export json`).

**Zweck:** Steuert Einrückung, welche Felder im JSON-Netzplan enthalten sind und ob optionale Felder (z. B. Ressourcen, Kosten) mit exportiert werden.

---

## ZIP-Export (kein separates .cfg)

Der ZIP-Export (`--export zip`) erzeugt alle Diagramme als SVG-Dateien in einem Archiv:

- Gantt-Chart
- Netzplan
- Ressourcen-Gantt je Person

Die Diagramme werden über [kroki.io](https://kroki.io) aus Mermaid-Syntax gerendert. Konfigurierbar ist das Rendering über `markdown_export.cfg`, da dieselben Mermaid-Definitionen verwendet werden.

---

## Feiertage

Feiertage kommen im Normalfall aus der Python-Bibliothek [holidays](https://pypi.org/project/holidays/) –
für **jedes Land und jede Region**. Eingestellt wird das global (für alle Projekte) in `cfg/defaults.cfg`:

```ini
[Holidays]
consider_holidays = true   # Feiertage berücksichtigen
country = DE               # z. B. DE, AT, CH, US, GB …
region  = NW               # Bundesland/Region, z. B. BY, BW, NW …
language =                 # Sprache der Feiertagsnamen (z. B. de, en); leer = Landessprache
holidays_file =            # leer = holidays-Bibliothek (Normalfall)

[CPM]
skip_holidays = true       # Feiertage bei der Terminberechnung überspringen
```

### Eigene Feiertagsdatei (optional)

Für Sonderfälle (z. B. Betriebsferien, Brückentage, regionale Feste) kann statt der Bibliothek eine eigene
JSON-Datei im `cfg/`-Ordner verwendet werden – `holidays_file = meine_feiertage.json`. Ist sie gesetzt, gelten
**nur** die Tage aus der Datei (die Bibliothek wird dann nicht verwendet). Fehlt die Datei oder ist sie ungültig,
erscheint eine Warnung und die Bibliothek springt ein.

```json
{
  "holidays": [
    {"date": "2026-01-01", "name": "Neujahr"},
    {"date": "2026-04-03", "name": "Karfreitag"},
    {"date": "2026-12-24", "name": "Betriebsferien"}
  ]
}
```

Pflichtfelder je Eintrag: `date` (`YYYY-MM-DD`) und `name`; weitere Felder werden ignoriert.

---

## Hinweise

- Kommentare beginnen mit `#`
- Boolean-Werte: `true`, `false`, `yes`, `no`, `1`, `0`
- Zahlen können Integer oder Float sein
- Listen werden mit Komma getrennt
- Pfade sollten relativ zum Projekt-Root sein
- Eigenes Config-Verzeichnis: `--cfg-dir ./meine_cfg`
