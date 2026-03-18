"""
Report models for sproject
===========================

Models for different report types (Gantt Chart, Resource List, etc.)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ReportBase(BaseModel):
    """
    Basis-Klasse für alle Report-Typen.

    Gemeinsame Felder:
    - id: Report-ID (eindeutiger Bezeichner)
    - name: Report-Name
    - headline: Überschrift für den Report
    - type: Report-Typ (gantt, resource_list, etc.)
    - columns: Liste der Spaltennamen
    - timeformat: Zeitformat für Datumsangaben (z.B. "%Y-%m-%d")
    - loadunit: Zeiteinheit für Berechnungen (hours, days, etc.)
    """

    id: str
    name: str
    headline: str
    type: str
    columns: List[str]
    timeformat: Optional[str] = "%Y-%m-%d"
    loadunit: Optional[str] = "days"

    model_config = {
        'extra': 'allow',
    }


class GanttReport(ReportBase):
    """
    Gantt Chart Report.

    Zeigt Tasks in einem Balkendiagramm mit Zeitstrahl.

    Spalten typischerweise:
    - Vorgang: Task-ID
    - name: Zugewiesene Person
    - start: Startdatum (falls angegeben)
    - end: Enddatum (falls angegeben)
    - effort: Aufwand
    - chart: Balkendiagramm

    Beispiel aus software_simple.json:
    {
        "id": "gantt_chart",
        "type": "gantt",
        "name": "Gantt Chart",
        "headline": "Projekt Zeitplan",
        "columns": ["Vorgang", "name", "start", "end", "effort", "chart"],
        "timeformat": "%Y-%m-%d",
        "loadunit": "days"
    }
    """

    type: Literal["gantt"] = "gantt"


class ResourceListReport(ReportBase):
    """
    Resource List Report.

    Zeigt Ressourcen/Personen mit ihrer Auslastung über die Zeit.

    Spalten typischerweise:
    - User: Person-Name
    - Rolle: Person-Rolle
    - start: Startdatum (falls angegeben)
    - end: Enddatum (falls angegeben)
    - chart: Balkendiagramm mit Tasks

    Beispiel aus software_simple.json:
    {
        "id": "resource_view",
        "type": "resource_list",
        "name": "StatusUpdate",
        "headline": "Resourcendiagramm",
        "columns": ["User", "Rolle", "start", "end", "chart"],
        "timeformat": "%Y-%m-%d",
        "loadunit": "days"
    }
    """

    type: Literal["resource_list"] = "resource_list"


# Union-Type für alle Report-Varianten
Report = GanttReport | ResourceListReport
