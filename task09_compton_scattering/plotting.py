"""Publication-quality deterministic figures for Task 9."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from PIL import Image

from task09_compton_scattering.analysis import Task09StudyResult
from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.cross_section import (
    KleinNishinaStudy,
    klein_nishina_total_cross_section_m2,
)
from task09_compton_scattering.cross_section_validation import (
    CrossSectionValidationReport,
    cross_section_study_digest,
)
from task09_compton_scattering.constants import BARN_M2, THOMSON_CROSS_SECTION_M2
from task09_compton_scattering.validation import (
    Task09ValidationReport,
    task09_study_digest,
)


TEXT = "#202124"
MUTED = "#5F6368"
GRID = "#E2E6EA"
PANEL = "#F7F8FA"
PHOTON = "#C44E00"
ELECTRON = "#0072B2"
EXTENSION = "#007A5E"
ENERGY_COLOURS = ("#0072B2", "#007A5E", "#C44E00", "#A64F83", "#332288")
ENERGY_LINESTYLES = ("solid", (0, (7, 4)), (0, (2, 3)), (0, (9, 3, 2, 3)), (0, (13, 4)))
ENERGY_STYLE_NAMES = ("solid", "dashed", "dotted", "dash–dot", "long dash")
FIGURE_FONT_FAMILY = "Times New Roman"

FIGURE_BASE_NAMES = (
    "required_kinematics",
    "energy_transfer_geometry",
    "klein_nishina_extension",
    "task09_summary",
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
    "font.size": 9.4,
    "axes.titlesize": 10.8,
    "axes.labelsize": 9.4,
    "axes.labelcolor": TEXT,
    "axes.edgecolor": "#69727D",
    "axes.linewidth": 0.8,
    "axes.facecolor": "white",
    "axes.titlecolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "xtick.labelsize": 8.8,
    "ytick.labelsize": 8.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "grid.color": GRID,
    "grid.linewidth": 0.55,
    "grid.alpha": 0.72,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "svg.hashsalt": "bpho-task09-v2",
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


def _figure(configuration: Task09Configuration, *, summary: bool = False) -> Figure:
    width = configuration.summary_width_px if summary else configuration.figure_width_px
    height = configuration.summary_height_px if summary else configuration.figure_height_px
    return plt.figure(
        figsize=(width / configuration.figure_dpi, height / configuration.figure_dpi),
        dpi=configuration.figure_dpi,
        facecolor="white",
    )


def _require_validated(
    study: Task09StudyResult,
    report: Task09ValidationReport,
    cross_section_study: KleinNishinaStudy,
    cross_section_report: CrossSectionValidationReport,
) -> None:
    if not isinstance(study, Task09StudyResult):
        raise TypeError("study must be a Task09StudyResult")
    if not isinstance(report, Task09ValidationReport):
        raise TypeError("report must be a Task09ValidationReport")
    if not isinstance(cross_section_study, KleinNishinaStudy):
        raise TypeError("cross_section_study must be a KleinNishinaStudy")
    if not isinstance(cross_section_report, CrossSectionValidationReport):
        raise TypeError("cross_section_report must be a CrossSectionValidationReport")
    if not report.passed:
        raise RuntimeError("figures require a passing Task 9 kinematic report")
    if not cross_section_report.passed:
        raise RuntimeError("figures require a passing Task 9 cross-section report")
    if report.study_digest != task09_study_digest(study):
        raise ValueError("kinematic report belongs to a different Task 9 study")
    if cross_section_report.study_digest != cross_section_study_digest(
        cross_section_study
    ):
        raise ValueError("cross-section report belongs to a different extension study")
    if cross_section_study.incident_energy_kev.shape != study.incident_energy_kev.shape:
        raise ValueError("kinematic and extension studies must share one grid")


def _format_axes(axis: plt.Axes, *, grid_axis: str = "both") -> None:
    axis.grid(True, axis=grid_axis, color=GRID, linewidth=0.55, alpha=0.72)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.set_axisbelow(True)


def _energy_label(energy: float, index: int) -> str:
    return f"{energy:g} keV · {ENERGY_STYLE_NAMES[index]}"


def _plot_energy_curves(
    axis: plt.Axes,
    study: Task09StudyResult,
    values: np.ndarray,
    *,
    linewidth: float = 2.15,
    labels: bool = False,
) -> None:
    for index, energy in enumerate(study.incident_energies_kev):
        axis.plot(
            study.theta_axis_deg,
            values[index],
            color=ENERGY_COLOURS[index],
            linestyle=ENERGY_LINESTYLES[index],
            linewidth=linewidth,
            label=_energy_label(float(energy), index) if labels else None,
        )


def _energy_legend_handles(study: Task09StudyResult) -> list[plt.Line2D]:
    return [
        plt.Line2D(
            [0],
            [0],
            color=ENERGY_COLOURS[index],
            linestyle=ENERGY_LINESTYLES[index],
            linewidth=2.15,
            label=_energy_label(float(energy), index),
        )
        for index, energy in enumerate(study.incident_energies_kev)
    ]


def _add_publication_header(
    figure: Figure,
    title: str,
    subtitle: str,
    *,
    extension: bool = False,
) -> None:
    figure.suptitle(
        title,
        x=0.07,
        y=0.955,
        ha="left",
        fontsize=13.4,
        fontweight="bold",
        color=TEXT,
    )
    figure.text(0.07, 0.895, subtitle, color=MUTED, fontsize=8.4)
    descriptor = "Optional Klein–Nishina extension" if extension else "Exact relativistic free-electron model"
    figure.text(
        0.93,
        0.94,
        descriptor,
        ha="right",
        va="center",
        color=EXTENSION if extension else MUTED,
        fontsize=8.2,
        fontstyle="italic",
    )


def _make_required_kinematics(
    study: Task09StudyResult,
    configuration: Task09Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        2,
        2,
        left=0.095,
        right=0.965,
        bottom=0.17,
        top=0.745,
        hspace=0.52,
        wspace=0.27,
        height_ratios=(1.03, 1.0),
    )
    shift_axis = figure.add_subplot(grid[0, :])
    beta_axis = figure.add_subplot(grid[1, 0])
    phi_axis = figure.add_subplot(grid[1, 1])

    _plot_energy_curves(
        shift_axis,
        study,
        study.fractional_wavelength_shift,
        labels=True,
    )
    shift_axis.set(
        title="(a) Fractional wavelength shift",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="Δλ / λ",
        xlim=(0.0, 180.0),
        ylim=(0.0, 4.12),
        xticks=(0, 30, 60, 90, 120, 150, 180),
    )
    figure.legend(
        handles=_energy_legend_handles(study),
        loc="upper center",
        bbox_to_anchor=(0.52, 0.845),
        ncol=5,
        fontsize=7.5,
        handlelength=3.0,
        columnspacing=1.15,
        frameon=False,
    )
    _format_axes(shift_axis)

    _plot_energy_curves(beta_axis, study, study.electron_beta)
    beta_axis.set(
        title="(b) Relativistic electron recoil speed",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="v / c",
        xlim=(0.0, 180.0),
        ylim=(0.0, 1.0),
        xticks=(0, 45, 90, 135, 180),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    _format_axes(beta_axis)

    _plot_energy_curves(phi_axis, study, study.electron_recoil_angle_deg)
    phi_axis.scatter(
        [0.0],
        [90.0],
        s=40,
        facecolor="white",
        edgecolor=TEXT,
        linewidth=1.2,
        zorder=5,
    )
    phi_axis.set(
        title="(c) Electron recoil angle",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="φ (°)",
        xlim=(0.0, 180.0),
        ylim=(0.0, 92.0),
        xticks=(0, 45, 90, 135, 180),
        yticks=(0, 30, 60, 90),
    )
    _format_axes(phi_axis)

    _add_publication_header(
        figure,
        "Compton scattering: the three required angular dependences",
        "Exact relativistic free-electron kinematics · five official incident energies · 721 points from 0° to 180°",
    )
    figure.text(
        0.51,
        0.035,
        "θ = 0°: zero electron momentum, so φ is undefined; the open point is its 90° limit.   ·   θ = 180°: φ = 0°.",
        ha="center",
        color=MUTED,
        fontsize=7.2,
    )
    return figure


def _collision_geometry(
    axis: plt.Axes,
    *,
    energy_kev: float,
    theta_deg: float,
    scattered_energy_kev: float,
    recoil_angle_deg: float,
    compact: bool = False,
) -> None:
    ratio = scattered_energy_kev / energy_kev
    theta_rad = np.radians(theta_deg)
    photon_end = (ratio * np.cos(theta_rad), ratio * np.sin(theta_rad))
    electron_end = (1.0 - photon_end[0], -photon_end[1])
    arrow_scale = 12 if compact else 14
    axis.add_patch(
        FancyArrowPatch(
            (-1.0, 0.0),
            (0.0, 0.0),
            arrowstyle="-|>",
            mutation_scale=arrow_scale,
            linewidth=2.8,
            color=PHOTON,
        )
    )
    axis.add_patch(
        FancyArrowPatch(
            (0.0, 0.0),
            photon_end,
            arrowstyle="-|>",
            mutation_scale=arrow_scale,
            linewidth=2.8,
            color=PHOTON,
        )
    )
    axis.add_patch(
        FancyArrowPatch(
            (0.0, 0.0),
            electron_end,
            arrowstyle="-|>",
            mutation_scale=arrow_scale,
            linewidth=2.8,
            color=ELECTRON,
        )
    )
    axis.add_patch(Circle((0.0, 0.0), 0.055, facecolor="white", edgecolor=TEXT, linewidth=1.5, zorder=4))
    axis.axhline(0.0, color="#9AAEC3", linewidth=0.8, linestyle=(0, (4, 4)), zorder=0)
    axis.text(-0.98, 0.08, "incident photon · E", color=PHOTON, fontsize=7.1, weight="bold")
    if not compact:
        axis.text(
            0.03,
            0.93,
            f"E = {energy_kev:g} keV · θ = {theta_deg:g}° · φ = {recoil_angle_deg:.1f}°",
            transform=axis.transAxes,
            color=TEXT,
            fontsize=8.0,
            weight="bold",
        )
        axis.text(photon_end[0], photon_end[1] + 0.08, "E′", color=PHOTON, fontsize=8.0, ha="center", weight="bold")
        axis.text(electron_end[0] + 0.03, electron_end[1] - 0.08, "pₑ", color=ELECTRON, fontsize=8.0, ha="center", weight="bold")
    axis.set(xlim=(-1.18, 1.62), ylim=(-1.05, 1.05), aspect="equal")
    axis.set_xticks([])
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)


def _make_energy_transfer_geometry(
    study: Task09StudyResult,
    configuration: Task09Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        2,
        2,
        left=0.09,
        right=0.965,
        bottom=0.11,
        top=0.745,
        hspace=0.55,
        wspace=0.25,
        height_ratios=(1.08, 0.92),
    )
    photon_axis = figure.add_subplot(grid[0, 0])
    electron_axis = figure.add_subplot(grid[0, 1])
    ratio = study.scattered_energy_kev / study.incident_energy_kev
    _plot_energy_curves(photon_axis, study, ratio)
    _plot_energy_curves(electron_axis, study, 1.0 - ratio)
    photon_axis.set(
        title="Scattered photon retains E′/E",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="E′ / E",
        xlim=(0, 180),
        ylim=(0, 1.02),
        xticks=(0, 45, 90, 135, 180),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    electron_axis.set(
        title="Electron receives K/E = 1 − E′/E",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="K / E",
        xlim=(0, 180),
        ylim=(0, 1.02),
        xticks=(0, 45, 90, 135, 180),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    _format_axes(photon_axis)
    _format_axes(electron_axis)
    figure.legend(
        handles=_energy_legend_handles(study),
        loc="upper center",
        bbox_to_anchor=(0.52, 0.845),
        ncol=5,
        fontsize=7.5,
        handlelength=3.0,
        columnspacing=1.15,
        frameon=False,
    )

    geometry_grid = grid[1, :].subgridspec(1, 3, wspace=0.08)
    energy_index = int(np.flatnonzero(np.isclose(study.incident_energies_kev, 200.0))[0])
    for column, theta in enumerate((45.0, 90.0, 135.0)):
        angle_index = int(np.flatnonzero(np.isclose(study.theta_axis_deg, theta))[0])
        axis = figure.add_subplot(geometry_grid[0, column])
        _collision_geometry(
            axis,
            energy_kev=200.0,
            theta_deg=theta,
            scattered_energy_kev=float(study.scattered_energy_kev[energy_index, angle_index]),
            recoil_angle_deg=float(study.electron_recoil_angle_deg[energy_index, angle_index]),
        )

    _add_publication_header(
        figure,
        "Energy transfer and exact momentum geometry",
        "Photon energy is redistributed, never lost: E = E′ + K · arrow lengths use one common momentum scale in each collision",
    )
    figure.text(
        0.5,
        0.038,
        "Representative momentum triangles use 200 keV. Electron transverse momentum cancels the scattered photon.",
        ha="center",
        color=MUTED,
        fontsize=7.2,
    )
    return figure


def _make_klein_nishina_extension(
    study: Task09StudyResult,
    cross_section_study: KleinNishinaStudy,
    configuration: Task09Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        2,
        2,
        left=0.095,
        right=0.965,
        bottom=0.17,
        top=0.745,
        hspace=0.52,
        wspace=0.27,
        height_ratios=(1.05, 1.0),
    )
    differential_axis = figure.add_subplot(grid[0, :])
    density_axis = figure.add_subplot(grid[1, 0])
    total_axis = figure.add_subplot(grid[1, 1])

    _plot_energy_curves(
        differential_axis,
        study,
        cross_section_study.relative_differential_cross_section,
        labels=True,
    )
    differential_axis.set(
        title="(a) Differential strength relative to forward scattering",
        xlabel="Photon scattering angle, θ (°)",
        ylabel="(dσ/dΩ) / (dσ/dΩ)θ=0",
        xlim=(0, 180),
        ylim=(0, 1.03),
        xticks=(0, 30, 60, 90, 120, 150, 180),
        yticks=np.linspace(0.0, 1.0, 5),
    )
    figure.legend(
        handles=_energy_legend_handles(study),
        loc="upper center",
        bbox_to_anchor=(0.52, 0.845),
        ncol=5,
        fontsize=7.5,
        handlelength=3.0,
        columnspacing=1.1,
        frameon=False,
    )
    _format_axes(differential_axis)

    _plot_energy_curves(density_axis, study, cross_section_study.theta_pdf_rad_inv)
    density_axis.set(
        title="(b) Normalized probability density in polar angle",
        xlabel="Photon scattering angle, θ (°)",
        ylabel=r"p(θ) (rad$^{-1}$)",
        xlim=(0, 180),
        ylim=(0, 0.9),
        xticks=(0, 45, 90, 135, 180),
    )
    _format_axes(density_axis)

    continuous_energy = np.geomspace(1.0, 5000.0, 500)
    continuous_total = klein_nishina_total_cross_section_m2(continuous_energy) / BARN_M2
    official_total = cross_section_study.total_cross_section_barn[:, 0]
    total_axis.plot(continuous_energy, continuous_total, color=EXTENSION, linewidth=2.4)
    total_axis.scatter(
        study.incident_energies_kev,
        official_total,
        s=47,
        color=ENERGY_COLOURS,
        edgecolor="white",
        linewidth=1.1,
        zorder=5,
    )
    total_axis.axhline(
        THOMSON_CROSS_SECTION_M2 / BARN_M2,
        color="#8799AE",
        linewidth=1.1,
        linestyle=(0, (4, 4)),
        label="Thomson low-energy limit",
    )
    total_axis.set_xscale("log")
    total_axis.set(
        title="(c) Total cross-section falls with photon energy",
        xlabel="Incident photon energy, E (keV)",
        ylabel="σKN (barn)",
        xlim=(1.0, 5000.0),
        ylim=(0.0, 0.7),
    )
    total_axis.legend(loc="lower left", fontsize=7.4)
    _format_axes(total_axis)

    _add_publication_header(
        figure,
        "Klein–Nishina angular weighting · optional extension",
        "Free, stationary, unpolarized electron model · the official kinematic curves remain exact and unweighted",
        extension=True,
    )
    figure.text(
        0.5,
        0.035,
        "p(θ) includes the 2π sinθ solid-angle factor and integrates to one.   ·   Binding, attenuation, detector response and multiple scattering are outside scope.",
        ha="center",
        color=MUTED,
        fontsize=7.0,
    )
    return figure


def _metric_card(
    axis: plt.Axes,
    y: float,
    title: str,
    value: str,
    detail: str,
    colour: str,
) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (0.02, y),
            0.96,
            0.19,
            boxstyle="round,pad=0.018,rounding_size=0.025",
            transform=axis.transAxes,
            facecolor="#F8FBFE",
            edgecolor="#D5DFEB",
            linewidth=1.0,
        )
    )
    axis.add_patch(
        FancyBboxPatch(
            (0.02, y),
            0.018,
            0.19,
            boxstyle="round,pad=0.0,rounding_size=0.01",
            transform=axis.transAxes,
            facecolor=colour,
            edgecolor=colour,
        )
    )
    axis.text(0.075, y + 0.145, title, transform=axis.transAxes, color=MUTED, fontsize=7.0, weight="bold")
    axis.text(0.075, y + 0.045, value, transform=axis.transAxes, color=TEXT, fontsize=16.0, weight="bold")
    axis.text(0.59, y + 0.052, detail, transform=axis.transAxes, color=MUTED, fontsize=7.0)


def _make_summary(
    study: Task09StudyResult,
    report: Task09ValidationReport,
    cross_section_report: CrossSectionValidationReport,
    configuration: Task09Configuration,
) -> Figure:
    figure = _figure(configuration, summary=True)
    grid = figure.add_gridspec(
        2,
        3,
        left=0.055,
        right=0.97,
        bottom=0.17,
        top=0.80,
        hspace=0.44,
        wspace=0.28,
        height_ratios=(1.08, 1.0),
    )
    collision_axis = figure.add_subplot(grid[0, :2])
    metrics_axis = figure.add_subplot(grid[0, 2])
    shift_axis = figure.add_subplot(grid[1, 0])
    beta_axis = figure.add_subplot(grid[1, 1])
    phi_axis = figure.add_subplot(grid[1, 2])

    energy_index = int(np.flatnonzero(np.isclose(study.incident_energies_kev, 200.0))[0])
    angle_index = int(np.flatnonzero(np.isclose(study.theta_axis_deg, 90.0))[0])
    _collision_geometry(
        collision_axis,
        energy_kev=200.0,
        theta_deg=90.0,
        scattered_energy_kev=float(study.scattered_energy_kev[energy_index, angle_index]),
        recoil_angle_deg=float(study.electron_recoil_angle_deg[energy_index, angle_index]),
    )
    collision_axis.set_title(
        "Exact 200 keV collision at θ = 90° · momentum-vector construction",
        loc="left",
        fontsize=11.0,
        fontweight="bold",
        color=TEXT,
        pad=8,
    )

    metrics_axis.axis("off")
    _metric_card(
        metrics_axis,
        0.72,
        "Fractional wavelength shift",
        f"{study.fractional_wavelength_shift[energy_index, angle_index]:.5f}",
        "Δλ = 2.426 pm",
        PHOTON,
    )
    _metric_card(
        metrics_axis,
        0.47,
        "Electron recoil speed",
        f"{study.electron_beta[energy_index, angle_index]:.5f} c",
        "fully relativistic",
        ELECTRON,
    )
    _metric_card(
        metrics_axis,
        0.22,
        "Electron recoil angle",
        f"{study.electron_recoil_angle_deg[energy_index, angle_index]:.2f}°",
        "below incident axis",
        "#6E58B6",
    )
    metrics_axis.text(
        0.04,
        0.05,
        f"E′ = {study.scattered_energy_kev[energy_index, angle_index]:.3f} keV   ·   K = {study.electron_kinetic_energy_kev[energy_index, angle_index]:.3f} keV",
        transform=metrics_axis.transAxes,
        color=TEXT,
        fontsize=7.8,
        weight="bold",
    )

    for axis, values, title, ylabel, ylim, yticks in (
        (shift_axis, study.fractional_wavelength_shift, "(a) Δλ/λ", "Fractional shift", (0, 4.12), None),
        (beta_axis, study.electron_beta, "(b) v/c", "Recoil speed", (0, 1), np.linspace(0, 1, 5)),
        (phi_axis, study.electron_recoil_angle_deg, "(c) φ", "Recoil angle (°)", (0, 92), (0, 30, 60, 90)),
    ):
        _plot_energy_curves(axis, study, values, linewidth=1.8)
        axis.axvline(90.0, color="#7C8FA5", linewidth=1.0, linestyle=(0, (3, 4)))
        axis.set(
            title=title,
            xlabel="Photon scattering angle, θ (°)",
            ylabel=ylabel,
            xlim=(0, 180),
            ylim=ylim,
            xticks=(0, 45, 90, 135, 180),
        )
        if yticks is not None:
            axis.set_yticks(yticks)
        _format_axes(axis)

    figure.suptitle(
        "Compton scattering · exact relativistic kinematics",
        x=0.055,
        y=0.95,
        ha="left",
        fontsize=21.5,
        fontweight="bold",
        color=TEXT,
    )
    figure.text(
        0.055,
        0.885,
        "BPhO Computational Challenge 2026 · Task 9 · five official incident energies · stationary free electron",
        color=MUTED,
        fontsize=10.3,
    )
    figure.text(
        0.965,
        0.89,
        f"{sum(check.passed for check in report.checks)}/{len(report.checks)} kinematic checks   ·   {sum(check.passed for check in cross_section_report.checks)}/{len(cross_section_report.checks)} extension checks",
        ha="right",
        color=MUTED,
        fontsize=9.0,
        fontstyle="italic",
    )
    figure.legend(
        handles=_energy_legend_handles(study),
        loc="lower center",
        bbox_to_anchor=(0.5, 0.012),
        ncol=5,
        fontsize=8.4,
        handlelength=3.1,
    )
    figure.text(
        0.055,
        0.075,
        "θ = 0°: zero electron momentum and undefined φ (the plots show its 90° limit) · θ = 180°: maximum shift and φ = 0°",
        color=MUTED,
        fontsize=7.4,
    )
    return figure


def _save_figure_set(
    figure: Figure,
    output_directory: Path,
    base_name: str,
    configuration: Task09Configuration,
) -> tuple[Path, Path, Path]:
    png_path = output_directory / f"{base_name}.png"
    svg_path = output_directory / f"{base_name}.svg"
    pdf_path = output_directory / f"{base_name}.pdf"
    figure.savefig(
        png_path,
        dpi=configuration.figure_dpi,
        metadata={"Software": "BPhO Task 9 deterministic renderer"},
    )
    figure.savefig(
        svg_path,
        metadata={"Date": None, "Creator": "BPhO Task 9 deterministic renderer"},
    )
    figure.savefig(
        pdf_path,
        metadata={
            "CreationDate": None,
            "ModDate": None,
            "Creator": "BPhO Task 9 deterministic renderer",
        },
    )
    plt.close(figure)
    return png_path, svg_path, pdf_path


def _verify_figure_files(
    paths: tuple[Path, ...],
    configuration: Task09Configuration,
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
                    if path.name == "task09_summary.png"
                    else (configuration.figure_width_px, configuration.figure_height_px)
                )
                dpi = image.info.get("dpi", (0.0, 0.0))
                if image.size != expected or image.format != "PNG":
                    raise ValueError(f"invalid PNG dimensions or format: {path.name}")
                if any(abs(float(value) - configuration.figure_dpi) > 0.1 for value in dpi):
                    raise ValueError(f"invalid PNG resolution metadata: {path.name}")
        elif path.suffix == ".svg":
            if not ET.parse(path).getroot().tag.endswith("svg"):
                raise ValueError(f"invalid SVG root: {path.name}")
            svg_text = path.read_text(encoding="utf-8")
            font_families = set(re.findall(r"font:[^;]+?'([^']+)'", svg_text))
            if font_families != {FIGURE_FONT_FAMILY}:
                raise ValueError(
                    f"SVG text font mismatch in {path.name}: {sorted(font_families)}"
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


def generate_task09_figures(
    study: Task09StudyResult,
    report: Task09ValidationReport,
    cross_section_study: KleinNishinaStudy,
    cross_section_report: CrossSectionValidationReport,
    output_directory: Path,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> tuple[Path, ...]:
    """Generate and verify all four approved PNG/SVG/PDF figure sets."""

    _require_validated(study, report, cross_section_study, cross_section_report)
    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    _require_figure_font()
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    builders = (
        (FIGURE_BASE_NAMES[0], lambda: _make_required_kinematics(study, configuration)),
        (FIGURE_BASE_NAMES[1], lambda: _make_energy_transfer_geometry(study, configuration)),
        (
            FIGURE_BASE_NAMES[2],
            lambda: _make_klein_nishina_extension(study, cross_section_study, configuration),
        ),
        (
            FIGURE_BASE_NAMES[3],
            lambda: _make_summary(study, report, cross_section_report, configuration),
        ),
    )
    generated: list[Path] = []
    with plt.rc_context(PLOT_STYLE):
        for base_name, builder in builders:
            generated.extend(
                _save_figure_set(builder(), directory, base_name, configuration)
            )
    paths = tuple(generated)
    _verify_figure_files(paths, configuration)
    return paths


__all__ = [
    "FIGURE_BASE_NAMES",
    "FIGURE_FILENAMES",
    "FIGURE_FONT_FAMILY",
    "generate_task09_figures",
]
