"""Publication-quality figures built only from validated Task 4 results."""

from __future__ import annotations

import os
import struct
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from task04_photoelectric_effect.analysis import Task04StudyResult
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.generate_task04 import (
    DEFAULT_FIGURE_DIRECTORY,
    FIGURE_FILENAMES,
)
from task04_photoelectric_effect.validation import (
    Task04ValidationReport,
    validate_task04,
)


FIGURE_DPI = 300
REGULAR_FIGURE_SIZE_IN = (3200 / FIGURE_DPI, 1800 / FIGURE_DPI)
WIDE_FIGURE_SIZE_IN = (3840 / FIGURE_DPI, 2160 / FIGURE_DPI)
VALIDATION_FIGURE_SIZE_IN = (3840 / FIGURE_DPI, 1920 / FIGURE_DPI)
SUMMARY_FIGURE_SIZE_IN = (3840 / FIGURE_DPI, 2160 / FIGURE_DPI)

GROUP_COLOURS = (
    "#0072B2",
    "#D55E00",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#222222",
)
PASS_COLOUR = "#14804A"
GRID_COLOUR = "#CBD5E1"
TEXT_COLOUR = "#172033"
VISIBLE_COLOUR = "#FDE68A"

PLOT_STYLE: dict[str, object] = {
    "font.family": "DejaVu Sans",
    "font.size": 12.0,
    "axes.titlesize": 15.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 13.0,
    "axes.labelcolor": TEXT_COLOUR,
    "axes.edgecolor": "#64748B",
    "axes.linewidth": 1.0,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID_COLOUR,
    "grid.alpha": 0.6,
    "grid.linewidth": 0.8,
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "legend.frameon": False,
    "legend.fontsize": 10.0,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.edgecolor": "white",
    "svg.hashsalt": "bpho-task04-2026",
}


@dataclass(frozen=True)
class CurveGroup:
    """One visually distinct ideal work-function group."""

    label: str
    symbols: tuple[str, ...]
    source_row: int
    colour: str


CURVE_GROUPS = (
    CurveGroup("Ag / Al / Pb", ("Ag", "Al", "Pb"), 0, GROUP_COLOURS[0]),
    CurveGroup("Au", ("Au",), 2, GROUP_COLOURS[1]),
    CurveGroup("Cu", ("Cu",), 3, GROUP_COLOURS[2]),
    CurveGroup("Sn", ("Sn",), 4, GROUP_COLOURS[3]),
    CurveGroup("W", ("W",), 6, GROUP_COLOURS[4]),
    CurveGroup("Ni", ("Ni",), 7, GROUP_COLOURS[5]),
    CurveGroup("Na", ("Na",), 8, GROUP_COLOURS[6]),
)

EXPECTED_PNG_DIMENSIONS = {
    "stopping_voltage_frequency.png": (3840, 2160),
    "stopping_voltage_wavelength.png": (3840, 2160),
    "copper_threshold_explanation.png": (3200, 1800),
    "photoelectric_validation.png": (3840, 1920),
    "task04_summary.png": (3840, 2160),
}


@dataclass(frozen=True)
class Task04FigureGenerationResult:
    """Passing validation report and ordered paths from one figure transaction."""

    report: Task04ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        """Protect result order and reject failed figure claims."""

        if not isinstance(self.report, Task04ValidationReport):
            raise TypeError("report must be a Task04ValidationReport")
        if not self.report.passed:
            raise ValueError("figure generation requires a passing report")
        try:
            paths = tuple(Path(path) for path in self.output_paths)
        except TypeError as exc:
            raise TypeError("output_paths must be an iterable of paths") from exc
        if tuple(path.name for path in paths) != FIGURE_FILENAMES:
            raise ValueError("output_paths must follow the frozen figure order")
        object.__setattr__(self, "output_paths", paths)


def _require_validated(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> None:
    """Require a passing report that exactly describes this study."""

    if not isinstance(study, Task04StudyResult):
        raise TypeError("study must be a Task04StudyResult")
    if not isinstance(report, Task04ValidationReport):
        raise TypeError("report must be a Task04ValidationReport")
    if not report.passed:
        failed_names = ", ".join(check.name for check in report.failed_checks)
        raise RuntimeError(
            "Task 4 figure generation refused because validation failed: "
            f"{failed_names}"
        )
    expected_report = validate_task04(study)
    if report != expected_report:
        raise ValueError("report does not exactly describe the supplied study")


def _style_axes(axis: Axes) -> None:
    """Apply the shared clean scientific-axis treatment."""

    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3.5, width=0.7)


