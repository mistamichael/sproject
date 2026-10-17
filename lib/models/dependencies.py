"""
Dependencies
============

Abhängigkeitstypen zwischen Tasks.

Im JSON stehen die Nachfolger in vier Listen (successors, successors_aa,
successors_ee, successors_ae). Intern wird damit als Liste von Dependency
gearbeitet; die Textform "3, 5[AA], 7[EE]" nutzen GUI und Exporte.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Union

TaskId = Union[int, str]


class DepType(str, Enum):
    """EA = Ende-Anfang (Standard), AA = Anfang-Anfang, EE = Ende-Ende, AE = Anfang-Ende."""
    EA = "EA"
    AA = "AA"
    EE = "EE"
    AE = "AE"


# DepType → Feldname in TaskBase / JSON
SUCCESSOR_FIELDS = {
    DepType.EA: "successors",
    DepType.AA: "successors_aa",
    DepType.EE: "successors_ee",
    DepType.AE: "successors_ae",
}


@dataclass(frozen=True)
class Dependency:
    target: TaskId
    type: DepType = DepType.EA


def parse_task_id(value: str) -> TaskId:
    """'3' → 3, 'A-1' → 'A-1'."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def parse_dependencies(text: str) -> List[Dependency]:
    """
    Parst "3, 5[AA], 7[EE]" in Dependencies. Ohne Suffix gilt EA, unbekannte Suffixe ebenfalls.

    Examples:
        >>> parse_dependencies("3, 5[AA]")
        [Dependency(target=3, type=<DepType.EA: 'EA'>), Dependency(target=5, type=<DepType.AA: 'AA'>)]
    """
    deps: List[Dependency] = []
    for item in (text or "").split(","):
        item = item.strip()
        if not item:
            continue
        dep_type = DepType.EA
        if "[" in item:
            item, suffix = item.rsplit("[", 1)
            try:
                dep_type = DepType(suffix.rstrip("]").strip().upper())
            except ValueError:
                pass
        deps.append(Dependency(parse_task_id(item.strip()), dep_type))
    return deps


def format_dependencies(deps: Iterable[Dependency]) -> str:
    """Gegenstück zu parse_dependencies; EA wird ohne Suffix geschrieben."""
    return ", ".join(
        str(d.target) if d.type == DepType.EA else f"{d.target}[{d.type.value}]"
        for d in deps
    )
