"""Publication-quality figures built only from validated Task 5 records."""

from __future__ import annotations

import os
import struct
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from task05_hydrogen_spectrum.analysis import Task05StudyResult, build_task05_study
from task05_hydrogen_spectrum.configuration import DEFAULT_CONFIGURATION
from task05_hydrogen_spectrum.constants import HC_EV_NM
from task05_hydrogen_spectrum.generate_task05 import (
    DEFAULT_FIGURE_DIRECTORY,
    FIGURE_FILENAMES,
)
from task05_hydrogen_spectrum.transitions import HIGHER_SERIES_DISPLAY_GROUP
from task05_hydrogen_spectrum.validation import (
    Task05ValidationReport,
    validate_task05,
)


FIGURE_DPI = 300
WIDE_SIZE_IN = (3840 / FIGURE_DPI, 2160 / FIGURE_DPI)
REGULAR_SIZE_IN = (3200 / FIGURE_DPI, 1800 / FIGURE_DPI)
VALIDATION_SIZE_IN = (3840 / FIGURE_DPI, 1920 / FIGURE_DPI)
SUMMARY_SIZE_IN = WIDE_SIZE_IN

TEXT_COLOUR = "#172033"
MUTED_TEXT = "#52627A"
GRID_COLOUR = "#CBD5E1"
VISIBLE_COLOUR = "#FDE68A"
PASS_COLOUR = "#14804A"

GROUP_ORDER = (
    "Lyman",
    "Balmer",
    "Paschen",
    "Brackett",
    "Pfund",
    HIGHER_SERIES_DISPLAY_GROUP,
)
GROUP_COLOURS = {
    "Lyman": "#0072B2",
    "Balmer": "#D55E00",
    "Paschen": "#009E73",
    "Brackett": "#CC79A7",
    "Pfund": "#E69F00",
    HIGHER_SERIES_DISPLAY_GROUP: "#596579",
}
GROUP_MARKERS = {
    "Lyman": "o",
    "Balmer": "s",
    "Paschen": "^",
    "Brackett": "D",
    "Pfund": "P",
    HIGHER_SERIES_DISPLAY_GROUP: "x",
}

PLOT_STYLE: dict[str, object] = {
    "font.family": "Times New Roman",
    "mathtext.fontset": "stix",
    "font.size": 12.0,
    "axes.titlesize": 15.0,
    "axes.titleweight": "bold",
    "axes.labelsize": 13.0,
    "axes.labelcolor": TEXT_COLOUR,
    "axes.edgecolor": "#64748B",
    "axes.linewidth": 1.0,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID_COLOUR,
    "grid.alpha": 0.58,
    "grid.linewidth": 0.8,
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "legend.frameon": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.edgecolor": "white",
    "svg.hashsalt": "bpho-task05-2026",
}

EXPECTED_PNG_DIMENSIONS = {
    "photon_energy_vs_wavelength.png": (3840, 2160),
    "bohr_energy_level_diagram.png": (3200, 1800),
    "balmer_visible_spectrum.png": (3200, 1800),
    "hydrogen_series_convergence.png": (3200, 1800),
    "hydrogen_validation.png": (3840, 1920),
    "task05_summary.png": (3840, 2160),
}


@dataclass(frozen=True)
class Task05FigureGenerationResult:
    report: Task05ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task05ValidationReport) or not self.report.passed:
            raise ValueError("figure result requires a passing Task 5 report")
        paths = tuple(Path(path) for path in self.output_paths)
        if tuple(path.name for path in paths) != FIGURE_FILENAMES:
            raise ValueError("output_paths must follow the frozen figure order")
        object.__setattr__(self, "output_paths", paths)


