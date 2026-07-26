"""Publication-quality figures and animation for BPhO Task 2."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    BrownianSimulationResult,
    run_simulation,
)


COLORS = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "yellow": "#E69F00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "dark": "#243447",
    "grey": "#7A8793",
    "light_grey": "#DCE3E8",
}


def apply_figure_style() -> None:
    """Apply a restrained, accessible style across every visual."""

    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "mathtext.fontset": "stix",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.7,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV into string dictionaries."""

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _save_figure(
    figure: Figure,
    output_stem: Path,
    *,
    dpi: int = 300,
) -> tuple[Path, Path]:
    """Save one figure as high-resolution PNG and editable SVG."""

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_stem.with_suffix(".png")
    svg_path = output_stem.with_suffix(".svg")
    figure.savefig(
        png_path,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.08,
    )
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        pad_inches=0.08,
    )
    svg_text = svg_path.read_text(encoding="utf-8")
    normalized_svg = "\n".join(
        line.rstrip() for line in svg_text.splitlines()
    )
    svg_path.write_text(f"{normalized_svg}\n", encoding="utf-8")
    return png_path, svg_path


def create_reference_scene(
    result: BrownianSimulationResult,
) -> Figure:
    """Create the final particle scene with the complete tracer trail."""

    apply_figure_style()
    parameters = result.parameters
    figure, axis = plt.subplots(figsize=(7.2, 6.4))
    final_small = result.small_position_frames_nm[-1]
    axis.scatter(
        final_small[:, 0],
        final_small[:, 1],
        s=7,
        color=COLORS["sky"],
        alpha=0.42,
        linewidths=0,
        label=f"{parameters.n_small:,} small particles",
        rasterized=True,
    )
    axis.plot(
        result.large_positions_nm[:, 0],
        result.large_positions_nm[:, 1],
        color=COLORS["orange"],
        linewidth=2.2,
        alpha=0.95,
        label="large-particle trail",
        zorder=7,
    )
    axis.add_patch(
        Circle(
            result.large_positions_nm[-1],
            parameters.large_radius_nm,
            facecolor=COLORS["yellow"],
            edgecolor=COLORS["dark"],
            linewidth=1.5,
            alpha=0.72,
            zorder=5,
            label="large tracer",
        )
    )
    axis.scatter(
        result.large_positions_nm[0, 0],
        result.large_positions_nm[0, 1],
        marker="x",
        s=70,
        linewidths=2,
        color=COLORS["green"],
        label="start",
        zorder=8,
    )
    axis.set(
        xlim=(0.0, parameters.box_size_nm),
        ylim=(0.0, parameters.box_size_nm),
        xlabel="x position (nm)",
        ylabel="y position (nm)",
        title=(
            "Collision-driven Brownian motion\n"
            f"N={parameters.n_small:,}, t={parameters.max_time_ps:g} ps, "
            f"seed={parameters.seed}"
        ),
    )
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="upper left", fontsize=9)
    figure.text(
        0.98,
        0.015,
        (
            f"final tracer displacement "
            f"{result.final_displacement_nm:.3f} nm"
        ),
        ha="right",
        va="bottom",
        color=COLORS["dark"],
        fontsize=9,
    )
    return figure


