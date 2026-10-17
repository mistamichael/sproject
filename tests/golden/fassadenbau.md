# Fassadensanierung & Kellerisolierung - CPM Report


## CPM Analyse

### Projektzusammenfassung

- **Projekt:** Fassadensanierung & Kellerisolierung
- **Projektdauer:** 38.0h
- **Startdatum:** 2026-03-02 00:00
- **Enddatum (geschätzt):** 2026-03-06 18:00
- **Zeiteinheit:** hours
- **Anzahl Tasks:** 8
- **Kritische Tasks:** 8

---

### Kritischer Pfad

Der kritische Pfad besteht aus folgenden Tasks:

- **[1]** Erdarbeiten & Freilegung (Dauer: 8.0h)
- **[1-BRK-P_ERD]** Pause: Thomas Tiefbau (Lenkzeitunterbrechung (falls Materialtransport anfällt)) (Dauer: 0.8h)
- **[2]** Kellerisolierung (Perimeter) (Dauer: 6.0h)
- **[2-BRK-P_ERD]** Pause: Thomas Tiefbau (Vorschrift laut Arbeitszeitgesetz für alle Gewerke) (Dauer: 0.5h)
- **[3]** Holzständerwerk & Holzfaserplatten (Dauer: 16.0h)
- **[3-BRK-P_ZIM]** Pause: Stefan Schnitt (Lenkzeitunterbrechung (falls Materialtransport anfällt)) (Dauer: 0.8h)
- **[4]** Zellulose Einblasdämmung (Dauer: 4.0h)
- **[5]** Verfüllen & Abschluss (Dauer: 4.0h)

---

### Netzplan

```mermaid
graph TD

    N1["<b>[1] | Erdarbeiten & Freilegung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N1-BRK-P_ERD["<b>[1-BRK-P_ERD] | Pause: Thomas Tiefbau (Lenkzeitunterbrechung (falls Materialtransport anfällt))<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N2["<b>[2] | Kellerisolierung (Perimeter)<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N2-BRK-P_ERD["<b>[2-BRK-P_ERD] | Pause: Thomas Tiefbau (Vorschrift laut Arbeitszeitgesetz für alle Gewerke)<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N3["<b>[3] | Holzständerwerk & Holzfaserplatten<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N3-BRK-P_ZIM["<b>[3-BRK-P_ZIM] | Pause: Stefan Schnitt (Lenkzeitunterbrechung (falls Materialtransport anfällt))<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N4["<b>[4] | Zellulose Einblasdämmung<br/>GP:0.0h | FP:0.0h</b>"]:::critical
    N5["<b>[5] | Verfüllen & Abschluss<br/>GP:0.0h | FP:0.0h</b>"]:::critical

    N1 --> N2
    N1 --> N1-BRK-P_ERD
    N2 --> N3
    N2 --> N2-BRK-P_ERD
    N3 --> N4
    N3 --> N3-BRK-P_ZIM
    N4 --> N5

    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    classDef normal   fill:#4472c4,stroke:#2f5496,color:#fff
```

---

### Alle Tasks

