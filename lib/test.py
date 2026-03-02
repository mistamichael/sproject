"""
test.py
=======
Unit tests für tjp_models und sproject.py
"""

import unittest
import json
import tempfile
from pathlib import Path
from pydantic import ValidationError

from tjp_models import (
    TJPRegistry,
    WorkingHours,
    WorkingHoursFile,
    Person,
    PersonsFile,
    ResourceGroup,
    Task,
    ProjectFile,
    Report,
    ReportsFile,
    Absence,
    TimeSlot,
    DaySchedule,
    Dependency,
)


class TestWorkingHours(unittest.TestCase):
    """Tests für WorkingHours und verwandte Klassen."""

    def test_timeslot_validation(self):
        """Test ob TimeSlot gültige Zeiten validiert."""
        valid_slot = TimeSlot(from_time="09:00", to_time="17:00")
        self.assertEqual(valid_slot.from_time, "09:00")
        self.assertEqual(valid_slot.to_time, "17:00")

    def test_timeslot_invalid_time(self):
        """Test ob ungültige Zeiten abgelehnt werden."""
        with self.assertRaises(ValidationError):
            TimeSlot(from_time="25:00", to_time="17:00")

    def test_day_schedule_valid_days(self):
        """Test ob nur gültige Wochentage akzeptiert werden."""
        schedule = DaySchedule(
            days=["mon", "tue", "wed"],
            hours=[TimeSlot(from_time="09:00", to_time="17:00")]
        )
        self.assertEqual(len(schedule.days), 3)

    def test_day_schedule_invalid_days(self):
        """Test ob ungültige Wochentage abgelehnt werden."""
        with self.assertRaises(ValidationError):
            DaySchedule(
                days=["invalid_day"],
                hours=[TimeSlot(from_time="09:00", to_time="17:00")]
            )

    def test_working_hours_is_working_day(self):
        """Test ob Arbeitstage korrekt erkannt werden."""
        wh = WorkingHours(
            id="standard",
            schedules=[
                DaySchedule(
                    days=["mon", "tue", "wed", "thu", "fri"],
                    hours=[TimeSlot(from_time="09:00", to_time="17:00")]
                ),
                DaySchedule(days=["sat", "sun"], hours="off")
            ]
        )
        self.assertTrue(wh.is_working_day("mon"))
        self.assertFalse(wh.is_working_day("sat"))

    def test_working_hours_hours_per_day(self):
        """Test Berechnung der täglichen Arbeitsstunden."""
        wh = WorkingHours(
            id="standard",
            schedules=[
                DaySchedule(
                    days=["mon"],
                    hours=[
                        TimeSlot(from_time="09:00", to_time="12:00"),
                        TimeSlot(from_time="13:00", to_time="17:00")
                    ]
                )
            ]
        )
        # 3h + 4h = 7h
        self.assertEqual(wh.hours_per_day("mon"), 7.0)


class TestAbsence(unittest.TestCase):
    """Tests für Abwesenheiten."""

    def test_absence_single_date(self):
        """Test Abwesenheit mit Einzeldatum."""
        absence = Absence(
            type="holiday",
            name="Neujahr",
            date="2025-01-01"
        )
        self.assertTrue(absence.is_global())
        self.assertEqual(absence.date, "2025-01-01")

    def test_absence_date_range(self):
        """Test Abwesenheit mit Datumsbereich."""
        absence = Absence(
            type="vacation",
            name="Urlaub",
            from_date="2025-07-01",
            to_date="2025-07-14",
            resource_id="alice"
        )
        self.assertFalse(absence.is_global())
        self.assertEqual(absence.from_date, "2025-07-01")

    def test_absence_requires_date_or_range(self):
        """Test dass entweder date oder from/to erforderlich ist."""
        with self.assertRaises(ValidationError):
            Absence(type="holiday", name="Invalid")