def create_baseline_statistics_figure(
    analysis_directory: Path,
) -> Figure:
    """Create MSD-with-fit and endpoint-isotropy panels."""

    apply_figure_style()
    time_rows = _read_csv(analysis_directory / "baseline_msd.csv")
    run_rows = _read_csv(analysis_directory / "run_metrics.csv")
    with (analysis_directory / "analysis_report.json").open(
        encoding="utf-8"
    ) as handle:
        report = json.load(handle)

    baseline_summary = next(
        summary
        for summary in report["summaries"]
        if summary["summary_id"].startswith("baseline_")
        and summary["factor_name"] == "baseline"
    )
    time = np.array([float(row["time_ps"]) for row in time_rows])
    msd = np.array([float(row["msd_nm2"]) for row in time_rows])
    msd_low = np.array(
        [float(row["msd_ci_low_nm2"]) for row in time_rows]
    )
    msd_high = np.array(
        [float(row["msd_ci_high_nm2"]) for row in time_rows]
    )
    baseline_runs = [
        row for row in run_rows if row["configuration_id"] == "baseline"
    ]
    final_x = np.array(
        [float(row["final_displacement_x_nm"]) for row in baseline_runs]
    )
    final_y = np.array(
        [float(row["final_displacement_y_nm"]) for row in baseline_runs]
    )

    figure, (msd_axis, endpoint_axis) = plt.subplots(
        1,
        2,
        figsize=(12.0, 5.0),
        gridspec_kw={"width_ratios": (1.22, 1.0)},
    )
    msd_axis.fill_between(
        time,
        np.maximum(msd_low, 0.0),
        msd_high,
        color=COLORS["sky"],
        alpha=0.25,
        linewidth=0,
        label="95% confidence band",
    )
    msd_axis.plot(
        time,
        msd,
        color=COLORS["blue"],
        linewidth=2.0,
        label="ensemble MSD",
    )
    fit_start = report["design"]["fit_start_ps"]
    fit_end = report["design"]["fit_end_ps"]
    fit_time = np.linspace(fit_start, fit_end, 200)
    fit_line = (
        baseline_summary["msd_fit_intercept_nm2"]
        + baseline_summary["msd_fit_slope_nm2_per_ps"] * fit_time
    )
    msd_axis.plot(
        fit_time,
        fit_line,
        color=COLORS["orange"],
        linewidth=2.2,
        linestyle="--",
        label=(
            f"20–100 ps fit, R²="
            f"{baseline_summary['msd_fit_r_squared']:.3f}"
        ),
    )
    msd_axis.axvspan(
        fit_start,
        fit_end,
        color=COLORS["yellow"],
        alpha=0.08,
        linewidth=0,
    )
    msd_axis.set(
        xlabel="time (ps)",
        ylabel="mean squared displacement (nm²)",
        title="A. Intermediate mean-squared displacement",
        xlim=(0.0, float(np.max(time))),
        ylim=(0.0, None),
    )
    msd_axis.legend(loc="upper left", fontsize=9)
    msd_axis.text(
        0.97,
        0.06,
        (
            f"D = {baseline_summary['diffusion_coefficient_nm2_per_ps']:.3e} "
            r"$\mathrm{nm^2\,ps^{-1}}$" "\n"
            "64 trajectories"
        ),
        transform=msd_axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=COLORS["dark"],
    )

    endpoint_axis.axhline(0.0, color=COLORS["grey"], linewidth=0.8)
    endpoint_axis.axvline(0.0, color=COLORS["grey"], linewidth=0.8)
    endpoint_axis.scatter(
        final_x,
        final_y,
        s=32,
        color=COLORS["purple"],
        alpha=0.72,
        edgecolors="white",
        linewidths=0.45,
        label="final displacement",
    )
    endpoint_axis.errorbar(
        baseline_summary["final_mean_x_nm"],
        baseline_summary["final_mean_y_nm"],
        xerr=[
            [
                baseline_summary["final_mean_x_nm"]
                - baseline_summary["final_mean_x_ci_low_nm"]
            ],
            [
                baseline_summary["final_mean_x_ci_high_nm"]
                - baseline_summary["final_mean_x_nm"]
            ],
        ],
        yerr=[
            [
                baseline_summary["final_mean_y_nm"]
                - baseline_summary["final_mean_y_ci_low_nm"]
            ],
            [
                baseline_summary["final_mean_y_ci_high_nm"]
                - baseline_summary["final_mean_y_nm"]
            ],
        ],
        fmt="o",
        markersize=7,
        color=COLORS["orange"],
        ecolor=COLORS["orange"],
        capsize=4,
        linewidth=1.5,
        label="mean and 95% CI",
        zorder=5,
    )
    limit = 1.08 * max(np.max(np.abs(final_x)), np.max(np.abs(final_y)))
    endpoint_axis.set(
        xlim=(-limit, limit),
        ylim=(-limit, limit),
        xlabel="final x displacement (nm)",
        ylabel="final y displacement (nm)",
        title="B. Isotropic endpoint cloud",
    )
    endpoint_axis.set_aspect("equal", adjustable="box")
    endpoint_axis.legend(loc="upper left", fontsize=9)
    figure.suptitle(
        "Task 2 baseline ensemble: unbiased diffusion",
        fontsize=14,
        fontweight="bold",
    )
    figure.tight_layout()
    return figure