def _group_work_function(study: Task04StudyResult, group: CurveGroup) -> float:
    return float(study.work_functions_ev[group.source_row])


def _threshold_guide(
    axis: Axes,
    study: Task04StudyResult,
    *,
    frequency: bool,
) -> None:
    """Draw a compact colour-keyed threshold table beside a main graph."""

    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")
    title = (
        "Analytical threshold\n$f_0$ ($10^{15}$ Hz)"
        if frequency
        else "Analytical cut-off\n$\\lambda_0$ (nm)"
    )
    axis.text(
        0.02,
        0.98,
        title,
        ha="left",
        va="top",
        fontsize=13.0,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    for position, group in enumerate(CURVE_GROUPS):
        y = 0.82 - position * 0.112
        row = group.source_row
        threshold = (
            study.cutoff_frequencies_hz[row] / 1.0e15
            if frequency
            else study.cutoff_wavelengths_nm[row]
        )
        axis.plot(
            [0.03, 0.18],
            [y, y],
            color=group.colour,
            linewidth=3.5,
            solid_capstyle="round",
        )
        axis.text(
            0.23,
            y,
            f"{group.label:<12} {threshold:.3f}",
            ha="left",
            va="center",
            fontsize=10.5,
            color=TEXT_COLOUR,
            family="DejaVu Sans Mono",
        )
    axis.text(
        0.02,
        0.025,
        "Ag, Al and Pb coincide\nbecause each is 4.3 eV.",
        ha="left",
        va="bottom",
        fontsize=9.8,
        color="#64748B",
    )


def _plot_frequency_curves(
    axis: Axes,
    study: Task04StudyResult,
    *,
    compact: bool = False,
) -> None:
    """Plot only physically defined frequency-domain curve segments."""

    scaled_frequency = study.frequency_hz / 1.0e15
    for group in CURVE_GROUPS:
        row = group.source_row
        work_function = _group_work_function(study, group)
        axis.plot(
            scaled_frequency,
            study.frequency_physical_voltage_v[row],
            color=group.colour,
            linewidth=1.8 if compact else 3.0,
            label=f"{group.label} ({work_function:.1f} eV)",
        )
        axis.scatter(
            [study.cutoff_frequencies_hz[row] / 1.0e15],
            [0.0],
            s=24 if compact else 64,
            color=group.colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
    axis.set_xlim(0.4, 2.4)
    axis.set_ylim(0.0, 7.9)
    axis.set_xlabel("Incident-light frequency, $f$ ($10^{15}$ Hz)")
    axis.set_ylabel("Stopping-potential magnitude, $V_s$ (V)")
    axis.set_title("Stopping potential versus frequency")
    axis.legend(
        ncol=2,
        loc="upper left",
        fontsize=6.6 if compact else 9.6,
        columnspacing=0.9,
        handlelength=2.0,
    )
    if not compact:
        axis.text(
            0.98,
            0.06,
            "Left of each coloured dot: no photoemission\n"
            "(the physical curve is intentionally absent).",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=10.2,
            color="#475569",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "#CBD5E1",
                "alpha": 0.94,
            },
        )
        axis.text(
            0.98,
            0.93,
            "Common gradient: $h/e = 4.136$ V per $10^{15}$ Hz",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=10.5,
            color="#475569",
        )
    _style_axes(axis)


def _plot_wavelength_curves(
    axis: Axes,
    study: Task04StudyResult,
    *,
    compact: bool = False,
) -> None:
    """Plot only physically defined wavelength-domain curve segments."""

    axis.axvspan(
        380.0,
        700.0,
        color=VISIBLE_COLOUR,
        alpha=0.30,
        linewidth=0.0,
        zorder=0,
    )
    axis.axvline(
        380.0,
        color="#9A7B14",
        linestyle="--",
        linewidth=1.0,
        alpha=0.75,
    )
    for group in CURVE_GROUPS:
        row = group.source_row
        work_function = _group_work_function(study, group)
        axis.plot(
            study.wavelength_nm,
            study.wavelength_physical_voltage_v[row],
            color=group.colour,
            linewidth=1.8 if compact else 3.0,
            label=f"{group.label} ({work_function:.1f} eV)",
        )
        axis.scatter(
            [study.cutoff_wavelengths_nm[row]],
            [0.0],
            s=24 if compact else 64,
            color=group.colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
    axis.set_xlim(150.0, 700.0)
    axis.set_ylim(0.0, 5.95)
    axis.set_xlabel("Incident vacuum wavelength, $\\lambda$ (nm)")
    axis.set_ylabel("Stopping-potential magnitude, $V_s$ (V)")
    axis.set_title("Stopping potential versus vacuum wavelength")
    axis.legend(
        ncol=2,
        loc="upper right",
        fontsize=6.6 if compact else 9.6,
        columnspacing=0.9,
        handlelength=2.0,
    )
    axis.text(
        535.0,
        4.25 if compact else 4.65,
        "Visible band",
        ha="center",
        va="top",
        fontsize=8.4 if compact else 11.0,
        color="#806515",
        fontweight="bold",
    )
    if not compact:
        axis.text(
            0.98,
            0.06,
            "Right of each coloured dot: no photoemission\n"
            "(not a zero stopping potential).",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=10.2,
            color="#475569",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "#CBD5E1",
                "alpha": 0.94,
            },
        )
        axis.annotate(
            "Only Na reaches visible light\n($\\lambda_0 = 516.6$ nm)",
            xy=(study.cutoff_wavelengths_nm[8], 0.0),
            xytext=(565.0, 1.55),
            ha="center",
            va="center",
            fontsize=10.5,
            color=GROUP_COLOURS[6],
            arrowprops={
                "arrowstyle": "->",
                "color": GROUP_COLOURS[6],
                "linewidth": 1.5,
            },
        )
    _style_axes(axis)


def _plot_copper_explanation(
    axis: Axes,
    study: Task04StudyResult,
    *,
    compact: bool = False,
) -> None:
    """Explain the physical threshold using the official copper example."""

    row = 3
    scaled_frequency = study.frequency_hz / 1.0e15
    cutoff = float(study.cutoff_frequencies_hz[row] / 1.0e15)
    mask = study.frequency_emission_mask[row]
    below_x = np.append(scaled_frequency[~mask], cutoff)
    below_y = np.append(study.frequency_linear_voltage_v[row, ~mask], 0.0)
    active_x = np.insert(scaled_frequency[mask], 0, cutoff)
    active_y = np.insert(study.frequency_physical_voltage_v[row, mask], 0, 0.0)

    axis.plot(
        below_x,
        below_y,
        color="#94A3B8",
        linestyle="--",
        linewidth=1.8 if compact else 3.0,
        label="Mathematical extrapolation",
    )
    axis.plot(
        active_x,
        active_y,
        color=GROUP_COLOURS[2],
        linewidth=2.1 if compact else 3.6,
        label="Physical stopping potential",
    )
    axis.axhline(0.0, color="#64748B", linewidth=1.1)
    axis.axvline(
        cutoff,
        color=GROUP_COLOURS[2],
        linestyle=":",
        linewidth=1.8,
    )
    axis.scatter(
        [cutoff],
        [0.0],
        s=32 if compact else 76,
        color=GROUP_COLOURS[2],
        edgecolor="white",
        linewidth=0.9,
        zorder=4,
    )
    axis.set_xlim(0.4, 1.8 if compact else 2.0)
    axis.set_ylim(-3.2, 3.2 if compact else 3.8)
    axis.set_xlabel("Incident-light frequency, $f$ ($10^{15}$ Hz)")
    axis.set_ylabel("Signed model voltage (V)")
    axis.set_title("Copper threshold: $W = 4.7$ eV")
    axis.legend(loc="upper left", fontsize=6.8 if compact else 10.0)
    if not compact:
        axis.text(
            0.05,
            0.08,
            "mathematical extrapolation: no photoemission",
            transform=axis.transAxes,
            ha="left",
            va="bottom",
            fontsize=10.2,
            color="#64748B",
            fontstyle="italic",
        )
        axis.annotate(
            "$f_0 = 1.136 \\times 10^{15}$ Hz\n$V_s = 0$ at threshold",
            xy=(cutoff, 0.0),
            xytext=(1.43, -1.45),
            ha="center",
            va="center",
            fontsize=10.5,
            color=TEXT_COLOUR,
            arrowprops={
                "arrowstyle": "->",
                "color": GROUP_COLOURS[2],
                "linewidth": 1.5,
            },
        )
        axis.text(
            0.97,
            0.08,
            "$eV_s = hf - W$",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=15.5,
            color=TEXT_COLOUR,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#F8FAFC",
                "edgecolor": "#CBD5E1",
            },
        )
    _style_axes(axis)


