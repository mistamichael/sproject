# Fassadensanierung & Kellerisolierung - CPM Report

Erstellt am: 2026-03-20 16:35:25

## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Fassadensanierung & Kellerisolierung
- **Projektdauer:** 38.0h
- **Startdatum:** 2026-03-20 16:35
- **Enddatum (geschätzt):** 2026-03-25 10:35
- **Zeiteinheit:** hours
- **Anzahl Tasks:** 5
- **Kritische Tasks:** 5

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Erdarbeiten & Freilegung (Dauer: 8.0h)
- **[2]** Kellerisolierung (Perimeter) (Dauer: 6.0h)
- **[3]** Holzständerwerk & Holzfaserplatten (Dauer: 16.0h)
- **[4]** Zellulose Einblasdämmung (Dauer: 4.0h)
- **[5]** Verfüllen & Abschluss (Dauer: 4.0h)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Erdarbeiten & Freilegung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N2["<b>[2] | Kellerisolierung (Perimeter)<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N3["<b>[3] | Holzständerwerk & Holzfaserplatten<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N4["<b>[4] | Zellulose Einblasdämmung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N5["<b>[5] | Verfüllen & Abschluss<br/>GP:0.0h | FP:0.0h</b>"]:::critical

    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Erdarbeiten & Freilegung | 8.0h | 0.0h | 8.0h | 0.0h | 8.0h | 0.0h | 0.0h | JA |
| 2 | Kellerisolierung (Perimeter) | 6.0h | 8.0h | 14.0h | 8.0h | 14.0h | 0.0h | 0.0h | JA |
| 3 | Holzständerwerk & Holzfaserplatten | 16.0h | 14.0h | 30.0h | 14.0h | 30.0h | 0.0h | 0.0h | JA |
| 4 | Zellulose Einblasdämmung | 4.0h | 30.0h | 34.0h | 30.0h | 34.0h | 0.0h | 0.0h | JA |
| 5 | Verfüllen & Abschluss | 4.0h | 34.0h | 38.0h | 34.0h | 38.0h | 0.0h | 0.0h | JA |

---

### Gantt Chart (mit Wochenenden)

```mermaid
gantt
    title Fassadensanierung & Kellerisolierung
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m

    section Feiertage
    section Tasks
    [1] Erdarbeiten & Freilegung (KRIT) :crit, 2026-03-20 16:35, 2026-03-21 16:35
    [2] Kellerisolierung (Perimeter) (KRIT) :crit, 2026-03-21 16:35, 2026-03-21 22:35
    [3] Holzständerwerk & Holzfaserplatten (KRIT) :crit, 2026-03-21 22:35, 2026-03-23 22:35
    [4] Zellulose Einblasdämmung (KRIT) :crit, 2026-03-23 22:35, 2026-03-24 18:35
    [5] Verfüllen & Abschluss (KRIT) :crit, 2026-03-24 18:35, 2026-03-24 22:35
```

---

### Resource List

#### Ressourcenauslastung (Textform)

| Farbe | Name | Ressource | Anzahl Tasks | Tasks |
|---|---|---|---|---|
| <span style="background-color:#4472C4;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Zellulose-Einblasmaschine (EB1) | 1 | 4 |
| <span style="background-color:#4F73C2;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Holzfaserplatten & Ständerwerk (MAT_WOOD) | 1 | 3 |
| <span style="background-color:#5B74C0;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Perimeterdämmung XPS (MAT_XPS) | 1 | 2 |
| <span style="background-color:#6776BE;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Minibagger 3.5t (MB1) | 2 | 1, 5 |
| <span style="background-color:#7377BC;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | PERS_ERD (PERS_ERD) | 3 | 1, 2, 5 |
| <span style="background-color:#7F78BA;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | PERS_ISO (PERS_ISO) | 1 | 4 |
| <span style="background-color:#8B7AB8;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | PERS_ZIM (PERS_ZIM) | 1 | 3 |

#### Ressourcenauslastung (Gantt-Diagramm)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4472C4', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Zellulose-Einblasmaschine
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Zellulose-Einblasmaschine

    Zellulose Einblasdämmung    :t0, 2026-03-23 22:35, 2026-03-24 18:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4F73C2', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Holzfaserplatten & Ständerwerk
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Holzfaserplatten & Ständerwerk

    Holzständerwerk & Holz...   :t0, 2026-03-21 22:35, 2026-03-23 22:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#5B74C0', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Perimeterdämmung XPS
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Perimeterdämmung XPS

    Kellerisolierung (Peri...   :t0, 2026-03-21 16:35, 2026-03-21 22:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#6776BE', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Minibagger 3.5t
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Minibagger 3.5t

    Erdarbeiten & Freilegung    :t0, 2026-03-20 16:35, 2026-03-21 16:35
    Verfüllen & Abschluss       :t1, 2026-03-24 18:35, 2026-03-24 22:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#7377BC', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: PERS_ERD
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section PERS_ERD

    Erdarbeiten & Freilegung    :t0, 2026-03-20 16:35, 2026-03-21 16:35
    Kellerisolierung (Peri...   :t1, 2026-03-21 16:35, 2026-03-21 22:35
    Verfüllen & Abschluss       :t2, 2026-03-24 18:35, 2026-03-24 22:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#7F78BA', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: PERS_ISO
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section PERS_ISO

    Zellulose Einblasdämmung    :t0, 2026-03-23 22:35, 2026-03-24 18:35
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#8B7AB8', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: PERS_ZIM
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section PERS_ZIM

    Holzständerwerk & Holz...   :t0, 2026-03-21 22:35, 2026-03-23 22:35
```

#### Personen

| Person | Kosten/Stunde | Abwesenheiten im Projektzeitraum | Abwesenheiten kurz nach dem Projektzeitraum |
|---|---|---|---|
| Thomas Tiefbau | 60.00 €/h | keine | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |
| Stefan Schnitt | 65.00 €/h | keine | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |
| Klaus Flocke | 55.00 €/h | keine | 2026-04-03 (Karfreitag), 2026-04-06 (Ostermontag) |

#### Ressourcen-Details

| Ressource | Person | Typ |
|---|---|---|
| Minibagger 3.5t (MB1) |  | machine |
| Zellulose-Einblasmaschine (EB1) |  | machine |
| Perimeterdämmung XPS (MAT_XPS) |  | material |
| Holzfaserplatten & Ständerwerk (MAT_WOOD) |  | material |

---

### Kostenübersicht

| Ressource | Typ | Stunden | €/h | Bereitst. € | Lohnkosten € | Gesamt € |
|---|---|---|---|---|---|---|
| Zellulose-Einblasmaschine | machine | 4.0 | 45.00 | 50.00 | 180.00 | **230.00** |
| Minibagger 3.5t | machine | 12.0 | 85.00 | 120.00 | 1020.00 | **1140.00** |

**Zusammenfassung:**

- Maschinenkosten (Lohn): **1200.00 €**
- Bereitstellungskosten: **170.00 €**
- **Gesamtkosten: 1370.00 €**