def create_parameter_experiments_figure(
    analysis_directory: Path,
) -> Figure:
    """Create four one-factor diffusion comparison panels."""

    apply_figure_style()
    rows = _read_csv(analysis_directory / "experiment_comparisons.csv")
    settings = (
        ("particle_count", "A. Particle count", "N", 1_000.0),
        ("mass_ratio", "B. Mass ratio", "M / m", 10.0),
        ("restitution", "C. Restitution", "C", 1.0),
        ("knudsen_parameter", "D. Direction persistence", "Kn", 15.0),
    )
    figure, axes = plt.subplots(2, 2, figsize=(11.0, 8.0))

    for axis, (experiment, title, x_label, baseline_value) in zip(
        axes.flat,
        settings,
    ):
        selected = sorted(
            (
                row
                for row in rows
                if row["experiment"] == experiment
            ),
            key=lambda row: float(row["factor_value"]),
        )
        x_values = np.array(
            [float(row["factor_value"]) for row in selected]
        )
        diffusion = np.array(
            [float(row["diffusion_coefficient_nm2_per_ps"]) for row in selected]
        )
        low = np.array(
            [float(row["diffusion_ci_low_nm2_per_ps"]) for row in selected]
        )
        high = np.array(
            [float(row["diffusion_ci_high_nm2_per_ps"]) for row in selected]
        )
        axis.errorbar(
            x_values,
            diffusion,
            yerr=np.vstack((diffusion - low, high - diffusion)),
            color=COLORS["blue"],
            marker="o",
            markersize=6,
            linewidth=1.8,
            capsize=4,
        )
        baseline_index = int(
            np.flatnonzero(np.isclose(x_values, baseline_value))[0]
        )
        axis.scatter(
            x_values[baseline_index],
            diffusion[baseline_index],
            s=70,
            color=COLORS["orange"],
            edgecolors="white",
            linewidths=0.8,
            zorder=5,
        )
        axis.annotate(
            "baseline",
            (x_values[baseline_index], diffusion[baseline_index]),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=COLORS["orange"],
        )
        axis.set(
            xlabel=x_label,
            ylabel=r"effective $D$ (nm$^2$ ps$^{-1}$)",
            title=title,
            ylim=(0.0, None),
        )
        axis.ticklabel_format(
            axis="y",
            style="sci",
            scilimits=(-2, 2),
            useMathText=True,
        )
        axis.text(
            0.98,
            0.94,
            "12 common seeds per level",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=8.5,
            color=COLORS["grey"],
        )

    figure.suptitle(
        "Controlled one-factor experiments",
        fontsize=14,
        fontweight="bold",
    )
    figure.tight_layout()
    return figure


