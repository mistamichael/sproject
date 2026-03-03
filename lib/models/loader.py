"""
Project loader with auto-detection
===================================

Automatische Erkennung und Laden von verschiedenen Projekt-Typen.
"""

import json
from pathlib import Path
from typing import Union
from pydantic import ValidationError

from .project import SimpleProject, CycleProject, LoopProject, PersonProject, Project


def detect_project_type(data: dict) -> str:
    """
    Erkennt den Projekt-Typ basierend auf vorhandenen Feldern.

    Args:
        data: Dictionary mit JSON-Daten

    Returns:
        Projekt-Typ als String: 'person', 'cycle', 'loop' oder 'simple'
    """
    # Prüfe auf charakteristische Felder
    if 'persons' in data:
        return 'person'
    elif 'order_volume' in data:
        return 'cycle'
    elif 'total_volume' in data:
        return 'loop'
    else:
        return 'simple'


def load_project(file_path: Union[str, Path]) -> Project:
    """
    Lädt eine Projekt-JSON-Datei und erkennt automatisch den Typ.

    Args:
        file_path: Pfad zur JSON-Datei

    Returns:
        Pydantic-Projekt-Modell (SimpleProject, CycleProject, LoopProject, oder PersonProject)

    Raises:
        ValidationError: Wenn die JSON-Struktur ungültig ist
        FileNotFoundError: Wenn die Datei nicht existiert
        json.JSONDecodeError: Wenn die Datei kein gültiges JSON enthält

    Examples:
        >>> project = load_project("examples/software_simple.json")
        >>> print(project.project)
        'Software Entwicklung Projekt'
        >>> if isinstance(project, PersonProject):
        ...     print(f"Personen: {len(project.persons)}")
    """
    file_path = Path(file_path)

    # Lade JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Erkenne Projekt-Typ
    project_type = detect_project_type(data)

    # Lade entsprechendes Modell
    try:
        if project_type == 'person':
            return PersonProject(**data)
        elif project_type == 'cycle':
            return CycleProject(**data)
        elif project_type == 'loop':
            return LoopProject(**data)
        else:
            return SimpleProject(**data)
    except ValidationError as e:
        # Erweitere Fehlermeldung mit Dateiinformationen
        print(f"Validation error in {file_path}:")
        print(f"Detected project type: {project_type}")
        raise


def load_project_from_dict(data: dict) -> Project:
    """
    Lädt ein Projekt aus einem Dictionary.

    Erkennt automatisch den Projekt-Typ und erstellt das entsprechende Modell.

    Args:
        data: Dictionary mit Projektdaten

    Returns:
        Pydantic-Projekt-Modell (SimpleProject, CycleProject, LoopProject, oder PersonProject)

    Examples:
        >>> data = {"project": "Test", "tasks": []}
        >>> project = load_project_from_dict(data)
        >>> isinstance(project, SimpleProject)
        True
    """
    # Erkenne Projekt-Typ
    project_type = detect_project_type(data)

    # Lade entsprechendes Modell
    if project_type == 'person':
        return PersonProject(**data)
    elif project_type == 'cycle':
        return CycleProject(**data)
    elif project_type == 'loop':
        return LoopProject(**data)
    else:
        return SimpleProject(**data)


def load_project_raw(file_path: Union[str, Path]) -> dict:
    """
    Lädt eine Projekt-JSON-Datei als rohes Dictionary.

    Nützlich für Debugging oder wenn man die Struktur vor der Validierung sehen möchte.

    Args:
        file_path: Pfad zur JSON-Datei

    Returns:
        Dictionary mit JSON-Daten
    """
    file_path = Path(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_project(project: Project, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Speichert ein Projekt-Modell als JSON-Datei.

    Args:
        project: Pydantic-Projekt-Modell
        file_path: Ziel-Pfad für JSON-Datei
        indent: JSON-Einrückung (Standard: 2)

    Examples:
        >>> project = load_project("examples/software_simple.json")
        >>> save_project(project, "output/project_copy.json")
    """
    file_path = Path(file_path)

    # Stelle sicher, dass Verzeichnis existiert
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Exportiere mit Aliasen (z.B. "from" statt "from_")
    data = project.model_dump(by_alias=True, exclude_none=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
