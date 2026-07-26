"""Integrity checks for the complete Task 9 explanatory documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTATION_DIRECTORY = Path("task09_compton_scattering")
DOCUMENTATION_FILENAMES = (
    "README.md",
    "RESULTS_AND_INTERPRETATION.md",
    "REPRODUCIBILITY.md",
    "requirements-task09.txt",
)


@dataclass(frozen=True)
class DocumentationCheck:
    """One deterministic documentation acceptance check."""

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name or not self.detail:
            raise ValueError("documentation checks require a name and detail")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")


@dataclass(frozen=True)
class DocumentationValidationReport:
    """Ordered documentation checks."""

    checks: tuple[DocumentationCheck, ...]

    def __post_init__(self) -> None:
        checks = tuple(self.checks)
        if not checks or any(not isinstance(check, DocumentationCheck) for check in checks):
            raise TypeError("checks must contain DocumentationCheck records")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("documentation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[DocumentationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _local_link_targets(path: Path, text: str) -> tuple[Path, ...]:
    targets: list[Path] = []
    for raw_target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = raw_target.strip().strip("<>").split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        targets.append((path.parent / target).resolve())
    return tuple(targets)


def _contains_all(text: str, values: tuple[str, ...]) -> bool:
    return all(value in text for value in values)


def validate_task09_documentation(
    repository_root: Path = REPOSITORY_ROOT,
) -> DocumentationValidationReport:
    """Validate files, links, scientific anchors and reproduction instructions."""

    root = Path(repository_root).resolve()
    directory = root / DOCUMENTATION_DIRECTORY
    paths = tuple(directory / name for name in DOCUMENTATION_FILENAMES)
    available = tuple(path for path in paths if path.is_file() and path.stat().st_size > 0)
    checks: list[DocumentationCheck] = [
        DocumentationCheck(
            name="required_files",
            passed=len(available) == len(paths),
            detail=f"{len(available)}/{len(paths)} required Task 9 documents are present and non-empty.",
        )
    ]
    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in available
        if path.suffix == ".md"
    }
    link_targets = tuple(
        target
        for path in available
        if path.suffix == ".md"
        for target in _local_link_targets(path, texts[path.name])
    )
    missing_links = tuple(target for target in link_targets if not target.exists())
    checks.append(
        DocumentationCheck(
            name="local_links",
            passed=not missing_links,
            detail=(
                f"{len(link_targets)} local documentation and evidence links resolve."
                if not missing_links
                else f"Missing local targets: {', '.join(str(path) for path in missing_links)}"
            ),
        )
    )

    combined = "\n".join(texts.values())
    normalized_combined = re.sub(r"\s+", " ", combined)
    results = texts.get("RESULTS_AND_INTERPRETATION.md", "")
    reproduction = texts.get("REPRODUCIBILITY.md", "")
    checks.extend(
        (
            DocumentationCheck(
                name="official_requirements",
                passed=_contains_all(
                    normalized_combined,
                    (
                        "50, 100, 200, 500 and 1000 keV",
                        "fractional wavelength shift",
                        "electron recoil speed",
                        "electron recoil angle",
                    ),
                ),
                detail="All five official energies and all three requested quantities are stated.",
            ),
            DocumentationCheck(
                name="equations_and_endpoints",
                passed=_contains_all(
                    normalized_combined,
                    (
                        "\\frac{\\Delta\\lambda}{\\lambda}",
                        "\\operatorname{atan2}",
                        "direction is undefined",
                        "\\phi=0^\\circ",
                    ),
                ),
                detail="The core equations and both endpoint conventions are explicit.",
            ),
            DocumentationCheck(
                name="numerical_anchors",
                passed=_contains_all(
                    results,
                    (
                        "0.391390",
                        "0.434186",
                        "35.7050",
                        "143.7411",
                        "56.2589",
                        "3.913902",
                        "0.920466",
                    ),
                ),
                detail="The 200 keV reference and 1000 keV backscatter anchors are tabulated.",
            ),
            DocumentationCheck(
                name="extension_separation",
                passed=_contains_all(
                    normalized_combined.lower(),
                    (
                        "optional klein–nishina",
                        "separate optional",
                        "does not alter the official kinematic curves",
                    ),
                ),
                detail="The Klein–Nishina layer is consistently labelled as an optional separate extension.",
            ),
            DocumentationCheck(
                name="scope_boundaries",
                passed=_contains_all(
                    normalized_combined.lower(),
                    (
                        "atomic binding",
                        "multiple scattering",
                        "detector response",
                        "not a full monte carlo experiment",
                    ),
                ),
                detail="Material, detector and experimental limitations are explicit.",
            ),
            DocumentationCheck(
                name="reproduction_commands",
                passed=_contains_all(
                    reproduction,
                    (
                        "generate_task09_cross_section",
                        "generate_task09_figures",
                        "task09_compton_scattering.animation",
                        "generate_task09_media_manifest",
                        "validate_task09_app",
                        "npm run test:ui",
                        "npm run test:a11y",
                    ),
                ),
                detail="Data, extension, media, app and browser reproduction commands are present.",
            ),
            DocumentationCheck(
                name="evidence_inventory",
                passed=_contains_all(
                    normalized_combined,
                    (
                        "compton_angle_study.csv",
                        "validation_report.json",
                        "klein_nishina_study.csv",
                        "required_kinematics",
                        "task09_summary",
                        "compton_angle_sweep.gif",
                        "3840 × 2160",
                        "1600 × 900",
                    ),
                ),
                detail="Core data, extension data, 4K artwork and animation are inventoried.",
            ),
            DocumentationCheck(
                name="markdown_fences",
                passed=all(text.count("```") % 2 == 0 for text in texts.values()),
                detail="Every fenced Markdown code block is closed.",
            ),
        )
    )

    requirement_path = directory / "requirements-task09.txt"
    requirement_text = (
        requirement_path.read_text(encoding="utf-8") if requirement_path.is_file() else ""
    )
    expected_requirements = (
        "numpy==2.0.2",
        "matplotlib==3.9.4",
        "Pillow==11.3.0",
    )
    checks.append(
        DocumentationCheck(
            name="accepted_python_environment",
            passed=tuple(requirement_text.splitlines()) == expected_requirements,
            detail="The accepted NumPy, Matplotlib and Pillow versions are exactly pinned.",
        )
    )
    return DocumentationValidationReport(checks=tuple(checks))


__all__ = [
    "DOCUMENTATION_FILENAMES",
    "DocumentationCheck",
    "DocumentationValidationReport",
    "validate_task09_documentation",
]