def create_numerical_validation_figure(
    validation_directory: Path,
) -> Figure:
    """Create controlled convergence and full-refinement panels."""

    apply_figure_style()
    controlled_rows = _read_csv(
        validation_directory / "controlled_collision_convergence.csv"
    )
    refinement_rows = _read_csv(
        validation_directory / "reference_time_step_refinement.csv"
    )
    time_step = np.array(
        [float(row["time_step_ps"]) for row in controlled_rows]
    )
    rms_error = np.array(
        [float(row["rms_endpoint_error_nm"]) for row in controlled_rows]
    )
    refinement_factor = np.array(
        [int(row["refinement_factor"]) for row in refinement_rows]
    )
    impulse_count = np.array(
        [int(row["total_impulses"]) for row in refinement_rows]
    )
    maximum_displacement = np.array(
        [float(row["maximum_displacement_nm"]) for row in refinement_rows]
    )

    figure, (convergence_axis, refinement_axis) = plt.subplots(
        1,
        2,
        figsize=(11.5, 4.7),
    )
    convergence_axis.loglog(
        time_step,
        rms_error,
        marker="o",
        markersize=6,
        linewidth=2,
        color=COLORS["blue"],
        label="measured RMS error",
    )
    reference = rms_error[-1] * (time_step / time_step[-1])
    convergence_axis.loglog(
        time_step,
        reference,
        linestyle="--",
        color=COLORS["orange"],
        linewidth=1.8,
        label="first-order reference",
    )
    convergence_axis.invert_xaxis()
    convergence_axis.set(
        xlabel="time step Δt (ps), finer →",
        ylabel="RMS endpoint error (nm)",
        title="A. Controlled collision convergence",
    )
    convergence_axis.legend(fontsize=9)
    convergence_axis.text(
        0.04,
        0.08,
        "minimum observed order = 1.003",
        transform=convergence_axis.transAxes,
        fontsize=9,
        color=COLORS["dark"],
    )

    refinement_axis.plot(
        refinement_factor,
        impulse_count,
        marker="o",
        markersize=6,
        linewidth=2,
        color=COLORS["green"],
        label="applied impulses",
    )
    refinement_axis.set(
        xlabel="time-step refinement factor",
        ylabel="applied impulses",
        title="B. Full reference refinement",
        xticks=refinement_factor,
    )
    distance_axis = refinement_axis.twinx()
    distance_axis.plot(
        refinement_factor,
        maximum_displacement,
        marker="s",
        markersize=5,
        linewidth=1.8,
        color=COLORS["purple"],
        label="maximum step distance",
    )
    distance_axis.axhline(
        0.016,
        color=COLORS["orange"],
        linestyle="--",
        linewidth=1.4,
        label="0.10r limit",
    )
    distance_axis.set_ylabel("maximum one-step distance (nm)")
    handles_a, labels_a = refinement_axis.get_legend_handles_labels()
    handles_b, labels_b = distance_axis.get_legend_handles_labels()
    refinement_axis.legend(
        handles_a + handles_b,
        labels_a + labels_b,
        loc="center right",
        fontsize=8.5,
    )
    figure.suptitle(
        "Numerical validation before statistical analysis",
        fontsize=14,
        fontweight="bold",
    )
    figure.tight_layout()
    return figure


