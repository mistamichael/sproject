"""
Project loader
==============

Lädt Projekt-JSON-Dateien als einheitliches Project-Modell.
"""

import json
from pathlib import Path
from typing import Union
from pydantic import ValidationError

from .project import Project


def load_project(file_path: Union[str, Path]) -> Project:
    """
    Lädt eine Projekt-JSON-Datei.

    Args:
        file_path: Pfad zur JSON-Datei

    Returns:
        Project-Modell

    Raises:
        ValidationError: Wenn die JSON-Struktur ungültig ist
        FileNotFoundError: Wenn die Datei nicht existiert
        json.JSONDecodeError: Wenn die Datei kein gültiges JSON enthält
    """
    file_path = Path(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    try:
        return Project(**data)
    except ValidationError:
        print(f"Validation error in {file_path}:")
        raise


def load_project_from_dict(data: dict) -> Project:
    """
    Lädt ein Projekt aus einem Dictionary.

    Args:
        data: Dictionary mit Projektdaten

    Returns:
        Project-Modell
    """
    return Project(**data)


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
