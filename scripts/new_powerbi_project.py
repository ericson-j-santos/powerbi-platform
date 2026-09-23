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
except ModuleNotFoundError:
    from validate_powerbi_repo import validate


DEFAULT_TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates" / "pbip-starter"
PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class GeneratorError(ValueError):
    pass


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_project_name(name: str) -> None:
    if not PROJECT_NAME_PATTERN.fullmatch(name):
        raise GeneratorError("invalid_project_name")
    if name.upper() in WINDOWS_RESERVED_NAMES:
        raise GeneratorError("reserved_project_name")


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GeneratorError(f"template_json_invalid:{path.name}") from exc
    if not isinstance(payload, dict):
        raise GeneratorError(f"template_json_invalid:{path.name}")
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _assert_template(template_root: Path) -> None:
    required = [
        template_root / "Starter.pbip",
        template_root / "Starter.Report" / "definition.pbir",
        template_root / "Starter.SemanticModel" / "definition.pbism",
        template_root / "Starter.SemanticModel" / "definition" / "database.tmdl",
        template_root / "Starter.SemanticModel" / "definition" / "model.tmdl",
    ]
    missing = [
        path.relative_to(template_root).as_posix()
        for path in required
        if not path.is_file()
    ]
    if missing:
        raise GeneratorError(f"template_incomplete:{','.join(missing)}")


def generate_project(
    name: str,
    output: Path,
    *,
    template_root: Path = DEFAULT_TEMPLATE_ROOT,
) -> Path:
    _validate_project_name(name)

    template_root = template_root.resolve()
    _assert_template(template_root)

    destination = output.expanduser().resolve()
    if destination.exists():
        raise GeneratorError("destination_already_exists")
    if _is_within(destination, template_root) or _is_within(template_root, destination):
        raise GeneratorError("destination_conflicts_with_template")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=destination.parent)
    )
    staging = temporary_root / "project"

    try:
        shutil.copytree(template_root, staging)
        starter_readme = staging / "README.md"
        if starter_readme.exists():
            starter_readme.unlink()

        starter_pbip = staging / "Starter.pbip"
        starter_report = staging / "Starter.Report"
        starter_model = staging / "Starter.SemanticModel"

        generated_pbip = staging / f"{name}.pbip"
        generated_report = staging / f"{name}.Report"
        generated_model = staging / f"{name}.SemanticModel"

        starter_pbip.rename(generated_pbip)
        starter_report.rename(generated_report)
        starter_model.rename(generated_model)

        pbip = _load_json(generated_pbip)
        artifacts = pbip.get("artifacts")
        if not isinstance(artifacts, list) or len(artifacts) != 1:
            raise GeneratorError("template_pbip_artifacts_invalid")
        report = artifacts[0].get("report") if isinstance(artifacts[0], dict) else None
        if not isinstance(report, dict):
            raise GeneratorError("template_pbip_report_invalid")
        report["path"] = f"{name}.Report"
        _write_json(generated_pbip, pbip)

        definition_pbir = generated_report / "definition.pbir"
        pbir = _load_json(definition_pbir)
        dataset_reference = pbir.get("datasetReference")
        by_path = (
            dataset_reference.get("byPath")
            if isinstance(dataset_reference, dict)
            else None
        )
        if not isinstance(by_path, dict):
            raise GeneratorError("template_dataset_reference_invalid")
        by_path["path"] = f"../{name}.SemanticModel"
        _write_json(definition_pbir, pbir)

        database_tmdl = generated_model / "definition" / "database.tmdl"
        database_lines = database_tmdl.read_text(encoding="utf-8").splitlines()
        if not database_lines or not database_lines[0].startswith("database "):
            raise GeneratorError("template_database_invalid")
        database_lines[0] = f"database {name}Model"
        database_tmdl.write_text(
            "\n".join(database_lines) + "\n",
            encoding="utf-8",
        )

        errors = validate(staging)
        if errors:
            raise GeneratorError("generated_project_invalid:" + " | ".join(errors))

        staging.replace(destination)
    except Exception:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    else:
        shutil.rmtree(temporary_root, ignore_errors=True)

    return destination / f"{name}.pbip"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera um projeto PBIP reutilizável a partir do starter canônico."
    )
    parser.add_argument("--name", required=True, help="Nome técnico do projeto.")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Diretório de destino exato do projeto gerado.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generated_pbip = generate_project(args.name, args.output)
    except (GeneratorError, OSError) as exc:
        print(f"POWERBI_PROJECT_GENERATION_FAILED reason={exc}", file=sys.stderr)
        return 1

    print(f"POWERBI_PROJECT_GENERATION_OK path={generated_pbip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
