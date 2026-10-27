# Projektdatei-Format (JSON)

> Teil der [sproject-Dokumentation](../../README.de.md#dokumentation). English: [doc/en/project-format.md](../en/project-format.md)

## Minimales Beispiel

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

## Dauerformate

| Angabe  | Bedeutung                 |
| ------- | ------------------------- |
| `"10d"` | 10 Arbeitstage            |
| `"2w"`  | 2 Wochen = 10 Arbeitstage |
| `"8h"`  | 8 Stunden = 1 Arbeitstag  |
| `"30m"` | 30 Minuten                |
| `10`    | 10 Tage (Zahl)            |

## Abhängigkeitstypen

| Feld | Typ | Bedeutung |
| ---- | --- | --------- |
| `successors` | EA | Ende→Anfang: Nachfolger startet nach Ende des Vorgängers (Standard) |
| `successors_aa` | AA | Anfang→Anfang: Nachfolger startet gleichzeitig mit Vorgänger |
| `successors_ae` | AE | Anfang→Ende: Nachfolger endet wenn Vorgänger beginnt |
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

## Projekt mit Ressourcen und Kosten

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

## Loop-Tasks (wiederkehrende Vorgänge)

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

## Unsicherheiten und Szenarien

Unsicherheiten für die Monte-Carlo-Simulation stehen am Task; Szenarien sind benannte Listen von Änderungen am Basisplan:

```json
{
  "tasks": [
    { "id": 4, "name": "Backend", "duration": "40h",
      "duration_range": ["32h", "72h"],
      "risk": { "probability": 0.2, "delay": "16h", "note": "API des Kunden noch instabil" } }
  ],
  "scenarios": [
    { "name": "Alice eine Woche krank", "probability": 0.15,
      "changes": [ { "person": "DEV1", "vacation": [ { "from": "2026-03-09", "to": "2026-03-13", "description": "krank" } ] } ] },
    { "name": "Backend 50 % aufwendiger",
      "changes": [ { "task": 4, "duration_factor": 1.5 } ] }
  ]
}
```

| Feld | Wirkung |
| ---- | ------- |
| `duration_range` | Dauer schwankt zwischen Minimum und Maximum, am häufigsten die geplante Dauer (Dreiecksverteilung) |
| `risk` | Mit `probability` verschiebt sich der Start um `delay` |
| `scenarios[].changes` | Genau eines von `task` (ID oder Muster wie `2-F*.1`), `resource` (`unavailable`), `person` (`vacation`); Task-Änderungen: `duration_factor` oder beliebige Task-Felder |
| `scenarios[].probability` | Das Szenario tritt in der Simulation mit dieser Wahrscheinlichkeit ein; ohne wird es nur verglichen |

Szenario-Vergleich (`--export scenarios`) und Monte-Carlo-Simulation mit Kritikalität (`--export simulation`)
für `examples/software_simple.json`:

![Szenario-Vergleich](../img/scenarios_de.svg)

![Monte-Carlo-Simulation](../img/simulation_de.svg)

![Kritikalität](../img/criticality_de.svg)

Details und Lesehilfe: [doc/de/termine-und-ist.md](termine-und-ist.md). Beispiel: `examples/software_simple.json`.
