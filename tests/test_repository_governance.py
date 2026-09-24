from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
ALLOWED_EXTERNAL_ACTIONS = {
    "actions/checkout",
    "actions/setup-python",
    "actions/upload-artifact",
}


class RepositoryGovernanceTests(unittest.TestCase):
    def test_external_actions_are_allowlisted_and_pinned_to_full_sha(self):
        found = 0
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow.read_text(encoding="utf-8")
            for action, ref in USES.findall(text):
                if action.startswith("./"):
                    continue
                found += 1
                self.assertIn(
                    action,
                    ALLOWED_EXTERNAL_ACTIONS,
                    f"{workflow.name}: action externa não allowlisted: {action}",
                )
                self.assertRegex(
                    ref,
                    SHA40,
                    f"{workflow.name}: {action} deve usar SHA completo, recebeu {ref}",
                )
        self.assertGreater(found, 0)

    def test_workflows_remain_read_only(self):
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow.read_text(encoding="utf-8")
            self.assertIn(
                "permissions:\n  contents: read",
                text,
                f"{workflow.name}: permissions mínimas ausentes",
            )
            self.assertNotRegex(
                text,
                re.compile(r"^\s+[A-Za-z0-9_-]+:\s*write\s*$", re.MULTILINE),
                f"{workflow.name}: permissão write exige revisão explícita",
            )
            self.assertNotIn("secrets.", text, f"{workflow.name}: segredo não permitido no CI atual")

    def test_governance_files_exist(self):
        required = (
            ROOT / "SECURITY.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "docs" / "gold-standard.md",
            ROOT / ".github" / "pull_request_template.md",
            ROOT / ".github" / "dependabot.yml",
        )
        for path in required:
            self.assertTrue(path.is_file(), f"arquivo de governança ausente: {path}")

    def test_dependabot_tracks_github_actions(self):
        text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn('package-ecosystem: "github-actions"', text)
        self.assertIn('interval: "weekly"', text)


if __name__ == "__main__":
    unittest.main()
