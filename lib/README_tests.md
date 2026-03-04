# sproject Tests

Umfassende Unit-Tests für alle sproject-Module.

## Test-Dateien

### `lib/test_sproject.py`
Haupt-Test-Suite mit umfassenden Tests für:

#### Projekt-Laden (TestProjectLoading)
- ✅ Laden verschiedener Projekt-Typen (Simple, Person, Cycle, Loop)
- ✅ Validierung der Projekt-Struktur
- ✅ Personen, Ressourcen und Tasks

#### Projekt-Methoden (TestProjectMethods)
- ✅ Zeiteinheit-Erkennung (`get_time_unit()`)
- ✅ Task-ID-Abruf (`get_all_task_ids()`)

#### CPM-Berechnung (TestCPMCalculation)
- ✅ CPM-Berechnung für einfache Projekte
- ✅ Kritischer Pfad-Identifikation
- ✅ CPM mit spezifischem Startdatum
- ✅ Validierung von FAZ, FEZ, SAZ, SEZ, Puffer

#### Projekt-Expansion (TestProjectExpansion)
- ✅ Zyklus-Expansion (`expand_cycles()`)
- ✅ Loop-Expansion (`expand_loops()`)
- ✅ Validierung expandierter Tasks

#### Report-Modelle (TestReportModels)
- ✅ GanttReport-Erstellung
- ✅ ResourceListReport-Erstellung
- ✅ Report-Konfiguration

#### Projekt Speichern/Laden (TestProjectSaveLoad)
- ✅ Projekt speichern und wieder laden
- ✅ JSON-Export/Import

#### Excel-Export (TestExcelExport)
- ✅ Excel-Export mit CPM-Daten
- ✅ Report-Sheets (Gantt Chart, Resource List)
- ✅ Multi-Sheet-Workbooks

#### PersonProject (TestPersonProject)
- ✅ Personen-Verwaltung
- ✅ Ressourcen-Zuordnung
- ✅ Stundensätze und Rollen

#### Task-Validierung (TestTaskValidation)
- ✅ Dauer-Validierung (10d, 5h, 30m, 2w)
- ✅ Abhängigkeiten-Validierung
- ✅ Task-Eigenschaften

#### Edge Cases: Leere und minimale Projekte (TestEdgeCasesEmptyProjects)
- ✅ Projekt mit leerer Task-Liste
- ✅ Einzelner Task ohne Abhängigkeiten

#### Edge Cases: Ungültige Dauern (TestEdgeCasesInvalidDurations)
- ✅ Task mit Dauer 0
- ✅ Task mit sehr großer Dauer (1000d)
- ✅ Verschiedene Zeiteinheiten (d, h, m, w)
- ✅ Fehlende Dauer wird als 0 behandelt

#### Edge Cases: Zirkuläre Abhängigkeiten (TestEdgeCasesCircularDependencies)
- ✅ Task der von sich selbst abhängt
- ✅ Zirkuläre Abhängigkeitskette (A→B→C→A)

#### Edge Cases: Ungültige Referenzen (TestEdgeCasesInvalidReferences)
- ✅ Abhängigkeit auf nicht existierenden Task
- ✅ Doppelte Task-IDs

#### Edge Cases: Datumsbehandlung (TestEdgeCasesDateHandling)
- ✅ Ungültiges Datumsformat wird akzeptiert
- ✅ Datum ohne Zeitangabe
- ✅ Datum mit Zeitangabe

#### Edge Cases: CPM-Berechnung (TestEdgeCasesCPMCalculation)
- ✅ Unverbundene Task-Gruppen
- ✅ Mehrere Start-Tasks
- ✅ Langer kritischer Pfad (10 Tasks)

#### Edge Cases: Zyklus-Expansion (TestEdgeCasesCycleExpansion)
- ✅ Zyklus mit Bestellvolumen 0
- ✅ Zyklus mit nur einer Instanz

