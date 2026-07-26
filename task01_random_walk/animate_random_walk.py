"""Create the presentation animation for BPhO Task 1."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.artist import Artist
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from numpy.typing import NDArray

from task01_random_walk.random_walk import (
    RandomWalkResult,
    simulate_random_walk,
    validate_walk,
)


IntegerArray = NDArray[np.int64]
DEFAULT_OUTPUT_PATH = Path("figures/task01/random_walk_animation.gif")


def _apply_figure_style() -> None:
    """Use the competition-wide serif typography for every Task 1 frame."""

    plt.rcParams.update(
        {"font.family": "Times New Roman", "mathtext.fontset": "stix"}
    )


@dataclass
class AnimationScene:
    """Figure, animation, schedule, and frame renderer for one walk."""

    figure: Figure
    animation: FuncAnimation
    frame_steps: IntegerArray
    render_step: Callable[[int], tuple[Artist, ...]]


def build_frame_schedule(
    n_steps: int,
    *,
    max_moving_frames: int = 220,
    start_hold_frames: int = 10,
    end_hold_frames: int = 35,
) -> IntegerArray:
    """Create a monotonic schedule that includes every important endpoint.

    Long walks are sampled evenly in time so the GIF remains compact. Repeated
    initial and final frames create brief holds for presentation clarity.
    """

    for value, name, minimum in (
        (n_steps, "n_steps", 1),
        (max_moving_frames, "max_moving_frames", 2),
        (start_hold_frames, "start_hold_frames", 0),
        (end_hold_frames, "end_hold_frames", 0),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")

    moving_count = min(n_steps + 1, max_moving_frames)
    moving_steps = np.unique(
        np.rint(np.linspace(0, n_steps, moving_count)).astype(np.int64)
    )
    schedule = np.concatenate(
        (
            np.zeros(start_hold_frames, dtype=np.int64),
            moving_steps,
            np.full(end_hold_frames, n_steps, dtype=np.int64),
        )
    )
    return schedule


def create_random_walk_animation(
    result: RandomWalkResult,
    *,
    max_moving_frames: int = 220,
    start_hold_frames: int = 10,
    end_hold_frames: int = 35,
    fps: int = 25,
) -> AnimationScene:
    """Build a fixed-scale animation of one validated random walk."""

    _apply_figure_style()
    report = validate_walk(result)
    if not report.passed:
        details = "; ".join(report.failures)
        raise ValueError(f"cannot animate an invalid random walk: {details}")
    if isinstance(fps, bool) or not isinstance(fps, int):
        raise TypeError("fps must be an integer")
    if fps <= 0:
        raise ValueError("fps must be greater than zero")

    frame_steps = build_frame_schedule(
        result.n_steps,
        max_moving_frames=max_moving_frames,
        start_hold_frames=start_hold_frames,
        end_hold_frames=end_hold_frames,
    )

    figure, axis = plt.subplots(figsize=(9.0, 7.0), layout="constrained")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("#f8fafc")

    points = result.positions.reshape(-1, 1, 2)
    all_segments = np.concatenate((points[:-1], points[1:]), axis=1)
    colour_scale = Normalize(vmin=0, vmax=result.n_steps)
    path = LineCollection(
        [],
        cmap="viridis",
        norm=colour_scale,
        linewidth=1.9,
        alpha=0.95,
        capstyle="round",
        joinstyle="round",
        zorder=3,
    )
    axis.add_collection(path)

    displacement_line, = axis.plot(
        [],
        [],
        color="#475569",
        linewidth=1.25,
        linestyle=(0, (5, 4)),
        alpha=0.82,
        zorder=2,
    )
    start_marker, = axis.plot(
        [0.0],
        [0.0],
        marker="o",
        markersize=9.5,
        markerfacecolor="#0f766e",
        markeredgecolor="white",
        markeredgewidth=1.3,
        linestyle="none",
        label="Start",
        zorder=5,
    )
    current_marker, = axis.plot(
        [0.0],
        [0.0],
        marker="o",
        markersize=7.5,
        markerfacecolor="#f59e0b",
        markeredgecolor="white",
        markeredgewidth=1.1,
        linestyle="none",
        label="Current position",
        zorder=6,
    )
    final_marker, = axis.plot(
        [],
        [],
        marker="*",
        markersize=14.0,
        markerfacecolor="#dc2626",
        markeredgecolor="white",
        markeredgewidth=1.0,
        linestyle="none",
        label="Finish",
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
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#94a3b8")
    axis.spines["bottom"].set_color("#94a3b8")

    axis.set_title(
        "Two-dimensional isotropic random walk",
        loc="left",
        fontsize=16,
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
        fontsize=10,
        color="#475569",
        va="bottom",
    )
    axis.set_xlabel("x position (distance units)", fontsize=10.5)
    axis.set_ylabel("y position (distance units)", fontsize=10.5)
    axis.tick_params(colors="#334155", labelsize=9)
    axis.legend(
        handles=(start_marker, current_marker, final_marker),
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="#cbd5e1",
        framealpha=0.94,
        fontsize=9,
    )

    status_text = axis.text(
        0.98,
        0.98,
        "",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        color="#334155",
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "#cbd5e1",
            "alpha": 0.94,
        },
        zorder=8,
    )

    colour_bar = figure.colorbar(path, ax=axis, pad=0.025, shrink=0.88)
    colour_bar.set_label("Step number", fontsize=10)
    colour_bar.ax.tick_params(labelsize=8.5)
    colour_bar.outline.set_edgecolor("#94a3b8")

    def render_step(step: int) -> tuple[Artist, ...]:
        """Update all dynamic artists for one step number."""

        step = int(np.clip(step, 0, result.n_steps))
        path.set_segments(all_segments[:step])
        path.set_array(np.arange(1, step + 1, dtype=np.float64))
        x_position, y_position = result.positions[step]
        if 0 < step < result.n_steps:
            current_marker.set_data([x_position], [y_position])
        else:
            current_marker.set_data([], [])
        displacement_line.set_data([0.0, x_position], [0.0, y_position])
        distance = float(np.hypot(x_position, y_position))
        status_text.set_text(
            f"Step {step:,} / {result.n_steps:,}\n"
            f"Position: ({x_position:.2f}, {y_position:.2f})\n"
            f"Displacement: {distance:.2f}"
        )
        if step == result.n_steps:
            final_marker.set_data([x_position], [y_position])
        else:
            final_marker.set_data([], [])
        return path, displacement_line, current_marker, final_marker, status_text

    render_step(0)
    animation = FuncAnimation(
        figure,
        render_step,
        frames=frame_steps,
        interval=1_000 / fps,
        repeat=False,
        blit=True,
        cache_frame_data=False,
    )
    return AnimationScene(
        figure=figure,
        animation=animation,
        frame_steps=frame_steps,
        render_step=render_step,
    )


def save_random_walk_animation(
    result: RandomWalkResult,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    *,
    max_moving_frames: int = 220,
    start_hold_frames: int = 10,
    end_hold_frames: int = 35,
    fps: int = 25,
    dpi: int = 100,
) -> tuple[Path, int]:
    """Save a compact GIF and return its path and frame count."""

    if isinstance(dpi, bool) or not isinstance(dpi, int):
        raise TypeError("dpi must be an integer")
    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")
    output_path = Path(output_path)
    if output_path.suffix.lower() != ".gif":
        output_path = output_path.with_suffix(".gif")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scene = create_random_walk_animation(
        result,
        max_moving_frames=max_moving_frames,
        start_hold_frames=start_hold_frames,
        end_hold_frames=end_hold_frames,
        fps=fps,
    )
    try:
        writer = PillowWriter(
            fps=fps,
            metadata={"title": "BPhO Task 1 random walk animation"},
        )
        scene.animation.save(output_path, writer=writer, dpi=dpi)
    finally:
        plt.close(scene.figure)

    return output_path, len(scene.frame_steps)


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for the animation."""

    parser = argparse.ArgumentParser(
        description="Generate the presentation GIF for BPhO Task 1."
    )
    parser.add_argument("-n", "--steps", type=int, default=1_000)
    parser.add_argument("-s", "--step-size", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--moving-frames", type=int, default=220)
    parser.add_argument("--start-hold", type=int, default=10)
    parser.add_argument("--end-hold", type=int, default=35)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--dpi", type=int, default=100)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Generate, validate, and save the animation."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = simulate_random_walk(
            args.steps,
            args.step_size,
            seed=args.seed,
        )
        output_path, frame_count = save_random_walk_animation(
            result,
            args.output,
            max_moving_frames=args.moving_frames,
            start_hold_frames=args.start_hold,
            end_hold_frames=args.end_hold,
            fps=args.fps,
            dpi=args.dpi,
        )
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    duration = frame_count / args.fps
    print(
        f"Saved {frame_count} frames ({duration:.2f} s at {args.fps} fps) "
        f"to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
