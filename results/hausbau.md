# Einfamilienhaus-Bau - CPM Report

Erstellt am: 2026-03-20 16:35:36

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Einfamilienhaus-Bau
- **Projektdauer:** 31.0d
- **Startdatum:** 2026-04-01 00:00
- **Enddatum (geschätzt):** 2026-05-02 00:00
- **Zeiteinheit:** days
- **Anzahl Tasks:** 10
- **Kritische Tasks:** 9

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Grube ausheben (Dauer: 3.0d)
- **[2]** Erde abtransportieren (Dauer: 4.0d)
- **[3]** Fundament gießen (Dauer: 2.0d)
- **[4]** Fundament trocknen (Dauer: 7.0d)
- **[5]** Mauerwerk errichten (Dauer: 10.0d)
- **[7]** Sanitärinstallation (Dauer: 6.0d)
- **[9]** Laufende Bauschuttreinigung (Dauer: 14.0d)
- **[8]** Innenausbau (Trockenbau/Böden) (Dauer: 12.0d)
- **[10]** Abnahme (Dauer: 1.0d)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Grube ausheben<br/>GP:0.0d | FP:-3.0d</b>"]:::critical
    N2["<b>[2] | Erde abtransportieren<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N3["<b>[3] | Fundament gießen<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N4["<b>[4] | Fundament trocknen<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N5["<b>[5] | Mauerwerk errichten<br/>GP:0.0d | FP:-10.0d</b>"]:::critical
    N6["[6] | Elektroinstallation<br/>GP:1.0d | FP:1.0d"]
    N7["<b>[7] | Sanitärinstallation<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N8["<b>[8] | Innenausbau (Trockenbau/Böden)<br/>GP:0.0d | FP:-14.0d</b>"]:::critical
    N9["<b>[9] | Laufende Bauschuttreinigung<br/>GP:0.0d | FP:0.0d</b>"]:::critical
    N10["<b>[10] | Abnahme<br/>GP:0.0d | FP:0.0d</b>"]:::critical

    N1 --> N3
    N1 ==> N2
    N3 --> N4
    N4 --> N5
    N5 --> N10
    N5 ==> N6
    N5 ==> N7
    N6 --> N8
    N7 --> N8
    N8 --> N10
    N8 --o N9
    N9 --> N10

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Grube ausheben | 3.0d | 0.0d | 3.0d | 0.0d | 3.0d | 0.0d | -3.0d | JA |
| 2 | Erde abtransportieren | 4.0d | 0.0d | 4.0d | 0.0d | 4.0d | 0.0d | 0.0d | JA |
| 3 | Fundament gießen | 2.0d | 3.0d | 5.0d | 3.0d | 5.0d | 0.0d | 0.0d | JA |
| 4 | Fundament trocknen | 7.0d | 5.0d | 12.0d | 5.0d | 12.0d | 0.0d | 0.0d | JA |
| 5 | Mauerwerk errichten | 10.0d | 12.0d | 22.0d | 12.0d | 22.0d | 0.0d | -10.0d | JA |
| 6 | Elektroinstallation | 5.0d | 12.0d | 17.0d | 13.0d | 18.0d | 1.0d | 1.0d |  |
| 7 | Sanitärinstallation | 6.0d | 12.0d | 18.0d | 12.0d | 18.0d | 0.0d | 0.0d | JA |
| 8 | Innenausbau (Trockenbau/Böden) | 12.0d | 18.0d | 30.0d | 18.0d | 30.0d | 0.0d | -14.0d | JA |
| 9 | Laufende Bauschuttreinigung | 14.0d | 16.0d | 30.0d | 16.0d | 30.0d | 0.0d | 0.0d | JA |
| 10 | Abnahme | 1.0d | 30.0d | 31.0d | 30.0d | 31.0d | 0.0d | 0.0d | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Einfamilienhaus-Bau
    dateFormat  YYYY-MM-DD
    axisFormat  %d.%m

    section Wochenenden
    WE 04.04 :crit, 2026-04-04, 2026-04-05
    WE 11.04 :crit, 2026-04-11, 2026-04-12
    WE 18.04 :crit, 2026-04-18, 2026-04-19
    WE 25.04 :crit, 2026-04-25, 2026-04-26
    WE 02.05 :crit, 2026-05-02, 2026-05-02
    section Feiertage
    03.04 Karfreitag :crit, 2026-04-03, 2026-04-03
    06.04 Ostermontag :crit, 2026-04-06, 2026-04-06
    01.05 Tag der Arbeit :crit, 2026-05-01, 2026-05-01
    section Tasks
    [1] Grube ausheben (KRIT) :crit, 2026-04-01, 2026-04-04
    [2] Erde abtransportieren (KRIT) :crit, 2026-04-01, 2026-04-05
    [3] Fundament gießen (KRIT) :crit, 2026-04-04, 2026-04-06
    [4] Fundament trocknen (KRIT) :crit, 2026-04-06, 2026-04-13
    [5] Mauerwerk errichten (KRIT) :crit, 2026-04-13, 2026-04-23
    [6] Elektroinstallation :2026-04-13, 2026-04-18
    [7] Sanitärinstallation (KRIT) :crit, 2026-04-13, 2026-04-19
    [8] Innenausbau (Trockenbau/Böden) (KRIT) :crit, 2026-04-19, 2026-05-01
    [9] Laufende Bauschuttreinigung (KRIT) :crit, 2026-04-17, 2026-05-01
    [10] Abnahme (KRIT) :crit, 2026-05-01, 2026-05-02
```

---

### Resource List

*Keine Ressourcen-Informationen verfügbar.*

---

### Kostenübersicht

*Keine Kostendaten verfügbar – Stundensätze fehlen.*
