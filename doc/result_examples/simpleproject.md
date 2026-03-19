# Montage Gesamtsystem - CPM Report

Erstellt am: 2026-03-19 14:39:59

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Montage Gesamtsystem
- **Projektdauer:** 30.0d
- **Startdatum:** 2026-03-09 08:00
- **Enddatum (geschätzt):** 2026-04-08 08:00
- **Zeiteinheit:** days
- **Anzahl Tasks:** 8
- **Kritische Tasks:** 5

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Transport/Anlieferung (Dauer: 3.0d)
- **[2]** Vormontage Prozessstationen (Dauer: 10.0d)
- **[6]** Montage Gesamtsystem (Dauer: 10.0d)
- **[7]** Test Gesamtsystem (Dauer: 5.0d)
- **[8]** Einweisung der Produktionsmitarbeiter (Dauer: 2.0d)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Transport/Anlieferung<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N2["<b>[2] | Vormontage Prozessstationen<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N3["[3] | Vormontage Transportband<br/>GP:3.0d | FP:3.0d"]
    N4["[4] | Anpassung Steuereinheiten<br/>GP:8.0d | FP:0.0d"]
    N5["[5] | Programmierung Steuereinheiten<br/>GP:10.0d | FP:10.0d"]
    N6["<b>[6] | Montage Gesamtsystem<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N7["<b>[7] | Test Gesamtsystem<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N8["<b>[8] | Einweisung der Produktionsmitarbeiter<br/>GP:0.0d | FP:0.0d</b>"]:::critical

    N1 --> N2
    N1 --> N3
    N1 --> N4
    N2 --> N6
    N3 --> N6
    N4 --> N5
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
| 1 | Transport/Anlieferung | 3.0d | 0.0d | 3.0d | 0.0d | 3.0d | 0.0d | 0.0d | JA |
| 2 | Vormontage Prozessstationen | 10.0d | 3.0d | 13.0d | 3.0d | 13.0d | 0.0d | 0.0d | JA |
| 3 | Vormontage Transportband | 7.0d | 3.0d | 10.0d | 6.0d | 13.0d | 3.0d | 3.0d |  |
| 4 | Anpassung Steuereinheiten | 2.0d | 3.0d | 5.0d | 11.0d | 13.0d | 8.0d | 0.0d |  |
| 5 | Programmierung Steuereinheiten | 8.0d | 5.0d | 13.0d | 15.0d | 23.0d | 10.0d | 10.0d |  |
| 6 | Montage Gesamtsystem | 10.0d | 13.0d | 23.0d | 13.0d | 23.0d | 0.0d | 0.0d | JA |
| 7 | Test Gesamtsystem | 5.0d | 23.0d | 28.0d | 23.0d | 28.0d | 0.0d | 0.0d | JA |
| 8 | Einweisung der Produktionsmitarb... | 2.0d | 28.0d | 30.0d | 28.0d | 30.0d | 0.0d | 0.0d | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Montage Gesamtsystem
    dateFormat  YYYY-MM-DD
    axisFormat  %d.%m

    section Wochenenden
    WE 14.03 :crit, 2026-03-14, 2026-03-15
    WE 21.03 :crit, 2026-03-21, 2026-03-22
    WE 28.03 :crit, 2026-03-28, 2026-03-29
    WE 04.04 :crit, 2026-04-04, 2026-04-05
    section Feiertage
    03.04 Karfreitag :crit, 2026-04-03, 2026-04-03
    06.04 Ostermontag :crit, 2026-04-06, 2026-04-06
    section Tasks
    [1] Transport/Anlieferung (KRIT) :crit, 2026-03-09, 2026-03-12
    [2] Vormontage Prozessstationen (KRIT) :crit, 2026-03-12, 2026-03-22
    [3] Vormontage Transportband :2026-03-12, 2026-03-19
    [4] Anpassung Steuereinheiten :2026-03-12, 2026-03-14
    [5] Programmierung Steuereinheiten :2026-03-14, 2026-03-22
    [6] Montage Gesamtsystem (KRIT) :crit, 2026-03-22, 2026-04-01
    [7] Test Gesamtsystem (KRIT) :crit, 2026-04-01, 2026-04-06
    [8] Einweisung der Produktionsmitarbeiter (KRIT) :crit, 2026-04-06, 2026-04-08
```

---

### Resource List

*Keine Ressourcen-Informationen verfügbar.*

---

### Kostenübersicht

*Keine Kostendaten verfügbar – Stundensätze fehlen.*
