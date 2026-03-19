#!/usr/bin/env python3
"""
Test script for Pydantic models
================================

Tests all JSON files in examples/ with the Pydantic models.
Zeigt am Ende einen Diff zwischen Original-JSON und dem pydantic-re-serialisierten
Ergebnis, um Normalisierungen oder Modellabweichungen sichtbar zu machen.
"""

import difflib
import json
import os
import sys
from pathlib import Path
from pydantic import ValidationError

# Add project root to path for lib import
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import load_project, PersonProject, CycleProject, LoopProject


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
            instance_tasks = [t for t in project.tasks if hasattr(t, 'instances')]
            print(f"[OK] Instance tasks: {len(instance_tasks)}")

        elif isinstance(project, LoopProject):
            print(f"[OK] Total volume: {project.total_volume} {project.unit}")
            print(f"[OK] Resources: {len(project.resources)}")
            loop_tasks = [t for t in project.tasks if hasattr(t, 'is_loop')]
            print(f"[OK] Loop tasks: {len(loop_tasks)}")
            if loop_tasks:
                for lt in loop_tasks:
                    print(f"  - {lt.name}: {len(lt.subtasks)} subtasks, until {lt.loop_until}")

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


def diff_project_file(file_path: Path) -> list[str]:
    """
    Vergleicht Original-JSON mit dem pydantic-re-serialisierten Ergebnis.

    Returns:
        Liste der Diff-Zeilen (leer wenn identisch)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    original_lines = json.dumps(original_data, indent=2, ensure_ascii=False).splitlines(keepends=True)

    project = load_project(file_path)
    reserialized_data = project.model_dump(by_alias=True, exclude_none=True)
    reserialized_lines = json.dumps(reserialized_data, indent=2, ensure_ascii=False).splitlines(keepends=True)

    return list(difflib.unified_diff(
        original_lines,
        reserialized_lines,
        fromfile=f"original/{file_path.name}",
        tofile=f"pydantic/{file_path.name}",
    ))


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
    diffs: dict[str, list[str]] = {}
    for json_file in json_files:
        success = test_project_file(json_file)
        results[json_file.name] = success
        if success:
            diffs[json_file.name] = diff_project_file(json_file)

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

    # Diff-Ausgabe
    files_with_diff = {name: lines for name, lines in diffs.items() if lines}
    if files_with_diff:
        print(f"\n{'='*70}")
        print("DIFF: Original JSON vs. Pydantic-Modell")
        print(f"{'='*70}")
        for filename, diff_lines in files_with_diff.items():
            print(f"\n--- {filename} ---")
            for line in diff_lines:
                print(line, end='')
            print()
    else:
        print(f"\n[OK] Kein Diff: Alle JSON-Dateien sind nach Pydantic-Roundtrip identisch.")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
