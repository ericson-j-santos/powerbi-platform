import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.new_powerbi_project import GenerationError, generate_project
from scripts.validate_powerbi_repo import validate


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "pbip-starter"


class NewPowerBIProjectTests(unittest.TestCase):
    def test_generates_valid_renamed_pbip_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "SalesAnalytics"

            generated = generate_project("SalesAnalytics", output)

            self.assertEqual(output.resolve(), generated)
            pbip = generated / "SalesAnalytics.pbip"
            report = generated / "SalesAnalytics.Report"
            model = generated / "SalesAnalytics.SemanticModel"

            self.assertTrue(pbip.is_file())
            self.assertTrue(report.is_dir())
            self.assertTrue(model.is_dir())

            pbip_payload = json.loads(pbip.read_text(encoding="utf-8"))
            self.assertEqual(
                "SalesAnalytics.Report",
                pbip_payload["artifacts"][0]["report"]["path"],
            )

            pbir_payload = json.loads(
                (report / "definition.pbir").read_text(encoding="utf-8")
            )
            self.assertEqual(
                "../SalesAnalytics.SemanticModel",
                pbir_payload["datasetReference"]["byPath"]["path"],
            )

            database = (
                model / "definition" / "database.tmdl"
            ).read_text(encoding="utf-8")
            self.assertIn("database SalesAnalyticsModel", database)
            self.assertEqual([], validate(generated))

    def test_rejects_existing_destination_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Existing"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")

            with self.assertRaisesRegex(GenerationError, "destination_exists"):
                generate_project("Existing", output)

            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))
            self.assertEqual(["keep.txt"], [path.name for path in output.iterdir()])

    def test_rejects_invalid_project_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("", "../Bad", "Bad Name", "-Bad", "Árvore"):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(GenerationError, "invalid_project_name"):
                        generate_project(name, root / "out")

    def test_rejects_reserved_windows_project_names_without_creating_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("CON", "prn", "AUX", "nul", "COM1", "com9", "LPT1", "lpt9"):
                with self.subTest(name=name):
                    output = root / name
                    with self.assertRaisesRegex(
                        GenerationError,
                        "reserved_windows_project_name",
                    ):
                        generate_project(name, output)
                    self.assertFalse(output.exists())

    def test_does_not_copy_powerbi_local_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            shutil.copytree(TEMPLATE, template)

            local_state = template / "Starter.SemanticModel" / ".pbi"
            local_state.mkdir()
            (local_state / "localSettings.json").write_text("{}", encoding="utf-8")
            (local_state / "cache.abf").write_bytes(b"cache")

            generated = generate_project(
                "CleanProject",
                root / "generated",
                template_root=template,
            )

            self.assertFalse(
                (generated / "CleanProject.SemanticModel" / ".pbi").exists()
            )
            self.assertEqual([], validate(generated))

    def test_template_contract_failure_leaves_no_partial_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            shutil.copytree(TEMPLATE, template)
            pbip = template / "Starter.pbip"
            payload = json.loads(pbip.read_text(encoding="utf-8"))
            payload["artifacts"] = []
            pbip.write_text(json.dumps(payload), encoding="utf-8")

            output = root / "Generated"
            with self.assertRaisesRegex(
                GenerationError,
                "template_pbip_expected_single_report",
            ):
                generate_project("Generated", output, template_root=template)

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
