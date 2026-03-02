"""
demo.py
=======
Demonstration aller Modell-Features:
  - Laden per from_json()
  - Querverweise aufgelöst über TJPRegistry
  - to_json() Serialisierung
  - Validierung
  - __repr__ / __str__
"""

from pathlib import Path
from tjp_models import TJPRegistry

BASE = Path("/mnt/user-data/outputs")

# ── 1. Alles laden & verknüpfen ─────────────────────────────────────────────
registry = TJPRegistry.load(
    persons_path = BASE / "persons.json",
    wh_path      = BASE / "workinghours_absences.json",
    project_path = BASE / "project.json",
    reports_path = BASE / "reports.json",
)

print(registry.summary())
print()

# ── 2. Personen & aufgelöste Arbeitszeiten ───────────────────────────────────
print("── Personen & Arbeitszeiten ──────────────────────────────")
for person in registry.persons.all_persons():
    wh = person.workinghours
    print(f"  {person}")          # __str__
    print(f"    WorkingHours: {wh}")
    if wh:
        for day in ["mon", "wed", "sat"]:
            h = wh.hours_per_day(day)
            print(f"      {day}: {h:.1f}h  (Arbeitstag: {wh.is_working_day(day)})")

print()

# ── 3. Abwesenheiten pro Person ──────────────────────────────────────────────
print("── Abwesenheiten ─────────────────────────────────────────")
for person in registry.persons.all_persons():
    absences = registry.absences_for(person.id)
    for a in absences:
        span = a.date or f"{a.from_date} → {a.to_date}"
        print(f"  {person.name:<10} [{a.type}] {a.name}: {span}")

print()

# ── 4. Tasks mit aufgelösten Personen ────────────────────────────────────────
print("── Tasks & zugewiesene Personen ──────────────────────────")
for task in registry.project.all_tasks():
    persons_str = ", ".join(p.name for p in task.persons) or "—"
    milestone   = " 🏁" if task.milestone else ""
    deps = [
        f"{d.task_id}({d.gapduration or '0'})" + (" [LEAD]" if d.is_lead() else "")
        for d in task.depends
    ]
    deps_str = ", ".join(deps) or "—"
    print(f"  [{task.id}]{milestone}")
    print(f"    Aufwand:  {task.effort or task.duration or 'milestone'}")
    print(f"    Personen: {persons_str}")
    print(f"    Abhängig von: {deps_str}")
    if task.charge:
        for c in task.charge:
            print(f"    Fixkosten: {c.amount} EUR ({c.event})")

print()

# ── 5. Accounts ──────────────────────────────────────────────────────────────
print("── Konten ────────────────────────────────────────────────")
def print_accounts(accounts, indent=0):
    for a in accounts:
        print("  " + "  " * indent + f"▸ {a.id}: {a.name}")
        print_accounts(a.accounts, indent + 1)

print_accounts(registry.project.accounts)
bal = registry.project.balance
if bal:
    print(f"  Balance: {bal.cost_account} ↔ {bal.rev_account}")

print()

# ── 6. Reports ───────────────────────────────────────────────────────────────
print("── Reports ───────────────────────────────────────────────")
for report in registry.reports.reports:
    print(f"  [{report.type}] {report.name}")
    if report.headline:
        print(f"    Headline: {report.headline}")
    if report.columns:
        print(f"    Spalten:  {', '.join(report.columns)}")
    if report.filters:
        print(f"    Filter:   {report.active_filters()}")
    if report.directives:
        print(f"    Direktiven: {report.directives}")

print()

# ── 7. to_json() Roundtrip ───────────────────────────────────────────────────
print("── to_json() Roundtrip (Auszug: alice) ──────────────────")
alice = registry.get_person("alice")
print(alice.to_json())

print()

# ── 8. Validierungsfehler demonstrieren ─────────────────────────────────────
print("── Validierung: ungültiger Stundensatz ───────────────────")
from pydantic import ValidationError
from tjp_models import ResourceGroup
try:
    ResourceGroup(id="x", name="Test", rate=-10.0)
except ValidationError as e:
    for err in e.errors():
        print(f"  ✗ {err['loc']} → {err['msg']}")

print()
print("── Validierung: Meilenstein mit Aufwand ──────────────────")
from tjp_models import Task
try:
    Task(id="bad", name="Fehler", milestone=True, effort="5d")
except ValidationError as e:
    for err in e.errors():
        print(f"  ✗ {err['loc']} → {err['msg']}")

print()
print("── repr() Beispiel ───────────────────────────────────────")
task = registry.get_task("coding_phase")
print(repr(task))
