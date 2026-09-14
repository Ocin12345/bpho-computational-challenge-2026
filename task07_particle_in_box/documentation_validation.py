"""Integrity checks for the complete Task 7 explanatory documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTATION_DIRECTORY = Path("task07_particle_in_box")
DOCUMENTATION_FILENAMES = (
    "README.md",
    "OFFICIAL_REQUIREMENTS.md",
    "MATHEMATICAL_MODEL.md",
    "RESULTS_AND_INTERPRETATION.md",
    "EXTENSION_DECISION.md",
    "REPRODUCIBILITY.md",
    "FINAL_ACCEPTANCE.md",
    "requirements-task07.txt",
)


@dataclass(frozen=True)
class DocumentationCheck:
    """One deterministic Task 7 documentation condition."""

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
    """Ordered Task 7 documentation checks."""

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


def validate_task07_documentation(
    repository_root: Path = REPOSITORY_ROOT,
) -> DocumentationValidationReport:
    """Validate Task 7 files, links, anchors, scope and build instructions."""

    root = Path(repository_root).resolve()
    directory = root / DOCUMENTATION_DIRECTORY
    paths = tuple(directory / name for name in DOCUMENTATION_FILENAMES)
    available = tuple(path for path in paths if path.is_file() and path.stat().st_size > 0)
    checks: list[DocumentationCheck] = [
        DocumentationCheck(
            name="required_files",
            passed=len(available) == len(paths),
            detail=f"{len(available)}/{len(paths)} required Task 7 documents are present and non-empty.",
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
    normalized = re.sub(r"\s+", " ", combined)
    normalized_lower = normalized.lower()
    official = texts.get("OFFICIAL_REQUIREMENTS.md", "")
    results = texts.get("RESULTS_AND_INTERPRETATION.md", "")
    reproduction = texts.get("REPRODUCIBILITY.md", "")
    checks.extend(
        (
            DocumentationCheck(
                name="official_source_traceability",
                passed=_contains_all(
                    official,
                    (
                        "PDF pages 48–49",
                        "32,210,979 bytes",
                        "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667",
                        "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6",
                        "e40a22145b96591aad32221e97035662228dadd09ff9e31562ce6b16da3202ff",
                    ),
                ),
                detail="The official pages, files, sizes and frozen SHA-256 digests are recorded.",
            ),
            DocumentationCheck(
                name="official_outputs_and_model",
                passed=_contains_all(
                    normalized,
                    (
                        "energy plotted against",
                        "probability densities",
                        "E_n=\\frac{n^2\\pi^2\\hbar^2}{2ma^2}",
                        "electron in a box of width",
                    ),
                ),
                detail="The two required plots, exact energy law and disclosed baseline are explicit.",
            ),
            DocumentationCheck(
                name="uncertainty_extension",
                passed=_contains_all(
                    normalized,
                    (
                        "\\langle x\\rangle",
                        "\\langle x^2\\rangle",
                        "\\langle p\\rangle",
                        "\\langle p^2\\rangle",
                        "0.567861808",
                        "\\geq\\frac{\\hbar}{2}",
                    ),
                ),
                detail="All four moments, the exact product, ground-state anchor and bound are documented.",
            ),
            DocumentationCheck(
                name="numerical_validation",
                passed=_contains_all(
                    normalized_lower,
                    (
                        "finite-difference",
                        "tridiagonal",
                        "second-order",
                        "0.999999",
                        "five grid",
                    ),
                ),
                detail="The independent eigensolver, refinement study and overlap evidence are explained.",
            ),
            DocumentationCheck(
                name="report_accessibility",
                passed=_contains_all(
                    reproduction,
                    (
                        "particle_in_box_uncertainty.tex",
                        "particle_in_box_uncertainty.pdf",
                        "particle_in_box_uncertainty_accessible.md",
                        "screen-reader-friendly companion",
                        "not structurally tagged",
                    ),
                ),
                detail="Editable, visual and semantic report forms are inventoried with an honest PDF-tagging disclosure.",
            ),
            DocumentationCheck(
                name="reproduction_commands",
                passed=_contains_all(
                    reproduction,
                    (
                        "generate_task07",
                        "validate_task07_documentation",
                        "validate_task07_final",
                        "generate_task07_report_manifest",
                        "npm run build",
                        "npm run preview",
                        "npm run validate",
                    ),
                ),
                detail="Scientific, report, documentation, final and presentation commands are present.",
            ),
            DocumentationCheck(
                name="evidence_inventory",
                passed=_contains_all(
                    normalized,
                    (
                        "energy_levels.csv",
                        "stationary_states.csv",
                        "numerical_eigenvalues.csv",
                        "numerical_moments.csv",
                        "uncertainty_convergence.csv",
                        "validation_report.json",
                        "probability_densities",
                        "uncertainty_principle",
                        "3840 × 2160",
                    ),
                ),
                detail="Core data, numerical evidence, analytical figures and 4K summary are inventoried.",
            ),
            DocumentationCheck(
                name="scope_boundaries",
                passed=_contains_all(
                    normalized_lower,
                    (
                        "finite barriers",
                        "tunnelling",
                        "time-dependent superpositions",
                        "probability density is time independent",
                    ),
                ),
                detail="Finite-well and time-dependent physics are explicitly outside the required stationary model.",
            ),
            DocumentationCheck(
                name="numerical_anchors",
                passed=_contains_all(
                    results,
                    (
                        "0.376030",
                        "0.567861808",
                        "1.99896",
                        "0.999999",
                    ),
                ),
                detail="The energy, uncertainty, convergence and overlap anchors are stated in the results narrative.",
            ),
            DocumentationCheck(
                name="markdown_fences",
                passed=all(text.count("```") % 2 == 0 for text in texts.values()),
                detail="Every fenced Markdown code block is closed.",
            ),
        )
    )

    requirement_path = directory / "requirements-task07.txt"
    requirement_text = (
        requirement_path.read_text(encoding="utf-8")
        if requirement_path.is_file()
        else ""
    )
    expected_requirements = (
        "numpy==2.0.2",
        "scipy==1.13.1",
        "matplotlib==3.9.4",
        "Pillow==11.3.0",
    )
    checks.append(
        DocumentationCheck(
            name="accepted_python_environment",
            passed=tuple(requirement_text.splitlines()) == expected_requirements,
            detail="NumPy, SciPy, Matplotlib and Pillow are exactly pinned.",
        )
    )
    return DocumentationValidationReport(checks=tuple(checks))


__all__ = [
    "DOCUMENTATION_FILENAMES",
    "DocumentationCheck",
    "DocumentationValidationReport",
    "REPOSITORY_ROOT",
    "validate_task07_documentation",
]
