"""Command-line generator for publication-quality Task 9 figures."""

from __future__ import annotations

import argparse
from pathlib import Path

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.cross_section import build_klein_nishina_study
from task09_compton_scattering.cross_section_validation import (
    validate_cross_section_study,
)
from task09_compton_scattering.plotting import generate_task09_figures
from task09_compton_scattering.validation import validate_task09


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task09"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate validated 300 DPI and Times New Roman vector Task 9 figures."
        )
    )
    parser.add_argument(
        "--figure-directory",
        type=Path,
        default=DEFAULT_FIGURE_DIRECTORY,
        help="Output directory (default: figures/task09)",
    )
    arguments = parser.parse_args(argv)
    study = build_task09_study()
    report = validate_task09(study)
    cross_section_study = build_klein_nishina_study(
        study.incident_energy_kev,
        study.theta_deg,
    )
    cross_section_report = validate_cross_section_study(cross_section_study)
    paths = generate_task09_figures(
        study,
        report,
        cross_section_study,
        cross_section_report,
        arguments.figure_directory,
    )
    print(
        f"Task 9 figures generated {len(paths)} files: "
        "3 figures at 2400x1500 and 1 summary at 3840x2160, "
        "each as PNG/SVG/PDF with Times New Roman typography."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
