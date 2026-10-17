"""
Cost Calculator
===============

Berechnet Projektkosten auf Basis der Stundensätze von Personen und Ressourcen
sowie einmaliger Bereitstellungskosten für Maschinen/Fahrzeuge.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .durations import hours_per_day, parse_duration_to_minutes


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
class FixedCostEntry:
    """Task mit explizitem Festpreis (task.cost)."""

    task_id: str
    task_name: str
    cost: float


@dataclass
class CostBreakdown:
    """Gesamtergebnis der Kostenrechnung."""

    entries: List[ResourceCostEntry] = field(default_factory=list)
    fixed_costs: List[FixedCostEntry] = field(default_factory=list)
    total_person_costs: float = 0.0
    total_machine_costs: float = 0.0      # Lohnkosten Maschinen/Fahrzeuge
    total_provisioning_costs: float = 0.0
    total_fixed_costs: float = 0.0        # Summe der Task-Festpreise
    total_costs: float = 0.0


def calculate_project_costs(project, cpm_result=None) -> Optional[CostBreakdown]:
    """
    Projektkosten aus Stundensätzen und Bereitstellungskosten.

    - Personen-Ressourcen: Stundensatz der verknüpften Person (person_id → hourly_rate)
    - Maschinen/Fahrzeuge: hourly_rate der Ressource, provisioning_costs einmalig
    - Pausen und Kalender-Blocker verursachen keine Kosten
    - Tasks mit task.cost haben einen Festpreis: ihre Ressourcenstunden zählen
      nicht als Lohn, stattdessen geht task.cost in die Summe ein (0.0 = kostenlos)
    - Dauer aus dem CPM-Ergebnis, sonst aus task.duration

    Returns:
        CostBreakdown oder None, wenn weder Stundensätze noch Festpreise vorhanden sind
    """
    if not project:
        return None

    person_rates = {p.id: p.hourly_rate for p in (project.persons or []) if p.hourly_rate and p.hourly_rate > 0}
    resources = {r.id: r for r in (project.resources or [])}

    hours_per_resource: Dict[str, float] = {}
    fixed_costs: List[FixedCostEntry] = []
    for task in project.tasks:
        if getattr(task, 'is_break', False) or getattr(task, 'is_blocker', False):
            continue
        if task.cost is not None:
            if task.cost:
                fixed_costs.append(FixedCostEntry(str(task.id), task.name, float(task.cost)))
            continue
        if not task.resources:
            continue
        cpm_task = cpm_result.tasks.get(task.id) if cpm_result else None
        if cpm_task is not None:
            if cpm_task.is_system:
                continue
            hours = cpm_task.duration * hours_per_day()
        else:
            hours = parse_duration_to_minutes(task.duration or '0') / 60.0
        for res_id in task.resources:
            hours_per_resource[res_id] = hours_per_resource.get(res_id, 0.0) + hours

    entries: List[ResourceCostEntry] = []
    for res_id in sorted(hours_per_resource):
        res = resources.get(res_id)
        rate = res.hourly_rate if res else None
        if res and res.person_id in person_rates:
            rate = person_rates[res.person_id]
        if not rate:
            continue  # Ressource ohne Stundensatz überspringen

        hours = hours_per_resource[res_id]
        provisioning = float(res.provisioning_costs or 0.0) if res else 0.0
        labor = hours * rate
        entries.append(ResourceCostEntry(
            resource_id=res_id,
            resource_name=(res.name or res_id) if res else res_id,
            resource_type=res.type if res else 'unknown',
            hours_worked=round(hours, 2),
            hourly_rate=float(rate),
            provisioning_costs=provisioning,
            labor_costs=round(labor, 2),
            total_costs=round(labor + provisioning, 2),
        ))

    if not entries and not fixed_costs:
        return None

    person_entries = [e for e in entries if e.resource_type == 'person']
    machine_entries = [e for e in entries if e.resource_type != 'person']
    return CostBreakdown(
        entries=entries,
        total_person_costs=round(sum(e.total_costs for e in person_entries), 2),
        total_machine_costs=round(sum(e.labor_costs for e in machine_entries), 2),
        total_provisioning_costs=round(sum(e.provisioning_costs for e in machine_entries), 2),
        total_fixed_costs=round(sum(f.cost for f in fixed_costs), 2),
        total_costs=round(sum(e.total_costs for e in entries) + sum(f.cost for f in fixed_costs), 2),
        fixed_costs=fixed_costs,
    )
