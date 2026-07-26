"""Repository-wide final artifact validation for Task 8."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from PIL import Image

from task08_quantum_cryptography.documentation_validation import (
    validate_task08_documentation,
)
from task08_quantum_cryptography.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class FinalAcceptanceCheck:
    """One complete-package Task 8 acceptance condition."""

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name or not self.detail:
            raise ValueError("final acceptance checks require name and detail")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")


@dataclass(frozen=True)
class FinalAcceptanceReport:
    """Ordered final Task 8 package checks."""

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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, detail: str) -> FinalAcceptanceCheck:
    return FinalAcceptanceCheck(name=name, passed=bool(passed), detail=detail)


def _load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _core_data_pass(root: Path) -> tuple[bool, str]:
    manifest = _read_json(root / "data/task08/manifest.json")
    failures: list[str] = []
    for relative_name, expected in manifest.get("sha256", {}).items():
        path = root / relative_name
        if not path.is_file():
            failures.append(f"missing {relative_name}")
        elif _sha256(path) != expected:
            failures.append(f"digest mismatch {relative_name}")
    source_hashes = manifest.get("official_source_sha256", {})
    traceable = (
        manifest.get("official_pages") == [53, 54, 55, 56, 57, 58]
        and source_hashes.get("BPhO_ComPhys_Challenge_2026.zip")
        == "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667"
        and source_hashes.get("BPhO CompPhys2026 Quantum.pdf")
        == "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6"
    )
    if not traceable:
        failures.append("official source traceability mismatch")
    return not failures, "; ".join(failures) if failures else "4 core digests"


def _statistics_pass(root: Path) -> tuple[bool, str]:
    directory = root / "data/task08"
    report = _read_json(directory / "statistical_validation_report.json")
    manifest = _read_json(directory / "statistics_manifest.json")
    failures: list[str] = []
    checks = report.get("checks", [])
    if len(checks) != 24 or not all(check.get("passed") for check in checks):
        failures.append("24-check statistical report did not pass")
    for filename, expected in manifest.get("sha256", {}).items():
        path = directory / filename
        if not path.is_file():
            failures.append(f"missing {filename}")
        elif _sha256(path) != expected:
            failures.append(f"digest mismatch {filename}")
    return not failures, "; ".join(failures) if failures else "24 checks, 2 digests"


def _figure_package_pass(root: Path) -> tuple[bool, str]:
    directory = root / "figures/task08"
    manifest = _read_json(directory / "manifest.json")
    records = manifest.get("files", [])
    failures: list[str] = []
    if manifest.get("figure_font_family") != FIGURE_FONT_FAMILY:
        failures.append("figure font manifest mismatch")
    if manifest.get("schema_version") != "task08-figure-manifest-v2":
        failures.append("figure manifest schema mismatch")
    if len(records) != len(FIGURE_FILENAMES):
        failures.append(
            f"figure manifest does not contain {len(FIGURE_FILENAMES)} files"
        )
    for record in records:
        filename = record.get("filename", "")
        path = directory / filename
        if not path.is_file():
            failures.append(f"missing {filename}")
            continue
        if path.stat().st_size != record.get("bytes") or _sha256(path) != record.get(
            "sha256"
        ):
            failures.append(f"integrity mismatch {filename}")
            continue
        if path.suffix == ".png":
            expected = (3840, 2160) if filename == "task08_summary.png" else (2400, 1500)
            with Image.open(path) as image:
                dpi = image.info.get("dpi", (0.0, 0.0))
                if image.size != expected or min(map(float, dpi)) < 299.0:
                    failures.append(f"dimensions or DPI mismatch {filename}")
        elif path.suffix == ".svg":
            families = set(
                re.findall(
                    r"font:[^;]+?'([^']+)'",
                    path.read_text(encoding="utf-8"),
                )
            )
            if families != {FIGURE_FONT_FAMILY}:
                failures.append(f"font mismatch {filename}: {sorted(families)}")
        else:
            pdf_bytes = path.read_bytes()
            if (
                not pdf_bytes.startswith(b"%PDF-")
                or b"TimesNewRoman" not in pdf_bytes
                or b"/FontFile2" not in pdf_bytes
                or record.get("font_type") != 42
                or record.get("font_embedded") is not True
            ):
                failures.append(f"invalid publication PDF {filename}")
    return (
        not failures,
        "; ".join(failures)
        if failures
        else f"{len(FIGURE_FILENAMES)} figure digests",
    )


def _browser_evidence_pass(root: Path) -> tuple[bool, str]:
    directory = root / "figures/task08/screenshots"
    manifest = _read_json(directory / "manifest.json")
    records = manifest.get("captures", [])
    failures: list[str] = []
    if manifest.get("external_network_requests") != 0:
        failures.append("browser evidence contains external requests")
    if manifest.get("font_family") != FIGURE_FONT_FAMILY:
        failures.append("browser evidence font mismatch")
    if len(records) != 4:
        failures.append("browser evidence does not contain 4 captures")
    for record in records:
        path = directory / record.get("file", "")
        dimensions = record.get("pixel_dimensions", {})
        expected = (dimensions.get("width"), dimensions.get("height"))
        if not path.is_file():
            failures.append(f"missing {path.name}")
        elif _sha256(path) != record.get("sha256"):
            failures.append(f"digest mismatch {path.name}")
        else:
            with Image.open(path) as image:
                if image.size != expected:
                    failures.append(f"dimension mismatch {path.name}")
    return not failures, "; ".join(failures) if failures else "4 browser captures"


def validate_task08_final(
    repository_root: Path = REPOSITORY_ROOT,
) -> FinalAcceptanceReport:
    """Validate the complete Task 8 package without regenerating it."""

    root = Path(repository_root).resolve()
    scientific = _read_json(root / "data/task08/validation_report.json")
    scientific_checks = scientific.get("checks", [])
    core_pass, core_detail = _core_data_pass(root)
    statistics_pass, statistics_detail = _statistics_pass(root)
    figures_pass, figures_detail = _figure_package_pass(root)
    browser_pass, browser_detail = _browser_evidence_pass(root)
    documentation = validate_task08_documentation(root)

    app_pass = True
    app_detail = "validated"
    try:
        app_validator = _load_module(
            root / "task08_quantum_cryptography/validate_task08_app.py",
            "task08_app_validator",
        )
        if app_validator.main() != 0:
            raise AssertionError("app validator returned a non-zero result")
    except (AssertionError, FileNotFoundError, ImportError, OSError, ValueError) as error:
        app_pass = False
        app_detail = str(error)

    presentation_pass = True
    presentation_detail = "validated"
    try:
        presentation_validator = _load_module(
            root / "presentation/task08/validate_task08_presentation.py",
            "task08_presentation_validator",
        )
        presentation_validator.validate()
    except (AssertionError, FileNotFoundError, ImportError, OSError, ValueError) as error:
        presentation_pass = False
        presentation_detail = str(error)

    records = (
        root / "task08_quantum_cryptography/FINAL_ACCEPTANCE.md",
        root / "presentation/task08/STAGE9_ACCEPTANCE.md",
    )
    presentation_pass = presentation_pass and all(path.is_file() for path in records)

    checks = (
        _check(
            "scientific_validation",
            len(scientific_checks) == 42
            and all(check.get("passed") for check in scientific_checks),
            "42 core scientific checks",
        ),
        _check("core_data_integrity", core_pass, core_detail),
        _check("statistical_integrity", statistics_pass, statistics_detail),
        _check("publication_figures", figures_pass, figures_detail),
        _check("browser_evidence", browser_pass, browser_detail),
        _check(
            "documentation",
            documentation.passed and len(documentation.checks) == 10,
            "10 documentation checks",
        ),
        _check("offline_application", app_pass, app_detail),
        _check("presentation_package", presentation_pass, presentation_detail),
    )
    return FinalAcceptanceReport(checks=checks)


__all__ = [
    "FinalAcceptanceCheck",
    "FinalAcceptanceReport",
    "validate_task08_final",
]
