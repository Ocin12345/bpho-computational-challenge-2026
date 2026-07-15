"""Create the 50-walk ensemble figure for BPhO Task 1."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from task01_random_walk.random_walk import (
    RandomWalkEnsembleResult,
    simulate_random_walk_ensemble,
    validate_ensemble,
)


DEFAULT_OUTPUT_STEM = Path("figures/task01/fifty_walks")


def create_ensemble_figure(result: RandomWalkEnsembleResult) -> Figure:
    """Build an equal-scale overlay of all trajectories in an ensemble."""

    report = validate_ensemble(result)
    if not report.passed:
        details = "; ".join(report.failures)
        raise ValueError(f"cannot plot an invalid random-walk ensemble: {details}")

    figure, axis = plt.subplots(figsize=(10.5, 8.0), layout="constrained")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("#f8fafc")

    colour_map = plt.get_cmap("turbo")
    colour_scale = Normalize(vmin=1, vmax=result.n_walks)
    walk_numbers = np.arange(1, result.n_walks + 1)
    colours = colour_map(colour_scale(walk_numbers))

    trajectories = LineCollection(
        result.positions,
        colors=colours,
        linewidths=1.0,
        alpha=0.62,
        capstyle="round",
        joinstyle="round",
        zorder=2,
    )
    axis.add_collection(trajectories)

    axis.scatter(
        result.final_positions[:, 0],
        result.final_positions[:, 1],
        s=35,
        c=colours,
        marker="o",
        edgecolor="white",
        linewidth=0.65,
        alpha=0.95,
        label="Final positions",
        zorder=4,
    )
    axis.scatter(
        0.0,
        0.0,
        s=150,
        marker="o",
        color="#0f172a",
        edgecolor="white",
        linewidth=1.8,
        label="Common start",
        zorder=5,
    )

    minimum = result.positions.min(axis=(0, 1))
    maximum = result.positions.max(axis=(0, 1))
    centre = 0.5 * (minimum + maximum)
    span = max(float(np.max(maximum - minimum)), result.step_size)
    half_width = 0.57 * span
    axis.set_xlim(centre[0] - half_width, centre[0] + half_width)
    axis.set_ylim(centre[1] - half_width, centre[1] + half_width)
    axis.set_aspect("equal", adjustable="box")

    axis.axhline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.axvline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.grid(True, color="#cbd5e1", linewidth=0.65, alpha=0.55, zorder=0)

    axis.set_title(
        f"Ensemble of {result.n_walks} isotropic random walks",
        loc="left",
        fontsize=17,
        fontweight="bold",
        color="#0f172a",
        pad=25,
    )
    axis.text(
        0.0,
        1.015,
        (
            f"Each walk: N = {result.n_steps:,} steps   |   "
            f"s = {result.step_size:g}   |   "
            f"master seed = {result.seed if result.seed is not None else 'random'}"
        ),
        transform=axis.transAxes,
        fontsize=10.5,
        color="#475569",
        va="bottom",
    )
    axis.set_xlabel("x position (distance units)", fontsize=11)
    axis.set_ylabel("y position (distance units)", fontsize=11)
    axis.tick_params(colors="#334155", labelsize=9.5)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#94a3b8")
    axis.spines["bottom"].set_color("#94a3b8")

    legend = axis.legend(
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="#cbd5e1",
        framealpha=0.94,
        fontsize=9.5,
    )
    legend.set_zorder(6)

    colour_bar = figure.colorbar(
        ScalarMappable(norm=colour_scale, cmap=colour_map),
        ax=axis,
        pad=0.025,
        shrink=0.88,
    )
    colour_bar.set_label("Walk number", fontsize=10.5)
    if result.n_walks == 1:
        colour_bar.set_ticks([1])
    else:
        colour_bar.set_ticks(
            np.linspace(1, result.n_walks, min(6, result.n_walks), dtype=int)
        )
    colour_bar.ax.tick_params(labelsize=9)
    colour_bar.outline.set_edgecolor("#94a3b8")

    return figure


def save_ensemble_figure(
    result: RandomWalkEnsembleResult,
    output_stem: str | Path = DEFAULT_OUTPUT_STEM,
    *,
    dpi: int = 240,
) -> tuple[Path, Path]:
    """Save PNG and SVG versions of the ensemble figure."""

    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")

    output_stem = Path(output_stem)
    if output_stem.suffix:
        output_stem = output_stem.with_suffix("")
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_stem.with_suffix(".png")
    svg_path = output_stem.with_suffix(".svg")

    figure = create_ensemble_figure(result)
    try:
        figure.savefig(
            png_path,
            dpi=dpi,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": "BPhO Task 1: 50 random walks"},
        )
        figure.savefig(
            svg_path,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": "BPhO Task 1: 50 random walks"},
        )
    finally:
        plt.close(figure)

    return png_path, svg_path


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for the ensemble figure."""

    parser = argparse.ArgumentParser(
        description="Generate the 50-walk ensemble figure for BPhO Task 1."
    )
    parser.add_argument("--walks", type=int, default=50)
    parser.add_argument("-n", "--steps", type=int, default=1_000)
    parser.add_argument("-s", "--step-size", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_STEM,
        help="output path without an extension",
    )
    parser.add_argument("--dpi", type=int, default=240)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Generate, validate, and save the ensemble figure."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = simulate_random_walk_ensemble(
            args.walks,
            args.steps,
            args.step_size,
            seed=args.seed,
        )
        png_path, svg_path = save_ensemble_figure(
            result,
            args.output,
            dpi=args.dpi,
        )
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    report = validate_ensemble(result)
    total_steps = result.n_walks * result.n_steps
    print(
        f"Validated {result.n_walks} walks x {result.n_steps:,} steps "
        f"= {total_steps:,} fixed-length steps"
    )
    print(f"Maximum step-length error: {report.max_step_length_error:.3e}")
    print(f"Saved {png_path}")
    print(f"Saved {svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
