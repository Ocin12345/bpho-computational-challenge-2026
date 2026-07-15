"""Create the presentation figure for one verified Task 1 random walk."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from task01_random_walk.random_walk import (
    RandomWalkResult,
    simulate_random_walk,
    validate_walk,
)


DEFAULT_OUTPUT_STEM = Path("figures/task01/single_walk")


def create_single_walk_figure(result: RandomWalkResult) -> Figure:
    """Build a polished, scientifically labelled figure for one walk.

    The path colour records the progression through the walk. Equal axis scales
    ensure that distances and angles are not visually distorted.
    """

    report = validate_walk(result)
    if not report.passed:
        details = "; ".join(report.failures)
        raise ValueError(f"cannot plot an invalid random walk: {details}")

    figure, axis = plt.subplots(figsize=(10.5, 8.0), layout="constrained")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("#f8fafc")

    points = result.positions.reshape(-1, 1, 2)
    segments = np.concatenate((points[:-1], points[1:]), axis=1)
    colour_scale = Normalize(vmin=0, vmax=result.n_steps)
    path = LineCollection(
        segments,
        cmap="viridis",
        norm=colour_scale,
        linewidth=1.55,
        alpha=0.92,
        capstyle="round",
        joinstyle="round",
        zorder=3,
    )
    path.set_array(np.arange(1, result.n_steps + 1, dtype=np.float64))
    axis.add_collection(path)

    final_x, final_y = result.final_position
    axis.plot(
        (0.0, final_x),
        (0.0, final_y),
        color="#334155",
        linewidth=1.2,
        linestyle=(0, (5, 4)),
        alpha=0.8,
        label=f"Final displacement: {result.final_distance:.2f}",
        zorder=2,
    )
    axis.scatter(
        0.0,
        0.0,
        s=115,
        marker="o",
        color="#0f766e",
        edgecolor="white",
        linewidth=1.5,
        label="Start",
        zorder=5,
    )
    axis.scatter(
        final_x,
        final_y,
        s=235,
        marker="*",
        color="#dc2626",
        edgecolor="white",
        linewidth=1.15,
        label="Finish",
        zorder=6,
    )
    axis.annotate(
        f"Finish  ({final_x:.2f}, {final_y:.2f})",
        xy=(final_x, final_y),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=9.5,
        color="#7f1d1d",
        fontweight="semibold",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": "#fecaca",
            "alpha": 0.94,
        },
        zorder=7,
    )

    minimum = result.positions.min(axis=0)
    maximum = result.positions.max(axis=0)
    centre = 0.5 * (minimum + maximum)
    span = max(float(np.max(maximum - minimum)), result.step_size)
    half_width = 0.60 * span
    axis.set_xlim(centre[0] - half_width, centre[0] + half_width)
    axis.set_ylim(centre[1] - half_width, centre[1] + half_width)
    axis.set_aspect("equal", adjustable="box")

    axis.axhline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.axvline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.grid(True, color="#cbd5e1", linewidth=0.65, alpha=0.55, zorder=0)

    axis.set_title(
        "Two-dimensional isotropic random walk",
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
            f"N = {result.n_steps:,} steps   |   s = {result.step_size:g}   |   "
            f"seed = {result.seed if result.seed is not None else 'random'}"
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
    legend.set_zorder(8)

    colour_bar = figure.colorbar(path, ax=axis, pad=0.025, shrink=0.88)
    colour_bar.set_label("Step number", fontsize=10.5)
    colour_bar.ax.tick_params(labelsize=9)
    colour_bar.outline.set_edgecolor("#94a3b8")

    return figure


def save_single_walk_figure(
    result: RandomWalkResult,
    output_stem: str | Path = DEFAULT_OUTPUT_STEM,
    *,
    dpi: int = 240,
) -> tuple[Path, Path]:
    """Save PNG and SVG versions of the single-walk figure."""

    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")

    output_stem = Path(output_stem)
    if output_stem.suffix:
        output_stem = output_stem.with_suffix("")
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_stem.with_suffix(".png")
    svg_path = output_stem.with_suffix(".svg")

    figure = create_single_walk_figure(result)
    try:
        figure.savefig(
            png_path,
            dpi=dpi,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": "BPhO Task 1: single random walk"},
        )
        figure.savefig(
            svg_path,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": "BPhO Task 1: single random walk"},
        )
    finally:
        plt.close(figure)

    return png_path, svg_path


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for generating the figure."""

    parser = argparse.ArgumentParser(
        description="Generate the polished single-walk figure for BPhO Task 1."
    )
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
    """Generate, validate, and save the single-walk figure."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = simulate_random_walk(
            args.steps,
            args.step_size,
            seed=args.seed,
        )
        png_path, svg_path = save_single_walk_figure(
            result,
            args.output,
            dpi=args.dpi,
        )
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    print(f"Saved {png_path}")
    print(f"Saved {svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