def _validation_ratios(
    report: Task04ValidationReport,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Extract dimensionless error-to-tolerance ratios from the report."""

    checks = {check.name: check for check in report.checks}
    general_specification = (
        ("Energy $f$", "frequency_energy_identity"),
        ("Energy $\\lambda$", "wavelength_energy_identity"),
        ("Gradient", "common_frequency_gradient"),
        ("Threshold $f$", "threshold_frequency_voltage"),
        ("Threshold $\\lambda$", "threshold_wavelength_voltage"),
        ("$f \\leftrightarrow \\lambda$", "frequency_wavelength_consistency"),
        ("Anchor $f$", "frequency_anchor"),
        ("Anchor $\\lambda$", "wavelength_anchor"),
    )
    labels = [label for label, _ in general_specification]
    general = np.array(
        [
            checks[name].observed / checks[name].tolerance
            for _, name in general_specification
        ],
        dtype=np.float64,
    )
    symbols = np.array(["Ag", "Al", "Au", "Cu", "Sn", "Pb", "W", "Ni", "Na"])
    frequency_errors = []
    wavelength_errors = []
    for symbol in symbols:
        frequency_check = checks[f"cutoff_frequency_{symbol.lower()}"]
        wavelength_check = checks[f"cutoff_wavelength_{symbol.lower()}"]
        frequency_errors.append(
            abs(frequency_check.observed - frequency_check.expected)
            / abs(frequency_check.expected)
            / frequency_check.tolerance
        )
        wavelength_errors.append(
            abs(wavelength_check.observed - wavelength_check.expected)
            / abs(wavelength_check.expected)
            / wavelength_check.tolerance
        )
    return (
        labels,
        general,
        np.asarray(frequency_errors),
        np.asarray(wavelength_errors),
    )


def _build_frequency_figure(study: Task04StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=WIDE_FIGURE_SIZE_IN,
            gridspec_kw={"width_ratios": (4.25, 1.45)},
        )
        _plot_frequency_curves(axes[0], study)
        _threshold_guide(axes[1], study, frequency=True)
        figure.suptitle(
            "Photoelectric stopping potential for nine official metals",
            fontsize=20.0,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.985,
            bottom=0.13,
            top=0.875,
            wspace=0.10,
        )
        return figure


def _build_wavelength_figure(study: Task04StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=WIDE_FIGURE_SIZE_IN,
            gridspec_kw={"width_ratios": (4.25, 1.45)},
        )
        _plot_wavelength_curves(axes[0], study)
        _threshold_guide(axes[1], study, frequency=False)
        figure.suptitle(
            "Vacuum wavelength reveals the photoemission cut-off",
            fontsize=20.0,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.985,
            bottom=0.13,
            top=0.875,
            wspace=0.10,
        )
        return figure


def _build_copper_figure(study: Task04StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_FIGURE_SIZE_IN)
        _plot_copper_explanation(axis, study)
        figure.text(
            0.12,
            0.955,
            "A negative line is algebraic continuation, not a physical "
            "stopping potential.",
            ha="left",
            va="top",
            fontsize=11.2,
            color="#475569",
        )
        figure.subplots_adjust(left=0.12, right=0.97, bottom=0.14, top=0.86)
        return figure


def _build_validation_figure(report: Task04ValidationReport) -> Figure:
    labels, general, frequency_errors, wavelength_errors = _validation_ratios(
        report
    )
    display_floor = 1.0e-6
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=VALIDATION_FIGURE_SIZE_IN,
            gridspec_kw={"width_ratios": (1.35, 1.0)},
        )
        axes[0].bar(
            np.arange(len(labels)),
            np.maximum(general, display_floor),
            color="#0072B2",
            alpha=0.88,
            width=0.72,
        )
        axes[0].axhline(
            1.0,
            color="#B91C1C",
            linestyle="--",
            linewidth=2.0,
            label="Declared tolerance",
        )
        axes[0].set_yscale("log")
        axes[0].set_ylim(display_floor / 2.0, 2.0)
        axes[0].set_xticks(np.arange(len(labels)), labels, rotation=25, ha="right")
        axes[0].set_ylabel("Observed error / declared tolerance")
        axes[0].set_title("Whole-study numerical checks")
        axes[0].legend(loc="upper left")
        _style_axes(axes[0])

        positions = np.arange(len(frequency_errors))
        axes[1].semilogy(
            positions,
            np.maximum(frequency_errors, display_floor),
            marker="o",
            linewidth=2.3,
            color="#E69F00",
            label="Frequency cut-off",
        )
        axes[1].semilogy(
            positions,
            np.maximum(wavelength_errors, display_floor),
            marker="s",
            linewidth=2.3,
            color="#009E73",
            label="Wavelength cut-off",
        )
        axes[1].axhline(
            1.0,
            color="#B91C1C",
            linestyle="--",
            linewidth=2.0,
            label="Declared tolerance",
        )
        axes[1].set_ylim(display_floor / 2.0, 2.0)
        axes[1].set_xticks(
            positions,
            ["Ag", "Al", "Au", "Cu", "Sn", "Pb", "W", "Ni", "Na"],
        )
        axes[1].set_xlabel("Metal")
        axes[1].set_ylabel("Relative error / declared tolerance")
        axes[1].set_title("Independent analytical cut-offs")
        axes[1].legend(loc="upper left", fontsize=9.5)
        _style_axes(axes[1])

        figure.suptitle(
            "Independent validation — every error remains below tolerance",
            fontsize=19.5,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.text(
            0.50,
            0.895,
            f"PASS  •  {len(report.checks)}/{len(report.checks)} checks  •  "
            "zero errors shown at display floor",
            ha="center",
            va="center",
            fontsize=11.5,
            fontweight="bold",
            color=PASS_COLOUR,
        )
        figure.subplots_adjust(
            left=0.085,
            right=0.98,
            bottom=0.22,
            top=0.82,
            wspace=0.28,
        )
        return figure


def _build_summary_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(2, 2, figsize=SUMMARY_FIGURE_SIZE_IN)
        _plot_frequency_curves(axes[0, 0], study, compact=True)
        _plot_wavelength_curves(axes[0, 1], study, compact=True)
        _plot_copper_explanation(axes[1, 0], study, compact=True)

        key_axis = axes[1, 1]
        key_axis.axis("off")
        key_axis.set_xlim(0.0, 1.0)
        key_axis.set_ylim(0.0, 1.0)
        key_axis.text(
            0.02,
            0.95,
            "What the simulation shows",
            ha="left",
            va="top",
            fontsize=13.0,
            fontweight="bold",
            color=TEXT_COLOUR,
        )
        key_axis.text(
            0.02,
            0.80,
            "$eV_s = hf-W$",
            ha="left",
            va="top",
            fontsize=18.0,
            color=TEXT_COLOUR,
        )
        key_axis.text(
            0.02,
            0.64,
            "• All frequency curves share gradient $h/e$.\n"
            "• Higher $W$ raises $f_0$ and shortens $\\lambda_0$.\n"
            "• Ag, Al and Pb coincide at 4.3 eV.\n"
            "• Only Na reaches visible light ($\\lambda_0=516.6$ nm).\n"
            "• Below threshold there are no photoelectrons.",
            ha="left",
            va="top",
            fontsize=10.0,
            linespacing=1.5,
            color="#334155",
        )
        key_axis.text(
            0.02,
            0.08,
            f"PASS  •  {len(report.checks)}/{len(report.checks)} independent checks",
            ha="left",
            va="bottom",
            fontsize=11.0,
            fontweight="bold",
            color=PASS_COLOUR,
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "#E8F5EE",
                "edgecolor": "#8ED1AC",
                "linewidth": 0.8,
            },
        )

        figure.suptitle(
            "Task 4 — Photoelectric stopping potential",
            fontsize=20.0,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.975,
        )
        figure.text(
            0.5,
            0.93,
            "Nine official metals • two equivalent coordinates • physical "
            "thresholds shown explicitly",
            ha="center",
            va="center",
            fontsize=10.5,
            color="#475569",
        )
        figure.subplots_adjust(
            left=0.07,
            right=0.98,
            bottom=0.07,
            top=0.875,
            wspace=0.23,
            hspace=0.38,
        )
        return figure


def create_stopping_voltage_frequency_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return the validated mandatory frequency comparison."""

    _require_validated(study, report)
    return _build_frequency_figure(study)


def create_stopping_voltage_wavelength_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return the validated supporting wavelength comparison."""

    _require_validated(study, report)
    return _build_wavelength_figure(study)


def create_copper_threshold_explanation_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return the validated physical-versus-extrapolated copper figure."""

    _require_validated(study, report)
    return _build_copper_figure(study)


def create_photoelectric_validation_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return the quantitative error-to-tolerance validation figure."""

    _require_validated(study, report)
    return _build_validation_figure(report)


def create_task04_summary_figure(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return the validated presentation-ready 16:9 summary figure."""

    _require_validated(study, report)
    return _build_summary_figure(study, report)


def _save_figure(figure: Figure, path: Path) -> None:
    """Serialize one deterministic figure and always release it."""

    file_format = path.suffix.removeprefix(".").lower()
    if file_format == "png":
        metadata = {"Software": "BPhO Computational Challenge 2026"}
    elif file_format == "svg":
        metadata = {
            "Creator": "BPhO Computational Challenge 2026",
            "Date": None,
        }
    else:
        raise ValueError(f"unsupported figure format: {file_format}")
    try:
        with matplotlib.rc_context(PLOT_STYLE):
            figure.savefig(
                path,
                format=file_format,
                dpi=FIGURE_DPI,
                metadata=metadata,
                facecolor="white",
                edgecolor="white",
            )
        if file_format == "svg":
            original = path.read_text(encoding="utf-8")
            normalized = "\n".join(
                line.rstrip() for line in original.splitlines()
            ) + "\n"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(normalized)
    finally:
        plt.close(figure)


def _verify_png(path: Path, expected_dimensions: tuple[int, int]) -> None:
    """Verify PNG signature and exact IHDR dimensions without Pillow."""

    content = path.read_bytes()
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"invalid PNG signature: {path.name}")
    dimensions = struct.unpack(">II", content[16:24])
    if dimensions != expected_dimensions:
        raise ValueError(
            f"invalid PNG dimensions for {path.name}: {dimensions}"
        )


