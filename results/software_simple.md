# Software Entwicklung Projekt - CPM Report

Erstellt am: 2026-03-20 16:36:11

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Software Entwicklung Projekt
- **Projektdauer:** 124.0h
- **Startdatum:** 2026-03-03 09:00
- **Enddatum (geschätzt):** 2026-03-18 21:00
- **Zeiteinheit:** hours
- **Anzahl Tasks:** 8
- **Kritische Tasks:** 7

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Projektinitialisierung (Dauer: 4.0h)
- **[2]** Requirements Analyse (Dauer: 16.0h)
- **[4]** Backend Entwicklung (Dauer: 40.0h)
- **[5]** Frontend Entwicklung (Dauer: 32.0h)
- **[6]** Testing & QA (Dauer: 20.0h)
- **[7]** Deployment (Dauer: 8.0h)
- **[8]** Projektabschluss (Dauer: 4.0h)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Projektinitialisierung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N2["<b>[2] | Requirements Analyse<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N3["[3] | UI/UX Design<br/>GP:16.0h | FP:16.0h"]
    N4["<b>[4] | Backend Entwicklung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N5["<b>[5] | Frontend Entwicklung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N6["<b>[6] | Testing & QA<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N7["<b>[7] | Deployment<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N8["<b>[8] | Projektabschluss<br/>GP:0.0h | FP:0.0h</b>"]:::critical

    N1 --> N2
    N2 --> N3
    N2 --> N4
    N3 --> N5
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Projektinitialisierung | 4.0h | 0.0h | 4.0h | 0.0h | 4.0h | 0.0h | 0.0h | JA |
| 2 | Requirements Analyse | 16.0h | 4.0h | 20.0h | 4.0h | 20.0h | 0.0h | 0.0h | JA |
| 3 | UI/UX Design | 24.0h | 20.0h | 44.0h | 36.0h | 60.0h | 16.0h | 16.0h |  |
| 4 | Backend Entwicklung | 40.0h | 20.0h | 60.0h | 20.0h | 60.0h | 0.0h | 0.0h | JA |
| 5 | Frontend Entwicklung | 32.0h | 60.0h | 92.0h | 60.0h | 92.0h | 0.0h | 0.0h | JA |
| 6 | Testing & QA | 20.0h | 92.0h | 112.0h | 92.0h | 112.0h | 0.0h | 0.0h | JA |
| 7 | Deployment | 8.0h | 112.0h | 120.0h | 112.0h | 120.0h | 0.0h | 0.0h | JA |
| 8 | Projektabschluss | 4.0h | 120.0h | 124.0h | 120.0h | 124.0h | 0.0h | 0.0h | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Software Entwicklung Projekt
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m

    section Feiertage
    section Tasks
    [1] Projektinitialisierung (KRIT) :crit, 2026-03-03 09:00, 2026-03-03 13:00
    [2] Requirements Analyse (KRIT) :crit, 2026-03-03 13:00, 2026-03-05 13:00
    [3] UI/UX Design :2026-03-05 13:00, 2026-03-08 13:00
    [4] Backend Entwicklung (KRIT) :crit, 2026-03-05 13:00, 2026-03-10 13:00
    [5] Frontend Entwicklung (KRIT) :crit, 2026-03-10 13:00, 2026-03-14 13:00
    [6] Testing & QA (KRIT) :crit, 2026-03-14 13:00, 2026-03-17 09:00
    [7] Deployment (KRIT) :crit, 2026-03-17 09:00, 2026-03-18 09:00
    [8] Projektabschluss (KRIT) :crit, 2026-03-18 09:00, 2026-03-18 13:00
```

---

### Resource List

#### Ressourcenauslastung (Textform)

| Farbe | Name | Ressource | Anzahl Tasks | Tasks |
|---|---|---|---|---|
| <span style="background-color:#4472C4;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Charlie | UI/UX Designer (R_DES1) | 1 | 3 |
| <span style="background-color:#5B74C0;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Alice | Senior Developer (R_DEV1) | 4 | 2, 4, 6, 7 |
| <span style="background-color:#7377BC;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Bob | Junior Developer (R_DEV2) | 2 | 5, 6 |
| <span style="background-color:#8B7AB8;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Diana | Project Manager (R_PM1) | 3 | 1, 2, 8 |

#### Ressourcenauslastung (Gantt-Diagramm)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4472C4', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: UI/UX Designer
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section UI/UX Designer

    UI/UX Design                :t0, 2026-03-05 13:00, 2026-03-08 13:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#5B74C0', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Senior Developer
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Senior Developer

    Requirements Analyse        :t0, 2026-03-03 13:00, 2026-03-05 13:00
    Backend Entwicklung         :t1, 2026-03-05 13:00, 2026-03-10 13:00
    Testing & QA                :t2, 2026-03-14 13:00, 2026-03-17 09:00
    Deployment                  :t3, 2026-03-17 09:00, 2026-03-18 09:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#7377BC', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Junior Developer
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Junior Developer

    Frontend Entwicklung        :t0, 2026-03-10 13:00, 2026-03-14 13:00
    Testing & QA                :t1, 2026-03-14 13:00, 2026-03-17 09:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#8B7AB8', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Project Manager
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Project Manager

    Projektinitialisierung      :t0, 2026-03-03 09:00, 2026-03-03 13:00
    Requirements Analyse        :t1, 2026-03-03 13:00, 2026-03-05 13:00
    Projektabschluss            :t2, 2026-03-18 09:00, 2026-03-18 13:00
```

#### Personen

| Person | Kosten/Stunde | Abwesenheiten im Projektzeitraum | Abwesenheiten kurz nach dem Projektzeitraum |
|---|---|---|---|
| Alice | 85.00 €/h | keine | 2026-04-01 – 2026-04-05 (Urlaub Alice), 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |
| Bob | 55.00 €/h | keine | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |
| Charlie | 70.00 €/h | 2026-03-16 (Fortbildung) | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |
| Diana | 95.00 €/h | keine | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |

#### Ressourcen-Details

| Ressource | Person | Typ |
|---|---|---|
| Senior Developer (R_DEV1) | Alice | person |
| Junior Developer (R_DEV2) | Bob | person |
| UI/UX Designer (R_DES1) | Charlie | person |
| Project Manager (R_PM1) | Diana | person |

---

### Kostenübersicht

| Ressource | Typ | Stunden | €/h | Bereitst. € | Lohnkosten € | Gesamt € |
|---|---|---|---|---|---|---|
| UI/UX Designer | person | 24.0 | 70.00 | — | 1680.00 | **1680.00** |
| Senior Developer | person | 84.0 | 85.00 | — | 7140.00 | **7140.00** |
| Junior Developer | person | 52.0 | 55.00 | — | 2860.00 | **2860.00** |
| Project Manager | person | 24.0 | 95.00 | — | 2280.00 | **2280.00** |

**Zusammenfassung:**

- Personalkosten: **13960.00 €**
- **Gesamtkosten: 13960.00 €**
