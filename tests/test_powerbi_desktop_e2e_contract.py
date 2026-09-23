from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "powerbi-desktop-e2e.yml"
SCRIPT = ROOT / "scripts" / "powerbi_desktop_e2e.ps1"


class PowerBIDesktopE2EContractTests(unittest.TestCase):
    def test_workflow_uses_ephemeral_windows_without_reqsys_runner(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: windows-2025", text)
        self.assertNotIn("self-hosted", text)
        self.assertNotIn("reqsys-dev", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("pull_request:", text)
        self.assertIn("push:", text)

    def test_workflow_is_read_only_and_secret_free(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("secrets.", text)
        self.assertIn("TARGET_SHA:", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertNotIn("\\${{", text)
        self.assertIn("ref: ${{ env.TARGET_SHA }}", text)
        self.assertIn("-Mode download", text)
        self.assertIn("-Mode install", text)
        self.assertIn("-Mode open", text)

    def test_script_uses_official_pinned_installer_and_real_pbip(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("https://download.microsoft.com/", text)
        self.assertIn('expectedVersionPrefix = "2.157.1354"', text)
        self.assertIn("ACCEPT_EULA=1", text)
        self.assertIn('ValidateSet("download", "install", "open")', text)
        self.assertIn("--max-time 240", text)
        self.assertIn("Wait-Process -Id $install.Id -Timeout 240", text)
        self.assertIn("templates/pbip-starter/Starter.pbip", text)
        self.assertIn('Get-Process -Name "PBIDesktop"', text)
        self.assertIn('Get-Process -Name "msmdsrv"', text)
        self.assertIn('Filter "localSettings.json"', text)

    def test_script_has_false_positive_controls(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("expected_sha_mismatch", text)
        self.assertIn("semantic_engine_not_started", text)
        self.assertIn("pbip_local_state_not_created", text)
        self.assertIn("powerbi_open_mutated_source", text)
        self.assertIn("production_touched = $false", text)
        self.assertIn("secrets_read = $false", text)


if __name__ == "__main__":
    unittest.main()