def _verify_svg(path: Path) -> None:
    """Verify SVG structure, deterministic metadata, and whitespace."""

    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        raise ValueError(f"SVG lacks final LF: {path.name}")
    if any(line != line.rstrip() for line in text.splitlines()):
        raise ValueError(f"SVG contains trailing whitespace: {path.name}")
    if "<dc:date>" in text:
        raise ValueError(f"SVG contains nondeterministic date metadata: {path.name}")
    root = ET.fromstring(text)
    if not root.tag.endswith("svg") or "viewBox" not in root.attrib:
        raise ValueError(f"invalid SVG root: {path.name}")


def _verify_prepared_figures(
    prepared: tuple[tuple[str, Path], ...],
) -> None:
    """Parse every temporary figure before any destination changes."""

    if tuple(filename for filename, _ in prepared) != FIGURE_FILENAMES:
        raise ValueError("prepared figure names do not match the frozen order")
    for filename, path in prepared:
        if path.stat().st_size == 0:
            raise ValueError(f"empty figure output: {filename}")
        if filename.endswith(".png"):
            _verify_png(path, EXPECTED_PNG_DIMENSIONS[filename])
        else:
            _verify_svg(path)
    total_bytes = sum(path.stat().st_size for _, path in prepared)
    if total_bytes > DEFAULT_CONFIGURATION.figure_size_budget_bytes:
        raise ValueError(
            "prepared figures exceed the configured size budget: "
            f"{total_bytes} bytes"
        )


