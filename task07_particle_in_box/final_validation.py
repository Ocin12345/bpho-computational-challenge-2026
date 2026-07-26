"""Artifact-level final acceptance validation for Task 7."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Mapping

from PIL import Image

from task07_particle_in_box.documentation_validation import (
    validate_task07_documentation,
)
from task07_particle_in_box.plotting import FIGURE_FILENAMES, FIGURE_FONT_FAMILY


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_FIGURE_DIMENSIONS = {
    filename: ((3840, 2160) if filename == "task07_summary.png" else (2400, 1500))
    for filename in FIGURE_FILENAMES
    if filename.endswith(".png")
}


@dataclass(frozen=True)
class FinalAcceptanceCheck:
    """One repository-wide Task 7 final acceptance condition."""

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name or not self.detail:
            raise ValueError("final acceptance checks require a name and detail")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")


@dataclass(frozen=True)
class FinalAcceptanceReport:
    """Complete Task 7 artifact-level acceptance result."""

    checks: tuple[FinalAcceptanceCheck, ...]

    def __post_init__(self) -> None:
        checks = tuple(self.checks)
        if not checks or any(
            not isinstance(check, FinalAcceptanceCheck) for check in checks
        ):
            raise TypeError("checks must contain FinalAcceptanceCheck records")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("final acceptance check names must be unique")
        object.__setattr__(self, "checks", checks)

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
    repository_root: Path,
    hashes: Mapping[str, str],
    *,
    prefix: str,
) -> tuple[bool, str]:
    selected = {name: digest for name, digest in hashes.items() if name.startswith(prefix)}
    failures: list[str] = []
    for relative_name, expected in selected.items():
        path = repository_root / relative_name
        if not path.is_file():
            failures.append(f"missing {relative_name}")
        elif _sha256(path) != expected:
            failures.append(f"digest mismatch {relative_name}")
    return (
        bool(selected) and not failures,
        "; ".join(failures) if failures else f"{len(selected)} digests",
    )


def _load_presentation_validator(path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "task07_presentation_validator", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load presentation validator: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _report_manifest_matches(report_directory: Path) -> tuple[bool, str]:
    manifest_path = report_directory / "manifest.json"
    if not manifest_path.is_file():
        return False, "missing reports/task07/manifest.json"
    manifest = _read_json(manifest_path)
    failures: list[str] = []
    files = manifest.get("files", [])
    for item in files:
        path = report_directory / item.get("filename", "")
        if not path.is_file():
            failures.append(f"missing {path.name}")
        elif path.stat().st_size != item.get("bytes"):
            failures.append(f"size mismatch {path.name}")
        elif _sha256(path) != item.get("sha256"):
            failures.append(f"digest mismatch {path.name}")
    pdf = manifest.get("pdf", {})
    accessibility = manifest.get("accessibility", {})
    valid_contract = (
        len(files) == 3
        and pdf.get("pages") == 4
        and "A4" in str(pdf.get("page_size", ""))
        and accessibility.get("semantic_alternative")
        == "particle_in_box_uncertainty_accessible.md"
        and accessibility.get("alternative_required_for_handoff") is True
        and accessibility.get("figure_descriptions_present") is True
    )
    if not valid_contract:
        failures.append("report accessibility or PDF contract mismatch")
    return not failures, "; ".join(failures) if failures else "3 report files"


def _figure_dimensions_pass(figure_directory: Path) -> tuple[bool, str]:
    failures: list[str] = []
    for filename, expected in EXPECTED_FIGURE_DIMENSIONS.items():
        path = figure_directory / filename
        if not path.is_file():
            failures.append(f"missing {filename}")
            continue
        with Image.open(path) as image:
            if image.size != expected:
                failures.append(f"{filename} is {image.size}, expected {expected}")
            dpi = image.info.get("dpi", (0.0, 0.0))
            if min(float(value) for value in dpi) < 299.0:
                failures.append(f"{filename} is below 300 DPI")
    for filename in FIGURE_FILENAMES:
        if filename.endswith(".svg"):
            path = figure_directory / filename
            if not path.is_file() or b"<svg" not in path.read_bytes()[:1000]:
                failures.append(f"invalid SVG {filename}")
                continue
            svg_text = path.read_text(encoding="utf-8")
            font_families = set(
                re.findall(r"font:[^;]+?'([^']+)'", svg_text)
            )
            if font_families != {FIGURE_FONT_FAMILY}:
                failures.append(
                    f"{filename} font families are {sorted(font_families)}"
                )
    return not failures, "; ".join(failures) if failures else "6 PNG/SVG pairs"


def validate_task07_final(
    repository_root: Path = REPOSITORY_ROOT,
) -> FinalAcceptanceReport:
    """Validate every accepted Task 7 artifact package without regeneration."""

    root = Path(repository_root).resolve()
    data_directory = root / "data/task07"
    figure_directory = root / "figures/task07"
    task_directory = root / "task07_particle_in_box"
    report_directory = root / "reports/task07"
    presentation_directory = root / "presentation/task07"

    validation_report = _read_json(data_directory / "validation_report.json")
    scientific_checks = validation_report.get("checks", [])
    manifest = _read_json(data_directory / "manifest.json")
    hashes = manifest.get("sha256", {})
    data_hashes_pass, data_hashes_detail = _manifest_hashes_match(
        root, hashes, prefix="data/task07/"
    )
    figure_hashes_pass, figure_hashes_detail = _manifest_hashes_match(
        root, hashes, prefix="figures/task07/"
    )
    dimensions_pass, dimensions_detail = _figure_dimensions_pass(figure_directory)
    report_pass, report_detail = _report_manifest_matches(report_directory)
    documentation_report = validate_task07_documentation(root)

    source_hashes = manifest.get("official_source_sha256", {})
    provenance_pass = (
        manifest.get("official_requirements")
        == "task07_particle_in_box/OFFICIAL_REQUIREMENTS.md"
        and manifest.get("official_pages") == [48, 49]
        and source_hashes.get("BPhO_ComPhys_Challenge_2026.zip")
        == "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667"
        and source_hashes.get("BPhO CompPhys2026 Quantum.pdf")
        == "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6"
        and manifest.get("figure_font_family") == FIGURE_FONT_FAMILY
    )

    presentation_pass = True
    presentation_detail = "validated"
    try:
        validator = _load_presentation_validator(
            presentation_directory / "validate_task07_presentation.py"
        )
        validator.validate()
    except (AssertionError, FileNotFoundError, ImportError, OSError, ValueError) as error:
        presentation_pass = False
        presentation_detail = str(error)

    required_records = (
        task_directory / "OFFICIAL_REQUIREMENTS.md",
        task_directory / "REPRODUCIBILITY.md",
        task_directory / "FINAL_ACCEPTANCE.md",
        report_directory / "manifest.json",
        presentation_directory / "STAGE10_ACCEPTANCE.md",
    )
    missing_records = [
        path.relative_to(root).as_posix()
        for path in required_records
        if not path.is_file()
    ]

    checks = (
        _check(
            "scientific_report",
            validation_report.get("passed") is True
            and len(scientific_checks) == 37
            and all(check.get("passed") is True for check in scientific_checks),
            f"{sum(check.get('passed') is True for check in scientific_checks)}/37 checks",
        ),
        _check("data_integrity", data_hashes_pass, data_hashes_detail),
        _check(
            "figure_integrity",
            figure_hashes_pass and dimensions_pass,
            f"{figure_hashes_detail}; {dimensions_detail}",
        ),
        _check(
            "source_provenance",
            provenance_pass,
            "official pages 48–49 and two frozen source digests",
        ),
        _check("report_package", report_pass, report_detail),
        _check(
            "documentation",
            documentation_report.passed and len(documentation_report.checks) == 13,
            f"{sum(check.passed for check in documentation_report.checks)}/13 checks",
        ),
        _check("presentation", presentation_pass, presentation_detail),
        _check(
            "acceptance_records",
            not missing_records,
            "5/5 records" if not missing_records else f"missing: {missing_records}",
        ),
    )
    return FinalAcceptanceReport(checks=checks)


__all__ = [
    "FinalAcceptanceCheck",
    "FinalAcceptanceReport",
    "validate_task07_final",
]
