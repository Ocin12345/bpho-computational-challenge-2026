"""Command-line generation entry point for Task 10 publication figures."""

from __future__ import annotations

from pathlib import Path

from task10_hydrogenic_orbitals.generate_task10 import REPOSITORY_ROOT
from task10_hydrogenic_orbitals.plotting import (
    generate_publication_figures,
    verify_data_gate,
    write_figure_manifest,
)


def main() -> int:
    data_directory = REPOSITORY_ROOT / "data/task10"
    output_directory = REPOSITORY_ROOT / "figures/task10"
    verify_data_gate(data_directory)
    outputs = generate_publication_figures(output_directory)
    manifest = write_figure_manifest(output_directory, data_directory, outputs)
    print(
        f"Task 10 figures generated {len(outputs)} graphics plus {manifest.name}: "
        "gallery 3840x2400, radial 2400x1500, coloured glass 3000x1875, "
        "comparison 3000x1800, summary 3840x2160."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
