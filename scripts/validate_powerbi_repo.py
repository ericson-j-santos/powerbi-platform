#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_SUFFIXES = {".pbix", ".pbit"}
JSON_SUFFIXES = {".json", ".pbip", ".pbir", ".pbism"}
LOCAL_STATE_FILES = {
    "localsettings.json",
    "cache.abf",
}


def _git_tracked_files(root: Path) -> set[str] | None:
    """Return Git-tracked paths, or None when Git state cannot be established."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    return {
        item.replace("\\", "/").casefold()
        for item in completed.stdout.split("\0")
        if item
    }


def _resolve_relative(
    *,
    root: Path,
    base: Path,
    raw_path: object,
    label: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label} deve conter caminho relativo não vazio")
        return None

    if "\\" in raw_path:
        errors.append(f"{label} deve usar '/' como separador: {raw_path}")
        return None

    if raw_path.startswith("/") or re.match(r"^[A-Za-z]:", raw_path):
        errors.append(f"{label} não pode usar caminho absoluto: {raw_path}")
        return None

    target = (base / Path(*raw_path.split("/"))).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} aponta para fora do repositório: {raw_path}")
        return None
    return target


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    payloads: dict[Path, object | None] = {}
    tracked_files = _git_tracked_files(root)

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(root)
        lower_parts = [part.lower() for part in relative.parts]

        relative_key = relative.as_posix().casefold()
        is_versioned = tracked_files is None or relative_key in tracked_files
        is_local_state = ".pbi" in lower_parts and path.name.lower() in LOCAL_STATE_FILES

        if path.suffix.lower() in FORBIDDEN_SUFFIXES and is_versioned:
            errors.append(f"arquivo binário Power BI não permitido: {relative}")

        if is_local_state:
            if is_versioned:
                errors.append(f"estado local do Power BI não pode ser versionado: {relative}")
            else:
                # Power BI Desktop legitimately creates these files locally.
                # They are valid when ignored/untracked and must not poison validation.
                continue

        if path.suffix.lower() in JSON_SUFFIXES:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"JSON inválido em {relative}: {exc}")
                payloads[path] = None
                continue

            payloads[path] = payload

            if path.suffix.lower() == ".pbism":
                version = str(payload.get("version", "")) if isinstance(payload, dict) else ""
                schema = str(payload.get("$schema", "")) if isinstance(payload, dict) else ""
                if not version.startswith("4."):
                    errors.append(f"definition.pbism deve usar versão 4.x: {relative}")
                if "semanticModel" not in schema:
                    errors.append(f"schema de semantic model ausente/incorreto: {relative}")

    def get_json(path: Path) -> dict | None:
        payload = payloads.get(path)
        return payload if isinstance(payload, dict) else None

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

    for pbip in root.rglob("*.pbip"):
        payload = get_json(pbip)
        if payload is None:
            continue

        relative = pbip.relative_to(root)
        schema = str(payload.get("$schema", ""))
        version = str(payload.get("version", ""))
        artifacts = payload.get("artifacts")

        if "/fabric/pbip/pbipProperties/" not in schema:
            errors.append(f"schema PBIP ausente/incorreto: {relative}")
        if not version.startswith("1."):
            errors.append(f"PBIP deve usar versão 1.x: {relative}")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"PBIP deve referenciar ao menos um relatório: {relative}")
            continue

        for index, artifact in enumerate(artifacts):
            report = artifact.get("report") if isinstance(artifact, dict) else None
            report_path = report.get("path") if isinstance(report, dict) else None
            target = _resolve_relative(
                root=root,
                base=pbip.parent,
                raw_path=report_path,
                label=f"{relative} artifacts[{index}].report.path",
                errors=errors,
            )
            if target is None:
                continue
            if target.suffix != ".Report":
                errors.append(f"PBIP deve apontar para pasta .Report: {relative} -> {report_path}")
            if not target.is_dir():
                errors.append(f"relatório referenciado pelo PBIP não existe: {relative} -> {report_path}")

    for report in root.rglob("*.Report"):
        if not report.is_dir():
            continue

        relative_report = report.relative_to(root)
        definition_pbir = report / "definition.pbir"
        version_json = report / "definition" / "version.json"
        report_json = report / "definition" / "report.json"
        pages_json = report / "definition" / "pages" / "pages.json"

        required = [definition_pbir, version_json, report_json, pages_json]
        for required_file in required:
            if not required_file.is_file():
                errors.append(
                    f"arquivo PBIR obrigatório ausente em {relative_report}: "
                    f"{required_file.relative_to(report)}"
                )

        pbir = get_json(definition_pbir)
        if pbir is not None:
            schema = str(pbir.get("$schema", ""))
            version = str(pbir.get("version", ""))
            dataset_reference = pbir.get("datasetReference")

            if "report/definitionProperties/" not in schema:
                errors.append(f"schema definition.pbir ausente/incorreto: {definition_pbir.relative_to(root)}")
            if not version.startswith("4."):
                errors.append(f"definition.pbir deve usar versão 4.x: {definition_pbir.relative_to(root)}")
            if not isinstance(dataset_reference, dict):
                errors.append(f"datasetReference ausente em {definition_pbir.relative_to(root)}")
            else:
                by_path = dataset_reference.get("byPath")
                by_connection = dataset_reference.get("byConnection")
                active_refs = sum(value is not None for value in (by_path, by_connection))
                if active_refs != 1:
                    errors.append(
                        f"datasetReference deve ter exatamente uma referência ativa em "
                        f"{definition_pbir.relative_to(root)}"
                    )
                if isinstance(by_path, dict):
                    target = _resolve_relative(
                        root=root,
                        base=report,
                        raw_path=by_path.get("path"),
                        label=f"{definition_pbir.relative_to(root)} datasetReference.byPath.path",
                        errors=errors,
                    )
                    if target is not None:
                        if target.suffix != ".SemanticModel":
                            errors.append(
                                f"byPath deve apontar para pasta .SemanticModel: "
                                f"{definition_pbir.relative_to(root)}"
                            )
                        if not target.is_dir():
                            errors.append(
                                f"modelo semântico referenciado não existe: "
                                f"{definition_pbir.relative_to(root)} -> {by_path.get('path')}"
                            )
                elif isinstance(by_connection, dict):
                    connection_string = by_connection.get("connectionString")
                    if not isinstance(connection_string, str) or not connection_string.strip():
                        errors.append(
                            f"byConnection deve conter connectionString: "
                            f"{definition_pbir.relative_to(root)}"
                        )

        version_payload = get_json(version_json)
        if version_payload is not None:
            version = str(version_payload.get("version", ""))
            schema = str(version_payload.get("$schema", ""))
            if not version.startswith("2."):
                errors.append(f"PBIR version.json deve usar versão 2.x: {version_json.relative_to(root)}")
            if "report/definition/versionMetadata/" not in schema:
                errors.append(f"schema version.json ausente/incorreto: {version_json.relative_to(root)}")

        report_payload = get_json(report_json)
        if report_payload is not None:
            schema = str(report_payload.get("$schema", ""))
            if "report/definition/report/" not in schema:
                errors.append(f"schema report.json ausente/incorreto: {report_json.relative_to(root)}")
            if "themeCollection" not in report_payload:
                errors.append(f"themeCollection ausente em {report_json.relative_to(root)}")
            if "layoutOptimization" not in report_payload:
                errors.append(f"layoutOptimization ausente em {report_json.relative_to(root)}")

        pages_payload = get_json(pages_json)
        if pages_payload is not None:
            page_order = pages_payload.get("pageOrder")
            active_page = pages_payload.get("activePageName")
            if not isinstance(page_order, list) or not page_order:
                errors.append(f"pageOrder deve conter ao menos uma página: {pages_json.relative_to(root)}")
                continue
            if active_page not in page_order:
                errors.append(f"activePageName deve existir em pageOrder: {pages_json.relative_to(root)}")

            for page_name in page_order:
                if not isinstance(page_name, str) or not page_name:
                    errors.append(f"pageOrder contém nome inválido: {pages_json.relative_to(root)}")
                    continue
                page_file = report / "definition" / "pages" / page_name / "page.json"
                if not page_file.is_file():
                    errors.append(
                        f"pageOrder referencia página inexistente: "
                        f"{pages_json.relative_to(root)} -> {page_name}"
                    )
                    continue
                page_payload = get_json(page_file)
                if page_payload is None:
                    continue
                if page_payload.get("name") != page_name:
                    errors.append(f"page.json name diverge da pasta: {page_file.relative_to(root)}")
                for dimension in ("height", "width"):
                    value = page_payload.get(dimension)
                    if not isinstance(value, (int, float)) or value <= 0:
                        errors.append(
                            f"{dimension} deve ser positivo em {page_file.relative_to(root)}"
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