def _require_validated(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> None:
    if not isinstance(study, Task05StudyResult):
        raise TypeError("study must be a Task05StudyResult")
    if not isinstance(report, Task05ValidationReport):
        raise TypeError("report must be a Task05ValidationReport")
    if not report.passed:
        raise RuntimeError("Task 5 figure generation requires a passing report")
    if report != validate_task05(study):
        raise ValueError("report does not exactly describe the supplied study")


def _style_axes(axis: Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3.5, width=0.7)


def _group_mask(study: Task05StudyResult, group: str) -> np.ndarray:
    return np.array([value == group for value in study.display_groups], dtype=bool)


def _transition_index(study: Task05StudyResult, initial: int, final: int) -> int:
    matches = np.where((study.initial_n == initial) & (study.final_n == final))[0]
    if matches.size != 1:
        raise ValueError("transition identity is missing or duplicated")
    return int(matches[0])


def _plot_energy_wavelength(
    axis: Axes,
    study: Task05StudyResult,
    *,
    compact: bool = False,
) -> None:
    x_guide = np.geomspace(80.0, 50000.0, 800)
    y_guide = HC_EV_NM / x_guide
    axis.plot(
        x_guide,
        y_guide,
        color="#94A3B8",
        linewidth=1.4 if compact else 2.0,
        linestyle="--",
        label="$E_\gamma=hc/\lambda$",
        zorder=1,
    )
    axis.axvspan(
        DEFAULT_CONFIGURATION.visible_min_nm,
        DEFAULT_CONFIGURATION.visible_max_nm,
        color=VISIBLE_COLOUR,
        alpha=0.30,
        linewidth=0.0,
        zorder=0,
    )
    for group in GROUP_ORDER:
        mask = _group_mask(study, group)
        legend_label = (
            "Higher series ($n_f\\geq6$)"
            if group == HIGHER_SERIES_DISPLAY_GROUP
            else group
        )
        axis.scatter(
            study.wavelength_nm[mask],
            study.photon_energy_ev[mask],
            s=30 if compact else 68,
            marker=GROUP_MARKERS[group],
            color=GROUP_COLOURS[group],
            edgecolors="white" if GROUP_MARKERS[group] != "x" else None,
            linewidths=0.8 if GROUP_MARKERS[group] != "x" else 1.6,
            label=legend_label,
            zorder=3,
        )
    for index, final in enumerate(study.series_limit_final_n):
        group = study.series_names[np.where(study.final_n == final)[0][0]]
        axis.scatter(
            [study.series_limit_wavelength_nm[index]],
            [study.series_limit_energy_ev[index]],
            s=32 if compact else 66,
            marker="D",
            facecolors="white",
            edgecolors=GROUP_COLOURS[group],
            linewidths=1.4,
            zorder=4,
        )

    axis.set_xscale("log")
    axis.set_xlim(80.0, 50000.0)
    axis.set_ylim(0.0, 14.2)
    axis.set_xlabel("Emitted-photon vacuum wavelength, $\lambda$ (nm)")
    axis.set_ylabel("Emitted-photon energy, $E_\gamma$ (eV)")
    axis.set_title(
        "Photon energy versus wavelength"
        if compact
        else "Discrete hydrogen emissions: photon energy versus wavelength",
        fontsize=10.8 if compact else None,
    )
    axis.legend(
        ncol=2 if compact else 3,
        loc="upper right",
        fontsize=6.4 if compact else 9.0,
        columnspacing=0.9,
        handletextpad=0.4,
    )
    axis.text(
        520.0,
        1.15 if compact else 1.35,
        "Visible band",
        color="#806515",
        fontweight="bold",
        fontsize=8.0 if compact else 10.5,
        ha="center",
    )
    if not compact:
        labels = (
            (2, 1, "Lyman-$\\alpha$", (165.0, 10.9)),
            (3, 2, "H-$\\alpha$", (860.0, 2.5)),
            (4, 2, "H-$\\beta$", (315.0, 4.15)),
            (4, 3, "Paschen-$\\alpha$", (2850.0, 1.25)),
        )
        for initial, final, label, text_position in labels:
            index = _transition_index(study, initial, final)
            axis.annotate(
                label,
                xy=(study.wavelength_nm[index], study.photon_energy_ev[index]),
                xytext=text_position,
                fontsize=9.5,
                color=TEXT_COLOUR,
                ha="center",
                arrowprops={"arrowstyle": "->", "color": "#64748B", "lw": 1.1},
            )
        axis.text(
            0.98,
            0.53,
            "45 declared level differences are shown as markers;\n"
            "hollow diamonds are analytical series limits, not finite lines.",
            transform=axis.transAxes,
            ha="right",
            va="center",
            fontsize=9.7,
            color=MUTED_TEXT,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": GRID_COLOUR,
                "alpha": 0.94,
            },
        )
    _style_axes(axis)