class TestPerson(unittest.TestCase):
    """Tests für Person und ResourceGroup."""

    def test_person_creation(self):
        """Test Personenerstellung."""
        person = Person(id="alice", name="Alice Smith", email="alice@example.com")
        self.assertEqual(person.id, "alice")
        self.assertEqual(person.name, "Alice Smith")
        self.assertIsNone(person.workinghours)

    def test_resource_group_positive_rate(self):
        """Test dass Stundensatz positiv sein muss."""
        group = ResourceGroup(id="dev", name="Developers", rate=100.0)
        self.assertEqual(group.rate, 100.0)

        with self.assertRaises(ValidationError):
            ResourceGroup(id="bad", name="Bad Group", rate=-10.0)


class TestTask(unittest.TestCase):
    """Tests für Tasks."""

    def test_task_creation(self):
        """Test Task-Erstellung."""
        task = Task(id="task1", name="Coding", effort="10d")
        self.assertEqual(task.id, "task1")
        self.assertEqual(task.effort, "10d")
        self.assertFalse(task.milestone)

    def test_milestone_no_effort(self):
        """Test dass Meilensteine keinen Aufwand haben dürfen."""
        milestone = Task(id="m1", name="Release", milestone=True)
        self.assertTrue(milestone.milestone)

        with self.assertRaises(ValidationError):
            Task(id="bad", name="Bad Milestone", milestone=True, effort="5d")

    def test_task_subtasks(self):
        """Test Task mit Unteraufgaben."""
        subtask1 = Task(id="sub1", name="Subtask 1", effort="3d")
        subtask2 = Task(id="sub2", name="Subtask 2", effort="2d")
        main_task = Task(
            id="main",
            name="Main Task",
            tasks=[subtask1, subtask2]
        )
        self.assertEqual(len(main_task.all_subtasks()), 2)

    def test_dependency_gap_calculation(self):
        """Test Gap/Lead-Berechnung in Dependencies."""
        dep_gap = Dependency(task_id="task1", gapduration="5d")
        self.assertEqual(dep_gap.gap_days(), 5.0)
        self.assertFalse(dep_gap.is_lead())

        dep_lead = Dependency(task_id="task2", gapduration="-3d")
        self.assertEqual(dep_lead.gap_days(), -3.0)
        self.assertTrue(dep_lead.is_lead())

        dep_week = Dependency(task_id="task3", gapduration="2w")
        self.assertEqual(dep_week.gap_days(), 10.0)  # 2 weeks = 10 days


class TestReport(unittest.TestCase):
    """Tests für Reports."""

    def test_report_creation(self):
        """Test Report-Erstellung."""
        report = Report(
            id="r1",
            type="taskreport",
            name="Task Overview",
            columns=["name", "start", "end"]
        )
        self.assertEqual(report.type, "taskreport")
        self.assertEqual(len(report.columns), 3)

    def test_textreport_no_columns(self):
        """Test dass textreport keine Spalten haben sollte."""
        with self.assertRaises(ValidationError):
            Report(
                id="bad",
                type="textreport",
                name="Bad Report",
                columns=["name"]
            )


