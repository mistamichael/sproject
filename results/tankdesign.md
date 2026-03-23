# Tank Design Project - CPM Report

Erstellt am: 2026-03-20 16:36:21

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Tank Design Project
- **Projektdauer:** 50.0d
- **Startdatum:** 2026-03-03 07:00
- **Enddatum (geschätzt):** 2026-04-22 07:00
- **Zeiteinheit:** days
- **Anzahl Tasks:** 8
- **Kritische Tasks:** 4

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** design tank projekt (Dauer: 10.0d)
- **[3]** construct tank foundation (Dauer: 25.0d)
- **[7]** assemble tank (Dauer: 15.0d)
- **[8]** test commisions tank (Dauer: 0.0d)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | design tank projekt<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N2["[2] | Select Tank supplyer<br/>GP:3.0d | FP:0.0d"]
    N3["<b>[3] | construct tank foundation<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N4["[4] | manufacture tank components<br/>GP:3.0d | FP:0.0d"]
    N5["[5] | prepare Installation drawings<br/>GP:14.0d | FP:14.0d"]
    N6["[6] | Deliver tank components<br/>GP:3.0d | FP:3.0d"]
    N7["<b>[7] | assemble tank<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N8["<b>[8] | test commisions tank<br/>GP:0.0d | FP:0.0d</b>"]:::critical

    N1 --> N2
    N1 --> N3
    N2 --> N4
    N2 --> N5
    N3 --> N7
    N4 --> N6
    N5 --> N7
    N6 --> N7
    N7 --> N8

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | design tank projekt | 10.0d | 0.0d | 10.0d | 0.0d | 10.0d | 0.0d | 0.0d | JA |
| 2 | Select Tank supplyer | 8.0d | 10.0d | 18.0d | 13.0d | 21.0d | 3.0d | 0.0d |  |
| 3 | construct tank foundation | 25.0d | 10.0d | 35.0d | 10.0d | 35.0d | 0.0d | 0.0d | JA |
| 4 | manufacture tank components | 10.0d | 18.0d | 28.0d | 21.0d | 31.0d | 3.0d | 0.0d |  |
| 5 | prepare Installation drawings | 3.0d | 18.0d | 21.0d | 32.0d | 35.0d | 14.0d | 14.0d |  |
| 6 | Deliver tank components | 4.0d | 28.0d | 32.0d | 31.0d | 35.0d | 3.0d | 3.0d |  |
| 7 | assemble tank | 15.0d | 35.0d | 50.0d | 35.0d | 50.0d | 0.0d | 0.0d | JA |
| 8 | test commisions tank | 0.0d | 50.0d | 50.0d | 50.0d | 50.0d | 0.0d | 0.0d | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Tank Design Project
    dateFormat  YYYY-MM-DD
    axisFormat  %d.%m

    section Wochenenden
    WE 07.03 :crit, 2026-03-07, 2026-03-08
    WE 14.03 :crit, 2026-03-14, 2026-03-15
    WE 21.03 :crit, 2026-03-21, 2026-03-22
    WE 28.03 :crit, 2026-03-28, 2026-03-29
    WE 04.04 :crit, 2026-04-04, 2026-04-05
    WE 11.04 :crit, 2026-04-11, 2026-04-12
    WE 18.04 :crit, 2026-04-18, 2026-04-19
    section Feiertage
    03.04 Karfreitag :crit, 2026-04-03, 2026-04-03
    06.04 Ostermontag :crit, 2026-04-06, 2026-04-06
    section Tasks
    [1] design tank projekt (KRIT) :crit, 2026-03-03, 2026-03-13
    [2] Select Tank supplyer :2026-03-13, 2026-03-21
    [3] construct tank foundation (KRIT) :crit, 2026-03-13, 2026-04-07
    [4] manufacture tank components :2026-03-21, 2026-03-31
    [5] prepare Installation drawings :2026-03-21, 2026-03-24
    [6] Deliver tank components :2026-03-31, 2026-04-04
    [7] assemble tank (KRIT) :crit, 2026-04-07, 2026-04-22
    [8] test commisions tank (KRIT) :crit, 2026-04-22, 2026-04-22
```

---

### Resource List

*Keine Ressourcen-Informationen verfügbar.*

---

### Kostenübersicht

*Keine Kostendaten verfügbar – Stundensätze fehlen.*
