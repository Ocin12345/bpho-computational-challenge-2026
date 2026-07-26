"""Integrity checks for the complete Task 10 explanatory documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTATION_DIRECTORY = Path("task10_hydrogenic_orbitals")
DOCUMENTATION_FILENAMES = (
    "README.md",
    "RESULTS_AND_INTERPRETATION.md",
    "REPRODUCIBILITY.md",
    "requirements-task10.txt",
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


def validate_task10_documentation(
    repository_root: Path = REPOSITORY_ROOT,
) -> DocumentationValidationReport:
    """Validate files, links, physics anchors, scope and reproduction steps."""

    root = Path(repository_root).resolve()
    directory = root / DOCUMENTATION_DIRECTORY
    paths = tuple(directory / name for name in DOCUMENTATION_FILENAMES)
    available = tuple(path for path in paths if path.is_file() and path.stat().st_size > 0)
    checks: list[DocumentationCheck] = [
        DocumentationCheck(
            name="required_files",
            passed=len(available) == len(paths),
            detail=f"{len(available)}/{len(paths)} required Task 10 documents are present and non-empty.",
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
    lower = normalized.lower()
    results = texts.get("RESULTS_AND_INTERPRETATION.md", "")
    reproduction = texts.get("REPRODUCIBILITY.md", "")
    checks.extend(
        (
            DocumentationCheck(
                name="official_gallery",
                passed=_contains_all(
                    normalized,
                    (
                        "1s, 2p, 3d, 4f and 5g",
                        "25 normalized real basis states",
                        "one 1s state",
                        "nine 5g states",
                    ),
                ),
                detail="All five official families and the complete 25-state inventory are explicit.",
            ),
            DocumentationCheck(
                name="equations_and_coordinates",
                passed=_contains_all(
                    normalized,
                    (
                        "\\psi_{nlm}",
                        "\\int |\\psi_{nlm}|^2",
                        "real tesseral",
                        "x=r\\sin\\vartheta\\cos\\varphi",
                        "polar colatitude",
                    ),
                ),
                detail="Normalization, real-harmonic basis and the spherical-coordinate convention are stated.",
            ),
            DocumentationCheck(
                name="numerical_anchors",
                passed=_contains_all(
                    results,
                    (
                        "−13.598233405346",
                        "0.529467506530",
                        "−1.510914822816",
                        "−54.420284669061",
                        "0.318309886184",
                        "0.488602511903",
                    ),
                ),
                detail="Hydrogen, 3d, carbon and analytic density/orientation anchors are present.",
            ),
            DocumentationCheck(
                name="nodes_degeneracy_and_scaling",
                passed=_contains_all(
                    normalized,
                    (
                        "N_r=n-l-1",
                        "2l+1",
                        "Z^2",
                        "1/Z",
                        "independent of \\(l\\) and \\(m\\)",
                    ),
                ),
                detail="Node counts, Coulomb degeneracy and charge scaling are explained.",
            ),
            DocumentationCheck(
                name="display_interpretation",
                passed=_contains_all(
                    lower,
                    (
                        "threshold changes visibility only",
                        "not electron motion",
                        "not a classical electron path",
                        "apparent boundary is a display choice",
                    ),
                ),
                detail="Probability, threshold, isosurface and camera-motion interpretations are explicit.",
            ),
            DocumentationCheck(
                name="scope_boundaries",
                passed=_contains_all(
                    lower,
                    (
                        "one non-relativistic electron",
                        "point-coulomb field",
                        "screening",
                        "spin-orbit coupling",
                        "radiative effects",
                        "external fields",
                    ),
                ),
                detail="The one-electron scope and omitted many-body, relativistic and external-field physics are explicit.",
            ),
            DocumentationCheck(
                name="reproduction_commands",
                passed=_contains_all(
                    reproduction,
                    (
                        "generate_task10",
                        "generate_task10_figures",
                        "generate_task10_motion",
                        "validate_task10_app",
                        "validate_task10_motion",
                        "validate_task10_documentation",
                        "npm run test:ui",
                        "npm run test:a11y",
                        "npm run test:motion",
                    ),
                ),
                detail="Data, figures, motion, app and browser reproduction commands are complete.",
            ),
            DocumentationCheck(
                name="evidence_inventory",
                passed=_contains_all(
                    normalized,
                    (
                        "orbital_state_catalog.csv",
                        "official_gallery.csv",
                        "reference_anchors.json",
                        "required_orbital_gallery",
                        "coloured_glass_density",
                        "task10_summary",
                        "204 real basis states",
                    ),
                ),
                detail="Scientific data and all principal static evidence are inventoried.",
            ),
            DocumentationCheck(
                name="motion_inventory",
                passed=_contains_all(
                    normalized,
                    (
                        "orbital_view_rotation.webp",
                        "orbital_view_rotation_poster.png",
                        "orbital_view_rotation_contact_sheet.png",
                        "3840×2160",
                        "80 frames",
                        "50 ms",
                        "continuous-loop flag",
                    ),
                ),
                detail="The 4K motion, exact timing, fallback and decoded inspection evidence are documented.",
            ),
            DocumentationCheck(
                name="markdown_fences",
                passed=all(text.count("```") % 2 == 0 for text in texts.values()),
                detail="Every fenced Markdown code block is closed.",
            ),
        )
    )

    requirement_path = directory / "requirements-task10.txt"
    requirement_text = requirement_path.read_text(encoding="utf-8") if requirement_path.is_file() else ""
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
    "validate_task10_documentation",
]
