from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "demand-tracker"
REPORT = PROJECT / "DemandTracker.Report"
MODEL = PROJECT / "DemandTracker.SemanticModel"
PAGE = REPORT / "definition" / "pages" / "9f3b7c1d2a4e6f809abc"

class DemandTrackerProjectTests(unittest.TestCase):
    def test_pbip_references_local_report_and_model(self):
        pbip=json.loads((PROJECT/"DemandTracker.pbip").read_text(encoding="utf-8"))
        self.assertEqual(pbip["artifacts"][0]["report"]["path"],"DemandTracker.Report")
        pbir=json.loads((REPORT/"definition.pbir").read_text(encoding="utf-8"))
        self.assertEqual(pbir["datasetReference"]["byPath"]["path"],"../DemandTracker.SemanticModel")

    def test_semantic_model_is_parameterized_without_secrets(self):
        model=(MODEL/"definition"/"model.tmdl").read_text(encoding="utf-8")
        demandas=(MODEL/"definition"/"tables"/"Demandas.tmdl").read_text(encoding="utf-8")
        combined=(model+"\n"+demandas).casefold()
        for expected in ("todosourcemode","todopostgresserver","todopostgresdatabase","todo_bus.queue_events",'= "postgres"'):
            self.assertIn(expected,combined)
        for forbidden in ("password=","authorization:","bearer ","todo_gateway_token"):
            self.assertNotIn(forbidden,combined)

    def test_measures_cover_operational_kpis(self):
        measures=(MODEL/"definition"/"tables"/"_Measures.tmdl").read_text(encoding="utf-8")
        for name in ("Total Demandas","P0","Em Andamento","Bloqueadas","Revalidar"):
            self.assertIn(name,measures)

    def test_page_has_expected_visual_contract(self):
        page=json.loads((PAGE/"page.json").read_text(encoding="utf-8"))
        self.assertEqual(page["displayName"],"Demandas Operacionais")
        visual_files=sorted((PAGE/"visuals").glob("*/visual.json"))
        self.assertEqual(len(visual_files),10)
        types=[]; serialized=[]
        for path in visual_files:
            payload=json.loads(path.read_text(encoding="utf-8"))
            types.append(payload["visual"]["visualType"])
            serialized.append(json.dumps(payload,ensure_ascii=False))
        self.assertEqual(types.count("cardVisual"),5)
        self.assertEqual(types.count("slicer"),3)
        self.assertEqual(types.count("barChart"),1)
        self.assertEqual(types.count("tableEx"),1)
        joined="\n".join(serialized)
        for field in ("Prioridade","Estado","Projeto","Próxima ação","Bloqueio"):
            self.assertIn(field,joined)

    def test_e2e_workflow_opens_this_pbip_on_target_sha(self):
        workflow=(ROOT/".github"/"workflows"/"demand-tracker-desktop-e2e.yml").read_text(encoding="utf-8")
        self.assertIn("TARGET_SHA",workflow)
        self.assertIn("projects\\demand-tracker\\DemandTracker.pbip",workflow)
        self.assertIn("-ProjectFile",workflow)
        self.assertIn("powerbi_desktop_e2e.ps1",workflow)

if __name__ == "__main__":
    unittest.main()
