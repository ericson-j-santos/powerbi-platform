import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_powerbi_repo import validate


class ValidatePowerBIRepoTests(unittest.TestCase):
    def test_accepts_minimal_semantic_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "Demo.SemanticModel"
            (model / "definition").mkdir(parents=True)
            (model / "definition.pbism").write_text(
                json.dumps(
                    {
                        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
                        "version": "4.2",
                    }
                ),
                encoding="utf-8",
            )
            (model / "definition" / "database.tmdl").write_text(
                "database Demo\n\tcompatibilityLevel: 1702\n",
                encoding="utf-8",
            )
            (model / "definition" / "model.tmdl").write_text(
                "model Model\n\tculture: pt-BR\n",
                encoding="utf-8",
            )

            self.assertEqual([], validate(root))

    def test_rejects_pbix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "report.pbix").write_bytes(b"binary")
            errors = validate(root)
            self.assertTrue(any("pbix" in error.lower() for error in errors))

    def test_rejects_local_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "Demo.SemanticModel" / ".pbi"
            cache.mkdir(parents=True)
            (cache / "localSettings.json").write_text("{}", encoding="utf-8")
            errors = validate(root)
            self.assertTrue(any("estado local" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
