# Beispielprojekte in sproject

## Übersicht

Die Beispielprojekte demonstrieren verschiedene Funktionen und Anwendungsfälle von sproject:

| Projekt | Hauptmerkmale | Verwendungszweck |
|---------|---------------|------------------|
| **hausbau.json** | AA, EE, AE Abhängigkeiten | Verschiedene Abhängigkeitstypen |
| **erdaushub.json** | Loop-Tasks, Subtasks, Pausen | Baustellenplanung mit Pausen |
| **tankdesign.json** | Klassische EA-Abhängigkeiten | Standard-Projektplanung |
| **pizzas.json** | Instance-Tasks | Produktionsplanung |
| **fassadenbau.json** | PersonProject mit Ressourcen | Ressourcenplanung |

---

## 1. hausbau.json - Verschiedene Abhängigkeitstypen

### Zweck
Demonstriert alle vier CPM-Abhängigkeitstypen in einem realitätsnahen Hausbau-Projekt.

### Projektstruktur

```
Bauphase:
├── 1. Grube ausheben (3d)
│   ├─[EA]→ 3. Fundament gießen
│   └─[AA]→ 2. Erde abtransportieren (parallel)
├── 3. Fundament gießen (2d)
│   └─[EA]→ 4. Fundament trocknen
├── 4. Fundament trocknen (7d)
│   └─[EA]→ 5. Mauerwerk errichten
└── 5. Mauerwerk errichten (10d)
    ├─[EA]→ 10. Abnahme
    ├─[AA]→ 6. Elektroinstallation (parallel)
    └─[AA]→ 7. Sanitärinstallation (parallel)

Software-Phase:
├── 8. Programmierung (8d)
│   ├─[EA]→ 10. Abnahme
│   └─[EE]→ 9. Dokumentation (endet gleichzeitig)
└── 9. Dokumentation (8d)
    └─[EA]→ 10. Abnahme
```

### Abhängigkeitstypen im Detail

#### 1. EA (Ende-Anfang) - Standard
```json
{
  "id": 3,
  "name": "Fundament gießen",
  "duration": "2d",
  "successors": [4]  // Task 4 startet NACH Ende von Task 3
}
```
**Anwendung:** Normale sequenzielle Abfolge (Grube → Fundament → Trocknen → Mauern)

#### 2. AA (Anfang-Anfang) - Parallele Arbeit
```json
{
  "id": 1,
  "name": "Grube ausheben",
  "duration": "3d",
  "successors": [3],
  "successors_aa": [2]  // Task 2 startet SOBALD Task 1 startet
}
```
**Anwendung:**
- **Erde abtransportieren** beginnt sobald **Grube ausheben** beginnt (parallel)
- **Elektroinstallation** beginnt sobald **Mauerwerk** beginnt (parallel)
- **Sanitärinstallation** beginnt sobald **Mauerwerk** beginnt (parallel)

**Vorteil:** Zeitersparnis durch parallele Ausführung

#### 3. EE (Ende-Ende) - Gleichzeitiges Ende
```json
{
  "id": 8,
  "name": "Programmierung",
  "duration": "8d",
  "successors": [10],
  "successors_ee": [9]  // Task 9 endet WENN Task 8 endet
}
```
**Anwendung:**
- **Dokumentation** endet wenn **Programmierung** endet
- Stellt sicher dass Doku und Code gleichzeitig fertig sind

**Vorteil:** Synchronisierte Abschlüsse

### Projektergebnisse

**Projektdauer:** 33 Tage (mit Wochenenden)

**Kritischer Pfad:** Grube → Fundament → Trocknen → Mauern → Abnahme

**Zeitersparnis durch AA:**
- Ohne AA: Erde abtransportieren würde nach Grube starten → +4 Tage
- Mit AA: Parallel während Grube → 0 zusätzliche Tage

### Verwendung
```bash
# Excel mit Gantt-Chart erstellen
python lib/sproject.py --project examples/hausbau.json --export xlsx --gantt --resource

# Ergebnis ansehen
results/hausbau.xlsx
```

---

## 2. erdaushub.json - Loop-Tasks mit Pausen

### Zweck
Realistische Baustellenplanung mit:
- Loop-Tasks (wiederholte Lade-/Transportzyklen)
- Automatische Pausenberechnung (Arbeitszeitgesetz, Lenkzeitunterbrechungen)
- Personenmodell mit Arbeitszeiten
- Wochenend-Blocker

### Projektstruktur

```
1. Initialisierung (15m)
   ↓
2. Belade-Zyklus (Loop: 84 Iterationen)
   ├── Beladen (8-12m, abhängig von Bagger-Kapazität)
   │   └── Pause nach 6h (Arbeitszeitgesetz)
   ├── Transport-Umlauf (40m, LKW-spezifisch)
   │   └── Pause nach 4.5h (Lenkzeitunterbrechung)
   └── Wochenende (nach Fr 17:00 → Mo 07:00)
```

