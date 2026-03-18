#!/usr/bin/env python3
"""
Test script for Pydantic models
================================

Tests all JSON files in examples/ with the Pydantic models.
"""

import os
import sys
from pathlib import Path
from pydantic import ValidationError

# Add parent to path for lib import
sys.path.insert(0, str(Path(os.environ.get("PROJECT", str(Path(__file__).parent.parent)))))

from lib import load_project, PersonProject, CycleProject, LoopProject, SimpleProject


def test_project_file(file_path: Path) -> bool:
    """
    Testet eine einzelne Projekt-Datei.

    Args:
        file_path: Pfad zur JSON-Datei

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    print(f"\n{'='*70}")
    print(f"Testing: {file_path.name}")
    print(f"{'='*70}")

    try:
        # Lade Projekt
        project = load_project(file_path)

        # Zeige Typ an
        project_type = type(project).__name__
        print(f"[OK] Project type: {project_type}")
        print(f"[OK] Project name: {project.project}")

        # Zeige Tasks an
        print(f"[OK] Tasks: {len(project.tasks)}")
        for task in project.tasks[:3]:  # Zeige erste 3 Tasks
            print(f"  - Task {task.id}: {task.name} ({task.duration})")
        if len(project.tasks) > 3:
            print(f"  ... and {len(project.tasks) - 3} more")

        # Zeige projekt-spezifische Informationen
        if isinstance(project, PersonProject):
            print(f"[OK] Persons: {len(project.persons)}")
            print(f"[OK] Resources: {len(project.resources)}")
            for person in project.persons:
                override_info = " (Teilzeit)" if person.workinghours_override else ""
                vacation_info = f" ({len(person.vacation)} Urlaube)" if person.vacation else ""
                print(f"  - {person.name}: {person.role} @ {person.hourly_rate}€/h{override_info}{vacation_info}")

        elif isinstance(project, CycleProject):
            print(f"[OK] Order volume: {project.order_volume} {project.unit}")
            print(f"[OK] Resources: {len(project.resources)}")
            # Zähle InstanceTasks
            instance_tasks = [t for t in project.tasks if hasattr(t, 'instances')]
            print(f"[OK] Instance tasks: {len(instance_tasks)}")

        elif isinstance(project, LoopProject):
            print(f"[OK] Total volume: {project.total_volume} {project.unit}")
            print(f"[OK] Resources: {len(project.resources)}")
            # Zähle LoopTasks
            loop_tasks = [t for t in project.tasks if hasattr(t, 'is_loop')]
            print(f"[OK] Loop tasks: {len(loop_tasks)}")
            if loop_tasks:
                for lt in loop_tasks:
                    print(f"  - {lt.name}: {len(lt.subtasks)} subtasks, until {lt.loop_until}")

        # Validierung OK
        print(f"\n[SUCCESS] {file_path.name} validated successfully!")
        return True

    except ValidationError as e:
        print(f"\n[VALIDATION ERROR]")
        print(e)
        return False

    except Exception as e:
        print(f"\n[ERROR]")
        print(e)
        return False


def main():
    """Testet alle JSON-Dateien in examples/"""

    # Finde alle JSON-Dateien
    examples_dir = Path(os.environ.get("PV_EXAMPLES", str(Path(__file__).parent.parent / "examples")))
    json_files = sorted(examples_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {examples_dir}")
        return 1

    print(f"\nFound {len(json_files)} JSON files to test:")
    for f in json_files:
        print(f"  - {f.name}")

    # Teste jede Datei
    results = {}
    for json_file in json_files:
        success = test_project_file(json_file)
        results[json_file.name] = success

    # Zusammenfassung
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    success_count = sum(results.values())
    total_count = len(results)

    for filename, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {filename}")

    print(f"\n{success_count}/{total_count} tests passed")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
