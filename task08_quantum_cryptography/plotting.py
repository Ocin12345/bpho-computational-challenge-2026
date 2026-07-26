"""Publication-quality deterministic figures for Task 8."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Circle
from matplotlib.ticker import PercentFormatter
from PIL import Image

from task08_quantum_cryptography.analysis import Task08StudyResult
from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.statistical_validation import (
    StatisticalValidationReport,
)
from task08_quantum_cryptography.statistics import (
    FinitePhotonSample,
    simulate_finite_photon_experiment,
)
from task08_quantum_cryptography.validation import (
    Task08ValidationReport,
    task08_study_digest,
)


TEXT = "#202124"
MUTED = "#5F6368"
AXIS = "#69727D"
CLASSICAL = "#D55E00"
QUANTUM = "#0072B2"
DETECTOR_A = QUANTUM
DETECTOR_B = "#CC79A7"
DIFFERENCE = "#4C5AA8"
OFFICIAL = "#E69F00"
FIGURE_FONT_FAMILY = "Times New Roman"

FIGURE_BASE_NAMES = (
    "probability_sweep",
    "mismatch_landscape",
    "finite_photon_sampling",
    "task08_summary",
)
FIGURE_FILENAMES = tuple(
    f"{base_name}.{extension}"
    for base_name in FIGURE_BASE_NAMES
    for extension in ("png", "svg", "pdf")
)

PLOT_STYLE = {
    "font.family": "serif",
    "font.serif": (FIGURE_FONT_FAMILY,),
    "mathtext.fontset": "custom",
    "mathtext.rm": FIGURE_FONT_FAMILY,
    "mathtext.it": f"{FIGURE_FONT_FAMILY}:italic",
    "mathtext.bf": f"{FIGURE_FONT_FAMILY}:bold",
    "mathtext.sf": FIGURE_FONT_FAMILY,
    "font.size": 9.0,
    "axes.titlesize": 10.5,
    "axes.labelsize": 9.0,
    "axes.labelcolor": TEXT,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.8,
    "axes.facecolor": "white",
    "axes.titlecolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "svg.hashsalt": "bpho-task08-v1",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def _require_figure_font() -> None:
    try:
        font_path = Path(
            font_manager.findfont(FIGURE_FONT_FAMILY, fallback_to_default=False)
        )
    except ValueError as error:
        raise RuntimeError(
            f"required figure font is not installed: {FIGURE_FONT_FAMILY}"
        ) from error
    if not font_path.is_file():
        raise RuntimeError(
            f"required figure font is not installed: {FIGURE_FONT_FAMILY}"
        )


def _figure(
    configuration: Task08Configuration,
    *,
    summary: bool = False,
) -> Figure:
    width = configuration.summary_width_px if summary else configuration.figure_width_px
    height = (
        configuration.summary_height_px if summary else configuration.figure_height_px
    )
    return plt.figure(
        figsize=(width / configuration.figure_dpi, height / configuration.figure_dpi),
        dpi=configuration.figure_dpi,
        facecolor="white",
    )


def _require_validated(
    study: Task08StudyResult,
    report: Task08ValidationReport,
    statistics_report: StatisticalValidationReport,
) -> None:
    if not isinstance(study, Task08StudyResult):
        raise TypeError("study must be a Task08StudyResult")
    if not isinstance(report, Task08ValidationReport):
        raise TypeError("report must be a Task08ValidationReport")
    if not isinstance(statistics_report, StatisticalValidationReport):
        raise TypeError("statistics_report must be a StatisticalValidationReport")
    if not report.passed:
        raise RuntimeError("figures require a passing Task 8 scientific report")
    if not statistics_report.passed:
        raise RuntimeError("figures require a passing Task 8 statistical report")
    if report.study_digest != task08_study_digest(study):
        raise ValueError("validation report belongs to a different Task 8 study")


def _format_axes(axis: plt.Axes) -> None:
    axis.grid(False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(AXIS)
    axis.spines["bottom"].set_color(AXIS)
    axis.tick_params(which="both", direction="out")


def _panel_label(
    axis: plt.Axes,
    label: str,
    *,
    x: float = -0.08,
    y: float = 1.04,
) -> None:
    """Place one compact Nature-style lowercase panel label."""

    axis.text(
        x,
        y,
        label,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        color=TEXT,
        fontsize=11.0,
        fontweight="bold",
    )


def _official_index(study: Task08StudyResult) -> int:
    indices = np.flatnonzero(np.isclose(study.sweep_phi_deg, 30.0, atol=1.0e-12))
    if indices.size != 1:
        raise ValueError("official phi angle is missing from the sweep")
    return int(indices[0])


def _make_probability_sweep(
    study: Task08StudyResult,
    configuration: Task08Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        2,
        1,
        left=0.105,
        right=0.965,
        bottom=0.15,
        top=0.82,
        hspace=0.50,
        height_ratios=(1.9, 0.9),
    )
    probability_axis = figure.add_subplot(grid[0, 0])
    difference_axis = figure.add_subplot(grid[1, 0], sharex=probability_axis)
    phi = study.sweep_phi_deg
    official = _official_index(study)

    probability_axis.plot(
        phi,
        study.sweep_classical_mismatch,
        color=CLASSICAL,
        linewidth=2.4,
        label="Classical model",
    )
    probability_axis.plot(
        phi,
        study.sweep_quantum_mismatch,
        color=QUANTUM,
        linewidth=2.4,
        linestyle=(0, (6, 3)),
        label="Quantum model",
    )
    probability_axis.axvline(30.0, color=AXIS, linewidth=1.0, linestyle=(0, (2, 3)))
    probability_axis.scatter(
        [30.0, 30.0],
        [
            study.sweep_classical_mismatch[official],
            study.sweep_quantum_mismatch[official],
        ],
        s=75,
        color=[CLASSICAL, "white"],
        edgecolor=["white", QUANTUM],
        linewidth=2.0,
        zorder=5,
    )
    probability_axis.plot(
        [33.0, 33.0],
        [study.sweep_classical_mismatch[official], study.sweep_quantum_mismatch[official]],
        color=AXIS,
        linewidth=0.9,
        zorder=3,
    )
    probability_axis.plot(
        [31.8, 34.2],
        [study.sweep_classical_mismatch[official]] * 2,
        color=AXIS,
        linewidth=0.9,
        zorder=3,
    )
    probability_axis.plot(
        [31.8, 34.2],
        [study.sweep_quantum_mismatch[official]] * 2,
        color=AXIS,
        linewidth=0.9,
        zorder=3,
    )
    probability_axis.text(
        35.5,
        0.565,
        "Δ = +37.5 pp",
        color=TEXT,
        fontsize=8.0,
        fontweight="bold",
        va="center",
    )
    probability_axis.annotate(
        "75.0%",
        xy=(30.0, study.sweep_quantum_mismatch[official]),
        xytext=(24.0, 0.84),
        ha="right",
        color=TEXT,
        fontsize=7.8,
        arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 0.8},
    )
    probability_axis.annotate(
        "37.5%",
        xy=(30.0, study.sweep_classical_mismatch[official]),
        xytext=(24.0, 0.28),
        ha="right",
        color=TEXT,
        fontsize=7.8,
        arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 0.8},
    )
    probability_axis.set(
        title="Exact mismatch probabilities at θ = −30°",
        ylabel="Mismatch probability",
        xlim=(-90.0, 90.0),
        ylim=(0.0, 1.04),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    probability_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    probability_axis.legend(loc="upper left", ncol=2, fontsize=8.0, handlelength=2.8)
    _format_axes(probability_axis)
    _panel_label(probability_axis, "a")

    difference = study.sweep_signed_difference
    difference_axis.plot(phi, difference, color=DIFFERENCE, linewidth=2.3)
    difference_axis.fill_between(
        phi,
        0.0,
        difference,
        where=difference >= 0.0,
        color=QUANTUM,
        alpha=0.12,
        interpolate=True,
        label="Quantum predicts more",
    )
    difference_axis.fill_between(
        phi,
        0.0,
        difference,
        where=difference < 0.0,
        color=CLASSICAL,
        alpha=0.11,
        interpolate=True,
        label="Quantum predicts less",
    )
    difference_axis.axhline(0.0, color=AXIS, linewidth=0.8)
    difference_axis.axvline(30.0, color=AXIS, linewidth=1.0, linestyle=(0, (2, 3)))
    difference_axis.scatter(
        [30.0],
        [difference[official]],
        s=55,
        color=DIFFERENCE,
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
    )
    difference_axis.set(
        title="Signed model contrast",
        xlabel="Detector B angle, φ (°)",
        ylabel="Quantum − classical",
        ylim=(-0.54, 0.54),
        xticks=(-90, -60, -30, 0, 30, 60, 90),
        yticks=(-0.5, -0.25, 0.0, 0.25, 0.5),
    )
    difference_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    _format_axes(difference_axis)
    _panel_label(difference_axis, "b")

    figure.suptitle(
        "Classical and quantum mismatch as detector B rotates",
        fontsize=14.0,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.89,
        "Detector A fixed at θ = −30°; the official setting is φ = +30° (vertical guide).",
        ha="center",
        color=MUTED,
        fontsize=8.2,
    )
    figure.text(
        0.5,
        0.045,
        "Source data: 361 analytically evaluated settings at 0.5° spacing; both probability curves share the full 0–100% scale.",
        ha="center",
        color=MUTED,
        fontsize=7.4,
    )
    return figure


def _make_mismatch_landscape(
    study: Task08StudyResult,
    configuration: Task08Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        3,
        left=0.085,
        right=0.97,
        bottom=0.20,
        top=0.81,
        wspace=0.25,
    )
    axes = [figure.add_subplot(grid[0, index]) for index in range(3)]
    extent = (-90.0, 90.0, -90.0, 90.0)
    probability_norm = Normalize(vmin=0.0, vmax=1.0)
    difference_norm = TwoSlopeNorm(vmin=-0.5, vcenter=0.0, vmax=0.5)
    values = (
        study.grid_classical_mismatch,
        study.grid_quantum_mismatch,
        study.grid_signed_difference,
    )
    titles = (
        "Classical mismatch",
        "Quantum mismatch",
        "Quantum − classical",
    )
    maps = ("cividis", "cividis", "RdBu_r")
    norms = (probability_norm, probability_norm, difference_norm)
    images = []
    for panel_label, axis, matrix, title, colour_map, norm in zip(
        ("a", "b", "c"),
        axes,
        values,
        titles,
        maps,
        norms,
    ):
        image = axis.imshow(
            matrix,
            origin="lower",
            extent=extent,
            aspect="equal",
            interpolation="nearest",
            cmap=colour_map,
            norm=norm,
        )
        images.append(image)
        axis.plot(
            [-90, 90],
            [-90, 90],
            color="white",
            linewidth=1.0,
            linestyle=(0, (4, 4)),
            alpha=0.82,
        )
        axis.scatter(
            [30.0],
            [-30.0],
            marker="*",
            s=105,
            color=OFFICIAL,
            edgecolor=TEXT,
            linewidth=0.8,
            zorder=4,
        )
        axis.set(
            title=title,
            xlabel="Detector B angle, φ (°)",
            ylabel="Detector A angle, θ (°)",
            xticks=(-90, -45, 0, 45, 90),
            yticks=(-90, -45, 0, 45, 90),
        )
        axis.tick_params(direction="out")
        _panel_label(axis, panel_label, x=-0.13, y=1.04)
    probability_bar = figure.colorbar(
        images[0],
        ax=axes[:2],
        orientation="horizontal",
        fraction=0.055,
        pad=0.13,
        aspect=38,
    )
    probability_bar.set_label("Mismatch probability (shared 0–100% scale)")
    probability_bar.ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    difference_bar = figure.colorbar(
        images[2],
        ax=axes[2],
        orientation="horizontal",
        fraction=0.055,
        pad=0.13,
        aspect=18,
    )
    difference_bar.set_label("Quantum − classical (percentage points)")
    difference_bar.ax.xaxis.set_major_formatter(PercentFormatter(1.0))

    figure.suptitle(
        "Mismatch landscape across both detector settings",
        fontsize=14.0,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.89,
        "Analytical 181 × 181 angle grid; star, official (θ, φ) = (−30°, +30°); dashed line, equal detector settings.",
        ha="center",
        color=MUTED,
        fontsize=8.1,
    )
    figure.text(
        0.5,
        0.04,
        "Quantum mismatch depends on φ − θ (diagonal bands); classical mismatch retains both absolute detector directions.",
        ha="center",
        color=MUTED,
        fontsize=7.4,
    )
    return figure


def _interval_error(sample: FinitePhotonSample) -> tuple[float, float]:
    return (
        sample.observed_probability - sample.wilson_interval.lower,
        sample.wilson_interval.upper - sample.observed_probability,
    )


def _plot_official_sampling(axis: plt.Axes) -> None:
    experiment = simulate_finite_photon_experiment(-30, 30, 1_000, 2_026)
    samples = (experiment.classical, experiment.quantum)
    colours = (CLASSICAL, QUANTUM)
    y_positions = (1.0, 0.0)
    for y, sample, colour in zip(y_positions, samples, colours):
        lower_error, upper_error = _interval_error(sample)
        axis.errorbar(
            sample.observed_probability,
            y,
            xerr=np.array([[lower_error], [upper_error]]),
            fmt="o",
            markersize=9,
            color=colour,
            ecolor=colour,
            elinewidth=7,
            capsize=6,
            alpha=0.90,
            label=f"{sample.model.title()} observed",
        )
        axis.scatter(
            [sample.theoretical_probability],
            [y],
            marker="|",
            s=650,
            linewidth=3.0,
            color=TEXT,
            zorder=5,
        )
        axis.text(
            0.56,
            y + 0.16,
            f"{sample.mismatches:,}/{sample.photon_pairs:,}  ·  "
            f"{100 * sample.observed_probability:.1f}% observed",
            ha="center",
            va="center",
            color=TEXT,
            fontsize=7.8,
            weight="bold",
        )
    axis.set(
        title="One reproducible sample",
        xlabel="Mismatch fraction",
        xlim=(0.25, 0.86),
        ylim=(-0.55, 1.55),
        yticks=y_positions,
        yticklabels=("Classical", "Quantum"),
    )
    axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    _format_axes(axis)
    axis.text(
        0.02,
        0.08,
        "horizontal interval, 95% Wilson\nvertical mark, exact theory",
        transform=axis.transAxes,
        color=MUTED,
        fontsize=7.3,
        va="bottom",
    )


def _make_finite_photon_sampling(
    study: Task08StudyResult,
    configuration: Task08Configuration,
) -> Figure:
    del study
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        2,
        left=0.125,
        right=0.965,
        bottom=0.19,
        top=0.81,
        wspace=0.30,
        width_ratios=(0.86, 1.34),
    )
    sample_axis = figure.add_subplot(grid[0, 0])
    convergence_axis = figure.add_subplot(grid[0, 1])
    _plot_official_sampling(sample_axis)
    _panel_label(sample_axis, "a", x=-0.12, y=1.04)

    pair_counts = np.array(
        [10, 30, 100, 300, 1_000, 3_000, 10_000, 30_000, 100_000],
        dtype=np.int64,
    )
    experiments = [
        simulate_finite_photon_experiment(-30, 30, int(count), 2_026)
        for count in pair_counts
    ]
    for model, colour, marker, offset in (
        ("classical", CLASSICAL, "o", 0.94),
        ("quantum", QUANTUM, "s", 1.06),
    ):
        samples = [getattr(experiment, model) for experiment in experiments]
        observed = np.array([sample.observed_probability for sample in samples])
        errors = np.array([_interval_error(sample) for sample in samples]).T
        theory = samples[0].theoretical_probability
        convergence_axis.errorbar(
            pair_counts * offset,
            observed,
            yerr=errors,
            fmt=marker,
            color=colour,
            ecolor=colour,
            markersize=5.5,
            linewidth=1.6,
            elinewidth=1.2,
            capsize=2.5,
            label=f"{model.title()} sample (95% Wilson interval)",
        )
        convergence_axis.axhline(
            theory,
            color=colour,
            linewidth=1.6,
            linestyle="-" if model == "classical" else (0, (6, 4)),
            alpha=0.82,
            label=f"{model.title()} exact",
        )
    convergence_axis.set_xscale("log")
    convergence_axis.set(
        title="Sampling variation decreases with N",
        xlabel="Detected photon pairs, N (log scale)",
        ylabel="Observed mismatch fraction",
        xlim=(7, 150_000),
        ylim=(0.0, 1.0),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    convergence_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    convergence_axis.legend(
        loc="lower right",
        fontsize=6.8,
        ncol=1,
        handlelength=2.2,
    )
    _format_axes(convergence_axis)
    _panel_label(convergence_axis, "b", x=-0.10, y=1.04)

    figure.suptitle(
        "Finite photon counts fluctuate around exact theory",
        fontsize=14.0,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.89,
        "Official angles (θ, φ) = (−30°, +30°); independent model streams; reproducible seed 2,026.",
        ha="center",
        color=MUTED,
        fontsize=8.1,
    )
    figure.text(
        0.5,
        0.052,
        "The 95% Wilson interval estimates a binomial mismatch fraction from one observed count; exact theory itself is not uncertain.",
        ha="center",
        color=MUTED,
        fontsize=7.2,
    )
    figure.text(
        0.5,
        0.022,
        "Seeded pseudo-random sampling is reproducible for demonstration and is not cryptographically secure.",
        ha="center",
        color=TEXT,
        fontsize=7.0,
        weight="bold",
    )
    return figure


def _draw_detector_geometry(axis: plt.Axes) -> None:
    axis.set_aspect("equal")
    axis.axis("off")
    axis.add_patch(Circle((0, 0), 1.0, facecolor="#F7FAFC", edgecolor="#BDCAD8", linewidth=1.5))
    axis.plot([-1.05, 1.05], [0, 0], color="#A5B3C4", linewidth=1.0, linestyle=(0, (3, 3)))
    for angle_deg, colour, label, linestyle in (
        (-30.0, DETECTOR_A, "Detector A · θ = −30°", "-"),
        (30.0, DETECTOR_B, "Detector B · φ = +30°", (0, (7, 4))),
    ):
        angle = math.radians(angle_deg)
        x, y = math.cos(angle), math.sin(angle)
        axis.plot(
            [-0.92 * x, 0.92 * x],
            [-0.92 * y, 0.92 * y],
            color=colour,
            linewidth=4.0,
            linestyle=linestyle,
            solid_capstyle="round",
            label=label,
        )
    axis.add_patch(
        Arc(
            (0, 0),
            0.85,
            0.85,
            theta1=-30,
            theta2=30,
            color=DIFFERENCE,
            linewidth=2.1,
        )
    )
    axis.text(0.48, 0.02, "60°", color=TEXT, weight="bold", fontsize=11)
    axis.scatter([0], [0], s=70, color="white", edgecolor=TEXT, linewidth=1.2, zorder=5)
    axis.set_xlim(-1.22, 1.22)
    axis.set_ylim(-1.16, 1.16)
    axis.legend(loc="lower center", bbox_to_anchor=(0.5, -0.19), fontsize=8.8)
    axis.set_title("Detector geometry", loc="left", pad=8)


def _make_summary(
    study: Task08StudyResult,
    report: Task08ValidationReport,
    statistics_report: StatisticalValidationReport,
    configuration: Task08Configuration,
) -> Figure:
    figure = _figure(configuration, summary=True)
    grid = figure.add_gridspec(
        2,
        2,
        left=0.055,
        right=0.97,
        bottom=0.14,
        top=0.80,
        hspace=0.52,
        wspace=0.24,
        width_ratios=(0.83, 1.35),
    )
    geometry_axis = figure.add_subplot(grid[0, 0])
    sweep_axis = figure.add_subplot(grid[0, 1])
    difference_axis = figure.add_subplot(grid[1, 0])
    sample_axis = figure.add_subplot(grid[1, 1])
    _draw_detector_geometry(geometry_axis)
    _panel_label(geometry_axis, "a", x=-0.05, y=1.04)

    official = _official_index(study)
    sweep_axis.plot(
        study.sweep_phi_deg,
        study.sweep_classical_mismatch,
        color=CLASSICAL,
        linewidth=2.5,
        label="Classical · solid",
    )
    sweep_axis.plot(
        study.sweep_phi_deg,
        study.sweep_quantum_mismatch,
        color=QUANTUM,
        linewidth=2.5,
        linestyle=(0, (7, 4)),
        label="Quantum · dashed",
    )
    sweep_axis.axvline(30.0, color="#6F7E92", linewidth=1.0, linestyle=(0, (2, 3)))
    sweep_axis.scatter(
        [30, 30],
        [study.sweep_classical_mismatch[official], study.sweep_quantum_mismatch[official]],
        s=65,
        color=[CLASSICAL, QUANTUM],
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
    )
    sweep_axis.set(
        title="Exact mismatch probabilities at θ = −30°",
        xlabel="Detector B angle, φ (°)",
        ylabel="Mismatch probability",
        xlim=(-90, 90),
        ylim=(0, 1.02),
        xticks=(-90, -45, 0, 45, 90),
        yticks=np.linspace(0, 1, 5),
    )
    sweep_axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    sweep_axis.legend(loc="upper left", ncol=2, fontsize=9)
    _format_axes(sweep_axis)
    _panel_label(sweep_axis, "b", x=-0.08, y=1.04)

    image = difference_axis.imshow(
        study.grid_signed_difference,
        origin="lower",
        extent=(-90, 90, -90, 90),
        aspect="equal",
        interpolation="nearest",
        cmap="RdBu_r",
        norm=TwoSlopeNorm(vmin=-0.5, vcenter=0.0, vmax=0.5),
    )
    difference_axis.plot([-90, 90], [-90, 90], color="white", linewidth=1, linestyle=(0, (4, 4)), alpha=0.75)
    difference_axis.scatter(
        [30],
        [-30],
        marker="*",
        s=105,
        color=OFFICIAL,
        edgecolor=TEXT,
        linewidth=0.8,
    )
    difference_axis.set(
        title="Quantum − classical contrast",
        xlabel="Detector B angle, φ (°)",
        ylabel="Detector A angle, θ (°)",
        xticks=(-90, -45, 0, 45, 90),
        yticks=(-90, -45, 0, 45, 90),
    )
    colorbar = figure.colorbar(image, ax=difference_axis, fraction=0.046, pad=0.04)
    colorbar.ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    colorbar.set_label("Difference")
    _panel_label(difference_axis, "c", x=-0.10, y=1.04)

    _plot_official_sampling(sample_axis)
    sample_axis.title.set_text("")
    sample_axis.set_title(
        "Finite 1,000-pair sample · seed 2,026",
        loc="left",
        fontsize=10.5,
        pad=7,
    )
    _panel_label(sample_axis, "d", x=-0.06, y=1.04)

    figure.suptitle(
        "Task 8 · Quantum mismatch calculator",
        fontsize=19,
        fontweight="bold",
        color=TEXT,
        y=0.965,
    )
    figure.text(
        0.5,
        0.89,
        "Exact predictions, full angle dependence and one reproducible finite-photon demonstration",
        ha="center",
        color=MUTED,
        fontsize=10.0,
    )
    figure.text(
        0.055,
        0.045,
        "Official anchor: θ = −30°, φ = +30° · PC = 37.5% · PQ = 75.0%",
        color=MUTED,
        fontsize=8.2,
    )
    figure.text(
        0.97,
        0.045,
        (
            f"Validated: {sum(check.passed for check in report.checks)}/{len(report.checks)} scientific; "
            f"{sum(check.passed for check in statistics_report.checks)}/{len(statistics_report.checks)} statistical checks"
        ),
        ha="right",
        color=TEXT,
        fontsize=8.2,
        fontweight="bold",
    )
    return figure


def _save_figure_pair(
    figure: Figure,
    output_directory: Path,
    base_name: str,
    configuration: Task08Configuration,
) -> tuple[Path, Path, Path]:
    png_path = output_directory / f"{base_name}.png"
    svg_path = output_directory / f"{base_name}.svg"
    pdf_path = output_directory / f"{base_name}.pdf"
    figure.savefig(
        png_path,
        dpi=configuration.figure_dpi,
        metadata={"Software": "BPhO Task 8 deterministic renderer"},
    )
    figure.savefig(
        svg_path,
        metadata={"Date": None, "Creator": "BPhO Task 8 deterministic renderer"},
    )
    figure.savefig(
        pdf_path,
        metadata={
            "CreationDate": None,
            "ModDate": None,
            "Creator": "BPhO Task 8 deterministic renderer",
        },
    )
    plt.close(figure)
    return png_path, svg_path, pdf_path


def _verify_figure_files(
    paths: tuple[Path, ...],
    configuration: Task08Configuration,
) -> None:
    if tuple(path.name for path in paths) != FIGURE_FILENAMES:
        raise ValueError("figure paths do not follow the frozen filename order")
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty figure: {path.name}")
        if path.suffix == ".png":
            with Image.open(path) as image:
                expected = (
                    (configuration.summary_width_px, configuration.summary_height_px)
                    if path.name == "task08_summary.png"
                    else (configuration.figure_width_px, configuration.figure_height_px)
                )
                dpi = image.info.get("dpi", (0.0, 0.0))
                if image.size != expected or image.format != "PNG":
                    raise ValueError(f"invalid PNG dimensions or format: {path.name}")
                if any(abs(float(value) - configuration.figure_dpi) > 0.1 for value in dpi):
                    raise ValueError(f"invalid PNG resolution metadata: {path.name}")
        elif path.suffix == ".svg":
            root = ET.parse(path).getroot()
            if not root.tag.endswith("svg"):
                raise ValueError(f"invalid SVG root: {path.name}")
            svg_text = path.read_text(encoding="utf-8")
            font_families = set(
                re.findall(r"font:[^;]+?'([^']+)'", svg_text)
            )
            if font_families != {FIGURE_FONT_FAMILY}:
                raise ValueError(
                    f"SVG text font mismatch in {path.name}: "
                    f"{sorted(font_families)}"
                )
        else:
            pdf_bytes = path.read_bytes()
            if (
                not pdf_bytes.startswith(b"%PDF-")
                or b"TimesNewRoman" not in pdf_bytes
                or b"/FontFile2" not in pdf_bytes
            ):
                raise ValueError(
                    f"invalid PDF or missing embedded Times New Roman: {path.name}"
                )
    if sum(path.stat().st_size for path in paths) > configuration.figure_size_budget_bytes:
        raise ValueError("figure package exceeds its size budget")


def generate_task08_figures(
    study: Task08StudyResult,
    report: Task08ValidationReport,
    statistics_report: StatisticalValidationReport,
    output_directory: Path,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> tuple[Path, ...]:
    """Generate and verify all four approved PNG/SVG/PDF figure sets."""

    _require_validated(study, report, statistics_report)
    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")
    _require_figure_font()
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    builders = (
        (FIGURE_BASE_NAMES[0], lambda: _make_probability_sweep(study, configuration)),
        (FIGURE_BASE_NAMES[1], lambda: _make_mismatch_landscape(study, configuration)),
        (FIGURE_BASE_NAMES[2], lambda: _make_finite_photon_sampling(study, configuration)),
        (
            FIGURE_BASE_NAMES[3],
            lambda: _make_summary(
                study,
                report,
                statistics_report,
                configuration,
            ),
        ),
    )
    generated: list[Path] = []
    with plt.rc_context(PLOT_STYLE):
        for base_name, builder in builders:
            generated.extend(
                _save_figure_pair(builder(), directory, base_name, configuration)
            )
    paths = tuple(generated)
    _verify_figure_files(paths, configuration)
    return paths


__all__ = [
    "FIGURE_BASE_NAMES",
    "FIGURE_FILENAMES",
    "FIGURE_FONT_FAMILY",
    "generate_task08_figures",
]