def _replace_figure_path(source: Path, destination: Path) -> None:
    """Atomically replace one figure path; isolated for failure tests."""

    os.replace(source, destination)


def _unused_figure_sibling(path: Path, *, suffix: str) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=suffix,
        dir=path.parent,
    )
    os.close(descriptor)
    sibling = Path(name)
    sibling.unlink()
    return sibling


def _restore_figure_transaction(
    installed: list[Path],
    backups: list[tuple[Path, Path]],
) -> None:
    rollback_errors: list[OSError] = []
    for destination in reversed(installed):
        try:
            if destination.exists():
                destination.unlink()
        except OSError as exc:
            rollback_errors.append(exc)
    for destination, backup in reversed(backups):
        try:
            if backup.exists():
                _replace_figure_path(backup, destination)
        except OSError as exc:
            rollback_errors.append(exc)
    if rollback_errors:
        raise RuntimeError("Task 4 figure rollback failed") from rollback_errors[0]


def _atomic_write_figures(
    output_directory: Path,
    writers: tuple[tuple[str, Callable[[Path], None]], ...],
) -> tuple[Path, ...]:
    """Prepare, verify, and atomically install every figure with rollback."""

    if output_directory.exists() and not output_directory.is_dir():
        raise NotADirectoryError(
            f"output path is not a directory: {output_directory}"
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    destinations = tuple(output_directory / name for name, _ in writers)
    for destination in destinations:
        if destination.exists() and destination.is_dir():
            raise IsADirectoryError(
                f"figure destination is a directory: {destination}"
            )

    temporary_paths: list[Path] = []
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for filename, writer in writers:
            suffix = Path(filename).suffix
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{Path(filename).stem}.",
                suffix=suffix,
                dir=output_directory,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_paths.append(temporary_path)
            writer(temporary_path)
            temporary_path.chmod(0o644)

        prepared = tuple(
            (filename, temporary_path)
            for (filename, _), temporary_path in zip(writers, temporary_paths)
        )
        _verify_prepared_figures(prepared)

        for destination in destinations:
            if destination.exists():
                backup = _unused_figure_sibling(destination, suffix=".bak")
                _replace_figure_path(destination, backup)
                backups.append((destination, backup))
        for temporary_path, destination in zip(temporary_paths, destinations):
            _replace_figure_path(temporary_path, destination)
            installed.append(destination)
        return destinations
    except Exception:
        _restore_figure_transaction(installed, backups)
        raise
    finally:
        for path in temporary_paths:
            if path.exists():
                path.unlink()
        for _, backup in backups:
            if backup.exists():
                backup.unlink()


def write_task04_figures(
    study: Task04StudyResult,
    report: Task04ValidationReport,
    output_directory: str | os.PathLike[str] = DEFAULT_FIGURE_DIRECTORY,
) -> Task04FigureGenerationResult:
    """Write five validated PNG/SVG pairs in one rollback-safe transaction."""

    _require_validated(study, report)
    factories: dict[str, Callable[[], Figure]] = {
        "stopping_voltage_frequency": lambda: _build_frequency_figure(study),
        "stopping_voltage_wavelength": lambda: _build_wavelength_figure(study),
        "copper_threshold_explanation": lambda: _build_copper_figure(study),
        "photoelectric_validation": lambda: _build_validation_figure(report),
        "task04_summary": lambda: _build_summary_figure(study, report),
    }
    writers = tuple(
        (
            filename,
            lambda path, factory=factories[Path(filename).stem]: _save_figure(
                factory(),
                path,
            ),
        )
        for filename in FIGURE_FILENAMES
    )
    output_paths = _atomic_write_figures(Path(output_directory), writers)
    return Task04FigureGenerationResult(report, output_paths)


__all__ = [
    "CURVE_GROUPS",
    "EXPECTED_PNG_DIMENSIONS",
    "FIGURE_DPI",
    "GROUP_COLOURS",
    "PLOT_STYLE",
    "Task04FigureGenerationResult",
    "create_copper_threshold_explanation_figure",
    "create_photoelectric_validation_figure",
    "create_stopping_voltage_frequency_figure",
    "create_stopping_voltage_wavelength_figure",
    "create_task04_summary_figure",
    "write_task04_figures",
]
