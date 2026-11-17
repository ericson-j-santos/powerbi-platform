#!/usr/bin/env python3
"""Pré-validação segura e SOMENTE LEITURA de arquivos PBIX.

Não transfere arquivos, não executa Power BI, não altera conexões,
não instala componentes nem interage com GUI. Projetado para ser chamado
por um Command Gateway já autenticado, com sessão e worktree válidos.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import sys
import zipfile
from pathlib import Path

MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_ENTRIES = 512
MAX_DECLARED_BYTES = 512 * 1024 * 1024
MAX_LAYOUT_BYTES = 16 * 1024 * 1024
MANDATORY_MEMBERS = frozenset(("Version", "Report/Layout", "Connections", "DataModel"))
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CORRELATION_RE = re.compile(r"^[A-Za-z0-9._-]{3,80}$")


class PreflightBlocked(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _read_stable_file(path: Path) -> bytes:
    if path.suffix.lower() != ".pbix":
        raise PreflightBlocked("invalid_extension")
    try:
        first = path.lstat()
        if not stat.S_ISREG(first.st_mode) or first.st_nlink != 1:
            raise PreflightBlocked("file_not_regular_or_hardlinked")
        if not 0 < first.st_size <= MAX_FILE_BYTES:
            raise PreflightBlocked("invalid_file_size")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size) != (
                first.st_dev, first.st_ino, first.st_size
            ):
                raise PreflightBlocked("file_changed_during_open")
            data = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
            if (
                after.st_size != opened.st_size
                or after.st_mtime_ns != opened.st_mtime_ns
                or after.st_ctime_ns != opened.st_ctime_ns
                or len(data) != opened.st_size
            ):
                raise PreflightBlocked("file_changed_during_read")
            return data
    except PreflightBlocked:
        raise
    except (FileNotFoundError, PermissionError, OSError):
        raise PreflightBlocked("file_unavailable") from None


def _inspect_pbix_bytes(data: bytes) -> tuple[int, int, int]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if not 0 < len(infos) <= MAX_ENTRIES:
                raise PreflightBlocked("zip_entry_limit")
            member_names: set[str] = set()
            total = 0
            for info in infos:
                name = info.filename
                parts = name.replace("\\", "/").split("/")
                if (
                    not name
                    or name.startswith(("/", "\\"))
                    or re.match(r"^[A-Za-z]:", name)
                    or any(part in ("", ".", "..") for part in parts if part != parts[-1])
                    or ".." in parts
                    or "\\" in name
                ):
                    raise PreflightBlocked("unsafe_zip_member")
                key = name.casefold()
                if key in member_names:
                    raise PreflightBlocked("duplicate_zip_member")
                member_names.add(key)
                if info.flag_bits & 0x1:
                    raise PreflightBlocked("encrypted_zip_member")
                if info.file_size > MAX_DECLARED_BYTES:
                    raise PreflightBlocked("zip_member_too_large")
                total += info.file_size
                if total > MAX_DECLARED_BYTES:
                    raise PreflightBlocked("zip_total_limit")
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise PreflightBlocked("zip_symlink_member")

            if not {x.casefold() for x in MANDATORY_MEMBERS}.issubset(member_names):
                raise PreflightBlocked("pbix_required_member_missing")
            layout_info = archive.getinfo("Report/Layout")
            if layout_info.file_size > MAX_LAYOUT_BYTES:
                raise PreflightBlocked("layout_too_large")
            # Lê todos os membros e valida o CRC sem extrair nada.
            if archive.testzip() is not None:
                raise PreflightBlocked("zip_crc_mismatch")
            layout = json.loads(archive.read("Report/Layout").decode("utf-16"))
            pages = layout.get("sections") if isinstance(layout, dict) else None
            if not isinstance(pages, list) or not pages:
                raise PreflightBlocked("pbix_no_pages")
            if len(pages) > 1000:
                raise PreflightBlocked("pbix_pages_limit")
            visuals = 0
            for section in pages:
                if not isinstance(section, dict):
                    raise PreflightBlocked("pbix_invalid_page")
                containers = section.get("visualContainers", [])
                if not isinstance(containers, list):
                    raise PreflightBlocked("pbix_invalid_visuals")
                visuals += len(containers)
            return len(pages), visuals, len(infos)
    except PreflightBlocked:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, KeyError, UnicodeError,
            json.JSONDecodeError, ValueError, RuntimeError, OSError):
        raise PreflightBlocked("pbix_invalid_container") from None


def _detect_desktop() -> str:
    """Verificação opcional, sem executar programa nem alterar o Registro."""
    if sys.platform != "win32":
        return "not_windows"
    roots = (
        os.environ.get("ProgramW6432"),
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    )
    for root in roots:
        if root:
            candidate = Path(root) / "Microsoft Power BI Desktop" / "bin" / "PBIDesktop.exe"
            if candidate.is_file():
                return "present"
    try:
        import winreg
        for key_name in (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\PBIDesktop.exe",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\PBIDesktop.exe",
        ):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name) as k:
                    executable, _ = winreg.QueryValueEx(k, "")
                if isinstance(executable, str) and Path(executable).is_file():
                    return "present"
            except OSError:
                continue
    except ImportError:
        pass
    return "not_found_in_known_paths"


def validate_file(path: Path, expected_sha256: str, expected_size: int | None,
                  correlation_id: str, check_desktop: bool = False) -> dict:
    if not SHA256_RE.fullmatch(expected_sha256):
        raise PreflightBlocked("invalid_expected_sha256")
    if not CORRELATION_RE.fullmatch(correlation_id):
        raise PreflightBlocked("invalid_correlation_id")
    if expected_size is not None and not 0 < expected_size <= MAX_FILE_BYTES:
        raise PreflightBlocked("invalid_expected_size")
    data = _read_stable_file(path)
    sha = hashlib.sha256(data).hexdigest()
    if sha != expected_sha256.lower():
        raise PreflightBlocked("sha256_mismatch")
    if expected_size is not None and len(data) != expected_size:
        raise PreflightBlocked("size_mismatch")
    pages, visuals, entries = _inspect_pbix_bytes(data)
    return {
        "status": "observed",
        "correlation_id": correlation_id,
        "file_sha256": sha,
        "file_size_bytes": len(data),
        "pages": pages,
        "visual_elements": visuals,
        "container_members": entries,
        "desktop": _detect_desktop() if check_desktop else "not_checked",
        "desktop_opened": False,
        "connections_refreshed": False,
        "mutations_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PBIX: pré-validação somente leitura")
    parser.add_argument("--pbix", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--correlation-id", required=True)
    parser.add_argument("--check-desktop", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_file(
            args.pbix, args.expected_sha256, args.expected_size,
            args.correlation_id, args.check_desktop,
        )
    except PreflightBlocked as exc:
        result = {
            "status": "blocked",
            "correlation_id": (
                args.correlation_id if CORRELATION_RE.fullmatch(args.correlation_id) else "invalid"
            ),
            "reason": exc.code,
            "desktop_opened": False,
            "connections_refreshed": False,
            "mutations_performed": False,
        }
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