### Loop-Task Mechanismus

```json
{
  "id": 2,
  "name": "Belade-Zyklus",
  "is_loop": true,
  "loop_until": "total_volume <= 0",  // Stoppe wenn 1000m³ abgebaut
  "cycle_prefix": "F",                // Erzeugt: 2-F1, 2-F2, ...
  "successors": [],
  "subtasks": [
    {
      "name": "Beladen",
      "required_resources": ["B1", "any_truck"],
      "resources": ["R_PERS3&B1", "R_PERS1&L1 | R_PERS2&L2"],
      "duration_formula": "resource.truck.capacity / resource.B1.loading_speed_per_min"
    },
    {
      "name": "Transport-Umlauf",
      "required_resources": ["current_truck"],
      "resources": ["R_PERS1&L1 | R_PERS2&L2"],
      "duration": "resource.truck.transport_cycle_fixed"
    }
  ]
}
```

### Automatische Pausenberechnung

#### 1. Arbeitszeitgesetz (§4 ArbZG)
**Regel:** Nach 6 Stunden Arbeit mindestens 30 Minuten Pause

```
Person: Bodo Schmidt (Baggerfahrer)
├── Task 2-F1-BEL bis 2-F44-BEL (6 Stunden gearbeitet)
├── [PAUSE] 2-F44-BEL-BRK-P3 (30 Minuten)
│   - is_break: true
│   - Puffer: 0.0 (keine Flexibilität)
│   - Kosten: 0 (Pause kostet nichts)
└── Task 2-F45-BEL (weiter arbeiten)
```

#### 2. Lenkzeitunterbrechungen (Fahrpersonalgesetz)
**Regel:** Nach 4,5 Stunden Lenkzeit mindestens 45 Minuten Pause

```
Person: Max Mustermann (LKW-Fahrer 1)
├── Task 2-F1-TRA bis 2-F11-TRA (4.5 Stunden gefahren)
├── [PAUSE] 2-F11-TRA-BRK-P1 (45 Minuten)
│   - is_break: true
│   - FAZ = SAZ (fixe Startzeit)
│   - FEZ = SEZ (fixe Endzeit)
└── Task 2-F12-TRA (weiter fahren)
```

#### 3. Wochenend-Blocker
**Regel:** Samstag 17:00 bis Montag 07:00 keine Arbeit

```
Freitag 17:00:
├── Task 2-F13-TRA (letzter Transport vor Wochenende)
├── [WOCHENENDE] WE-2-F13-TRA-2-F14-BEL (2 Tage)
│   - is_blocker: true
│   - Duration: 2.0 Tage
│   - Puffer: 0.0 (kritisch)
│   - Kosten: 0 (keine Arbeit)
└── Montag 07:00: Task 2-F14-BEL (erste Beladung nach Wochenende)
```

### Ressourcen & Personen

#### Personen (3)
```json
{
  "id": "PERS_MAX",
  "name": "Max Mustermann",
  "role": "LKW-Fahrer",
  "hourly_rate": 35.0,
  "workinghours_override": {
    "days": ["mon", "tue", "wed", "thu", "fri"],
    "start": "07:00",
    "end": "17:00"
  },
  "rest_intervals": "resting_times"  // Verweis auf Pausen-Regeln
}
```

#### Maschinen (3)
- **B1**: Raupenbagger (Baggerkapazität: 0.9m³, Geschwindigkeit: 12m³/h)
- **L1**: LKW 18 Tonnen (Kapazität: 12m³, Umlaufzeit: 40 min)
- **L2**: LKW 26 Tonnen (Kapazität: 18m³, Umlaufzeit: 40 min)

### Dynamische Dauer-Berechnung

```javascript
// Beladen-Dauer hängt von LKW-Größe ab
duration = resource.truck.capacity / resource.B1.loading_speed_per_min

// Beispiel:
// LKW 18t (12m³) / Bagger (12m³/h) = 60 Minuten = 1 Stunde ❌
// Korrekt: 12m³ / (12m³/60min) = 12m³ / 0.2m³/min = 60 min ✓
```

### Projektergebnisse

**Projektdauer:** 12.4 Tage (inkl. 2 Wochenenden)
- Reine Arbeitszeit: ~8.4 Tage
- Wochenenden: 2x2 = 4 Tage

**Anzahl Tasks:** 174
- Init: 1
- Belade-Zyklen: 84
- Transport-Zyklen: 84
- Pausen: 5 (3x Arbeitszeitgesetz, 2x Lenkzeit)
- Wochenenden: 2

**Kosten:**
- Personalkosten: ~84 Stunden × 35€/h = ~2.940€
- Maschinenkosten: Nach Maschinenstunden

### Verwendung

```bash
# Vollständige Auswertung mit Excel
python lib/sproject.py --project examples/erdaushub.json --export xlsx --gantt --resource

# Nur Text-Ausgabe
python lib/sproject.py --project examples/erdaushub.json --export txt

# Ergebnisse ansehen
results/erdaushub.xlsx  # Excel mit Gantt (Stunden-Auflösung!)
results/erdaushub.txt   # Text-Report
```

