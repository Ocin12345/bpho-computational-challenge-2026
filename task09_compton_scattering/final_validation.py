"""Artifact-level final acceptance validation for Task 9."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Mapping

from task09_compton_scattering.documentation_validation import (
    validate_task09_documentation,
)
from task09_compton_scattering.generate_task09_media_manifest import MEDIA_FILENAMES
from task09_compton_scattering.plotting import FIGURE_FONT_FAMILY
from task09_compton_scattering.validate_task09_app import validate_app


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class FinalAcceptanceCheck:
    """One repository-wide final acceptance condition."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class FinalAcceptanceReport:
    """Complete Task 9 artifact-level acceptance result."""

    checks: tuple[FinalAcceptanceCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[FinalAcceptanceCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _check(name: str, passed: bool, detail: str) -> FinalAcceptanceCheck:
    return FinalAcceptanceCheck(name=name, passed=bool(passed), detail=detail)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_hashes_match(
    repository_root: Path, hashes: Mapping[str, str]
) -> tuple[bool, str]:
    failures: list[str] = []
    for relative_name, expected in hashes.items():
        path = repository_root / relative_name
        if not path.is_file():
            failures.append(f"missing {relative_name}")
        elif _sha256(path) != expected:
            failures.append(f"digest mismatch {relative_name}")
    return not failures, "; ".join(failures) if failures else f"{len(hashes)} digests"


def _load_presentation_validator(path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "task09_presentation_validator", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load presentation validator: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_task09_final(
    repository_root: Path = REPOSITORY_ROOT,
) -> FinalAcceptanceReport:
    """Validate every accepted Task 9 artifact package without regeneration."""

    repository_root = Path(repository_root).resolve()
    data_directory = repository_root / "data/task09"
    media_directory = repository_root / "figures/task09"
    task_directory = repository_root / "task09_compton_scattering"
    presentation_directory = repository_root / "presentation/task09"

    core_report = _read_json(data_directory / "validation_report.json")
    extension_report = _read_json(
        data_directory / "cross_section_validation_report.json"
    )
    core_checks = core_report.get("checks", [])
    extension_checks = extension_report.get("checks", [])

    core_manifest = _read_json(data_directory / "manifest.json")
    extension_manifest = _read_json(data_directory / "cross_section_manifest.json")
    core_hashes_pass, core_hashes_detail = _manifest_hashes_match(
        repository_root, core_manifest.get("sha256", {})
    )
    extension_hashes_pass, extension_hashes_detail = _manifest_hashes_match(
        repository_root, extension_manifest.get("sha256", {})
    )

    media_manifest = _read_json(media_directory / "manifest.json")
    media_failures: list[str] = []
    media_total = 0
    for item in media_manifest.get("files", []):
        path = media_directory / item["filename"]
        if not path.is_file():
            media_failures.append(f"missing {item['filename']}")
            continue
        media_total += path.stat().st_size
        if _sha256(path) != item["sha256"]:
            media_failures.append(f"digest mismatch {item['filename']}")
    media_pass = (
        len(media_manifest.get("files", [])) == len(MEDIA_FILENAMES)
        and not media_failures
        and media_total == media_manifest.get("total_bytes")
        and media_manifest.get("rendering_contract", {}).get("font_family")
        == FIGURE_FONT_FAMILY
    )

    app_report = validate_app(task_directory / "app")
    documentation_report = validate_task09_documentation(repository_root)

    presentation_pass = True
    presentation_detail = "validated"
    try:
        validator = _load_presentation_validator(
            presentation_directory / "validate_task09_presentation.py"
        )
        validator.validate()
    except (AssertionError, FileNotFoundError, ImportError, OSError, ValueError) as error:
        presentation_pass = False
        presentation_detail = str(error)

    required_acceptance_records = (
        task_directory / "STAGE1_ACCEPTANCE.md",
        task_directory / "STAGE6_ACCEPTANCE.md",
        task_directory / "STAGE7_ACCEPTANCE.md",
        task_directory / "STAGE8_ACCEPTANCE.md",
        task_directory / "STAGE9_ACCEPTANCE.md",
        presentation_directory / "STAGE10_ACCEPTANCE.md",
        task_directory / "FINAL_ACCEPTANCE.md",
    )
    missing_records = [
        path.relative_to(repository_root).as_posix()
        for path in required_acceptance_records
        if not path.is_file()
    ]

    checks = (
        _check(
            "core_scientific_report",
            core_report.get("passed") is True
            and len(core_checks) == 44
            and all(check.get("passed") is True for check in core_checks),
            f"{sum(check.get('passed') is True for check in core_checks)}/44 checks",
        ),
        _check(
            "extension_scientific_report",
            extension_report.get("passed") is True
            and len(extension_checks) == 30
            and all(check.get("passed") is True for check in extension_checks),
            f"{sum(check.get('passed') is True for check in extension_checks)}/30 checks",
        ),
        _check(
            "data_integrity",
            core_hashes_pass and extension_hashes_pass,
            f"core {core_hashes_detail}; extension {extension_hashes_detail}",
        ),
        _check(
            "media_integrity",
            media_pass,
            (
                f"{len(MEDIA_FILENAMES)} files, {media_total} bytes"
                if not media_failures
                else "; ".join(media_failures)
            ),
        ),
        _check(
            "static_application",
            app_report.passed and len(app_report.checks) == 21,
            f"{sum(check.passed for check in app_report.checks)}/21 checks",
        ),
        _check(
            "documentation",
            documentation_report.passed and len(documentation_report.checks) == 11,
            f"{sum(check.passed for check in documentation_report.checks)}/11 checks",
        ),
        _check("presentation", presentation_pass, presentation_detail),
        _check(
            "acceptance_records",
            not missing_records,
            "7/7 records" if not missing_records else f"missing: {missing_records}",
        ),
    )
    return FinalAcceptanceReport(checks=checks)
