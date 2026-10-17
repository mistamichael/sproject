# Termine, Ressourcen und Plan gegen Ist

Alle hier beschriebenen Angaben sind optional. Ohne sie rechnet sproject wie bisher.

## Feste Termine

Pro Task in der Projektdatei:

```json
{ "id": 3, "name": "Fundament gießen", "duration": "2d",
  "not_before": "2026-04-15",
  "deadline":   "2026-04-30" }
```

| Feld | Bedeutung |
| --- | --- |
| `not_before` | Frühester Start (z. B. Materiallieferung). Datum ohne Uhrzeit = Tagesbeginn. |
| `deadline` | Spätestes Ende. Datum ohne Uhrzeit = Ende des Tages. |

Eine verfehlte Deadline erscheint als negativer Puffer und als Warnung in CLI, TXT, Markdown,
JSON, GUI und im Plotly-Gantt (rote Raute). Bei Loop- und Instance-Tasks gilt `not_before` für den
ersten, `deadline` für den letzten Zyklus.

## Ressourcen: wer kann wie viel gleichzeitig?

| Ressource | Gleichzeitige Aufgaben |
| --- | --- |
| mit `count` | `count` |
| `machine` / `oven` mit `capacity` | `capacity` (z. B. Ofen mit 4 Plätzen) |
| `material` | unbegrenzt |
| alle anderen (Personen, LKW, Bagger …) | 1 |

Beim LKW ist `capacity` die **Ladekapazität** (m³), nicht die Zahl paralleler Fahrten.

Teilen sich Tasks eine Ressource, plant sproject sie nacheinander ein. Die Wartebeziehung zählt wie
eine Abhängigkeit – Puffer und kritischer Pfad passen dadurch zum eingeplanten Ablauf. Im
Plotly-Tooltip steht, um wie viel ein Task verschoben wurde und auf wen er wartet.

## Urlaub und Teilzeit

An der Person (`persons`):

```json
{ "id": "DEV1", "name": "Alice", "role": "Entwicklerin", "hourly_rate": 85,
  "vacation": [ { "from": "2026-04-01", "to": "2026-04-05", "description": "Urlaub" },
                { "date": "2026-03-16", "description": "Fortbildung" } ],
  "workinghours_override": { "description": "halbtags", "days": ["mon", "tue", "wed", "thu", "fri"],
                             "hours": [ { "from": "08:00", "to": "12:00" } ] } }
```

- **Urlaub** unterbricht einen Task; er läuft nach dem Urlaub weiter.
- **Teilzeit** verlangsamt einen Task (4 h von 8 h → halbes Tempo, doppelte Dauer).
- Arbeiten mehrere Personen an einem Task, bestimmt die am wenigsten verfügbare das Tempo.

## Plan gegen Ist

Auf Projektebene:

```json
"status_date": "2026-03-13",
"actuals": {
  "1": { "start": "2026-03-03 09:00", "finish": "2026-03-03 13:00" },
  "4": { "start": "2026-03-06", "progress": 0.6 },
  "5": { "start": "2026-03-12", "remaining": "2d", "note": "Schätzung nach Review" }
},
"baseline": { "created": "...", "project_end": "...", "tasks": { "...": { "start": "...", "finish": "..." } } }
```

| Feld | Bedeutung |
| --- | --- |
| `status_date` | Stichtag des Ist-Stands (Ende des Tages). Nicht begonnene Tasks starten frühestens hier. |
| `actuals` | Ist-Stand je Task-ID (auch expandierte IDs wie `2-F1.1`). |
| `start` + `finish` | erledigt – liegt fest. |
| nur `start` | läuft – Restarbeit ab Stichtag aus `remaining` oder `duration × (1 − progress)`. |
| `baseline` | eingefrorener Plan, wird nicht von Hand gepflegt (siehe unten). |

**Baseline speichern** (einmal, wenn der Plan freigegeben ist):

```bash
python lib/sproject.py --project mein_projekt.json --save-baseline
```

oder in der GUI im Ergebnis-Tab „Baseline speichern“ und danach das Projekt speichern.

Ausgaben: Stichtag, erledigte/laufende Tasks, Prognose-Ende, Baseline-Ende und Verzug in allen
Reports; im Gantt ein grauer Baseline-Balken unter jedem Task, der erledigte Anteil in Grün und eine
Stichtag-Linie. Beispiel: [examples/software_simple_ist.json](../../examples/software_simple_ist.json).