| ID | Name | Dauer | FAZ | FEZ | SAZ | SEZ | GP | FP | Krit. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Erdarbeiten & Freilegung | 8.0h | 0.0h | 8.0h | 0.0h | 8.0h | 0.0h | 0.0h | JA |
| 1-BRK-P_ERD | Pause: Thomas Tiefbau (Lenkzeitu... | 0.8h | 8.0h | 8.8h | 8.0h | 8.8h | 0.0h | 0.0h | JA |
| 2 | Kellerisolierung (Perimeter) | 6.0h | 8.0h | 14.0h | 8.0h | 14.0h | 0.0h | 0.0h | JA |
| 2-BRK-P_ERD | Pause: Thomas Tiefbau (Vorschrif... | 0.5h | 14.0h | 14.5h | 14.0h | 14.5h | 0.0h | 0.0h | JA |
| 3 | Holzständerwerk & Holzfaserplatten | 16.0h | 14.0h | 30.0h | 14.0h | 30.0h | 0.0h | 0.0h | JA |
| 3-BRK-P_ZIM | Pause: Stefan Schnitt (Lenkzeitu... | 0.8h | 30.0h | 30.8h | 30.0h | 30.8h | 0.0h | 0.0h | JA |
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
    [1] Erdarbeiten & Freilegung (KRIT) :crit, 2026-03-02 00:00, 2026-03-03 00:00
    [1-BRK-P_ERD] Pause Thomas Tiefbau (Lenkzeitunterbrechung (falls Materialtransport anfällt)) (KRIT) :crit, 2026-03-03 00:00, 2026-03-03 00:00
    [2] Kellerisolierung (Perimeter) (KRIT) :crit, 2026-03-03 00:00, 2026-03-03 06:00
    [2-BRK-P_ERD] Pause Thomas Tiefbau (Vorschrift laut Arbeitszeitgesetz für alle Gewerke) (KRIT) :crit, 2026-03-03 06:00, 2026-03-03 06:00
    [3] Holzständerwerk & Holzfaserplatten (KRIT) :crit, 2026-03-03 06:00, 2026-03-05 06:00
    [3-BRK-P_ZIM] Pause Stefan Schnitt (Lenkzeitunterbrechung (falls Materialtransport anfällt)) (KRIT) :crit, 2026-03-05 06:00, 2026-03-05 06:00
    [4] Zellulose Einblasdämmung (KRIT) :crit, 2026-03-05 06:00, 2026-03-06 02:00
    [5] Verfüllen & Abschluss (KRIT) :crit, 2026-03-06 02:00, 2026-03-06 06:00
```

---

### Resource List

#### Ressourcenauslastung (Textform)

| Farbe | Name | Ressource | Anzahl Tasks | Tasks |
|---|---|---|---|---|
| <span style="background-color:#4472C4;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Zellulose-Einblasmaschine (EB1) | 1 | 4 |
| <span style="background-color:#5B74C0;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Holzfaserplatten & Ständerwerk (MAT_WOOD) | 1 | 3 |
| <span style="background-color:#7377BC;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Perimeterdämmung XPS (MAT_XPS) | 1 | 2 |
| <span style="background-color:#8B7AB8;padding:2px 6px;color:#fff;border-radius:3px;">■</span> |  | Minibagger 3.5t (MB1) | 2 | 1, 5 |
| <span style="background-color:#5B9BD5;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Thomas Tiefbau | LKW-Fahrer Max (R_PERS_ERD) | 3 | 1, 2, 5 |
| <span style="background-color:#2F5597;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Klaus Flocke | Baggerführer Bodo (R_PERS_ISO) | 1 | 4 |
| <span style="background-color:#4472C4;padding:2px 6px;color:#fff;border-radius:3px;">■</span> | Stefan Schnitt | LKW-Fahrer Heinz (R_PERS_ZIM) | 1 | 3 |

#### Ressourcenauslastung (Gantt-Diagramm)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4472C4', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Zellulose-Einblasmaschine
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Zellulose-Einblasmaschine

    Zellulose Einblasdämmung    :t0, 2026-03-05 06:00, 2026-03-06 02:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#5B74C0', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Holzfaserplatten & Ständerwerk
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Holzfaserplatten & Ständerwerk

    Holzständerwerk & Holz...   :t0, 2026-03-03 06:00, 2026-03-05 06:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#7377BC', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Perimeterdämmung XPS
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Perimeterdämmung XPS

    Kellerisolierung (Peri...   :t0, 2026-03-03 00:00, 2026-03-03 06:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#8B7AB8', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Minibagger 3.5t
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Minibagger 3.5t

    Erdarbeiten & Freilegung    :t0, 2026-03-02 00:00, 2026-03-03 00:00
    Verfüllen & Abschluss       :t1, 2026-03-06 02:00, 2026-03-06 06:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#5B9BD5', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: LKW-Fahrer Max
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section LKW-Fahrer Max

    Erdarbeiten & Freilegung    :t0, 2026-03-02 00:00, 2026-03-03 00:00
    Kellerisolierung (Peri...   :t1, 2026-03-03 00:00, 2026-03-03 06:00
    Verfüllen & Abschluss       :t2, 2026-03-06 02:00, 2026-03-06 06:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#2F5597', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: Baggerführer Bodo
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section Baggerführer Bodo

    Zellulose Einblasdämmung    :t0, 2026-03-05 06:00, 2026-03-06 02:00
```

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'taskBkgColor': '#4472C4', 'taskBorderColor': '#333', 'taskTextColor': '#fff'}}}%%
gantt
    title Ressourcen-Auslastung: LKW-Fahrer Heinz
    dateFormat  YYYY-MM-DD HH:mm
    axisFormat  %d.%m
    excludes    weekends, 2026-01-01, 2026-01-06, 2026-04-03, 2026-04-06, 2026-05-01, 2026-05-14, 2026-05-25, 2026-06-04, 2026-08-15, 2026-10-03, 2026-11-01, 2026-12-25, 2026-12-26

    section LKW-Fahrer Heinz

    Holzständerwerk & Holz...   :t0, 2026-03-03 06:00, 2026-03-05 06:00
```

#### Personen

| Person | Kosten/Stunde | Abwesenheiten im Projektzeitraum | Abwesenheiten kurz nach dem Projektzeitraum |
|---|---|---|---|
| Thomas Tiefbau | 60.00 €/h | keine | keine |
| Stefan Schnitt | 65.00 €/h | keine | keine |
| Klaus Flocke | 55.00 €/h | keine | keine |

#### Ressourcen-Details

| Ressource | Person | Typ |
|---|---|---|
| LKW-Fahrer Max (R_PERS_ERD) | Thomas Tiefbau | person |
| LKW-Fahrer Heinz (R_PERS_ZIM) | Stefan Schnitt | person |
| Baggerführer Bodo (R_PERS_ISO) | Klaus Flocke | person |
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
| LKW-Fahrer Max | person | 18.0 | 60.00 | — | 1080.00 | **1080.00** |
| Baggerführer Bodo | person | 4.0 | 55.00 | — | 220.00 | **220.00** |
| LKW-Fahrer Heinz | person | 16.0 | 65.00 | — | 1040.00 | **1040.00** |

**Zusammenfassung:**

- Personalkosten: **2340.00 €**
- Maschinenkosten (Lohn): **1200.00 €**
- Bereitstellungskosten: **170.00 €**
- **Gesamtkosten: 3710.00 €**
