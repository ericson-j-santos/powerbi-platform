#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

FORBIDDEN_SUFFIXES = {".pbix", ".pbit"}
JSON_SUFFIXES = {".json", ".pbip", ".pbir", ".pbism"}


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(root)
        lower_parts = [part.lower() for part in relative.parts]

        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"arquivo binário Power BI não permitido: {relative}")

        if ".pbi" in lower_parts and path.name.lower() in {
            "localsettings.json",
            "cache.abf",
        }:
            errors.append(f"estado local do Power BI não pode ser versionado: {relative}")

        if path.suffix.lower() in JSON_SUFFIXES:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"JSON inválido em {relative}: {exc}")
                continue

            if path.suffix.lower() == ".pbism":
                version = str(payload.get("version", ""))
                schema = str(payload.get("$schema", ""))
                if not version.startswith("4."):
                    errors.append(f"definition.pbism deve usar versão 4.x: {relative}")
                if "semanticModel" not in schema:
                    errors.append(f"schema de semantic model ausente/incorreto: {relative}")

    for semantic_model in root.rglob("*.SemanticModel"):
        if not semantic_model.is_dir():
            continue
        required = [
            semantic_model / "definition.pbism",
            semantic_model / "definition" / "database.tmdl",
            semantic_model / "definition" / "model.tmdl",
        ]
        for required_file in required:
            if not required_file.is_file():
                errors.append(
                    f"arquivo obrigatório ausente em {semantic_model.relative_to(root)}: "
                    f"{required_file.relative_to(semantic_model)}"
                )

    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("POWERBI_REPO_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("POWERBI_REPO_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
