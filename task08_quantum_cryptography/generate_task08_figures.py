"""Command-line generator for publication-quality Task 8 figures."""

from __future__ import annotations

import argparse
from pathlib import Path

from task08_quantum_cryptography.analysis import build_task08_study
from task08_quantum_cryptography.generate_task08_figure_manifest import (
    generate_task08_figure_manifest,
)
from task08_quantum_cryptography.plotting import generate_task08_figures
from task08_quantum_cryptography.statistical_validation import (
    validate_task08_statistics,
)
from task08_quantum_cryptography.validation import validate_task08


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task08"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate validated 300 DPI and editable vector Task 8 figures."
    )
    parser.add_argument(
        "--figure-directory",
        type=Path,
        default=DEFAULT_FIGURE_DIRECTORY,
        help="Output directory (default: figures/task08)",
    )
    arguments = parser.parse_args(argv)
    study = build_task08_study()
    report = validate_task08(study)
    statistics_report = validate_task08_statistics()
    paths = generate_task08_figures(
        study,
        report,
        statistics_report,
        arguments.figure_directory,
    )
    manifest_path = generate_task08_figure_manifest(arguments.figure_directory)
    print(
        f"Task 8 figures generated {len(paths)} files: "
        "3 figures at 2400x1500 and 1 summary at 3840x2160, "
        "each as PNG/SVG/PDF; "
        f"integrity manifest: {manifest_path.name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
