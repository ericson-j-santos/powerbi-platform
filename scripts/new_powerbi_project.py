#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

try:
    from scripts.validate_powerbi_repo import validate
except ModuleNotFoundError:  # direct execution: python scripts/new_powerbi_project.py
    from validate_powerbi_repo import validate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "templates" / "pbip-starter"
PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
LOCAL_STATE_NAMES = {"localsettings.json", "cache.abf"}


class GenerationError(RuntimeError):
    pass


def _ignore_local_state(_directory: str, names: list[str]) -> list[str]:
    ignored: list[str] = []
    for name in names:
        lowered = name.casefold()
        if lowered == ".pbi" or lowered in LOCAL_STATE_NAMES:
            ignored.append(name)
    return ignored


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationError(f"invalid_template_json:{path.name}:{exc}") from exc
    if not isinstance(payload, dict):
        raise GenerationError(f"invalid_template_json_root:{path.name}")
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_project_name(name: str) -> None:
    if not PROJECT_NAME_RE.fullmatch(name):
        raise GenerationError(
            "invalid_project_name: use 1-64 characters, starting with a letter, "
            "and only ASCII letters, digits, or underscore"
        )


def _assert_template(template_root: Path) -> None:
    required = [
        template_root / "Starter.pbip",
        template_root / "Starter.Report" / "definition.pbir",
        template_root / "Starter.SemanticModel" / "definition.pbism",
        template_root / "Starter.SemanticModel" / "definition" / "database.tmdl",
    ]
    missing = [path.relative_to(template_root).as_posix() for path in required if not path.is_file()]
    if missing:
        raise GenerationError(f"template_missing_required_files:{','.join(missing)}")


def _rewrite_pbip(path: Path, name: str) -> None:
    payload = _read_json(path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1:
        raise GenerationError("template_pbip_expected_single_report")
    report = artifacts[0].get("report") if isinstance(artifacts[0], dict) else None
    if not isinstance(report, dict) or report.get("path") != "Starter.Report":
        raise GenerationError("template_pbip_report_reference_changed")
    report["path"] = f"{name}.Report"
    _write_json(path, payload)


def _rewrite_pbir(path: Path, name: str) -> None:
    payload = _read_json(path)
    dataset_reference = payload.get("datasetReference")
    by_path = dataset_reference.get("byPath") if isinstance(dataset_reference, dict) else None
    if not isinstance(by_path, dict) or by_path.get("path") != "../Starter.SemanticModel":
        raise GenerationError("template_pbir_semantic_reference_changed")
    by_path["path"] = f"../{name}.SemanticModel"
    _write_json(path, payload)


def _rewrite_database(path: Path, name: str) -> None:
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(?m)^database\s+StarterModel\s*$",
        f"database {name}Model",
        original,
        count=1,
    )
    if count != 1:
        raise GenerationError("template_database_identifier_changed")
    path.write_text(updated, encoding="utf-8")


def generate_project(
    name: str,
    output: Path,
    *,
    template_root: Path = DEFAULT_TEMPLATE,
) -> Path:
    _validate_project_name(name)

    template_root = template_root.resolve()
    output = output.resolve()

    if output.exists():
        raise GenerationError(f"destination_exists:{output}")
    if output == template_root or template_root in output.parents:
        raise GenerationError("destination_inside_template")

    _assert_template(template_root)
    output.parent.mkdir(parents=True, exist_ok=True)

    temp_root = Path(
        tempfile.mkdtemp(
            prefix=f".{name}.powerbi-gen-",
            dir=output.parent,
        )
    )

    try:
        report_target = temp_root / f"{name}.Report"
        model_target = temp_root / f"{name}.SemanticModel"
        pbip_target = temp_root / f"{name}.pbip"

        shutil.copytree(
            template_root / "Starter.Report",
            report_target,
            ignore=_ignore_local_state,
        )
        shutil.copytree(
            template_root / "Starter.SemanticModel",
            model_target,
            ignore=_ignore_local_state,
        )
        shutil.copy2(template_root / "Starter.pbip", pbip_target)

        _rewrite_pbip(pbip_target, name)
        _rewrite_pbir(report_target / "definition.pbir", name)
        _rewrite_database(model_target / "definition" / "database.tmdl", name)

        errors = validate(temp_root)
        if errors:
            raise GenerationError(
                "generated_project_validation_failed:" + " | ".join(errors)
            )

        temp_root.replace(output)
        return output
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a reusable PBIP project from templates/pbip-starter."
    )
    parser.add_argument("--name", required=True, help="Project identifier, e.g. SalesAnalytics")
    parser.add_argument("--output", required=True, type=Path, help="Destination directory")
    args = parser.parse_args(argv[1:])

    try:
        generated = generate_project(args.name, args.output)
    except GenerationError as exc:
        print(f"POWERBI_PROJECT_GENERATION_FAILED reason={exc}", file=sys.stderr)
        return 2

    print(f"POWERBI_PROJECT_GENERATED path={generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
