"""Static regression contracts; real installation is validated by Desktop E2E."""
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "powerbi_desktop_e2e.ps1"
EXPECTED_HASH = "9996c3c015d33e1a05041ee0631727890c75ab66685e268f2c3cd2c7b8cb0209"


class InstallerPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8-sig")

    def test_versioned_microsoft_installer_matches_approved_release(self):
        match = re.search(r'^\$installerUrl = "([^"]+)"', self.source, re.MULTILINE)
        self.assertIsNotNone(match)
        url = urlparse(match.group(1))
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.hostname, "download.microsoft.com")
        self.assertTrue(url.path.endswith("/PBIDesktopSetup-2026-08_x64.exe"))
        self.assertIn('$expectedVersionPrefix = "2.157.1354"', self.source)
        self.assertIn(f'$expectedInstallerSha256 = "{EXPECTED_HASH}"', self.source)

    def test_download_rejects_wrong_digest_before_success(self):
        start = self.source.index('if ($Mode -eq "download")')
        end = self.source.index('if ($Mode -eq "install")')
        download = self.source[start:end]
        guard = download.index('if ($state.installer_sha256 -ne $expectedInstallerSha256)')
        rejection = download.index('throw "installer_sha256_mismatch"')
        success = download.index('POWERBI_E2E_STAGE=download_completed')
        self.assertLess(guard, rejection)
        self.assertLess(rejection, success)

    def test_install_rechecks_pinned_digest_before_starting_process(self):
        start = self.source.index('if ($Mode -eq "install")')
        install = self.source[start:]
        guard = install.index('$observedHash -ne $expectedInstallerSha256')
        rejection = install.index('throw "installer_hash_changed"')
        process = install.index('Start-Process -FilePath $installerPath')
        self.assertLess(guard, rejection)
        self.assertLess(rejection, process)

    def test_version_failure_keeps_observed_evidence_and_stays_blocking(self):
        observation = self.source.index('$state.installed_version = $installedVersion')
        persisted = self.source.index('Write-State $state', observation)
        rejection = self.source.index('throw "powerbi_version_mismatch"')
        self.assertLess(persisted, rejection)
        self.assertIn('expected_sha256 = $expectedInstallerSha256', self.source)
        self.assertIn('throw "semantic_engine_not_started"', self.source)
        self.assertIn('throw "powerbi_open_mutated_source"', self.source)
        self.assertIn('throw "installer_timeout"', self.source)


if __name__ == "__main__":
    unittest.main()
