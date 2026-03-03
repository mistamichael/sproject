# Konfigurationsdateien

Dieses Verzeichnis enthält Konfigurationsdateien für das sproject-Projektmanagementsystem.

## defaults.cfg

Die Datei `defaults.cfg` enthält alle Standard-Werte, die verwendet werden, wenn keine spezifischen Angaben in den Projektdateien vorhanden sind.

### Verfügbare Sektionen:

#### [Project]
Projekt-weite Einstellungen:
- `start_date`: Standard-Projektstartdatum (Format: YYYY-MM-DD oder "today")
- `timezone`: Zeitzone (z.B. Europe/Berlin)
- `currency`: Währung (z.B. EUR, USD)
- `timeformat`: Zeitformat für Ausgaben

#### [Resource]
Standard-Ressource (Mitarbeiter):
- `name`: Name des Standard-Mitarbeiters
- `email`: E-Mail-Adresse
- `id`: Eindeutige ID
- `hourly_rate`: Stundensatz in der definierten Währung

**Beispiel:**
```ini
[Resource]
name = Max Mustermann
email = max@mustermann.com
id = default_resource
hourly_rate = 100.00
```

#### [WorkingHours]
Arbeitszeiteinstellungen:
- `hours_per_day`: Arbeitsstunden pro Tag
- `days_per_week`: Arbeitstage pro Woche
- `working_days`: Arbeitswochentage (kommasepariert)
- `morning_shift`: Vormittagsarbeitszeit (Format: HH:MM-HH:MM)
- `afternoon_shift`: Nachmittagsarbeitszeit (Format: HH:MM-HH:MM)
- `lunch_break`: Mittagspause in Minuten

#### [CPM]
Einstellungen für die Critical Path Method Berechnung:
- `round_slack`: Pufferzeiten auf ganze Tage runden (true/false)
- `critical_tolerance`: Toleranz für Puffer=0 Erkennung (Float)
- `skip_weekends`: Wochenenden bei Datumsberechnung überspringen (true/false)
- `skip_holidays`: Feiertage bei Datumsberechnung überspringen (true/false)

#### [Duration]
Konvertierungsfaktoren für Dauern:
- `week_to_days`: Anzahl Arbeitstage pro Woche
- `day_to_hours`: Anzahl Arbeitsstunden pro Tag
- `month_to_days`: Durchschnittliche Arbeitstage pro Monat

#### [Output]
Ausgabeeinstellungen:
- `results_dir`: Verzeichnis für Berechnungsergebnisse
- `graphs_dir`: Verzeichnis für Graphen
- `json_indent`: Einrückung in JSON-Dateien
- `include_dates`: Kalenderdaten in Ausgabe einschließen (true/false)
- `verbose_output`: Detaillierte Ausgabe (true/false)

#### [Costs]
Kostenberechnungseinstellungen:
- `overhead_factor`: Overhead-Faktor (Multiplikator)
- `risk_buffer_percent`: Risikopuffer in Prozent
- `vat_percent`: Mehrwertsteuer in Prozent

#### [Logging]
Logging-Einstellungen:
- `log_level`: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_dir`: Verzeichnis für Log-Dateien
- `log_file_format`: Format für Log-Dateinamen
- `max_log_size`: Maximale Größe einer Log-Datei in MB
- `log_retention`: Anzahl aufzubewahrende Log-Dateien

## Verwendung

Die Konfiguration wird automatisch geladen, wenn Sie das sproject-Tool verwenden:

```bash
# CPM-Berechnung mit Defaults aus Config
python lib/sproject.py --project examples/tankdesign.json --calculate-cpm

# Config-Werte ansehen
python lib/config_loader.py
```

## Anpassung

Um die Defaults anzupassen:

1. Öffnen Sie `cfg/defaults.cfg` in einem Texteditor
2. Ändern Sie die gewünschten Werte
3. Speichern Sie die Datei
4. Die neuen Werte werden beim nächsten Programmstart verwendet

## Beispiel: Eigene Ressource definieren

Wenn Sie einen anderen Standard-Mitarbeiter verwenden möchten:

```ini
[Resource]
name = Anna Schmidt
email = anna.schmidt@example.com
id = anna_schmidt
hourly_rate = 120.00
```

## Beispiel: Andere Arbeitszeiten

Für ein Projekt mit 7-Stunden-Tag:

```ini
[WorkingHours]
hours_per_day = 7
morning_shift = 09:00-12:00
afternoon_shift = 13:00-16:00
lunch_break = 60
```

## Hinweise

- Kommentare beginnen mit `#`
- Boolean-Werte: `true`, `false`, `yes`, `no`, `1`, `0`
- Zahlen können Integer oder Float sein
- Listen werden mit Komma getrennt
- Pfade sollten relativ zum Projekt-Root sein

## Support

Bei Fragen oder Problemen mit der Konfiguration:
1. Überprüfen Sie die Syntax (INI-Format)
2. Schauen Sie sich `lib/config_loader.py` für verfügbare Optionen an
3. Verwenden Sie `python lib/config_loader.py` um die aktuellen Werte anzuzeigen
