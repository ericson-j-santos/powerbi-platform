import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_powerbi_repo import validate


SEMANTIC_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/"
    "semanticModel/definitionProperties/1.0.0/schema.json"
)
PBIP_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/pbip/"
    "pbipProperties/1.0.0/schema.json"
)
PBIR_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definitionProperties/2.0.0/schema.json"
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def create_semantic_model(root: Path, name: str = "Demo") -> Path:
    model = root / f"{name}.SemanticModel"
    (model / "definition").mkdir(parents=True)
    write_json(
        model / "definition.pbism",
        {
            "$schema": SEMANTIC_SCHEMA,
            "version": "4.2",
        },
    )
    (model / "definition" / "database.tmdl").write_text(
        f"database {name}\n\tcompatibilityLevel: 1702\n",
        encoding="utf-8",
    )
    (model / "definition" / "model.tmdl").write_text(
        "model Model\n\tculture: pt-BR\n",
        encoding="utf-8",
    )
    return model


def create_pbip_project(root: Path, name: str = "Demo") -> tuple[Path, Path, Path]:
    create_semantic_model(root, name)

    report = root / f"{name}.Report"
    page_name = "b8c5fb8d635f898326c6"
    write_json(
        report / "definition.pbir",
        {
            "$schema": PBIR_SCHEMA,
            "version": "4.0",
            "datasetReference": {
                "byPath": {
                    "path": f"../{name}.SemanticModel",
                }
            },
        },
    )
    write_json(
        report / "definition" / "version.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/versionMetadata/1.0.0/schema.json"
            ),
            "version": "2.0.0",
        },
    )
    write_json(
        report / "definition" / "report.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/report/1.2.0/schema.json"
            ),
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU10",
                    "reportVersionAtImport": "5.61",
                    "type": "SharedResources",
                }
            },
            "layoutOptimization": "None",
        },
    )
    write_json(
        report / "definition" / "pages" / "pages.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/pagesMetadata/1.0.0/schema.json"
            ),
            "pageOrder": [page_name],
            "activePageName": page_name,
        },
    )
    write_json(
        report / "definition" / "pages" / page_name / "page.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/page/1.3.0/schema.json"
            ),
            "name": page_name,
            "displayName": "Page 1",
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        },
    )

    pbip = root / f"{name}.pbip"
    write_json(
        pbip,
        {
            "$schema": PBIP_SCHEMA,
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{name}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    return pbip, report, root / f"{name}.SemanticModel"


class ValidatePowerBIRepoTests(unittest.TestCase):
    def test_accepts_minimal_semantic_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_semantic_model(root)
            self.assertEqual([], validate(root))

    def test_accepts_complete_pbip_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_pbip_project(root)
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

    def test_rejects_pbip_missing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pbip, _, _ = create_pbip_project(root)
            payload = json.loads(pbip.read_text(encoding="utf-8"))
            payload["artifacts"][0]["report"]["path"] = "Missing.Report"
            write_json(pbip, payload)

            errors = validate(root)
            self.assertTrue(
                any("relatório referenciado pelo PBIP não existe" in error for error in errors)
            )

    def test_rejects_absolute_semantic_model_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, report, _ = create_pbip_project(root)
            pbir = report / "definition.pbir"
            payload = json.loads(pbir.read_text(encoding="utf-8"))
            payload["datasetReference"]["byPath"]["path"] = "C:/outside/Model.SemanticModel"
            write_json(pbir, payload)

            errors = validate(root)
            self.assertTrue(any("caminho absoluto" in error for error in errors))

    def test_rejects_active_page_outside_page_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, report, _ = create_pbip_project(root)
            pages = report / "definition" / "pages" / "pages.json"
            payload = json.loads(pages.read_text(encoding="utf-8"))
            payload["activePageName"] = "missing"
            write_json(pages, payload)

            errors = validate(root)
            self.assertTrue(any("activePageName" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
