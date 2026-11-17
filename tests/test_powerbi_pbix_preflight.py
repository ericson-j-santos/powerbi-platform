from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path


FILE = Path(__file__).resolve().parents[1] / "scripts" / "powerbi_pbix_preflight.py"
SPEC = importlib.util.spec_from_file_location("preflight", FILE)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def make_pbix(extra=None, skip=None):
    data = {
        "Version": b"1",
        "Report/Layout": json.dumps({"sections": [{"visualContainers": [{}, {}]}]}).encode("utf-16"),
        "Connections": b"{}",
        "DataModel": b"model",
    }
    data.update(extra or {})
    for k in (skip or []):
        del data[k]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as arc:
        for name, value in data.items():
            arc.writestr(name, value)
    return out.getvalue()


class PbixReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.path = Path(self.d.name) / "test.pbix"

    def validate(self, data, digest=None, size=None):
        self.path.write_bytes(data)
        return preflight.validate_file(
            self.path,
            digest or hashlib.sha256(data).hexdigest(),
            len(data) if size is None else size,
            "powerbi-store-test",
        )

    def assertBlocked(self, expected, fn):
        with self.assertRaises(preflight.PreflightBlocked) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, expected)

    def test_positive(self):
        r = self.validate(make_pbix())
        self.assertEqual((r["status"], r["pages"], r["visual_elements"]),
                         ("observed", 1, 2))
        self.assertFalse(r["mutations_performed"])
        self.assertFalse(r["desktop_opened"])

    def test_replay_is_read_only_and_stable(self):
        original = make_pbix()
        self.path.write_bytes(original)
        digest = hashlib.sha256(original).hexdigest()
        before = self.path.stat().st_mtime_ns
        a = preflight.validate_file(self.path, digest, len(original), "powerbi-store-test")
        b = preflight.validate_file(self.path, digest, len(original), "powerbi-store-test")
        self.assertEqual(a, b)
        self.assertEqual(self.path.stat().st_mtime_ns, before)

    def test_wrong_sha(self):
        self.assertBlocked("sha256_mismatch", lambda: self.validate(make_pbix(), "0" * 64))

    def test_wrong_size(self):
        data = make_pbix()
        self.assertBlocked("size_mismatch", lambda: self.validate(data, size=len(data) + 1))

    def test_required_member_missing(self):
        self.assertBlocked("pbix_required_member_missing",
                           lambda: self.validate(make_pbix(skip=["DataModel"])))

    def test_zip_path_traversal(self):
        self.assertBlocked("unsafe_zip_member",
                           lambda: self.validate(make_pbix(extra={"../bad": b"x"})))

    def test_zip_duplicate_case(self):
        self.assertBlocked("duplicate_zip_member",
                           lambda: self.validate(make_pbix(extra={"version": b"x"})))

    def test_invalid_zip(self):
        self.assertBlocked("pbix_invalid_container", lambda: self.validate(b"not a zip"))

    def test_reject_symlink(self):
        real = Path(self.d.name) / "real.pbix"
        real.write_bytes(make_pbix())
        try:
            self.path.symlink_to(real)
        except (OSError, NotImplementedError):
            self.skipTest("Sistema sem criação de symlink")
        data = real.read_bytes()
        self.assertBlocked("file_not_regular_or_hardlinked",
                           lambda: preflight.validate_file(
                               self.path, hashlib.sha256(data).hexdigest(),
                               len(data), "powerbi-store-test"))

    def test_invalid_correlation(self):
        self.assertBlocked("invalid_correlation_id",
                           lambda: preflight.validate_file(
                               self.path, "a"*64, None, "bad token!"))

    def test_missing_file_is_blocked(self):
        self.assertBlocked("file_unavailable", lambda: preflight.validate_file(
            self.path, "a" * 64, 200, "powerbi-store-test"))

    def test_invalid_expected_sha(self):
        self.assertBlocked("invalid_expected_sha256", lambda: preflight.validate_file(
            self.path, "invalid", None, "powerbi-store-test"))

    def test_too_large_file_is_rejected_before_read(self):
        with self.path.open("wb") as handle:
            handle.truncate(preflight.MAX_FILE_BYTES + 1)
        self.assertBlocked("invalid_file_size", lambda: preflight.validate_file(
            self.path, "a" * 64, None, "powerbi-store-test"))

    def test_malformed_layout(self):
        self.assertBlocked("pbix_invalid_container", lambda: self.validate(
            make_pbix(extra={"Report/Layout": "invalid-json".encode("utf-16")})))

    def test_empty_page_list(self):
        self.assertBlocked("pbix_no_pages", lambda: self.validate(
            make_pbix(extra={"Report/Layout": json.dumps({"sections": []}).encode("utf-16")})))

    def test_desktop_discovery_is_non_windows_safe(self):
        from unittest.mock import patch
        with patch.object(preflight.sys, "platform", "linux"):
            self.assertEqual(preflight._detect_desktop(), "not_windows")

    def test_detect_desktop_from_allowed_program_files_location(self):
        from unittest.mock import patch
        fake = Path(self.d.name) / "Microsoft Power BI Desktop" / "bin" / "PBIDesktop.exe"
        fake.parent.mkdir(parents=True)
        fake.write_bytes(b"fixture-only")
        with patch.object(preflight.sys, "platform", "win32"), patch.dict(
            preflight.os.environ, {"ProgramW6432": self.d.name}
        ):
            self.assertEqual(preflight._detect_desktop(), "present")


if __name__ == "__main__":
    unittest.main()
