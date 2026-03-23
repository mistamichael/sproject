# Pizza Project - CPM Report

Erstellt am: 2026-03-20 16:35:45

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Pizza Project
- **Projektdauer:** 84.0m
- **Startdatum:** 2026-03-03 09:00
- **Enddatum (geschätzt):** 2026-03-03 13:12
- **Zeiteinheit:** minutes
- **Anzahl Tasks:** 10
- **Kritische Tasks:** 7

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Zutaten abwiegen & bereitstellen (Dauer: 5.0m)
- **[2]** Teig mischen & kneten (Dauer: 10.0m)
- **[3]** Teig gehen lassen (Gare) (Dauer: 60.0m)
- **[7]** Teig ausrollen / formen (Dauer: 1.0m)
- **[8]** Pizza belegen (Soße + Belag) (Dauer: 2.0m)
- **[9]** Pizza backen (Dauer: 5.0m)
- **[10]** Pizza servieren (Dauer: 1.0m)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Zutaten abwiegen & bereitstellen<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2["<b>[2] | Teig mischen & kneten<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N3["<b>[3] | Teig gehen lassen (Gare)<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N4["[4] | Soße zubereiten<br/>GP:61.0m | FP:61.0m"]
    N5["[5] | Belag schneiden (Käse, Gemüse, etc.)<br/>GP:61.0m | FP:61.0m"]
    N6["[6] | Ofen vorheizen<br/>GP:58.0m | FP:58.0m"]
    N7["<b>[7] | Teig ausrollen / formen<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N8["<b>[8] | Pizza belegen (Soße + Belag)<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N9["<b>[9] | Pizza backen<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N10["<b>[10] | Pizza servieren<br/>GP:0.0m | FP:0.0m</b>"]:::critical

    N1 --> N2
    N1 --> N4
    N1 --> N5
    N2 --> N3
    N3 --> N7
    N4 --> N8
    N5 --> N8
    N6 --> N9
    N7 --> N8
    N8 --> N9
    N9 --> N10

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Zutaten abwiegen & bereitstellen | 5.0m | 0.0m | 5.0m | 0.0m | 5.0m | 0.0m | 0.0m | JA |
| 2 | Teig mischen & kneten | 10.0m | 5.0m | 15.0m | 5.0m | 15.0m | 0.0m | 0.0m | JA |
| 3 | Teig gehen lassen (Gare) | 60.0m | 15.0m | 75.0m | 15.0m | 75.0m | 0.0m | 0.0m | JA |
| 4 | Soße zubereiten | 10.0m | 5.0m | 15.0m | 66.0m | 76.0m | 61.0m | 61.0m |  |
| 5 | Belag schneiden (Käse, Gemüse, e... | 10.0m | 5.0m | 15.0m | 66.0m | 76.0m | 61.0m | 61.0m |  |
| 6 | Ofen vorheizen | 20.0m | 0.0m | 20.0m | 58.0m | 78.0m | 58.0m | 58.0m |  |
| 7 | Teig ausrollen / formen | 1.0m | 75.0m | 76.0m | 75.0m | 76.0m | 0.0m | 0.0m | JA |
| 8 | Pizza belegen (Soße + Belag) | 2.0m | 76.0m | 78.0m | 76.0m | 78.0m | 0.0m | 0.0m | JA |
| 9 | Pizza backen | 5.0m | 78.0m | 83.0m | 78.0m | 83.0m | 0.0m | 0.0m | JA |
| 10 | Pizza servieren | 1.0m | 83.0m | 84.0m | 83.0m | 84.0m | 0.0m | 0.0m | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Pizza Project
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m

    section Feiertage
    section Tasks
    [1] Zutaten abwiegen & bereitstellen (KRIT) :crit, 2026-03-03 09:00, 2026-03-03 09:05
    [2] Teig mischen & kneten (KRIT) :crit, 2026-03-03 09:05, 2026-03-03 09:15
    [3] Teig gehen lassen (Gare) (KRIT) :crit, 2026-03-03 09:15, 2026-03-03 10:15
    [4] Soße zubereiten :2026-03-03 09:05, 2026-03-03 09:15
    [5] Belag schneiden (Käse Gemüse etc.) :2026-03-03 09:05, 2026-03-03 09:15
    [6] Ofen vorheizen :2026-03-03 09:00, 2026-03-03 09:20
    [7] Teig ausrollen / formen (KRIT) :crit, 2026-03-03 10:15, 2026-03-03 10:16
    [8] Pizza belegen (Soße + Belag) (KRIT) :crit, 2026-03-03 10:16, 2026-03-03 10:18
    [9] Pizza backen (KRIT) :crit, 2026-03-03 10:18, 2026-03-03 10:23
    [10] Pizza servieren (KRIT) :crit, 2026-03-03 10:23, 2026-03-03 10:24
```

---

### Resource List

*Keine Ressourcen-Informationen verfügbar.*

---

### Kostenübersicht

*Keine Kostendaten verfügbar – Stundensätze fehlen.*