def _series_guide(axis: Axes, study: Task05StudyResult) -> None:
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")
    axis.text(
        0.02,
        0.98,
        "Series limits\n$\lambda_{\infty}$ (nm)",
        ha="left",
        va="top",
        fontsize=13.0,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    counts = {name: study.series_names.count(name) for name in GROUP_ORDER[:5]}
    for position, final in enumerate(study.series_limit_final_n):
        group = GROUP_ORDER[int(final) - 1]
        y = 0.78 - position * 0.137
        axis.plot(
            [0.03, 0.18],
            [y, y],
            color=GROUP_COLOURS[group],
            linewidth=3.5,
            solid_capstyle="round",
        )
        axis.text(
            0.23,
            y,
            f"{group:<9} {study.series_limit_wavelength_nm[position]:8.1f}",
            ha="left",
            va="center",
            fontsize=10.2,
            color=TEXT_COLOUR,
            family="Times New Roman",
        )
        axis.text(
            0.23,
            y - 0.044,
            f"{counts[group]} finite lines through n=10",
            ha="left",
            va="center",
            fontsize=8.1,
            color=MUTED_TEXT,
        )
    axis.text(
        0.02,
        0.025,
        "Ten additional $n_f\\geq6$ transitions\n"
        "remain in the full 45-line catalogue.",
        ha="left",
        va="bottom",
        fontsize=9.2,
        color=MUTED_TEXT,
    )


def _plot_energy_levels(axis: Axes, study: Task05StudyResult, *, compact: bool = False) -> None:
    shown = 6
    x0, x1 = 0.18, 0.72
    display_y = {
        1: float(study.level_energy_ev[0]),
        2: float(study.level_energy_ev[1]),
        3: -1.82,
        4: -1.23,
        5: -0.65,
        6: -0.08,
    }
    for index in range(shown):
        energy = float(study.level_energy_ev[index])
        level = index + 1
        axis.hlines(
            energy,
            x0,
            x1,
            color="#334155",
            linewidth=1.8 if compact else 2.8,
        )
        axis.annotate(
            f"n={level}",
            xy=(x0, energy),
            xytext=(x0 - 0.035, display_y[level]),
            textcoords="data",
            ha="right",
            va="center",
            fontsize=7.5 if compact else 10.0,
            color=TEXT_COLOUR,
            arrowprops={
                "arrowstyle": "-",
                "color": "#94A3B8",
                "lw": 0.6 if compact else 0.9,
            }
            if level >= 3
            else None,
        )
        axis.annotate(
            f"{energy:.3f} eV",
            xy=(x1, energy),
            xytext=(x1 + 0.035, display_y[level]),
            textcoords="data",
            ha="left",
            va="center",
            fontsize=7.0 if compact else 9.3,
            color=MUTED_TEXT,
            arrowprops={
                "arrowstyle": "-",
                "color": "#94A3B8",
                "lw": 0.6 if compact else 0.9,
            }
            if level >= 3
            else None,
        )
    axis.axhline(0.0, color="#94A3B8", linestyle="--", linewidth=1.3)
    axis.text(0.75, 0.36, "ionization limit", va="center", fontsize=8.5, color=MUTED_TEXT)

    arrows = (
        (2, 1, 0.28, "Lyman-$\\alpha$", GROUP_COLOURS["Lyman"]),
        (3, 2, 0.40, "H-$\\alpha$", GROUP_COLOURS["Balmer"]),
        (4, 2, 0.52, "H-$\\beta$", "#E69F00"),
        (4, 3, 0.64, "Paschen-$\\alpha$", GROUP_COLOURS["Paschen"]),
    )
    for initial, final, x, label, colour in arrows:
        initial_energy = float(study.level_energy_ev[initial - 1])
        final_energy = float(study.level_energy_ev[final - 1])
        axis.annotate(
            "",
            xy=(x, final_energy),
            xytext=(x, initial_energy),
            arrowprops={"arrowstyle": "-|>", "color": colour, "lw": 1.7 if compact else 2.4},
        )
        if not compact:
            axis.text(
                x + 0.012,
                (initial_energy + final_energy) / 2.0,
                label,
                rotation=90,
                ha="left",
                va="center",
                fontsize=8.4,
                color=colour,
            )
    axis.set_xlim(0.08, 0.98)
    axis.set_ylim(-14.4, 0.8)
    axis.set_xticks([])
    axis.set_ylabel("Atomic bound-state energy, $E_n$ (eV)")
    axis.set_title(
        "Bohr energy levels and emissions"
        if compact
        else "Bohr levels and representative downward transitions",
        fontsize=10.8 if compact else None,
    )
    axis.grid(axis="y", alpha=0.42)
    axis.spines["bottom"].set_visible(False)
    _style_axes(axis)


def _wavelength_rgb(wavelength_nm: float) -> tuple[float, float, float]:
    wavelength = float(wavelength_nm)
    if wavelength < 380.0 or wavelength > 750.0:
        return (0.45, 0.50, 0.58)
    if wavelength < 440.0:
        red, green, blue = -(wavelength - 440.0) / 60.0, 0.0, 1.0
    elif wavelength < 490.0:
        red, green, blue = 0.0, (wavelength - 440.0) / 50.0, 1.0
    elif wavelength < 510.0:
        red, green, blue = 0.0, 1.0, -(wavelength - 510.0) / 20.0
    elif wavelength < 580.0:
        red, green, blue = (wavelength - 510.0) / 70.0, 1.0, 0.0
    elif wavelength < 645.0:
        red, green, blue = 1.0, -(wavelength - 645.0) / 65.0, 0.0
    else:
        red, green, blue = 1.0, 0.0, 0.0
    if wavelength < 420.0:
        factor = 0.35 + 0.65 * (wavelength - 380.0) / 40.0
    elif wavelength > 700.0:
        factor = 0.35 + 0.65 * (750.0 - wavelength) / 50.0
    else:
        factor = 1.0
    gamma = 0.8
    return tuple((max(channel * factor, 0.0)) ** gamma for channel in (red, green, blue))


def _plot_balmer_spectrum(axis: Axes, study: Task05StudyResult, *, compact: bool = False) -> None:
    wavelengths = np.linspace(380.0, 750.0, 900)
    gradient = np.array([_wavelength_rgb(value) for value in wavelengths])[None, :, :]
    axis.imshow(
        gradient,
        aspect="auto",
        extent=(380.0, 750.0, 0.12, 0.28),
        interpolation="bilinear",
        alpha=0.78,
        zorder=0,
    )
    axis.axvspan(360.0, 380.0, color="#E2E8F0", alpha=0.7, zorder=0)
    balmer = study.final_n == 2
    for index in np.where(balmer)[0]:
        wavelength = float(study.wavelength_nm[index])
        colour = _wavelength_rgb(wavelength)
        axis.vlines(
            wavelength,
            0.20,
            0.88,
            color=colour,
            linewidth=2.2 if compact else 4.0,
            zorder=3,
        )
    limit = float(study.series_limit_wavelength_nm[1])
    axis.axvline(limit, color="#64748B", linestyle="--", linewidth=1.6)
    if not compact:
        axis.text(
            limit + 2.0,
            0.58,
            "Balmer limit\n364.507 nm",
            ha="left",
            va="center",
            fontsize=9.0,
            color=MUTED_TEXT,
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.80,
            },
        )
        for initial, final, label, y in (
            (3, 2, "H-$\\alpha$\n656.112 nm", 0.94),
            (4, 2, "H-$\\beta$\n486.009 nm", 0.78),
            (5, 2, "H-$\\gamma$\n433.937 nm", 0.98),
            (6, 2, "H-$\\delta$\n410.070 nm", 0.72),
        ):
            index = _transition_index(study, initial, final)
            wavelength = float(study.wavelength_nm[index])
            axis.text(
                wavelength,
                y,
                label,
                ha="center",
                va="bottom",
                fontsize=8.7,
                color=TEXT_COLOUR,
            )
    axis.set_xlim(360.0, 750.0)
    axis.set_ylim(0.0, 1.12)
    axis.set_yticks([])
    axis.set_xlabel("Ideal Bohr-model vacuum wavelength (nm)")
    axis.set_title(
        "Visible Balmer line positions"
        if compact
        else "Balmer series: discrete line positions across the visible band",
        fontsize=10.8 if compact else None,
    )
    axis.grid(axis="x", alpha=0.5)
    axis.spines["left"].set_visible(False)
    _style_axes(axis)
    axis.text(
        0.99,
        0.035,
        "Equal heights show positions only — intensity and linewidth are not modelled.",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.7 if compact else 9.2,
        color=MUTED_TEXT,
        fontstyle="italic",
    )


