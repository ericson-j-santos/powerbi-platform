from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-powerbi.yml"


class ValidateWorkflowContractTests(unittest.TestCase):
    def test_structural_ci_is_bound_to_immutable_target_sha(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "TARGET_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
            text,
        )
        self.assertIn("Checkout immutable target SHA", text)
        self.assertIn("ref: ${{ env.TARGET_SHA }}", text)
        self.assertIn('actual_sha="$(git rev-parse HEAD)"', text)
        self.assertIn('test "$actual_sha" = "$TARGET_SHA"', text)

    def test_structural_ci_keeps_read_only_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read", text)


if __name__ == "__main__":
    unittest.main()
