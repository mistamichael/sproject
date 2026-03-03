# Pydantic Models für sproject

Type-safe Pydantic-Modelle zum Laden und Validieren von Projekt-JSON-Dateien.

## Übersicht

Diese Modelle bieten:

- ✅ **Type-Safety**: Automatische Validierung aller JSON-Daten
- ✅ **Auto-Detection**: Automatische Erkennung des Projekt-Typs
- ✅ **Autocomplete**: Vollständige IDE-Unterstützung
- ✅ **JSON Schema**: Automatische Schema-Generierung
- ✅ **Flexible**: Unterstützt alle vorhandenen JSON-Formate

## Installation

```bash
pip install pydantic
```

## Schnellstart

```python
from lib import load_project

# Lade beliebige Projekt-JSON
project = load_project("examples/software_simple.json")

print(project.project)  # Type-safe Zugriff
print(f"Tasks: {len(project.tasks)}")

# Type-Guards für spezifische Funktionen
if isinstance(project, PersonProject):
    for person in project.persons:
        print(f"{person.name}: {person.hourly_rate}€/h")
```

## Unterstützte Projekt-Typen

### 1. SimpleProject
Einfache Projekte (tankdesign.json, pizza.json)

```python
project = load_project("examples/tankdesign.json")
# SimpleProject mit tasks
```

### 2. CycleProject
Projekte mit Instanzen/Zyklen (pizzas.json)

```python
project = load_project("examples/pizzas.json")
# CycleProject mit order_volume, resources, instance tasks
```

### 3. LoopProject
Projekte mit Loops (erdaushub.json)

```python
project = load_project("examples/erdaushub.json")
# LoopProject mit total_volume, resources, loop tasks mit subtasks
```

### 4. PersonProject
Projekte mit Personen (software_simple.json)

```python
project = load_project("examples/software_simple.json")
# PersonProject mit persons, resources, workinghours_override, vacation
```

## Modul-Struktur

```
lib/models/
├── __init__.py           # Public API
├── base.py               # TaskBase - Basis für alle Tasks
├── tasks.py              # SimpleTask, InstanceTask, LoopTask, SubTask
├── resources.py          # ResourceBase, MachineResource, PersonResource, TruckResource, Person
├── project.py            # SimpleProject, CycleProject, LoopProject, PersonProject
├── loader.py             # load_project(), save_project()
└── README.md             # Diese Datei
```

## Beispiele

### Beispiel 1: Projekt laden und Typ prüfen

```python
from lib import load_project, PersonProject

project = load_project("examples/software_simple.json")

if isinstance(project, PersonProject):
    print(f"Personen: {len(project.persons)}")
    print(f"Geschätzte Stunden: {project.total_hours}")
```

### Beispiel 2: Mit Personen arbeiten

```python
project = load_project("examples/software_simple.json")

for person in project.persons:
    # Prüfe auf Teilzeit
    if person.workinghours_override:
        print(f"{person.name} arbeitet {person.workinghours_override.description}")

    # Prüfe auf Urlaub
    if person.vacation:
        for v in person.vacation:
            print(f"{person.name} hat Urlaub: {v.description}")
```

### Beispiel 3: Tasks mit Zyklen

```python
from lib import load_project, CycleProject

project = load_project("examples/pizzas.json")

if isinstance(project, CycleProject):
    print(f"Produziere {project.order_volume} {project.unit}")

    # Finde Tasks mit Instanzen
    for task in project.tasks:
        if hasattr(task, 'instances'):
            print(f"Task {task.id} wird {task.instances}x ausgeführt")
            print(f"Mit Präfix: {task.cycle_prefix}")
```

### Beispiel 4: Loop-Tasks analysieren

```python
from lib import load_project, LoopProject

project = load_project("examples/erdaushub.json")

if isinstance(project, LoopProject):
    for task in project.tasks:
        if hasattr(task, 'is_loop') and task.is_loop:
            print(f"Loop: {task.name}")
            print(f"Bedingung: {task.loop_until}")
            print(f"Subtasks:")
            for subtask in task.subtasks:
                print(f"  - {subtask.name}")
```

### Beispiel 5: JSON Export

```python
from lib import load_project, save_project

# Lade, modifiziere, speichere
project = load_project("examples/software_simple.json")

# Modifiziere
project.project = "Neuer Projektname"

# Speichere
save_project(project, "output/modified_project.json")

# Oder exportiere direkt zu JSON-String
json_str = project.model_dump_json(indent=2, by_alias=True, exclude_none=True)
```

### Beispiel 6: JSON Schema generieren

```python
from lib import PersonProject

# Generiere JSON Schema
schema = PersonProject.model_json_schema()

# Nutze für Dokumentation oder Validierung
import json
print(json.dumps(schema, indent=2))
```

## Validierung

Pydantic validiert automatisch alle Daten:

```python
from pydantic import ValidationError
from lib import load_project

try:
    project = load_project("invalid.json")
except ValidationError as e:
    print("Validierungsfehler gefunden:")
    print(e)
```

### Beispiele für Validierungen:

- ✅ Dauer-Strings: "10d", "5h", "30m" werden validiert
- ✅ Dependencies: Müssen Liste sein
- ✅ E-Mails: Werden für Personen validiert
- ✅ Required Fields: Fehlende Pflichtfelder führen zu Fehler
- ✅ Type-Safety: Falsche Typen werden abgelehnt

## Advanced Usage

### Custom Validators

Die Modelle nutzen bereits Custom Validators, z.B. für Dauer-Strings:

```python
# In base.py
@field_validator('duration')
@classmethod
def validate_duration(cls, v: Optional[str]) -> Optional[str]:
    # Validiert "10d", "5h", "30m", "2w"
    ...
```

### Model Configuration

Alle Modelle verwenden:

```python
model_config = {
    'extra': 'allow',  # Zusätzliche Felder erlauben (Zukunftssicherheit)
    'populate_by_name': True,  # Aliases + Feldnamen erlauben
}
```

### Field Aliases

Für JSON-Felder die Python-Keywords sind:

```python
class TimeRange(BaseModel):
    from_: str = Field(alias="from")  # "from" in JSON wird zu "from_" in Python
    to: str
```

## Testing

Teste alle Modelle:

```bash
cd lib
python test_models.py
```

Beispiel-Nutzung:

```bash
cd examples
python example_pydantic_usage.py
```

## Migration von dict zu Pydantic

### Vorher (dict):

```python
with open("project.json") as f:
    data = json.load(f)

# Unsicher - keine Validierung
project_name = data["project"]  # KeyError möglich
tasks = data.get("tasks", [])   # Typ unbekannt
```

### Nachher (Pydantic):

```python
from lib import load_project

# Type-safe, validiert
project = load_project("project.json")
project_name = project.project  # Garantiert String
tasks = project.tasks          # Garantiert Liste von Tasks
```

## Troubleshooting

### "Validation error: Field required"

Ein Pflichtfeld fehlt in der JSON. Prüfe die JSON-Struktur oder mache das Feld optional:

```python
field_name: Optional[str] = None
```

### "Union type not matching"

Bei Union-Types (z.B. `Task = Union[LoopTask, InstanceTask, SimpleTask]`):
- Reihenfolge ist wichtig (spezifischste zuerst)
- Falls nötig: Discriminator nutzen

### "Character encoding error"

Nutze UTF-8 encoding:

```python
with open(file_path, encoding='utf-8') as f:
    ...
```

## Weiterführende Links

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JSON Schema](https://json-schema.org/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