def _plot_series_convergence(axis: Axes, study: Task05StudyResult) -> None:
    for final in range(1, 6):
        group = GROUP_ORDER[final - 1]
        mask = study.final_n == final
        axis.plot(
            study.initial_n[mask],
            study.wavelength_nm[mask],
            marker=GROUP_MARKERS[group],
            markersize=6.2,
            linewidth=2.2,
            color=GROUP_COLOURS[group],
            label=group,
        )
        axis.hlines(
            study.series_limit_wavelength_nm[final - 1],
            final + 1,
            10.15,
            color=GROUP_COLOURS[group],
            linestyle="--",
            linewidth=1.2,
            alpha=0.72,
        )
        axis.text(
            10.20,
            study.series_limit_wavelength_nm[final - 1],
            f"{study.series_limit_wavelength_nm[final - 1]:.1f} nm",
            va="center",
            ha="left",
            fontsize=8.3,
            color=GROUP_COLOURS[group],
        )
    axis.set_yscale("log")
    axis.set_xlim(1.7, 11.25)
    axis.set_ylim(75.0, 10000.0)
    axis.set_xticks(np.arange(2, 11))
    axis.set_xlabel("Initial level, $n_i$")
    axis.set_ylabel("Emitted-photon wavelength, $\lambda$ (nm)")
    axis.set_title("Each hydrogen series converges toward an analytical limit")
    axis.legend(ncol=5, loc="upper right", fontsize=8.8)
    _style_axes(axis)
    axis.text(
        0.02,
        0.91,
        "Dashed lines are $n_i\\rightarrow\\infty$ limits; they are not finite transitions.",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9.4,
        color=MUTED_TEXT,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": GRID_COLOUR,
            "alpha": 0.90,
        },
    )


