# Pizza Service Express - CPM Report


## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Pizza Service Express
- **Projektdauer:** 108.5m
- **Startdatum:** 2026-03-03 09:00
- **Enddatum (geschätzt):** 2026-03-03 10:48
- **Zeiteinheit:** minutes
- **Anzahl Tasks:** 51
- **Kritische Tasks:** 20

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Teigvorbereitung (Batch für alle Pizzen) (Dauer: 60.0m)
- **[2-P1.1]** Pizza formen & belegen #1 (Dauer: 3.0m)
- **[2-P1.2]** Pizza in den Ofen #1 (Dauer: 0.5m)
- **[2-P2.1]** Pizza formen & belegen #2 (Dauer: 3.0m)
- **[2-P2.2]** Pizza in den Ofen #2 (Dauer: 0.5m)
- **[2-P2.3]** Pizza backen #2 (Dauer: 7.0m)
- **[2-P2.4]** Pizza aus dem Ofen holen #2 (Dauer: 0.5m)
- **[2-P4.2]** Pizza in den Ofen #4 (Dauer: 0.5m)
- **[2-P4.3]** Pizza backen #4 (Dauer: 7.0m)
- **[2-P4.4]** Pizza aus dem Ofen holen #4 (Dauer: 0.5m)
- **[2-P6.2]** Pizza in den Ofen #6 (Dauer: 0.5m)
- **[2-P6.3]** Pizza backen #6 (Dauer: 7.0m)
- **[2-P6.4]** Pizza aus dem Ofen holen #6 (Dauer: 0.5m)
- **[2-P8.2]** Pizza in den Ofen #8 (Dauer: 0.5m)
- **[2-P8.3]** Pizza backen #8 (Dauer: 7.0m)
- **[2-P8.4]** Pizza aus dem Ofen holen #8 (Dauer: 0.5m)
- **[2-P10.2]** Pizza in den Ofen #10 (Dauer: 0.5m)
- **[2-P10.3]** Pizza backen #10 (Dauer: 7.0m)
- **[2-P10.4]** Pizza aus dem Ofen holen #10 (Dauer: 0.5m)
- **[2-P10.5]** Pizza verkaufen #10 (Dauer: 2.0m)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Teigvorbereitung (Batch für alle Pizzen)<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P1.1["<b>[2-P1.1] | Pizza formen & belegen #1<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P1.2["<b>[2-P1.2] | Pizza in den Ofen #1<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P1.3["[2-P1.3] | Pizza backen #1<br/>GP:0.5m | FP:0.0m"]
    N2-P1.4["[2-P1.4] | Pizza aus dem Ofen holen #1<br/>GP:0.5m | FP:0.0m"]
    N2-P1.5["[2-P1.5] | Pizza verkaufen #1<br/>GP:35.5m | FP:35.5m"]
    N2-P2.1["<b>[2-P2.1] | Pizza formen & belegen #2<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P2.2["<b>[2-P2.2] | Pizza in den Ofen #2<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P2.3["<b>[2-P2.3] | Pizza backen #2<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P2.4["<b>[2-P2.4] | Pizza aus dem Ofen holen #2<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P2.5["[2-P2.5] | Pizza verkaufen #2<br/>GP:32.0m | FP:32.0m"]
    N2-P3.1["[2-P3.1] | Pizza formen & belegen #3<br/>GP:1.0m | FP:0.0m"]
    N2-P3.2["[2-P3.2] | Pizza in den Ofen #3<br/>GP:1.0m | FP:0.0m"]
    N2-P3.3["[2-P3.3] | Pizza backen #3<br/>GP:1.0m | FP:0.5m"]
    N2-P3.4["[2-P3.4] | Pizza aus dem Ofen holen #3<br/>GP:0.5m | FP:0.0m"]
    N2-P3.5["[2-P3.5] | Pizza verkaufen #3<br/>GP:28.0m | FP:28.0m"]
    N2-P4.1["[2-P4.1] | Pizza formen & belegen #4<br/>GP:0.5m | FP:0.5m"]
    N2-P4.2["<b>[2-P4.2] | Pizza in den Ofen #4<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P4.3["<b>[2-P4.3] | Pizza backen #4<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P4.4["<b>[2-P4.4] | Pizza aus dem Ofen holen #4<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P4.5["[2-P4.5] | Pizza verkaufen #4<br/>GP:24.0m | FP:24.0m"]
    N2-P5.1["[2-P5.1] | Pizza formen & belegen #5<br/>GP:0.5m | FP:0.5m"]
    N2-P5.2["[2-P5.2] | Pizza in den Ofen #5<br/>GP:0.5m | FP:0.0m"]
    N2-P5.3["[2-P5.3] | Pizza backen #5<br/>GP:0.5m | FP:0.0m"]
    N2-P5.4["[2-P5.4] | Pizza aus dem Ofen holen #5<br/>GP:0.5m | FP:0.0m"]
    N2-P5.5["[2-P5.5] | Pizza verkaufen #5<br/>GP:20.0m | FP:20.0m"]
    N2-P6.1["[2-P6.1] | Pizza formen & belegen #6<br/>GP:0.5m | FP:0.5m"]
    N2-P6.2["<b>[2-P6.2] | Pizza in den Ofen #6<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P6.3["<b>[2-P6.3] | Pizza backen #6<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P6.4["<b>[2-P6.4] | Pizza aus dem Ofen holen #6<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P6.5["[2-P6.5] | Pizza verkaufen #6<br/>GP:16.0m | FP:16.0m"]
    N2-P7.1["[2-P7.1] | Pizza formen & belegen #7<br/>GP:1.0m | FP:0.5m"]
    N2-P7.2["[2-P7.2] | Pizza in den Ofen #7<br/>GP:0.5m | FP:0.0m"]
    N2-P7.3["[2-P7.3] | Pizza backen #7<br/>GP:0.5m | FP:0.0m"]
    N2-P7.4["[2-P7.4] | Pizza aus dem Ofen holen #7<br/>GP:0.5m | FP:0.0m"]
    N2-P7.5["[2-P7.5] | Pizza verkaufen #7<br/>GP:12.0m | FP:12.0m"]
    N2-P8.1["[2-P8.1] | Pizza formen & belegen #8<br/>GP:0.5m | FP:0.5m"]
    N2-P8.2["<b>[2-P8.2] | Pizza in den Ofen #8<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P8.3["<b>[2-P8.3] | Pizza backen #8<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P8.4["<b>[2-P8.4] | Pizza aus dem Ofen holen #8<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P8.5["[2-P8.5] | Pizza verkaufen #8<br/>GP:8.0m | FP:8.0m"]
    N2-P9.1["[2-P9.1] | Pizza formen & belegen #9<br/>GP:1.0m | FP:0.5m"]
    N2-P9.2["[2-P9.2] | Pizza in den Ofen #9<br/>GP:0.5m | FP:0.0m"]
    N2-P9.3["[2-P9.3] | Pizza backen #9<br/>GP:4.0m | FP:0.0m"]
    N2-P9.4["[2-P9.4] | Pizza aus dem Ofen holen #9<br/>GP:4.0m | FP:0.0m"]
    N2-P9.5["[2-P9.5] | Pizza verkaufen #9<br/>GP:4.0m | FP:4.0m"]
    N2-P10.1["[2-P10.1] | Pizza formen & belegen #10<br/>GP:0.5m | FP:0.5m"]
    N2-P10.2["<b>[2-P10.2] | Pizza in den Ofen #10<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P10.3["<b>[2-P10.3] | Pizza backen #10<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P10.4["<b>[2-P10.4] | Pizza aus dem Ofen holen #10<br/>GP:0.0m | FP:0.0m</b>"]:::critical
    N2-P10.5["<b>[2-P10.5] | Pizza verkaufen #10<br/>GP:0.0m | FP:0.0m</b>"]:::critical

    N1 --> N2-P1.1
    N2-P1.1 --> N2-P1.2
    N2-P1.1 --> N2-P2.1
    N2-P1.2 --> N2-P1.3
    N2-P1.3 --> N2-P1.4
    N2-P1.4 --> N2-P1.5
    N2-P2.1 --> N2-P2.2
    N2-P2.1 --> N2-P3.1
    N2-P2.2 --> N2-P2.3
    N2-P2.3 --> N2-P2.4
    N2-P2.4 --> N2-P2.5
    N2-P3.1 --> N2-P3.2
    N2-P3.1 --> N2-P4.1
    N2-P3.2 --> N2-P3.3
    N2-P3.3 --> N2-P3.4
    N2-P3.4 --> N2-P3.5
    N2-P4.1 --> N2-P4.2
    N2-P4.1 --> N2-P5.1
    N2-P4.2 --> N2-P4.3
    N2-P4.3 --> N2-P4.4
    N2-P4.4 --> N2-P4.5
    N2-P5.1 --> N2-P5.2
    N2-P5.1 --> N2-P6.1
    N2-P5.2 --> N2-P5.3
    N2-P5.3 --> N2-P5.4
    N2-P5.4 --> N2-P5.5
    N2-P6.1 --> N2-P6.2
    N2-P6.1 --> N2-P7.1
    N2-P6.2 --> N2-P6.3
    N2-P6.3 --> N2-P6.4
    N2-P6.4 --> N2-P6.5
    N2-P7.1 --> N2-P7.2
    N2-P7.1 --> N2-P8.1
    N2-P7.2 --> N2-P7.3
    N2-P7.3 --> N2-P7.4
    N2-P7.4 --> N2-P7.5
    N2-P8.1 --> N2-P8.2
    N2-P8.1 --> N2-P9.1
    N2-P8.2 --> N2-P8.3
    N2-P8.3 --> N2-P8.4
    N2-P8.4 --> N2-P8.5
    N2-P9.1 --> N2-P9.2
    N2-P9.1 --> N2-P10.1
    N2-P9.2 --> N2-P9.3
    N2-P9.3 --> N2-P9.4
    N2-P9.4 --> N2-P9.5
    N2-P10.1 --> N2-P10.2
    N2-P10.2 --> N2-P10.3
    N2-P10.3 --> N2-P10.4
    N2-P10.4 --> N2-P10.5

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Teigvorbereitung (Batch für alle... | 60.0m | 0.0m | 60.0m | 0.0m | 60.0m | 0.0m | 0.0m | JA |
| 2-P1.1 | Pizza formen & belegen #1 | 3.0m | 60.0m | 63.0m | 60.0m | 63.0m | 0.0m | 0.0m | JA |
| 2-P1.2 | Pizza in den Ofen #1 | 0.5m | 63.0m | 63.5m | 63.0m | 63.5m | 0.0m | 0.0m | JA |
| 2-P1.3 | Pizza backen #1 | 7.0m | 63.5m | 70.5m | 64.0m | 71.0m | 0.5m | 0.0m |  |
| 2-P1.4 | Pizza aus dem Ofen holen #1 | 0.5m | 70.5m | 71.0m | 71.0m | 71.5m | 0.5m | 0.0m |  |
| 2-P1.5 | Pizza verkaufen #1 | 2.0m | 71.0m | 73.0m | 106.5m | 108.5m | 35.5m | 35.5m |  |
| 2-P2.1 | Pizza formen & belegen #2 | 3.0m | 63.5m | 66.5m | 63.5m | 66.5m | 0.0m | 0.0m | JA |
| 2-P2.2 | Pizza in den Ofen #2 | 0.5m | 66.5m | 67.0m | 66.5m | 67.0m | 0.0m | 0.0m | JA |
| 2-P2.3 | Pizza backen #2 | 7.0m | 67.0m | 74.0m | 67.0m | 74.0m | 0.0m | 0.0m | JA |
| 2-P2.4 | Pizza aus dem Ofen holen #2 | 0.5m | 74.0m | 74.5m | 74.0m | 74.5m | 0.0m | 0.0m | JA |
| 2-P2.5 | Pizza verkaufen #2 | 2.0m | 74.5m | 76.5m | 106.5m | 108.5m | 32.0m | 32.0m |  |
| 2-P3.1 | Pizza formen & belegen #3 | 3.0m | 67.0m | 70.0m | 68.0m | 71.0m | 1.0m | 0.0m |  |
| 2-P3.2 | Pizza in den Ofen #3 | 0.5m | 70.0m | 70.5m | 71.0m | 71.5m | 1.0m | 0.0m |  |
| 2-P3.3 | Pizza backen #3 | 7.0m | 70.5m | 77.5m | 71.5m | 78.5m | 1.0m | 0.5m |  |
| 2-P3.4 | Pizza aus dem Ofen holen #3 | 0.5m | 78.0m | 78.5m | 78.5m | 79.0m | 0.5m | 0.0m |  |
| 2-P3.5 | Pizza verkaufen #3 | 2.0m | 78.5m | 80.5m | 106.5m | 108.5m | 28.0m | 28.0m |  |
| 2-P4.1 | Pizza formen & belegen #4 | 3.0m | 71.0m | 74.0m | 71.5m | 74.5m | 0.5m | 0.5m |  |
| 2-P4.2 | Pizza in den Ofen #4 | 0.5m | 74.5m | 75.0m | 74.5m | 75.0m | 0.0m | 0.0m | JA |
| 2-P4.3 | Pizza backen #4 | 7.0m | 75.0m | 82.0m | 75.0m | 82.0m | 0.0m | 0.0m | JA |
| 2-P4.4 | Pizza aus dem Ofen holen #4 | 0.5m | 82.0m | 82.5m | 82.0m | 82.5m | 0.0m | 0.0m | JA |
| 2-P4.5 | Pizza verkaufen #4 | 2.0m | 82.5m | 84.5m | 106.5m | 108.5m | 24.0m | 24.0m |  |
| 2-P5.1 | Pizza formen & belegen #5 | 3.0m | 75.0m | 78.0m | 75.5m | 78.5m | 0.5m | 0.5m |  |
| 2-P5.2 | Pizza in den Ofen #5 | 0.5m | 78.5m | 79.0m | 79.0m | 79.5m | 0.5m | 0.0m |  |
| 2-P5.3 | Pizza backen #5 | 7.0m | 79.0m | 86.0m | 79.5m | 86.5m | 0.5m | 0.0m |  |
| 2-P5.4 | Pizza aus dem Ofen holen #5 | 0.5m | 86.0m | 86.5m | 86.5m | 87.0m | 0.5m | 0.0m |  |
| 2-P5.5 | Pizza verkaufen #5 | 2.0m | 86.5m | 88.5m | 106.5m | 108.5m | 20.0m | 20.0m |  |
| 2-P6.1 | Pizza formen & belegen #6 | 3.0m | 79.0m | 82.0m | 79.5m | 82.5m | 0.5m | 0.5m |  |
| 2-P6.2 | Pizza in den Ofen #6 | 0.5m | 82.5m | 83.0m | 82.5m | 83.0m | 0.0m | 0.0m | JA |
| 2-P6.3 | Pizza backen #6 | 7.0m | 83.0m | 90.0m | 83.0m | 90.0m | 0.0m | 0.0m | JA |
| 2-P6.4 | Pizza aus dem Ofen holen #6 | 0.5m | 90.0m | 90.5m | 90.0m | 90.5m | 0.0m | 0.0m | JA |
| 2-P6.5 | Pizza verkaufen #6 | 2.0m | 90.5m | 92.5m | 106.5m | 108.5m | 16.0m | 16.0m |  |
| 2-P7.1 | Pizza formen & belegen #7 | 3.0m | 83.0m | 86.0m | 84.0m | 87.0m | 1.0m | 0.5m |  |
| 2-P7.2 | Pizza in den Ofen #7 | 0.5m | 86.5m | 87.0m | 87.0m | 87.5m | 0.5m | 0.0m |  |
| 2-P7.3 | Pizza backen #7 | 7.0m | 87.0m | 94.0m | 87.5m | 94.5m | 0.5m | 0.0m |  |
| 2-P7.4 | Pizza aus dem Ofen holen #7 | 0.5m | 94.0m | 94.5m | 94.5m | 95.0m | 0.5m | 0.0m |  |
| 2-P7.5 | Pizza verkaufen #7 | 2.0m | 94.5m | 96.5m | 106.5m | 108.5m | 12.0m | 12.0m |  |
| 2-P8.1 | Pizza formen & belegen #8 | 3.0m | 87.0m | 90.0m | 87.5m | 90.5m | 0.5m | 0.5m |  |
| 2-P8.2 | Pizza in den Ofen #8 | 0.5m | 90.5m | 91.0m | 90.5m | 91.0m | 0.0m | 0.0m | JA |
| 2-P8.3 | Pizza backen #8 | 7.0m | 91.0m | 98.0m | 91.0m | 98.0m | 0.0m | 0.0m | JA |
| 2-P8.4 | Pizza aus dem Ofen holen #8 | 0.5m | 98.0m | 98.5m | 98.0m | 98.5m | 0.0m | 0.0m | JA |
| 2-P8.5 | Pizza verkaufen #8 | 2.0m | 98.5m | 100.5m | 106.5m | 108.5m | 8.0m | 8.0m |  |
| 2-P9.1 | Pizza formen & belegen #9 | 3.0m | 91.0m | 94.0m | 92.0m | 95.0m | 1.0m | 0.5m |  |
| 2-P9.2 | Pizza in den Ofen #9 | 0.5m | 94.5m | 95.0m | 95.0m | 95.5m | 0.5m | 0.0m |  |
| 2-P9.3 | Pizza backen #9 | 7.0m | 95.0m | 102.0m | 99.0m | 106.0m | 4.0m | 0.0m |  |
| 2-P9.4 | Pizza aus dem Ofen holen #9 | 0.5m | 102.0m | 102.5m | 106.0m | 106.5m | 4.0m | 0.0m |  |
| 2-P9.5 | Pizza verkaufen #9 | 2.0m | 102.5m | 104.5m | 106.5m | 108.5m | 4.0m | 4.0m |  |
| 2-P10.1 | Pizza formen & belegen #10 | 3.0m | 95.0m | 98.0m | 95.5m | 98.5m | 0.5m | 0.5m |  |
| 2-P10.2 | Pizza in den Ofen #10 | 0.5m | 98.5m | 99.0m | 98.5m | 99.0m | 0.0m | 0.0m | JA |
| 2-P10.3 | Pizza backen #10 | 7.0m | 99.0m | 106.0m | 99.0m | 106.0m | 0.0m | 0.0m | JA |
| 2-P10.4 | Pizza aus dem Ofen holen #10 | 0.5m | 106.0m | 106.5m | 106.0m | 106.5m | 0.0m | 0.0m | JA |
| 2-P10.5 | Pizza verkaufen #10 | 2.0m | 106.5m | 108.5m | 106.5m | 108.5m | 0.0m | 0.0m | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Pizza Service Express
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m

    section Feiertage
    section Tasks
    [1] Teigvorbereitung (Batch für alle Pizzen) (KRIT) :crit, 2026-03-03 09:00, 2026-03-03 10:00
    [2-P1.1] Pizza formen & belegen #1 (KRIT) :crit, 2026-03-03 10:00, 2026-03-03 10:03
    [2-P1.2] Pizza in den Ofen #1 (KRIT) :crit, 2026-03-03 10:03, 2026-03-03 10:03
    [2-P1.3] Pizza backen #1 :2026-03-03 10:03, 2026-03-03 10:10
    [2-P1.4] Pizza aus dem Ofen holen #1 :2026-03-03 10:10, 2026-03-03 10:11
    [2-P1.5] Pizza verkaufen #1 :2026-03-03 10:11, 2026-03-03 10:13
    [2-P2.1] Pizza formen & belegen #2 (KRIT) :crit, 2026-03-03 10:03, 2026-03-03 10:06
    [2-P2.2] Pizza in den Ofen #2 (KRIT) :crit, 2026-03-03 10:06, 2026-03-03 10:07
    [2-P2.3] Pizza backen #2 (KRIT) :crit, 2026-03-03 10:07, 2026-03-03 10:14
    [2-P2.4] Pizza aus dem Ofen holen #2 (KRIT) :crit, 2026-03-03 10:14, 2026-03-03 10:14
    [2-P2.5] Pizza verkaufen #2 :2026-03-03 10:14, 2026-03-03 10:16
    [2-P3.1] Pizza formen & belegen #3 :2026-03-03 10:07, 2026-03-03 10:10
    [2-P3.2] Pizza in den Ofen #3 :2026-03-03 10:10, 2026-03-03 10:10
    [2-P3.3] Pizza backen #3 :2026-03-03 10:10, 2026-03-03 10:17
    [2-P3.4] Pizza aus dem Ofen holen #3 :2026-03-03 10:18, 2026-03-03 10:18
    [2-P3.5] Pizza verkaufen #3 :2026-03-03 10:18, 2026-03-03 10:20
    [2-P4.1] Pizza formen & belegen #4 :2026-03-03 10:11, 2026-03-03 10:14
    [2-P4.2] Pizza in den Ofen #4 (KRIT) :crit, 2026-03-03 10:14, 2026-03-03 10:15
    [2-P4.3] Pizza backen #4 (KRIT) :crit, 2026-03-03 10:15, 2026-03-03 10:22
    [2-P4.4] Pizza aus dem Ofen holen #4 (KRIT) :crit, 2026-03-03 10:22, 2026-03-03 10:22
    [2-P4.5] Pizza verkaufen #4 :2026-03-03 10:22, 2026-03-03 10:24
    [2-P5.1] Pizza formen & belegen #5 :2026-03-03 10:15, 2026-03-03 10:18
    [2-P5.2] Pizza in den Ofen #5 :2026-03-03 10:18, 2026-03-03 10:19
    [2-P5.3] Pizza backen #5 :2026-03-03 10:19, 2026-03-03 10:26
    [2-P5.4] Pizza aus dem Ofen holen #5 :2026-03-03 10:26, 2026-03-03 10:26
    [2-P5.5] Pizza verkaufen #5 :2026-03-03 10:26, 2026-03-03 10:28
    [2-P6.1] Pizza formen & belegen #6 :2026-03-03 10:19, 2026-03-03 10:22
    [2-P6.2] Pizza in den Ofen #6 (KRIT) :crit, 2026-03-03 10:22, 2026-03-03 10:23
    [2-P6.3] Pizza backen #6 (KRIT) :crit, 2026-03-03 10:23, 2026-03-03 10:30
    [2-P6.4] Pizza aus dem Ofen holen #6 (KRIT) :crit, 2026-03-03 10:30, 2026-03-03 10:30
    [2-P6.5] Pizza verkaufen #6 :2026-03-03 10:30, 2026-03-03 10:32
    [2-P7.1] Pizza formen & belegen #7 :2026-03-03 10:23, 2026-03-03 10:26
    [2-P7.2] Pizza in den Ofen #7 :2026-03-03 10:26, 2026-03-03 10:27
    [2-P7.3] Pizza backen #7 :2026-03-03 10:27, 2026-03-03 10:34
    [2-P7.4] Pizza aus dem Ofen holen #7 :2026-03-03 10:34, 2026-03-03 10:34
    [2-P7.5] Pizza verkaufen #7 :2026-03-03 10:34, 2026-03-03 10:36
    [2-P8.1] Pizza formen & belegen #8 :2026-03-03 10:27, 2026-03-03 10:30
    [2-P8.2] Pizza in den Ofen #8 (KRIT) :crit, 2026-03-03 10:30, 2026-03-03 10:31
    [2-P8.3] Pizza backen #8 (KRIT) :crit, 2026-03-03 10:31, 2026-03-03 10:38
    [2-P8.4] Pizza aus dem Ofen holen #8 (KRIT) :crit, 2026-03-03 10:38, 2026-03-03 10:38
    [2-P8.5] Pizza verkaufen #8 :2026-03-03 10:38, 2026-03-03 10:40
    [2-P9.1] Pizza formen & belegen #9 :2026-03-03 10:31, 2026-03-03 10:34
    [2-P9.2] Pizza in den Ofen #9 :2026-03-03 10:34, 2026-03-03 10:35
    [2-P9.3] Pizza backen #9 :2026-03-03 10:35, 2026-03-03 10:42
    [2-P9.4] Pizza aus dem Ofen holen #9 :2026-03-03 10:42, 2026-03-03 10:42
    [2-P9.5] Pizza verkaufen #9 :2026-03-03 10:42, 2026-03-03 10:44
    [2-P10.1] Pizza formen & belegen #10 :2026-03-03 10:35, 2026-03-03 10:38
    [2-P10.2] Pizza in den Ofen #10 (KRIT) :crit, 2026-03-03 10:38, 2026-03-03 10:39
    [2-P10.3] Pizza backen #10 (KRIT) :crit, 2026-03-03 10:39, 2026-03-03 10:46
    [2-P10.4] Pizza aus dem Ofen holen #10 (KRIT) :crit, 2026-03-03 10:46, 2026-03-03 10:46
    [2-P10.5] Pizza verkaufen #10 (KRIT) :crit, 2026-03-03 10:46, 2026-03-03 10:48
```

---

### Resource List

#### Ressourcenauslastung (Textform)

| Farbe | Name | Ressource | Anzahl Tasks | Tasks |
|---|---|---|---|---|
| <span style="background-color:#4472C4;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Max Mustermann | Bäcker Max (R_BAECKER) | 31 | 1, 2-P1.1, 2-P1.2, 2-P1.4, 2-P2.1, 2-P2.2, 2-P2.4, 2-P3.1, 2-P3.2, 2-P3.4 ... (+21 weitere) |
| <span style="background-color:#6776BE;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Steinofen (R_OFEN) | 10 | 2-P1.3, 2-P2.3, 2-P3.3, 2-P4.3, 2-P5.3, 2-P6.3, 2-P7.3, 2-P8.3, 2-P9.3, 2-P10.3 |
| <span style="background-color:#8B7AB8;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Heinz Müller | Verkäufer Heinz (R_VERKAEUFER) | 10 | 2-P1.5, 2-P2.5, 2-P3.5, 2-P4.5, 2-P5.5, 2-P6.5, 2-P7.5, 2-P8.5, 2-P9.5, 2-P10.5 |

#### Ressourcenauslastung (Gantt-Diagramm)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4472C4', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Bäcker Max
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2025-01-01, 2025-01-06, 2025-04-18, 2025-04-21, 2025-05-01, 2025-05-29, 2025-06-09, 2025-06-19, 2025-10-03, 2025-11-01, 2025-12-25, 2025-12-26, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26, 2027-01-01, 2027-01-06, 2027-03-26, 2027-03-29, 2027-05-01, 2027-05-06, 2027-05-17, 2027-05-27, 2027-10-03, 2027-11-01, 2027-12-25, 2027-12-26

    section Bäcker Max

    Teigvorbereitung (Batc...   :t0, 2026-03-03 09:00, 2026-03-03 10:00
    Pizza formen & belegen #1   :t1, 2026-03-03 10:00, 2026-03-03 10:03
    Pizza in den Ofen #1        :t2, 2026-03-03 10:03, 2026-03-03 10:03
    Pizza formen & belegen #2   :t3, 2026-03-03 10:03, 2026-03-03 10:06
    Pizza in den Ofen #2        :t4, 2026-03-03 10:06, 2026-03-03 10:07
    Pizza formen & belegen #3   :t5, 2026-03-03 10:07, 2026-03-03 10:10
    Pizza in den Ofen #3        :t6, 2026-03-03 10:10, 2026-03-03 10:10
    Pizza aus dem Ofen hol...   :t7, 2026-03-03 10:10, 2026-03-03 10:11
    Pizza formen & belegen #4   :t8, 2026-03-03 10:11, 2026-03-03 10:14
    Pizza aus dem Ofen hol...   :t9, 2026-03-03 10:14, 2026-03-03 10:14
    Pizza in den Ofen #4        :t10, 2026-03-03 10:14, 2026-03-03 10:15
    Pizza formen & belegen #5   :t11, 2026-03-03 10:15, 2026-03-03 10:18
    Pizza aus dem Ofen hol...   :t12, 2026-03-03 10:18, 2026-03-03 10:18
    Pizza in den Ofen #5        :t13, 2026-03-03 10:18, 2026-03-03 10:19
    Pizza formen & belegen #6   :t14, 2026-03-03 10:19, 2026-03-03 10:22
    Pizza aus dem Ofen hol...   :t15, 2026-03-03 10:22, 2026-03-03 10:22
    Pizza in den Ofen #6        :t16, 2026-03-03 10:22, 2026-03-03 10:23
    Pizza formen & belegen #7   :t17, 2026-03-03 10:23, 2026-03-03 10:26
    Pizza aus dem Ofen hol...   :t18, 2026-03-03 10:26, 2026-03-03 10:26
    Pizza in den Ofen #7        :t19, 2026-03-03 10:26, 2026-03-03 10:27
    Pizza formen & belegen #8   :t20, 2026-03-03 10:27, 2026-03-03 10:30
    Pizza aus dem Ofen hol...   :t21, 2026-03-03 10:30, 2026-03-03 10:30
    Pizza in den Ofen #8        :t22, 2026-03-03 10:30, 2026-03-03 10:31
    Pizza formen & belegen #9   :t23, 2026-03-03 10:31, 2026-03-03 10:34
    Pizza aus dem Ofen hol...   :t24, 2026-03-03 10:34, 2026-03-03 10:34
    Pizza in den Ofen #9        :t25, 2026-03-03 10:34, 2026-03-03 10:35
    Pizza formen & belegen...   :t26, 2026-03-03 10:35, 2026-03-03 10:38
    Pizza aus dem Ofen hol...   :t27, 2026-03-03 10:38, 2026-03-03 10:38
    Pizza in den Ofen #10       :t28, 2026-03-03 10:38, 2026-03-03 10:39
    Pizza aus dem Ofen hol...   :t29, 2026-03-03 10:42, 2026-03-03 10:42
    Pizza aus dem Ofen hol...   :t30, 2026-03-03 10:46, 2026-03-03 10:46
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#6776BE', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Steinofen
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2025-01-01, 2025-01-06, 2025-04-18, 2025-04-21, 2025-05-01, 2025-05-29, 2025-06-09, 2025-06-19, 2025-10-03, 2025-11-01, 2025-12-25, 2025-12-26, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26, 2027-01-01, 2027-01-06, 2027-03-26, 2027-03-29, 2027-05-01, 2027-05-06, 2027-05-17, 2027-05-27, 2027-10-03, 2027-11-01, 2027-12-25, 2027-12-26

    section Steinofen

    Pizza backen #1             :t0, 2026-03-03 10:03, 2026-03-03 10:10
    Pizza backen #2             :t1, 2026-03-03 10:07, 2026-03-03 10:14
    Pizza backen #3             :t2, 2026-03-03 10:10, 2026-03-03 10:17
    Pizza backen #4             :t3, 2026-03-03 10:15, 2026-03-03 10:22
    Pizza backen #5             :t4, 2026-03-03 10:19, 2026-03-03 10:26
    Pizza backen #6             :t5, 2026-03-03 10:23, 2026-03-03 10:30
    Pizza backen #7             :t6, 2026-03-03 10:27, 2026-03-03 10:34
    Pizza backen #8             :t7, 2026-03-03 10:31, 2026-03-03 10:38
    Pizza backen #9             :t8, 2026-03-03 10:35, 2026-03-03 10:42
    Pizza backen #10            :t9, 2026-03-03 10:39, 2026-03-03 10:46
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#8B7AB8', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Verkäufer Heinz
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2025-01-01, 2025-01-06, 2025-04-18, 2025-04-21, 2025-05-01, 2025-05-29, 2025-06-09, 2025-06-19, 2025-10-03, 2025-11-01, 2025-12-25, 2025-12-26, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26, 2027-01-01, 2027-01-06, 2027-03-26, 2027-03-29, 2027-05-01, 2027-05-06, 2027-05-17, 2027-05-27, 2027-10-03, 2027-11-01, 2027-12-25, 2027-12-26

    section Verkäufer Heinz

    Pizza verkaufen #1          :t0, 2026-03-03 10:11, 2026-03-03 10:13
    Pizza verkaufen #2          :t1, 2026-03-03 10:14, 2026-03-03 10:16
    Pizza verkaufen #3          :t2, 2026-03-03 10:18, 2026-03-03 10:20
    Pizza verkaufen #4          :t3, 2026-03-03 10:22, 2026-03-03 10:24
    Pizza verkaufen #5          :t4, 2026-03-03 10:26, 2026-03-03 10:28
    Pizza verkaufen #6          :t5, 2026-03-03 10:30, 2026-03-03 10:32
    Pizza verkaufen #7          :t6, 2026-03-03 10:34, 2026-03-03 10:36
    Pizza verkaufen #8          :t7, 2026-03-03 10:38, 2026-03-03 10:40
    Pizza verkaufen #9          :t8, 2026-03-03 10:42, 2026-03-03 10:44
    Pizza verkaufen #10         :t9, 2026-03-03 10:46, 2026-03-03 10:48
```

#### Personen

| Person | Kosten/Stunde | Abwesenheiten im Projektzeitraum | Abwesenheiten kurz nach dem Projektzeitraum |
|---|---|---|---|
| Max Mustermann | 45.00 €/h | keine | keine |
| Heinz Müller | 35.00 €/h | keine | keine |

#### Ressourcen-Details

| Ressource | Person | Typ |
|---|---|---|
| Bäcker Max (R_BAECKER) | Max Mustermann | person |
| Verkäufer Heinz (R_VERKAEUFER) | Heinz Müller | person |
| Steinofen (R_OFEN) |  | machine |

---

### Kostenübersicht

| Ressource | Typ | Stunden | €/h | Bereitst. € | Lohnkosten € | Gesamt € |
|---|---|---|---|---|---|---|
| Bäcker Max | person | 1.7 | 45.00 | — | 75.00 | **75.00** |
| Verkäufer Heinz | person | 0.3 | 35.00 | — | 11.67 | **11.67** |

**Zusammenfassung:**

- Personalkosten: **86.67 €**
- **Gesamtkosten: 86.67 €**