### Besonderheiten

#### 1. Stunden-Auflösung im Gantt-Chart
Da minimale Task-Dauer 8 Minuten beträgt, wird automatisch **Stunden-Auflösung** gewählt:
- Timeline: 0-7 Uhr (8 Stunden Arbeitstag)
- Wochenenden: Sa/So als einzelne Spalten
- Pausen: Sichtbar als kurze Tasks

#### 2. Kritischer Pfad
Der gesamte Belade-Zyklus ist kritisch:
```
Init → F1-BEL → F1-TRA → F2-BEL → ... → F84-TRA
```
Jede Verzögerung verschiebt das Projektende!

#### 3. Ressourcen-Auslastung
In der Resource List sieht man:
- Bagger B1: Durchgehend ausgelastet (außer Pausen)
- LKW L1/L2: Abwechselnd im Einsatz
- Personen: Arbeitszeit vs. Pausen visualisiert

---

## 3. Weitere Beispiele (Kurzübersicht)

### tankdesign.json - Klassisches Projektmanagement
**Merkmale:**
- Reine EA-Abhängigkeiten (Standard)
- 8 Tasks, 70 Tage Projektdauer
- Demonstriert klassische CPM-Berechnung

**Verwendung:** Lernbeispiel für Standard-CPM

### pizzas.json - Produktionsplanung
**Merkmale:**
- Instance-Tasks (mehrere Pizzen)
- Sehr kurze Dauern (Minuten)
- Zeigt Stunden-Auflösung

**Verwendung:** Produktions-/Fertigungsplanung

### fassadenbau.json - Ressourcenplanung
**Merkmale:**
- PersonProject mit 3 Personen
- Verschiedene Materialien und Maschinen
- Zeigt Ressourcen-Reports

**Verwendung:** Bauplanung mit Ressourcen

---

## Ausführung aller Beispiele

```bash
# Alle Beispiele auf einmal verarbeiten
cd bin
run_test.bat

# Ergebnisse in results/ Ordner:
results/hausbau.xlsx      # AA/EE Abhängigkeiten
results/erdaushub.xlsx    # Loop-Tasks mit Pausen (Stunden!)
results/tankdesign.xlsx   # Standard EA
results/pizzas.xlsx       # Instance-Tasks (Stunden!)
results/fassadenbau.xlsx  # PersonProject (Tage)
```

---

## Vergleich der Beispiele

| Feature | hausbau | erdaushub | tankdesign | pizzas | fassadenbau |
|---------|---------|-----------|------------|--------|-------------|
| **Abhängigkeitstypen** | EA, AA, EE | EA | EA | EA | EA |
| **Loop-Tasks** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Pausen** | ❌ | ✅ Auto | ❌ | ❌ | ❌ |
| **Wochenenden** | ✅ | ✅ Blocker | ✅ | ✅ | ✅ |
| **Personen** | ❌ | ✅ 3 | ❌ | ❌ | ✅ 3 |
| **Maschinen** | ❌ | ✅ 3 | ❌ | ✅ 1 | ✅ 2 |
| **Gantt-Auflösung** | Tage | **Stunden** | Tage | **Stunden** | Tage |
| **Projektdauer** | 33d | 12.4d | 70d | 1.2h | 6.8d |
| **Anzahl Tasks** | 10 | 174 | 8 | 4 | 5 |

---

## Weiterführende Dokumentation

- [DEPENDENCY_TYPES.md](DEPENDENCY_TYPES.md) - Detaillierte Erklärung aller Abhängigkeitstypen
- [../cfg/defaults.cfg](../cfg/defaults.cfg) - Projekt-Standards

---

## Eigene Beispiele erstellen

### Minimales Beispiel (EA)
```json
{
  "project": "Mein Projekt",
  "project_start": "2026-04-01",
  "tasks": [
    {"id": 1, "name": "Task A", "duration": "3d", "successors": [2]},
    {"id": 2, "name": "Task B", "duration": "2d", "successors": []}
  ]
}
```

### Mit AA-Abhängigkeiten
```json
{
  "id": 1,
  "name": "Hauptarbeit",
  "duration": "5d",
  "successors": [3],
  "successors_aa": [2]  // Task 2 startet parallel
}
```

### Mit PersonProject
```json
{
  "project": "Mein Projekt",
  "project_start": "2026-04-01",
  "persons": [
    {"id": "P1", "name": "Max", "email": "max@example.com", "role": "Dev", "hourly_rate": 50}
  ],
  "resources": [
    {"id": "PC1", "name": "Laptop", "type": "machine"}
  ],
  "tasks": [
    {"id": 1, "name": "Entwicklung", "duration": "5d", "resources": ["P1", "PC1"]}
  ]
}
```

Viel Erfolg beim Projektmanagement mit sproject! 🚀