def _validation_values(
    report: Task05ValidationReport,
) -> tuple[list[str], np.ndarray]:
    checks = {check.name: check for check in report.checks}
    specification = (
        ("Level $E_n$", "level_energy_reference"),
        ("Energy difference", "transition_energy_difference"),
        ("Energy reference", "transition_energy_reference"),
        ("$E_\gamma\lambda$", "energy_wavelength_identity"),
        ("$f\lambda$", "frequency_wavelength_identity"),
        ("Rydberg $\lambda$", "rydberg_wavelength_reference"),
        ("Frequency", "frequency_reference"),
    )
    labels = [label for label, _ in specification]
    values = [checks[name].observed / checks[name].tolerance for _, name in specification]
    named = [check for check in report.checks if check.name.startswith("named_line_")]
    limits = [check for check in report.checks if check.name.startswith("series_limit_")]
    labels.extend(["Named lines", "Series limits"])
    values.extend(
        [
            max(check.observed / check.tolerance for check in named),
            max(check.observed / check.tolerance for check in limits),
        ]
    )
    return labels, np.asarray(values, dtype=np.float64)


def _build_primary_figure(study: Task05StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=WIDE_SIZE_IN,
            gridspec_kw={"width_ratios": (4.35, 1.35)},
        )
        _plot_energy_wavelength(axes[0], study)
        _series_guide(axes[1], study)
        figure.suptitle(
            "Hydrogen emission energies from the ideal Bohr model",
            fontsize=20.0,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(left=0.075, right=0.985, bottom=0.13, top=0.875, wspace=0.11)
        return figure


def _build_level_figure(study: Task05StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_SIZE_IN)
        _plot_energy_levels(axis, study)
        figure.suptitle(
            "Photon emission is the positive energy lost by the atom",
            fontsize=18.5,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.text(
            0.5,
            0.035,
            "Diagram shows n=1--6 for clarity; the numerical study includes n=1--10.",
            ha="center",
            va="bottom",
            fontsize=9.3,
            color=MUTED_TEXT,
        )
        figure.subplots_adjust(left=0.12, right=0.94, bottom=0.14, top=0.84)
        return figure


def _build_balmer_figure(study: Task05StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_SIZE_IN)
        _plot_balmer_spectrum(axis, study)
        figure.suptitle(
            "Only discrete Balmer wavelengths appear in the ideal spectrum",
            fontsize=18.5,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.82)
        return figure


def _build_convergence_figure(study: Task05StudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_SIZE_IN)
        _plot_series_convergence(axis, study)
        figure.suptitle(
            "Higher initial levels crowd toward each spectral-series limit",
            fontsize=18.5,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(left=0.105, right=0.88, bottom=0.14, top=0.82)
        return figure


def _build_validation_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    labels, ratios = _validation_values(report)
    floor = 1.0e-6
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=VALIDATION_SIZE_IN,
            gridspec_kw={"width_ratios": (1.7, 0.9)},
        )
        positions = np.arange(len(labels))
        axes[0].bar(
            positions,
            np.maximum(ratios, floor),
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
        axes[0].set_ylim(floor / 2.0, 2.0)
        axes[0].set_xticks(positions, labels, rotation=24, ha="right")
        axes[0].set_ylabel("Observed error / declared tolerance")
        axes[0].set_title("Independent numerical comparisons")
        axes[0].legend(loc="upper left")
        _style_axes(axes[0])

        axes[1].axis("off")
        axes[1].set_xlim(0.0, 1.0)
        axes[1].set_ylim(0.0, 1.0)
        axes[1].text(
            0.06,
            0.90,
            f"PASS  •  {len(report.checks)}/{len(report.checks)} checks",
            ha="left",
            va="top",
            fontsize=15.0,
            fontweight="bold",
            color=PASS_COLOUR,
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "#E8F5EE",
                "edgecolor": "#8ED1AC",
            },
        )
        summary = (
            f"{study.levels_n.size} immutable Bohr levels\n"
            f"{study.initial_n.size} unique downward emissions\n"
            f"{study.spectral_regions.count('visible')} visible-band transitions\n"
            "5 analytical series limits\n"
            "6 frozen named-line anchors\n"
            "Independent Decimal/Rydberg reference path"
        )
        axes[1].text(
            0.06,
            0.68,
            summary,
            ha="left",
            va="top",
            fontsize=11.0,
            linespacing=1.65,
            color=TEXT_COLOUR,
        )
        axes[1].text(
            0.06,
            0.14,
            "Bars below 1.0 pass. Exact structural checks\n"
            "are counted separately in the 30-check report.",
            ha="left",
            va="bottom",
            fontsize=9.8,
            color=MUTED_TEXT,
        )
        figure.suptitle(
            "Independent validation — every Task 5 check passes",
            fontsize=19.5,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.965,
        )
        figure.subplots_adjust(left=0.075, right=0.98, bottom=0.22, top=0.84, wspace=0.16)
        return figure


def _build_summary_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(2, 2, figsize=SUMMARY_SIZE_IN)
        _plot_energy_wavelength(axes[0, 0], study, compact=True)
        _plot_energy_levels(axes[0, 1], study, compact=True)
        _plot_balmer_spectrum(axes[1, 0], study, compact=True)
        key = axes[1, 1]
        key.axis("off")
        key.set_xlim(0.0, 1.0)
        key.set_ylim(0.0, 1.0)
        key.text(0.02, 0.94, "What the model shows", fontsize=13.5, fontweight="bold", color=TEXT_COLOUR, va="top")
        key.text(0.02, 0.79, "$E_n=-E_{\\mathrm{R}}/n^2$", fontsize=17.0, color=TEXT_COLOUR, va="top")
        key.text(0.02, 0.67, "$E_\\gamma=hc/\\lambda$", fontsize=17.0, color=TEXT_COLOUR, va="top")
        key.text(
            0.02,
            0.49,
            "• 45 downward transitions among n=1--10.\n"
            "• Integer levels produce discrete photon energies.\n"
            "• H-$\\alpha$: 656.112 nm in the ideal model.\n"
            "• Seven declared transitions lie in 380--750 nm.",
            fontsize=9.2,
            linespacing=1.35,
            color="#334155",
            va="top",
        )
        key.text(
            0.02,
            0.055,
            f"PASS  •  {len(report.checks)}/{len(report.checks)} independent checks",
            fontsize=11.0,
            fontweight="bold",
            color=PASS_COLOUR,
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "#E8F5EE",
                "edgecolor": "#8ED1AC",
                "linewidth": 0.8,
            },
        )
        figure.suptitle(
            "Task 5 — Hydrogen spectrum and the Bohr model",
            fontsize=20.0,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.977,
        )
        figure.text(
            0.5,
            0.93,
            "Ten energy levels • forty-five emissions • ultraviolet to infrared",
            ha="center",
            va="center",
            fontsize=10.5,
            color=MUTED_TEXT,
        )
        figure.subplots_adjust(left=0.075, right=0.98, bottom=0.07, top=0.87, wspace=0.32, hspace=0.38)
        return figure


def create_photon_energy_vs_wavelength_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_primary_figure(study)


def create_bohr_energy_level_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_level_figure(study)


def create_balmer_visible_spectrum_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_balmer_figure(study)


def create_hydrogen_series_convergence_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_convergence_figure(study)


def create_hydrogen_validation_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_validation_figure(study, report)


def create_task05_summary_figure(
    study: Task05StudyResult,
    report: Task05ValidationReport,
) -> Figure:
    _require_validated(study, report)
    return _build_summary_figure(study, report)


def _save_figure(figure: Figure, path: Path) -> None:
    file_format = path.suffix.removeprefix(".").lower()
    if file_format == "png":
        metadata = {"Software": "BPhO Computational Challenge 2026"}
    elif file_format == "svg":
        metadata = {"Creator": "BPhO Computational Challenge 2026", "Date": None}
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
            normalized = "\n".join(
                line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()
            ) + "\n"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(normalized)
    finally:
        plt.close(figure)


def _verify_png(path: Path, expected: tuple[int, int]) -> None:
    content = path.read_bytes()
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"invalid PNG signature: {path.name}")
    if struct.unpack(">II", content[16:24]) != expected:
        raise ValueError(f"invalid PNG dimensions: {path.name}")