#### Edge Cases: Loop-Expansion (TestEdgeCasesLoopExpansion)
- ✅ Loop-Projekt mit minimaler Konfiguration

#### Edge Cases: Ressourcen-Validierung (TestEdgeCasesResourceValidation)
- ✅ Negativer Stundensatz wird akzeptiert
- ✅ Stundensatz 0 ist gültig
- ✅ Sehr hoher Stundensatz (1000€/h)

#### Edge Cases: Leere Strings (TestEdgeCasesEmptyStrings)
- ✅ Leerer Projektname
- ✅ Leerer Task-Name
- ✅ Task-Name mit nur Whitespace

#### Edge Cases: Komplexe Abhängigkeiten (TestEdgeCasesComplexDependencies)
- ✅ Task mit vielen Abhängigkeiten (10 Tasks)
- ✅ Diamant-Abhängigkeitsmuster (A→B,C→D)

## Tests ausführen

### Mit Batch-Datei (empfohlen für Windows)

```batch
REM Alle Tests ausführen
bin\run_unittests.bat

REM Mit ausführlicher Ausgabe
bin\run_unittests.bat -v

REM Nur eine Test-Klasse
bin\run_unittests.bat TestCPMCalculation

REM Nur einen spezifischen Test
bin\run_unittests.bat TestCPMCalculation.test_cpm_critical_path

REM Hilfe anzeigen
bin\run_unittests.bat --help
```

### Direkt mit Python

#### Alle Tests
```bash
python lib/test_sproject.py
```

#### Mit unittest discover
```bash
python -m unittest discover -s lib -p "test_*.py" -v
```

#### Einzelne Test-Klasse
```bash
python -m unittest lib.test_sproject.TestCPMCalculation -v
```

#### Einzelner Test
```bash
python -m unittest lib.test_sproject.TestCPMCalculation.test_cpm_critical_path -v
```

## Test-Abdeckung

Die Tests decken folgende Module ab:
- ✅ `lib/models/` - Alle Pydantic-Modelle
  - `project.py` - SimpleProject, PersonProject, CycleProject, LoopProject
  - `tasks.py` - SimpleTask, InstanceTask, LoopTask
  - `resources.py` - Person, Resource
  - `reports.py` - GanttReport, ResourceListReport
  - `cpm.py` - CPMCalculator, CPMResult, CPMTaskResult
  - `loader.py` - load_project, save_project

- ✅ `lib/sproject.py` - Haupt-Anwendung
  - `export_cpm_to_xlsx()` - Excel-Export

- ✅ `lib/excel_reports.py` - Excel-Report-Generierung
  - Gantt Chart mit Timeline
  - Resource List
  - Farbverläufe und kritischer Pfad

- ✅ `lib/cpm_calculator.py` - CPM-Berechnung
  - SimpleCPMCalculator

## Testdaten

Die Tests verwenden die Beispiel-Dateien in `examples/`:
- `tankdesign.json` - Einfaches Projekt
- `software_simple.json` - PersonProject mit Reports
- `pizzas.json` - CycleProject mit Instanzen
- `erdaushub.json` - LoopProject mit Loops

## Abhängigkeiten

Erforderlich:
- `pydantic` - Für Modell-Validierung

Optional (für Excel-Tests):
- `openpyxl` - Für Excel-Export

Installieren:
```bash
pip install pydantic openpyxl
```

## Ergebnis

Alle 46 Tests sollten erfolgreich sein:

```
Ran 46 tests in 0.6s

OK
```

Die Test-Suite umfasst:
- **18 ursprüngliche Tests** - Kernfunktionalität
- **28 neue Edge-Case-Tests** - Robustheit und Fehlerbehandlung

## CI/CD Integration

Die Tests können in CI/CD-Pipelines integriert werden:

```yaml
# GitHub Actions Beispiel
- name: Run Tests
  run: python lib/test_sproject.py
```

```yaml
# GitLab CI Beispiel
test:
  script:
    - python lib/test_sproject.py
```
