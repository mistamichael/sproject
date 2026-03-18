"""
Cost Calculator
===============

Berechnet Projektkosten auf Basis der Stundensätze von Personen und Ressourcen
sowie einmaliger Bereitstellungskosten für Maschinen/Fahrzeuge.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

HOURS_PER_DAY = 8.0  # Arbeitsstunden pro Tag (für Umrechnung CPM-Tage → Stunden)


@dataclass
class ResourceCostEntry:
    """Kostenzeile für eine einzelne Ressource."""

    resource_id: str
    resource_name: str
    resource_type: str          # 'person', 'machine', 'truck', 'unknown'
    hours_worked: float
    hourly_rate: float
    provisioning_costs: float   # Einmalige Bereitstellungskosten (0 für Personen)
    labor_costs: float          # hours_worked × hourly_rate
    total_costs: float          # labor_costs + provisioning_costs


@dataclass
class CostBreakdown:
    """Gesamtergebnis der Kostenrechnung."""

    entries: List[ResourceCostEntry] = field(default_factory=list)
    total_person_costs: float = 0.0
    total_machine_costs: float = 0.0      # Lohnkosten Maschinen/Fahrzeuge
    total_provisioning_costs: float = 0.0
    total_costs: float = 0.0


def _cpm_days_to_hours(days: float) -> float:
    """Konvertiert CPM-interne Dauer (immer in Tagen) in Stunden."""
    return days * HOURS_PER_DAY


def calculate_project_costs(project: Any, cpm_result: Any) -> Optional[CostBreakdown]:
    """
    Berechnet Projektkosten aus Personen- und Ressourcen-Stundensätzen.

    Für Personen-Ressourcen (type='person') wird der Stundensatz aus dem
    verknüpften Person-Objekt (hourly_rate) gelesen.
    Für Maschinen/Fahrzeuge wird hourly_rate direkt aus der Ressource gelesen,
    provisioning_costs werden einmalig pro Ressource addiert.

    Args:
        project:    Projekt-Objekt mit tasks, resources und persons
        cpm_result: CPM-Berechnungsergebnis (für Zeiteinheit und Dauern)

    Returns:
        CostBreakdown oder None wenn keine Kostendaten verfügbar
    """
    if not project or not hasattr(project, 'tasks'):
        return None

    # Personen-Stundensätze aufbauen: person_id → hourly_rate
    person_rates: Dict[str, float] = {}
    if hasattr(project, 'persons') and project.persons:
        for person in project.persons:
            rate = getattr(person, 'hourly_rate', None)
            if rate is not None and rate > 0:
                person_rates[person.id] = float(rate)

    # Ressourcen-Info aufbauen: resource_id → {name, type, hourly_rate, provisioning_costs}
    resource_info: Dict[str, Dict] = {}
    if hasattr(project, 'resources') and project.resources:
        for res in project.resources:
            person_id = getattr(res, 'person_id', None)
            hourly_rate = getattr(res, 'hourly_rate', None)

            # Für Personen-Ressourcen: Stundensatz aus verknüpfter Person
            if person_id and person_id in person_rates:
                hourly_rate = person_rates[person_id]

            resource_info[res.id] = {
                'name': getattr(res, 'name', res.id) or res.id,
                'type': getattr(res, 'type', 'unknown') or 'unknown',
                'hourly_rate': float(hourly_rate) if hourly_rate is not None else None,
                'provisioning_costs': float(getattr(res, 'provisioning_costs', 0.0) or 0.0),
            }

    # Stunden pro Ressource aus Tasks akkumulieren
    hours_per_resource: Dict[str, float] = {}

    for task in project.tasks:
        if not hasattr(task, 'resources') or not task.resources:
            continue
        if getattr(task, 'is_break', False) or getattr(task, 'is_blocker', False):
            continue

        # Dauer aus CPM-Ergebnis holen (in Tagen, CPM-intern immer Tage)
        if cpm_result and task.id in cpm_result.tasks:
            cpm_task = cpm_result.tasks[task.id]
            if cpm_task.is_break:
                continue
            duration_hours = _cpm_days_to_hours(cpm_task.duration)
        else:
            # Fallback: task.duration string direkt parsen
            try:
                from utils import parse_duration_to_minutes
            except ImportError:
                from .utils import parse_duration_to_minutes
            duration_min = parse_duration_to_minutes(task.duration or '0')
            duration_hours = duration_min / 60.0

        for res_id in task.resources:
            hours_per_resource[res_id] = hours_per_resource.get(res_id, 0.0) + duration_hours

    if not hours_per_resource:
        return None

    # Kostenzeilen aufbauen (nur Ressourcen mit Stundensatz)
    entries: List[ResourceCostEntry] = []

    for res_id in sorted(hours_per_resource.keys()):
        info = resource_info.get(res_id, {
            'name': res_id,
            'type': 'unknown',
            'hourly_rate': None,
            'provisioning_costs': 0.0,
        })

        hourly_rate = info.get('hourly_rate')
        if not hourly_rate:
            continue  # Ressource ohne Stundensatz überspringen

        hours = hours_per_resource[res_id]
        provisioning = info.get('provisioning_costs') or 0.0
        labor = hours * hourly_rate
        total = labor + provisioning

        entries.append(ResourceCostEntry(
            resource_id=res_id,
            resource_name=info['name'],
            resource_type=info['type'],
            hours_worked=round(hours, 2),
            hourly_rate=hourly_rate,
            provisioning_costs=provisioning,
            labor_costs=round(labor, 2),
            total_costs=round(total, 2),
        ))

    if not entries:
        return None

    person_entries  = [e for e in entries if e.resource_type == 'person']
    machine_entries = [e for e in entries if e.resource_type != 'person']

    return CostBreakdown(
        entries=entries,
        total_person_costs=round(sum(e.total_costs for e in person_entries), 2),
        total_machine_costs=round(sum(e.labor_costs for e in machine_entries), 2),
        total_provisioning_costs=round(sum(e.provisioning_costs for e in machine_entries), 2),
        total_costs=round(sum(e.total_costs for e in entries), 2),
    )
