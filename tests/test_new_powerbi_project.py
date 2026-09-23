import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.new_powerbi_project import GeneratorError, generate_project
from scripts.validate_powerbi_repo import validate


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "new_powerbi_project.py"


class NewPowerBIProjectTests(unittest.TestCase):
    def test_generates_named_project_with_valid_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "SalesAnalytics"
            pbip_path = generate_project("SalesAnalytics", target)

            self.assertEqual(target / "SalesAnalytics.pbip", pbip_path)
            self.assertTrue((target / "SalesAnalytics.Report").is_dir())
            self.assertTrue((target / "SalesAnalytics.SemanticModel").is_dir())
            self.assertFalse((target / "README.md").exists())

            pbip = json.loads(pbip_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "SalesAnalytics.Report",
                pbip["artifacts"][0]["report"]["path"],
            )

            pbir = json.loads(
                (target / "SalesAnalytics.Report" / "definition.pbir").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                "../SalesAnalytics.SemanticModel",
                pbir["datasetReference"]["byPath"]["path"],
            )

            database = (
                target
                / "SalesAnalytics.SemanticModel"
                / "definition"
                / "database.tmdl"
            ).read_text(encoding="utf-8")
            self.assertTrue(database.startswith("database SalesAnalyticsModel\n"))
            self.assertEqual([], validate(target))

    def test_rejects_unsafe_or_reserved_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (
                "../Escape",
                "Bad Name",
                "bad-name",
                "1StartsWithDigit",
                "CON",
            ):
                with self.subTest(name=name):
                    with self.assertRaises(GeneratorError):
                        generate_project(name, root / name.replace("/", "_"))

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Existing"
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")

            with self.assertRaisesRegex(
                GeneratorError,
                "destination_already_exists",
            ):
                generate_project("Existing", target)

            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))
            self.assertEqual(
                ["keep.txt"],
                sorted(path.name for path in target.iterdir()),
            )

    def test_cli_generates_project_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "E2EGenerated"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--name",
                    "E2EGenerated",
                    "--output",
                    str(target),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("POWERBI_PROJECT_GENERATION_OK", completed.stdout)
            self.assertEqual([], validate(target))


if __name__ == "__main__":
    unittest.main()