def create_reference_animation(
    result: BrownianSimulationResult,
    output_path: Path,
    *,
    frames_per_second: int = 20,
    dpi: int = 110,
) -> Path:
    """Save a fixed-axis GIF of particles, tracer, and accumulated trail."""

    if frames_per_second < 1:
        raise ValueError("frames_per_second must be positive")
    if dpi < 1:
        raise ValueError("dpi must be positive")
    apply_figure_style()
    parameters = result.parameters
    figure, axis = plt.subplots(figsize=(6.4, 6.4))
    axis.set(
        xlim=(0.0, parameters.box_size_nm),
        ylim=(0.0, parameters.box_size_nm),
        xlabel="x position (nm)",
        ylabel="y position (nm)",
        title="Task 2: collision-driven Brownian motion",
    )
    axis.set_aspect("equal", adjustable="box")
    particles = axis.scatter(
        [],
        [],
        s=5,
        color=COLORS["sky"],
        alpha=0.45,
        linewidths=0,
        animated=True,
    )
    trail, = axis.plot(
        [],
        [],
        color=COLORS["orange"],
        linewidth=2.1,
        zorder=7,
        animated=True,
    )
    tracer = Circle(
        result.large_positions_nm[0],
        parameters.large_radius_nm,
        facecolor=COLORS["yellow"],
        edgecolor=COLORS["dark"],
        linewidth=1.3,
        alpha=0.72,
        animated=True,
        zorder=5,
    )
    axis.add_patch(tracer)
    axis.scatter(
        result.large_positions_nm[0, 0],
        result.large_positions_nm[0, 1],
        marker="x",
        s=55,
        linewidths=1.8,
        color=COLORS["green"],
        zorder=8,
    )
    time_text = axis.text(
        0.98,
        0.97,
        "",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        color=COLORS["dark"],
        animated=True,
    )

    def update(frame_index: int) -> tuple[Any, ...]:
        step_index = int(result.frame_steps[frame_index])
        particles.set_offsets(result.small_position_frames_nm[frame_index])
        trail.set_data(
            result.large_positions_nm[: step_index + 1, 0],
            result.large_positions_nm[: step_index + 1, 1],
        )
        tracer.center = tuple(result.large_positions_nm[step_index])
        time_text.set_text(
            f"t = {result.time_grid.times_ps[step_index]:.1f} ps"
        )
        return particles, trail, tracer, time_text

    animation = FuncAnimation(
        figure,
        update,
        frames=result.n_recorded_frames,
        interval=1_000 / frames_per_second,
        blit=True,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(
        output_path,
        writer=PillowWriter(fps=frames_per_second),
        dpi=dpi,
    )
    plt.close(figure)
    return output_path


def create_all_visuals(
    repository_root: Path | str,
    *,
    max_animation_frames: int = 180,
    dpi: int = 300,
) -> tuple[Path, ...]:
    """Generate every Step 9 visual and a machine-readable manifest."""

    if max_animation_frames < 2:
        raise ValueError("max_animation_frames must be at least two")
    if dpi < 1:
        raise ValueError("dpi must be positive")
    root = Path(repository_root)
    task_directory = root / "task02_brownian_motion"
    analysis_directory = task_directory / "analysis"
    validation_directory = task_directory / "validation"
    output_directory = task_directory / "figures"
    output_directory.mkdir(parents=True, exist_ok=True)

    result = run_simulation(
        BrownianParameters(),
        max_frames=max_animation_frames,
    )
    outputs: list[Path] = []
    figures = (
        (
            "reference_particle_scene",
            create_reference_scene(result),
        ),
        (
            "baseline_statistics",
            create_baseline_statistics_figure(analysis_directory),
        ),
        (
            "parameter_experiments",
            create_parameter_experiments_figure(analysis_directory),
        ),
        (
            "numerical_validation",
            create_numerical_validation_figure(validation_directory),
        ),
    )
    for filename, figure in figures:
        outputs.extend(
            _save_figure(
                figure,
                output_directory / filename,
                dpi=dpi,
            )
        )
        plt.close(figure)

    animation_frames_per_second = 20
    animation_dpi = 110
    animation_path = create_reference_animation(
        result,
        output_directory / "reference_animation.gif",
        frames_per_second=animation_frames_per_second,
        dpi=animation_dpi,
    )
    outputs.append(animation_path)

    manifest = {
        "task": "BPhO 2026 Task 2 Brownian motion",
        "reference_seed": result.parameters.seed,
        "reference_parameters": {
            "n_small": result.parameters.n_small,
            "max_time_ps": result.parameters.max_time_ps,
            "restitution": result.parameters.restitution,
            "time_step_ps": result.time_grid.step_size_ps,
        },
        "generation": {
            "static_png_dpi": dpi,
            "static_vector_format": "SVG",
            "animation_frame_count": result.n_recorded_frames,
            "animation_frames_per_second": animation_frames_per_second,
            "animation_dpi": animation_dpi,
            "statistical_ensembles_rerun": False,
        },
        "visuals": [
            {
                "filename": "reference_particle_scene.png",
                "caption": (
                    "Final molecular scene and complete large-tracer trail "
                    "for the reproducible seed-2026 reference run."
                ),
                "source": "reference simulation",
            },
            {
                "filename": "baseline_statistics.png",
                "caption": (
                    "Baseline MSD with pre-declared fit and final displacement "
                    "cloud with mean confidence intervals."
                ),
                "source": "analysis/baseline_msd.csv and run_metrics.csv",
            },
            {
                "filename": "parameter_experiments.png",
                "caption": (
                    "One-factor effective-diffusion comparisons with fixed "
                    "bootstrap confidence intervals."
                ),
                "source": "analysis/experiment_comparisons.csv",
            },
            {
                "filename": "numerical_validation.png",
                "caption": (
                    "Controlled first-order collision convergence and complete "
                    "reference time-step refinement."
                ),
                "source": "validation CSV evidence",
            },
            {
                "filename": "reference_animation.gif",
                "caption": (
                    "Small-particle motion, collision-driven tracer motion, "
                    "and accumulated tracer trail over 200 ps."
                ),
                "source": "reference simulation",
            },
        ],
    }
    manifest_path = output_directory / "visual_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    outputs.append(manifest_path)
    return tuple(outputs)
