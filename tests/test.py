"""
test.py
=======
Unit tests für sproject.py
"""

import unittest
import tempfile
from pathlib import Path


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