def _verify_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or "<dc:date>" in text:
        raise ValueError(f"non-deterministic SVG metadata: {path.name}")
    root = ET.fromstring(text)
    if not root.tag.endswith("svg") or "viewBox" not in root.attrib:
        raise ValueError(f"invalid SVG structure: {path.name}")


def _replace_path(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _restore_path(destination: Path, content: bytes | None) -> None:
    if content is None:
        if destination.exists():
            destination.unlink()
        return
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.restore-", delete=False) as handle:
        restore = Path(handle.name)
        handle.write(content)
    os.replace(restore, destination)


def _commit_prepared(
    prepared: tuple[tuple[str, Path], ...],
    output_directory: Path,
) -> tuple[Path, ...]:
    destinations = tuple(output_directory / filename for filename, _ in prepared)
    originals = {path: path.read_bytes() if path.exists() else None for path in destinations}
    replaced: list[Path] = []
    try:
        for (_, source), destination in zip(prepared, destinations):
            _replace_path(source, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            _restore_path(destination, originals[destination])
        raise
    return destinations


def generate_task05_figures(
    output_directory: Path = DEFAULT_FIGURE_DIRECTORY,
    *,
    study: Task05StudyResult | None = None,
    report: Task05ValidationReport | None = None,
) -> Task05FigureGenerationResult:
    normalized_study = build_task05_study() if study is None else study
    normalized_report = validate_task05(normalized_study) if report is None else report
    _require_validated(normalized_study, normalized_report)
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    builders = (
        _build_primary_figure,
        _build_level_figure,
        _build_balmer_figure,
        _build_convergence_figure,
        lambda value: _build_validation_figure(value, normalized_report),
        lambda value: _build_summary_figure(value, normalized_report),
    )
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".task05-figures-") as temporary:
        temp = Path(temporary)
        prepared: list[tuple[str, Path]] = []
        for pair_index, builder in enumerate(builders):
            for filename in FIGURE_FILENAMES[pair_index * 2 : pair_index * 2 + 2]:
                path = temp / filename
                _save_figure(builder(normalized_study), path)
                prepared.append((filename, path))
        prepared_tuple = tuple(prepared)
        if tuple(name for name, _ in prepared_tuple) != FIGURE_FILENAMES:
            raise ValueError("prepared figures do not match the frozen order")
        for filename, path in prepared_tuple:
            if path.stat().st_size == 0:
                raise ValueError(f"empty figure output: {filename}")
            if filename.endswith(".png"):
                _verify_png(path, EXPECTED_PNG_DIMENSIONS[filename])
            else:
                _verify_svg(path)
        if sum(path.stat().st_size for _, path in prepared_tuple) > DEFAULT_CONFIGURATION.figure_size_budget_bytes:
            raise ValueError("prepared figures exceed the configured size budget")
        output_paths = _commit_prepared(prepared_tuple, destination)
    return Task05FigureGenerationResult(normalized_report, output_paths)


__all__ = [
    "EXPECTED_PNG_DIMENSIONS",
    "FIGURE_DPI",
    "Task05FigureGenerationResult",
    "create_balmer_visible_spectrum_figure",
    "create_bohr_energy_level_figure",
    "create_hydrogen_series_convergence_figure",
    "create_hydrogen_validation_figure",
    "create_photon_energy_vs_wavelength_figure",
    "create_task05_summary_figure",
    "generate_task05_figures",
]
