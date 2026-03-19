# Abhängigkeitstypen in sproject

## Übersicht

sproject unterstützt vier verschiedene Abhängigkeitstypen für Tasks, basierend auf der Critical Path Method (CPM):

1. **EA** - Ende-Anfang (Normalfolge) - **Standard**
2. **AA** - Anfang-Anfang (Anfangsfolge)
3. **EE** - Ende-Ende (Endfolge)
4. **AE** - Anfang-Ende (Sprungfolge)

## 1. EA - Ende-Anfang (Normalfolge) ✅ Standard

**Regel:** Der Nachfolger kann erst beginnen, wenn der Vorgänger beendet ist.

**Formel:** `FAZ(Nachfolger) >= FEZ(Vorgänger)`

**Beispiel:**
```json
{
  "id": 3,
  "name": "Wand verputzen",
  "duration": "2d",
  "successors": [2]  // Task 2 muss vorher beendet sein
}
```

**Anwendung:**
- Wand mauern → Wand verputzen
- Fundament gießen → Fundament trocknen
- Code schreiben → Code testen

## 2. AA - Anfang-Anfang (Anfangsfolge)

**Regel:** Der Nachfolger kann erst beginnen, wenn der Vorgänger begonnen hat.

**Formel:** `FAZ(Nachfolger) >= FAZ(Vorgänger)`

**Beispiel:**
```json
{
  "id": 1,
  "name": "Grube ausheben",
  "duration": "3d",
  "successors_aa": [2]  // Task 2 startet parallel sobald Task 1 startet
},
{
  "id": 2,
  "name": "Erde abtransportieren",
  "duration": "4d"
}
```

**Anwendung:**
- Grube ausheben → Erde abtransportieren (parallel)
- Mauerwerk errichten → Elektroinstallation beginnen (parallel)
- Daten sammeln → Datenanalyse beginnen (parallel)

## 3. EE - Ende-Ende (Endfolge)

**Regel:** Der Nachfolger kann erst beendet werden, wenn der Vorgänger beendet ist.

**Formel:** `FEZ(Nachfolger) >= FEZ(Vorgänger)`

**Beispiel:**
```json
{
  "id": 8,
  "name": "Programmierung",
  "duration": "8d",
  "successors_ee": [9]  // Task 9 endet gleichzeitig mit Task 8
},
{
  "id": 9,
  "name": "Dokumentation",
  "duration": "8d"
}
```

**Anwendung:**
- Programmierung → Dokumentation (endet gleichzeitig)
- Hauptprojekt → Qualitätssicherung (endet gleichzeitig)
- Produktion → Qualitätskontrolle (endet gleichzeitig)

## 4. AE - Anfang-Ende (Sprungfolge)

**Regel:** Der Nachfolger kann erst beendet werden, wenn der Vorgänger begonnen hat.

**Formel:** `FEZ(Nachfolger) >= FAZ(Vorgänger)`

**Beispiel:**
```json
{
  "id": 10,
  "name": "Nachtwächter Schicht 1",
  "duration": "8h",
  "successors_ae": [11]  // Schicht 1 endet wenn Schicht 2 beginnt
},
{
  "id": 11,
  "name": "Nachtwächter Schicht 2",
  "duration": "8h"
}
```

**Anwendung:**
- Schichtablösung (Schicht 1 endet wenn Schicht 2 beginnt)
- Übergabe-Szenarien
- Just-in-Time Lieferungen

## JSON-Syntax

### Einfache EA-Abhängigkeit (Standard)
```json
{
  "id": 5,
  "name": "Task Name",
  "duration": "3d",
  "successors": [3, 4]  // Wartet auf Task 3 und 4 (EA)
}
```

### Mehrere Abhängigkeitstypen kombiniert
```json
{
  "id": 5,
  "name": "Mauerwerk errichten",
  "duration": "10d",
  "successors": [4],        // EA: Nach Task 4
  "successors_aa": [6, 7],  // AA: Task 6,7 starten parallel
  "successors_ee": [8]      // EE: Task 8 endet gleichzeitig
}
```

## Beispielprojekte

### hausbau.json
Demonstriert AA und EE Beziehungen:
- Grube ausheben → Erde abtransportieren (AA)
- Mauerwerk → Elektrik/Sanitär (AA)
- Programmierung → Dokumentation (EE)

### tankdesign.json
Klassisches Projekt mit reinen EA-Beziehungen.

### erdaushub.json
Komplexes Loop-basiertes Projekt mit EA-Beziehungen und automatischen Pausen.

## CPM-Berechnung

### Vorwärtsrechnung (Forward Pass)

**EA:** `FAZ(j) = max(FEZ(i))` für alle Vorgänger i
**AA:** `FAZ(j) = max(FAZ(i))` für alle Vorgänger i
**EE:** `FEZ(j) = max(FEZ(i))` für alle Vorgänger i (FAZ wird rückgerechnet)
**AE:** `FAZ(j) = max(FAZ(i) - Dauer(j))` für alle Vorgänger i

### Rückwärtsrechnung (Backward Pass)

**EA:** `SEZ(i) = min(SAZ(j))` für alle Nachfolger j
**AA:** `SEZ(i) = min(SAZ(j) + Dauer(i))` für alle Nachfolger j
**EE:** `SEZ(i) = min(SEZ(j))` für alle Nachfolger j
**AE:** `SEZ(i) = min(SEZ(j) + Dauer(i))` für alle Nachfolger j

## Hinweise

- **successors** ohne Suffix = EA (Standard, rückwärtskompatibel)
- Mehrere Abhängigkeitstypen können kombiniert werden
- Bei Konflikten gewinnt immer die restriktivste Bedingung (Maximum bei FAZ, Minimum bei SEZ)
- Wochenenden werden automatisch berücksichtigt (FAZ wird zu Montag verschoben)
- Alle Abhängigkeiten zeigen auf **Nachfolger** (Successors), nicht Vorgänger

## Weitere Informationen

- `lib/models/base.py` - TaskBase mit dependency-Feldern
- `lib/models/cpm.py` - CPMCalculator mit Forward/Backward Pass
- `examples/hausbau.json` - Beispielprojekt mit AA/EE
