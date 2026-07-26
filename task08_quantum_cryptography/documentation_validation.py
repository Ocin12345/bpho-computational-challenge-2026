"""Integrity checks for the complete Task 8 explanatory documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTATION_DIRECTORY = Path("task08_quantum_cryptography")
DOCUMENTATION_FILENAMES = (
    "README.md",
    "OFFICIAL_REQUIREMENTS.md",
    "FIGURE_CONTRACT.md",
    "RESULTS_AND_INTERPRETATION.md",
    "REPRODUCIBILITY.md",
    "FINAL_ACCEPTANCE.md",
    "requirements-task08.txt",
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


def validate_task08_documentation(
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
            detail=f"{len(available)}/{len(paths)} required Task 8 documents are present and non-empty.",
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
    checks.extend(
        (
            DocumentationCheck(
                name="official_traceability",
                passed=_contains_all(
                    texts.get("OFFICIAL_REQUIREMENTS.md", ""),
                    (
                        "pages 53--58",
                        "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667",
                        "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6",
                    ),
                ),
                detail="The official pages and frozen archive/PDF digests are recorded.",
            ),
            DocumentationCheck(
                name="official_answer",
                passed=_contains_all(
                    combined,
                    ("37.5%", "75.0%", "37.5 percentage points", "-30^\\circ"),
                ),
                detail="The official angles, both exact probabilities and their signed difference are stated.",
            ),
            DocumentationCheck(
                name="interpretive_derivation",
                passed=_contains_all(
                    texts.get("RESULTS_AND_INTERPRETATION.md", ""),
                    (
                        "\\Delta P=P_{\\mathrm Q}-P_{\\mathrm C}",
                        "-\\frac12\\sin(2\\theta)\\sin(2\\phi)",
                        "Maximum positive contrast",
                        "two-dimensional landscape",
                    ),
                ),
                detail="The results narrative derives and interprets the complete signed-contrast surface.",
            ),
            DocumentationCheck(
                name="scope_boundaries",
                passed=_contains_all(
                    combined.lower(),
                    (
                        "not a complete quantum-key-distribution",
                        "not a cryptographically secure",
                        "not by itself constitute a laboratory bell test",
                    ),
                ),
                detail="Protocol, randomness and physical-inference limitations are explicit.",
            ),
            DocumentationCheck(
                name="reproduction_commands",
                passed=_contains_all(
                    texts.get("REPRODUCIBILITY.md", ""),
                    (
                        "generate_task08",
                        "generate_task08_statistics",
                        "generate_task08_figures",
                        "validate_task08_app",
                        "validate_task08_final",
                        "npm run test:ui",
                        "npm run test:a11y",
                        "npm run evidence",
                    ),
                ),
                detail="Core, statistical, figure, app and browser reproduction commands are present.",
            ),
            DocumentationCheck(
                name="evidence_inventory",
                passed=_contains_all(
                    combined,
                    (
                        "angle_sweep.csv",
                        "mismatch_grid.csv",
                        "validation_report.json",
                        "finite_photon_reference.json",
                        "probability_sweep",
                        "task08_summary",
                        "3840 × 2160",
                    ),
                ),
                detail="The validated data, statistical fixtures, figures and 4K output are inventoried.",
            ),
            DocumentationCheck(
                name="markdown_fences",
                passed=all(text.count("```") % 2 == 0 for text in texts.values()),
                detail="Every fenced Markdown code block is closed.",
            ),
        )
    )

    requirement_path = directory / "requirements-task08.txt"
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
    "validate_task08_documentation",
]