class TestTJPRegistry(unittest.TestCase):
    """Tests für TJPRegistry mit Querverweisen."""

    def setUp(self):
        """Erstellt temporäre Test-JSON-Dateien."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # WorkingHours
        wh_data = {
            "global_workinghours": {
                "id": "standard",
                "description": "Standard 40h/week",
                "schedules": [
                    {
                        "days": ["mon", "tue", "wed", "thu", "fri"],
                        "hours": [{"from": "09:00", "to": "17:00"}]
                    },
                    {"days": ["sat", "sun"], "hours": "off"}
                ]
            },
            "workinghours_overrides": [],
            "global_leaves": [
                {
                    "type": "holiday",
                    "name": "Neujahr",
                    "date": "2025-01-01",
                    "applies_to": "all"
                }
            ],
            "personal_absences": []
        }
        (self.temp_path / "workinghours_absences.json").write_text(
            json.dumps(wh_data), encoding="utf-8"
        )

        # Persons
        persons_data = {
            "resource_groups": [
                {
                    "id": "dev",
                    "name": "Developers",
                    "rate": 100.0,
                    "members": [
                        {"id": "alice", "name": "Alice Smith"},
                        {"id": "bob", "name": "Bob Jones"}
                    ]
                }
            ]
        }
        (self.temp_path / "persons.json").write_text(
            json.dumps(persons_data), encoding="utf-8"
        )

        # Project
        project_data = {
            "project": {
                "id": "test_project",
                "name": "Test Project",
                "version": "1.0",
                "start": "2025-01-01",
                "duration": "30d",
                "timezone": "Europe/Berlin",
                "timeformat": "%Y-%m-%d",
                "currency": "EUR",
                "now": "2025-01-01",
                "workinghours_ref": "standard"
            },
            "accounts": [],
            "tasks": [
                {
                    "id": "coding",
                    "name": "Coding Phase",
                    "effort": "20d",
                    "allocate": ["alice", "bob"]
                }
            ]
        }
        (self.temp_path / "project.json").write_text(
            json.dumps(project_data), encoding="utf-8"
        )

        # Reports
        reports_data = {
            "reports": [
                {
                    "id": "overview",
                    "type": "taskreport",
                    "name": "Overview",
                    "columns": ["name", "start"]
                }
            ]
        }
        (self.temp_path / "reports.json").write_text(
            json.dumps(reports_data), encoding="utf-8"
        )

    def test_registry_load(self):
        """Test ob Registry korrekt lädt."""
        registry = TJPRegistry.load(
            persons_path=self.temp_path / "persons.json",
            wh_path=self.temp_path / "workinghours_absences.json",
            project_path=self.temp_path / "project.json",
            reports_path=self.temp_path / "reports.json",
        )
        self.assertIsNotNone(registry)
        self.assertEqual(len(registry.persons.all_persons()), 2)
        self.assertEqual(len(registry.project.all_tasks()), 1)

    def test_registry_person_workinghours_resolution(self):
        """Test ob Person.workinghours aufgelöst wird."""
        registry = TJPRegistry.load(
            persons_path=self.temp_path / "persons.json",
            wh_path=self.temp_path / "workinghours_absences.json",
            project_path=self.temp_path / "project.json",
            reports_path=self.temp_path / "reports.json",
        )
        alice = registry.get_person("alice")
        self.assertIsNotNone(alice)
        self.assertIsNotNone(alice.workinghours)
        self.assertEqual(alice.workinghours.id, "standard")

    def test_registry_task_persons_resolution(self):
        """Test ob Task.persons aufgelöst wird."""
        registry = TJPRegistry.load(
            persons_path=self.temp_path / "persons.json",
            wh_path=self.temp_path / "workinghours_absences.json",
            project_path=self.temp_path / "project.json",
            reports_path=self.temp_path / "reports.json",
        )
        coding_task = registry.get_task("coding")
        self.assertIsNotNone(coding_task)
        self.assertEqual(len(coding_task.persons), 2)
        person_names = [p.name for p in coding_task.persons]
        self.assertIn("Alice Smith", person_names)
        self.assertIn("Bob Jones", person_names)

    def test_registry_summary(self):
        """Test ob summary() funktioniert."""
        registry = TJPRegistry.load(
            persons_path=self.temp_path / "persons.json",
            wh_path=self.temp_path / "workinghours_absences.json",
            project_path=self.temp_path / "project.json",
            reports_path=self.temp_path / "reports.json",
        )
        summary = registry.summary()
        self.assertIn("Test Project", summary)
        self.assertIn("Alice Smith", summary)


class TestSProjectIntegration(unittest.TestCase):
    """Integrationstests für sproject.py Funktionen."""

    def test_find_project_files(self):
        """Test ob find_project_files korrekt funktioniert."""
        from sproject import find_project_files

        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / "project1.json").write_text("{}")
        (temp_dir / "project_example.json").write_text("{}")
        (temp_dir / "other.json").write_text("{}")

        files = find_project_files(temp_dir)
        self.assertEqual(len(files), 2)
        file_names = [f.name for f in files]
        self.assertIn("project1.json", file_names)
        self.assertIn("project_example.json", file_names)
        self.assertNotIn("other.json", file_names)


if __name__ == "__main__":
    unittest.main()
