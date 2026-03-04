# Quick Start: Neue Architektur

## Was ist neu?

Das Projekt wurde teilweise refactored:

✅ **lib/utils.py** - Zentrale Utility-Funktionen
✅ **lib/models/** - Type-safe Pydantic-Models mit Methoden
⏳ **Migration** - Schrittweise Migration des alten Codes

## Schnellstart

### 1. Mit Pydantic-Models arbeiten

```python
from lib import load_project

# Laden & validieren
project = load_project("examples/software_simple.json")

# Type-safe Zugriff
print(f"Projekt: {project.project}")
print(f"Tasks: {len(project.tasks)}")
print(f"Zeiteinheit: {project.get_time_unit()}")

# Task-Details
for task in project.tasks:
    print(f"  {task.id}: {task.name} - {task.duration}")
    print(f"    In Tagen: {task.to_days()}")
```

### 2. Mit Utils arbeiten

```python
from lib import (
    parse_duration_to_days,
    parse_duration_to_minutes,
    format_time_value,
    generate_cycle_id
)

# Duration parsing
days = parse_duration_to_days("10d")  # 10.0
hours_in_days = parse_duration_to_days("40h")  # 5.0
minutes_in_days = parse_duration_to_days("480m")  # 1.0

# Minutes parsing
minutes = parse_duration_to_minutes("1h")  # 60.0

# Formatierung
formatted = format_time_value(1.5, 'days')  # "1.5d"
formatted = format_time_value(1.5, 'hours')  # "12.0h"

# Zyklus-IDs
cycle_id = generate_cycle_id(2, 1, "P")  # "2-P1"
```

### 3. Projekt-Typen

```python
from lib import load_project, PersonProject, CycleProject, LoopProject

project = load_project("examples/software_simple.json")

# Type checking
if isinstance(project, PersonProject):
    print(f"Personen: {len(project.persons)}")
    for person in project.persons:
        if person.workinghours_override:
            print(f"{person.name} ist Teilzeit")

elif isinstance(project, CycleProject):
    print(f"Order volume: {project.order_volume}")
    # TODO: project.expand_cycles() kommt später

elif isinstance(project, LoopProject):
    print(f"Total volume: {project.total_volume}")
    # TODO: project.expand_loops() kommt später
```

### 4. Alter Code funktioniert weiter

```python
# Bestehender Code funktioniert ohne Änderungen
from cpm_calculator import SimpleCPMCalculator

calc = SimpleCPMCalculator.from_file("examples/tankdesign.json")
calc.calculate()
calc.print_summary()
calc.export_to_json("output/result.json")
```

## Verfügbare Utility-Funktionen

### Duration

```python
# Parsing
parse_duration_to_days("10d")     # → 10.0
parse_duration_to_days("2w")      # → 10.0 (5 Arbeitstage)
parse_duration_to_days("40h")     # → 5.0 (8h/Tag)
parse_duration_to_days("480m")    # → 1.0 (480min = 1 Tag)

parse_duration_to_minutes("1d")   # → 480.0
parse_duration_to_minutes("1h")   # → 60.0

# Detection
detect_time_unit(["10m", "20m"])  # → 'minutes'
detect_time_unit(["10d", "20d"])  # → 'days'

# Formatting
format_time_value(1.5, 'days')    # → "1.5d"
format_time_value(1.5, 'hours')   # → "12.0h"
format_time_value(1.5, 'minutes') # → "720.0m"

# Validation
validate_duration_string("10d")   # → True
validate_duration_string("bad")   # → False
```

### Dates

```python
from datetime import datetime

# Arbeitstage addieren (ohne Wochenenden)
start = datetime(2026, 3, 3)  # Dienstag
result = add_workdays(start, 5.0)  # +5 Arbeitstage

# Wochenenden zählen
start = datetime(2026, 3, 1)  # Sonntag
end = datetime(2026, 3, 8)    # Sonntag
weekends = count_weekend_days(start, end)  # 2
```

### IDs

```python
# Zyklus-IDs generieren
id1 = generate_cycle_id(2, 1, "P")     # "2-P1"
id2 = generate_cycle_id(2, 5, "F")     # "2-F5"
id3 = generate_cycle_id("task", 3, "C")  # "task-C3"

# Zyklus-IDs parsen
task_id, cycle_num, prefix = parse_cycle_id("2-P1")
# task_id=2, cycle_num=1, prefix="P"
```

## Model-Methoden

### TaskBase

```python
task = SimpleTask(id=1, name="Test", duration="10d")

# Duration konvertieren
days = task.to_days()  # 10.0
```

### ProjectBase

```python
project = load_project("examples/pizzas.json")

# Zeiteinheit erkennen
unit = project.get_time_unit()  # "minutes" | "hours" | "days"

# Alle Task-IDs
ids = project.get_all_task_ids()  # [1, 2, 3, 4]
```

## Dateien-Übersicht

```
lib/
├── utils.py              # ✅ Gemeinsame Utils
├── models/               # ✅ Pydantic-Models
│   ├── base.py          #   TaskBase mit to_days()
│   ├── tasks.py         #   SimpleTask, InstanceTask, LoopTask
│   ├── resources.py     #   Resource, Person
│   ├── project.py       #   Project-Typen mit Methoden
│   └── loader.py        #   load_project(), save_project()
├── cpm_calculator.py    # ⚠️ Legacy (funktioniert weiter)
└── cycle_expander.py    # ⚠️ Legacy (funktioniert weiter)
```

## Nächste Schritte (optional)

Falls Sie die Migration fortsetzen möchten, siehe [REFACTORING.md](REFACTORING.md) für:
- ⏳ `CycleProject.expand_cycles()`
- ⏳ `LoopProject.expand_loops()`
- ⏳ `Project.calculate_cpm()`
- ⏳ Migration von `cpm_calculator.py`
- ⏳ Migration von `cycle_expander.py`

## Fragen?

- **Models**: Siehe [lib/models/README.md](../lib/models/README.md)
- **Refactoring**: Siehe [REFACTORING.md](REFACTORING.md)
- **Beispiele**: Siehe [examples/example_pydantic_usage.py](../examples/example_pydantic_usage.py)
