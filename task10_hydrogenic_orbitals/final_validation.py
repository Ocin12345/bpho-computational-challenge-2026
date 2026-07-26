"""Artifact-level final acceptance validation for Task 10."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Mapping

from task10_hydrogenic_orbitals.documentation_validation import (
    validate_task10_documentation,
)
from task10_hydrogenic_orbitals.generate_task10_motion import (
    build_motion_manifest,
)
from task10_hydrogenic_orbitals.plotting import FIGURE_FONT_FAMILY
from task10_hydrogenic_orbitals.validate_task10_app import validate_app


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_STATE_DIGEST = (
    "d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e"
)


@dataclass(frozen=True)
class FinalAcceptanceCheck:
    """One repository-wide final acceptance condition."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class FinalAcceptanceReport:
    """Complete Task 10 artifact-level acceptance result."""

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
        "task10_presentation_validator", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load presentation validator: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_task10_final(
    repository_root: Path = REPOSITORY_ROOT,
) -> FinalAcceptanceReport:
    """Validate every accepted Task 10 artifact package without regeneration."""

    repository_root = Path(repository_root).resolve()
    data_directory = repository_root / "data/task10"
    figure_directory = repository_root / "figures/task10"
    report_directory = repository_root / "reports/task10"
    task_directory = repository_root / "task10_hydrogenic_orbitals"
    presentation_directory = repository_root / "presentation/task10"

    scientific_report = _read_json(data_directory / "validation_report.json")
    scientific_checks = scientific_report.get("checks", [])
    data_manifest = _read_json(data_directory / "manifest.json")
    data_hashes_pass, data_hashes_detail = _manifest_hashes_match(
        repository_root, data_manifest.get("sha256", {})
    )

    figure_manifest = _read_json(figure_directory / "manifest.json")
    figure_failures: list[str] = []
    figure_total = 0
    for item in figure_manifest.get("figures", []):
        path = repository_root / item["path"]
        if not path.is_file():
            figure_failures.append(f"missing {item['path']}")
            continue
        figure_total += path.stat().st_size
        if _sha256(path) != item["sha256"]:
            figure_failures.append(f"digest mismatch {item['path']}")
        if path.stat().st_size != item["bytes"]:
            figure_failures.append(f"size mismatch {item['path']}")
    figure_gate = figure_manifest.get("science_gate", {})
    figure_pass = (
        len(figure_manifest.get("figures", [])) == 13
        and not figure_failures
        and figure_gate.get("checks_passed") == 22
        and figure_gate.get("checks_total") == 22
        and figure_gate.get("state_digest") == EXPECTED_STATE_DIGEST
        and figure_manifest.get("renderer", {}).get("font_family")
        == FIGURE_FONT_FAMILY
    )

    motion_pass = True
    motion_detail = "current media match the stored manifest"
    try:
        stored_motion = _read_json(figure_directory / "motion_manifest.json")
        observed_motion = build_motion_manifest(figure_directory, report_directory)
        if stored_motion != observed_motion:
            motion_pass = False
            motion_detail = "stored motion manifest differs from current media"
    except (AssertionError, FileNotFoundError, KeyError, OSError, ValueError) as error:
        motion_pass = False
        motion_detail = str(error)

    app_report = validate_app(task_directory / "app")
    documentation_report = validate_task10_documentation(repository_root)

    presentation_pass = True
    presentation_detail = "validated"
    try:
        validator = _load_presentation_validator(
            presentation_directory / "validate_task10_presentation.py"
        )
        validator.validate()
    except (AssertionError, FileNotFoundError, ImportError, OSError, ValueError) as error:
        presentation_pass = False
        presentation_detail = str(error)

    required_acceptance_records = tuple(
        task_directory / f"STAGE{stage}_ACCEPTANCE.md" for stage in range(10)
    ) + (
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
            "scientific_report",
            scientific_report.get("passed") is True
            and scientific_report.get("state_digest") == EXPECTED_STATE_DIGEST
            and len(scientific_checks) == 22
            and all(check.get("passed") is True for check in scientific_checks),
            f"{sum(check.get('passed') is True for check in scientific_checks)}/22 checks",
        ),
        _check(
            "data_integrity",
            data_hashes_pass
            and len(data_manifest.get("sha256", {})) == 6
            and data_manifest.get("validation", {}).get("state_digest")
            == EXPECTED_STATE_DIGEST,
            data_hashes_detail,
        ),
        _check(
            "static_figure_integrity",
            figure_pass,
            (
                f"13 files, {figure_total} bytes; {FIGURE_FONT_FAMILY}"
                if not figure_failures
                else "; ".join(figure_failures)
            ),
        ),
        _check("motion_integrity", motion_pass, motion_detail),
        _check(
            "static_application",
            app_report.passed and len(app_report.checks) == 23,
            f"{sum(check.passed for check in app_report.checks)}/23 checks",
        ),
        _check(
            "documentation",
            documentation_report.passed and len(documentation_report.checks) == 13,
            f"{sum(check.passed for check in documentation_report.checks)}/13 checks",
        ),
        _check("presentation", presentation_pass, presentation_detail),
        _check(
            "acceptance_records",
            not missing_records,
            "12/12 records" if not missing_records else f"missing: {missing_records}",
        ),
    )
    return FinalAcceptanceReport(checks=checks)


__all__ = [
    "EXPECTED_STATE_DIGEST",
    "FinalAcceptanceCheck",
    "FinalAcceptanceReport",
    "_manifest_hashes_match",
    "validate_task10_final",
]
