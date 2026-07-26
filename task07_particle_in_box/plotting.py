"""Competition-quality deterministic figures for Task 7."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from task07_particle_in_box.analysis import Task07StudyResult
from task07_particle_in_box.configuration import (
    DEFAULT_CONFIGURATION,
    Task07Configuration,
)
from task07_particle_in_box.constants import REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.validation import (
    Task07ValidationReport,
    task07_study_digest,
)


TEXT = "#172033"
MUTED = "#5C6B80"
GRID = "#D9E1EA"
PANEL = "#F7FAFC"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"
YELLOW = "#E6AB02"
COLOURS = (BLUE, ORANGE, GREEN, MAGENTA, YELLOW)
FIGURE_FONT_FAMILY = "Times New Roman"

FIGURE_BASE_NAMES = (
    "energy_spectrum",
    "probability_densities",
    "wavefunctions_and_density",
    "energy_level_wavefunctions",
    "uncertainty_principle",
    "task07_summary",
)
FIGURE_FILENAMES = tuple(
    f"{base_name}.{extension}"
    for base_name in FIGURE_BASE_NAMES
    for extension in ("png", "svg")
)

PLOT_STYLE = {
    "font.family": "serif",
    "font.serif": (FIGURE_FONT_FAMILY,),
    "mathtext.fontset": "custom",
    "mathtext.rm": FIGURE_FONT_FAMILY,
    "mathtext.it": f"{FIGURE_FONT_FAMILY}:italic",
    "mathtext.bf": f"{FIGURE_FONT_FAMILY}:bold",
    "mathtext.sf": FIGURE_FONT_FAMILY,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "axes.labelcolor": TEXT,
    "axes.edgecolor": "#AEB9C7",
    "axes.linewidth": 0.9,
    "axes.facecolor": "white",
    "axes.titlecolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "grid.alpha": 0.72,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "svg.hashsalt": "bpho-task07-v1",
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
    configuration: Task07Configuration,
    *,
    summary: bool = False,
) -> Figure:
    width = configuration.summary_width_px if summary else configuration.figure_width_px
    height = configuration.summary_height_px if summary else configuration.figure_height_px
    return plt.figure(
        figsize=(width / configuration.figure_dpi, height / configuration.figure_dpi),
        dpi=configuration.figure_dpi,
        facecolor="white",
    )


def _require_validated(
    study: Task07StudyResult,
    report: Task07ValidationReport,
) -> None:
    if not isinstance(study, Task07StudyResult):
        raise TypeError("study must be a Task07StudyResult")
    if not isinstance(report, Task07ValidationReport):
        raise TypeError("report must be a Task07ValidationReport")
    if not report.passed:
        raise RuntimeError("figures require a passing Task 7 validation report")
    if report.study_digest != task07_study_digest(study):
        raise ValueError("validation report belongs to a different Task 7 study")


def _format_axes(axis: plt.Axes, *, grid_axis: str = "both") -> None:
    axis.grid(True, axis=grid_axis)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)


def _make_energy_spectrum(
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        2,
        left=0.075,
        right=0.97,
        bottom=0.245,
        top=0.79,
        wspace=0.28,
        width_ratios=(1.25, 1.0),
    )
    spectrum = figure.add_subplot(grid[0, 0])
    spacing = figure.add_subplot(grid[0, 1])

    n = study.quantum_numbers
    energies = study.energies_ev
    spectrum.vlines(n, 0.0, energies, color=BLUE, linewidth=2.2, alpha=0.72)
    spectrum.scatter(
        n,
        energies,
        s=54,
        color=BLUE,
        edgecolor="white",
        linewidth=0.9,
        zorder=3,
        label="Allowed energy",
    )
    spectrum.set(
        title="Discrete energy spectrum",
        xlabel="Quantum number, $n$",
        ylabel="Energy, $E_n$ / eV",
        xlim=(0.5, configuration.maximum_quantum_number + 0.5),
        ylim=(0.0, float(energies[-1]) * 1.09),
        xticks=n,
    )
    _format_axes(spectrum)
    spectrum.text(
        0.04,
        0.94,
        rf"$E_1={energies[0]:.3f}\ \mathrm{{eV}}$",
        transform=spectrum.transAxes,
        va="top",
        color=TEXT,
        weight="bold",
    )
    spectrum.text(
        0.04,
        0.84,
        rf"$E_{{10}}={energies[-1]:.2f}\ \mathrm{{eV}}$",
        transform=spectrum.transAxes,
        va="top",
        color=MUTED,
    )

    delta = np.diff(energies)
    lower_n = n[:-1]
    spacing.bar(
        lower_n,
        delta,
        width=0.68,
        color=ORANGE,
        alpha=0.82,
        edgecolor="white",
        linewidth=0.8,
    )
    spacing.set(
        title="Adjacent levels separate as $n$ rises",
        xlabel=r"Transition $n\rightarrow n+1$",
        ylabel=r"Energy gap, $E_{n+1}-E_n$ / eV",
        xlim=(0.4, configuration.maximum_quantum_number - 0.4),
        xticks=lower_n,
    )
    spacing.set_xticklabels([rf"{value}$\to${value + 1}" for value in lower_n], rotation=38)
    _format_axes(spacing, grid_axis="y")
    spacing.text(
        0.04,
        0.94,
        r"$E_n/E_1=n^2$",
        transform=spacing.transAxes,
        ha="left",
        va="top",
        fontsize=14,
        weight="bold",
        color=ORANGE,
    )

    figure.suptitle(
        "Quantised energies in a 1.00 nm infinite well",
        fontsize=21,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.865,
        r"Electron model: $E_n=n^2\pi^2\hbar^2/(2m_\mathrm{e}a^2)$; markers emphasise that $n$ is discrete.",
        ha="center",
        color=MUTED,
        fontsize=11.5,
    )
    figure.text(
        0.5,
        0.045,
        r"The spectrum grows quadratically, while the successive energy gaps grow linearly: "
        r"$E_{n+1}-E_n=(2n+1)E_1$.",
        ha="center",
        color=MUTED,
        fontsize=10.5,
    )
    return figure


def _make_probability_densities(
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        2,
        2,
        left=0.075,
        right=0.97,
        bottom=0.18,
        top=0.78,
        hspace=0.62,
        wspace=0.22,
    )
    normalized_x = study.positions_m / configuration.box_width_m
    normalized_density = (
        configuration.box_width_m * study.probability_densities_m_inv
    )
    for index, n in enumerate(study.density_quantum_numbers):
        axis = figure.add_subplot(grid[index // 2, index % 2])
        colour = COLOURS[index]
        values = normalized_density[:, index]
        axis.plot(normalized_x, values, color=colour, linewidth=2.2)
        axis.fill_between(normalized_x, 0.0, values, color=colour, alpha=0.18)
        for node in np.arange(1, int(n), dtype=np.float64) / float(n):
            axis.axvline(node, color="#8290A3", linestyle=(0, (3, 3)), linewidth=0.9)
            axis.scatter([node], [0.0], s=24, color=TEXT, zorder=4, clip_on=False)
        axis.set(
            title=rf"$n={int(n)}$ · {int(n) - 1} interior node{'s' if n != 2 else ''}",
            xlabel=r"Normalized position, $x/a$",
            xlim=(0.0, 1.0),
            ylim=(0.0, 2.18),
            xticks=np.linspace(0.0, 1.0, 6),
            yticks=(0.0, 1.0, 2.0),
        )
        _format_axes(axis)
        axis.text(
            0.97,
            0.90,
            r"area $=1$",
            transform=axis.transAxes,
            ha="right",
            color=colour,
            weight="bold",
        )

    figure.suptitle(
        "First four stationary-state probability densities",
        fontsize=19.0,
        fontweight="bold",
        color=TEXT,
        y=0.965,
    )
    figure.text(
        0.5,
        0.875,
        r"$a|\psi_n|^2=2\sin^2(n\pi x/a)$ · each curve integrates to one and vanishes at both walls",
        ha="center",
        color=MUTED,
        fontsize=11.2,
    )
    figure.text(
        0.022,
        0.47,
        r"Normalized density, $a|\psi_n|^2$",
        ha="center",
        va="center",
        rotation=90,
        color=TEXT,
        fontsize=11.2,
    )
    figure.text(
        0.5,
        0.040,
        "Higher-energy states have more nodes, but every density remains symmetric about the centre of the box.",
        ha="center",
        color=MUTED,
        fontsize=10.5,
    )
    return figure


def _make_wavefunctions_and_density(
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        2,
        left=0.10,
        right=0.97,
        bottom=0.22,
        top=0.79,
        wspace=0.25,
    )
    wave_axis = figure.add_subplot(grid[0, 0])
    density_axis = figure.add_subplot(grid[0, 1])
    x = study.positions_m / configuration.box_width_m
    dimensionless_wavefunctions = (
        np.sqrt(configuration.box_width_m) * study.wavefunctions_m_neg_half
    )
    dimensionless_densities = (
        configuration.box_width_m * study.probability_densities_m_inv
    )

    for index, n in enumerate(study.density_quantum_numbers):
        label = rf"$n={int(n)}$"
        wave_axis.plot(
            x,
            dimensionless_wavefunctions[:, index],
            color=COLOURS[index],
            linewidth=2.0,
            label=label,
        )
        density_axis.plot(
            x,
            dimensionless_densities[:, index],
            color=COLOURS[index],
            linewidth=2.0,
            label=label,
        )
    wave_axis.axhline(0.0, color="#7D8898", linewidth=0.9)
    wave_axis.set(
        title="Signed wavefunction amplitude",
        xlabel=r"Normalized position, $x/a$",
        ylabel=r"Normalized amplitude, $√a\,\psi_n$",
        xlim=(0.0, 1.0),
        ylim=(-1.62, 1.62),
    )
    density_axis.set(
        title="Non-negative probability density",
        xlabel=r"Normalized position, $x/a$",
        ylabel=r"Normalized density, $a|\psi_n|^2$",
        xlim=(0.0, 1.0),
        ylim=(0.0, 2.18),
    )
    for axis in (wave_axis, density_axis):
        _format_axes(axis)
        axis.legend(ncol=2, loc="upper center")

    figure.suptitle(
        "Wavefunctions and Born probability densities",
        fontsize=19.5,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.86,
        r"The sign of $\psi$ controls interference; a position probability is obtained only after taking $|\psi|^2$.",
        ha="center",
        color=MUTED,
        fontsize=11.3,
    )
    figure.text(
        0.5,
        0.045,
        r"For a single energy eigenstate the phase $e^{-iE_nt/\hbar}$ changes with time, but $|\psi_n(x,t)|^2$ does not.",
        ha="center",
        color=MUTED,
        fontsize=10.5,
    )
    return figure


def _make_energy_level_wavefunctions(
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        2,
        left=0.07,
        right=0.965,
        bottom=0.20,
        top=0.78,
        wspace=0.20,
        width_ratios=(1.55, 0.78),
    )
    level_axis = figure.add_subplot(grid[0, 0])
    card_axis = figure.add_subplot(grid[0, 1])
    card_axis.axis("off")

    displayed_states = 5
    x = study.positions_m / configuration.box_width_m
    energy_ev = study.energies_ev[:displayed_states]
    dimensionless_wave = (
        np.sqrt(configuration.box_width_m)
        * np.column_stack(
            [
                np.sqrt(2.0) * np.sin(n * np.pi * x) / np.sqrt(configuration.box_width_m)
                for n in range(1, displayed_states + 1)
            ]
        )
    )
    amplitude = 0.70
    level_axis.axvspan(-0.10, 0.0, color="#DCE3EA", alpha=0.9)
    level_axis.axvspan(1.0, 1.10, color="#DCE3EA", alpha=0.9)
    level_axis.axvline(0.0, color=TEXT, linewidth=3.0)
    level_axis.axvline(1.0, color=TEXT, linewidth=3.0)
    for index in range(displayed_states):
        level = float(energy_ev[index])
        colour = COLOURS[index]
        shifted = level + amplitude * dimensionless_wave[:, index]
        level_axis.hlines(level, 0.0, 1.0, color=colour, linewidth=1.0, alpha=0.55)
        level_axis.plot(x, shifted, color=colour, linewidth=2.0)
        level_axis.fill_between(x, level, shifted, color=colour, alpha=0.16)
        level_axis.text(
            1.025,
            level,
            rf"$n={index + 1}$  ·  {level:.3g} eV",
            va="center",
            color=colour,
            weight="bold",
            fontsize=9.4,
        )
    level_axis.set(
        title="Eigenfunctions displayed at their allowed energies",
        xlabel=r"Normalized position, $x/a$",
        ylabel="Energy / eV",
        xlim=(-0.10, 1.25),
        ylim=(-0.55, float(energy_ev[-1]) + 1.25),
        xticks=(0.0, 0.25, 0.5, 0.75, 1.0),
    )
    _format_axes(level_axis, grid_axis="y")
    level_axis.text(-0.05, float(energy_ev[-1]) + 0.75, r"$V=∞$", ha="center", color=MUTED)
    level_axis.text(1.05, float(energy_ev[-1]) + 0.75, r"$V=∞$", ha="center", color=MUTED)

    cards = (
        (0.03, 0.70, 0.94, 0.23, "Boundary conditions", r"$\psi(0)=\psi(a)=0$", "#EAF3F9", BLUE),
        (
            0.03,
            0.39,
            0.94,
            0.23,
            "Energy scaling",
            r"$E_na^2/n^2=\mathrm{constant}$",
            "#FFF1E8",
            ORANGE,
        ),
        (0.03, 0.08, 0.94, 0.23, "Node count", r"$n-1$ interior nodes", "#EAF7F1", GREEN),
    )
    for x0, y0, width, height, heading, value, face, accent in cards:
        card_axis.add_patch(
            FancyBboxPatch(
                (x0, y0),
                width,
                height,
                boxstyle="round,pad=0.012,rounding_size=0.025",
                facecolor=face,
                edgecolor="#CBD5E1",
                linewidth=1.0,
            )
        )
        card_axis.text(x0 + 0.05, y0 + height - 0.065, heading, color=MUTED, weight="bold", fontsize=10)
        card_axis.text(x0 + 0.05, y0 + 0.065, value, color=accent, weight="bold", fontsize=13.2)
    card_axis.set_xlim(0.0, 1.0)
    card_axis.set_ylim(0.0, 1.0)

    figure.suptitle(
        "Infinite-well boundaries select standing waves",
        fontsize=19.8,
        fontweight="bold",
        color=TEXT,
        y=0.96,
    )
    figure.text(
        0.5,
        0.87,
        "Curves are vertically offset to their energy levels; their vertical wave amplitude is schematic.",
        ha="center",
        color=MUTED,
        fontsize=11.0,
    )
    figure.text(
        0.5,
        0.045,
        "The walls exclude the particle from the exterior and force an integer number of half-wavelengths into the box.",
        ha="center",
        color=MUTED,
        fontsize=10.4,
    )
    return figure


def _make_uncertainty_principle(
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration)
    grid = figure.add_gridspec(
        1,
        2,
        left=0.075,
        right=0.97,
        bottom=0.22,
        top=0.77,
        wspace=0.42,
    )
    components = figure.add_subplot(grid[0, 0])
    product = figure.add_subplot(grid[0, 1])
    n = study.quantum_numbers
    delta_x_over_a = study.position_uncertainties_m / configuration.box_width_m
    delta_p_a_over_hbar = (
        study.momentum_uncertainties_kg_m_s
        * configuration.box_width_m
        / REDUCED_PLANCK_CONSTANT_J_S
    )

    components.plot(
        n,
        delta_x_over_a,
        marker="o",
        color=BLUE,
        linewidth=2.0,
        label=r"$\Delta x/a$",
    )
    components.axhline(
        1.0 / math.sqrt(12.0),
        color=BLUE,
        linestyle=(0, (4, 3)),
        linewidth=1.1,
        alpha=0.7,
        label=r"large-$n$ limit $1/√12$",
    )
    components.set(
        title="Position and momentum uncertainties",
        xlabel="Quantum number, $n$",
        ylabel=r"Position, $\Delta x/a$",
        xlim=(0.5, configuration.maximum_quantum_number + 0.5),
        xticks=n,
        ylim=(0.15, 0.31),
    )
    _format_axes(components)
    components.legend(loc="lower right", fontsize=9.2)
    momentum_axis = components.twinx()
    momentum_axis.plot(
        n,
        delta_p_a_over_hbar,
        marker="s",
        color=ORANGE,
        linewidth=1.8,
        label=r"$a\Delta p/\hbar=n\pi$",
    )
    momentum_axis.set_ylabel(r"Momentum, $a\Delta p/\hbar$", color=ORANGE)
    momentum_axis.tick_params(axis="y", colors=ORANGE)
    momentum_axis.spines["top"].set_visible(False)
    momentum_axis.spines["right"].set_color(ORANGE)
    momentum_axis.legend(loc="upper left", fontsize=9.2, frameon=False)

    uncertainty = study.uncertainty_products_over_hbar
    product.plot(
        n,
        uncertainty,
        marker="o",
        markersize=6.0,
        color=GREEN,
        linewidth=2.2,
        label=r"$\Delta x\Delta p/\hbar$",
    )
    product.axhline(
        0.5,
        color=MAGENTA,
        linestyle=(0, (5, 3)),
        linewidth=2.0,
        label=r"Heisenberg bound $1/2$",
    )
    product.fill_between(n, 0.5, uncertainty, color=GREEN, alpha=0.10)
    product.scatter([1], [uncertainty[0]], s=70, color=GREEN, edgecolor="white", zorder=4)
    product.annotate(
        rf"ground state = {uncertainty[0]:.4f}$\hbar$",
        xy=(1, uncertainty[0]),
        xytext=(2.0, 1.35),
        arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1.0},
        color=TEXT,
        fontsize=10,
    )
    product.set(
        title="Uncertainty product and lower bound",
        xlabel="Quantum number, $n$",
        ylabel=r"Product, $\Delta x\Delta p/\hbar$",
        xlim=(0.5, configuration.maximum_quantum_number + 0.5),
        xticks=n,
        ylim=(0.0, float(uncertainty[-1]) * 1.10),
    )
    _format_axes(product)
    product.legend(loc="upper left", fontsize=9.4)

    figure.suptitle(
        "Heisenberg uncertainty in the particle-in-a-box",
        fontsize=19.5,
        fontweight="bold",
        color=TEXT,
        y=0.955,
    )
    figure.text(
        0.5,
        0.86,
        r"$ΔxΔp/\hbar=√(n^2π^2/12−1/2)≥1/2$",
        ha="center",
        color=MUTED,
        fontsize=12.5,
    )
    figure.text(
        0.5,
        0.045,
        "The ground state gives the smallest product; momentum uncertainty then grows with quantum number.",
        ha="center",
        color=MUTED,
        fontsize=10.2,
    )
    return figure


def _make_summary(
    study: Task07StudyResult,
    report: Task07ValidationReport,
    configuration: Task07Configuration,
) -> Figure:
    figure = _figure(configuration, summary=True)
    grid = figure.add_gridspec(
        2,
        3,
        left=0.055,
        right=0.97,
        bottom=0.15,
        top=0.82,
        hspace=0.38,
        wspace=0.28,
        width_ratios=(1.25, 1.0, 0.92),
    )
    density_axis = figure.add_subplot(grid[:, 0])
    energy_axis = figure.add_subplot(grid[0, 1])
    uncertainty_axis = figure.add_subplot(grid[1, 1])
    result_axis = figure.add_subplot(grid[:, 2])
    result_axis.axis("off")

    x = study.positions_m / configuration.box_width_m
    densities = configuration.box_width_m * study.probability_densities_m_inv
    for index, n in enumerate(study.density_quantum_numbers):
        density_axis.plot(
            x,
            densities[:, index],
            color=COLOURS[index],
            linewidth=2.1,
            label=rf"$n={int(n)}$",
        )
    density_axis.set(
        title="Stationary probability densities",
        xlabel=r"Normalized position, $x/a$",
        ylabel=r"$a|\psi_n|^2$",
        xlim=(0.0, 1.0),
        ylim=(0.0, 2.18),
    )
    _format_axes(density_axis)
    density_axis.legend(ncol=2, loc="upper center")

    energy_axis.vlines(
        study.quantum_numbers,
        0.0,
        study.energies_ev,
        color=BLUE,
        linewidth=1.9,
        alpha=0.7,
    )
    energy_axis.scatter(study.quantum_numbers, study.energies_ev, color=BLUE, s=32, zorder=3)
    energy_axis.set(
        title=r"Quantised energy: $E_n/E_1=n^2$",
        xlabel="$n$",
        ylabel="$E_n$ / eV",
        xticks=study.quantum_numbers,
        xlim=(0.5, 10.5),
        ylim=(0.0, float(study.energies_ev[-1]) * 1.08),
    )
    _format_axes(energy_axis)

    uncertainty_axis.plot(
        study.quantum_numbers,
        study.uncertainty_products_over_hbar,
        color=GREEN,
        marker="o",
        linewidth=2.0,
    )
    uncertainty_axis.axhline(0.5, color=MAGENTA, linestyle=(0, (5, 3)), linewidth=1.8)
    uncertainty_axis.set(
        title="Heisenberg product",
        xlabel="$n$",
        ylabel=r"$\Delta x\Delta p/\hbar$",
        xticks=study.quantum_numbers,
        xlim=(0.5, 10.5),
        ylim=(0.0, float(study.uncertainty_products_over_hbar[-1]) * 1.08),
    )
    _format_axes(uncertainty_axis)
    uncertainty_axis.text(
        0.96,
        0.12,
        r"bound $=0.5$",
        transform=uncertainty_axis.transAxes,
        ha="right",
        color=MAGENTA,
        weight="bold",
    )

    result_axis.text(0.03, 0.95, "MODEL", fontsize=10.5, color=MUTED, weight="bold")
    result_axis.text(
        0.03,
        0.87,
        r"$ψ_n=√(2/a)\sin(nπx/a)$",
        fontsize=15,
        color=TEXT,
        weight="bold",
    )
    result_axis.text(
        0.03,
        0.79,
        r"$E_n=n^2\pi^2\hbar^2/(2m_\mathrm{e}a^2)$",
        fontsize=13.5,
        color=TEXT,
        weight="bold",
    )
    cards = (
        (0.03, 0.56, 0.94, 0.15, "Ground energy", f"{study.ground_energy_ev:.6f} eV", "#EAF3F9", BLUE),
        (0.03, 0.36, 0.94, 0.15, "Ground uncertainty", f"{study.ground_uncertainty_over_hbar:.6f} ħ", "#EAF7F1", GREEN),
        (0.03, 0.16, 0.94, 0.15, "Numerical check", f"max error {np.max(study.numerical_relative_errors[-1]):.2e}", "#FFF1E8", ORANGE),
    )
    for x0, y0, width, height, heading, value, face, accent in cards:
        result_axis.add_patch(
            FancyBboxPatch(
                (x0, y0),
                width,
                height,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor=face,
                edgecolor="#CBD5E1",
                linewidth=1.0,
            )
        )
        result_axis.text(x0 + 0.05, y0 + height - 0.05, heading, color=MUTED, weight="bold", fontsize=10.0)
        result_axis.text(x0 + 0.05, y0 + 0.04, value, color=accent, weight="bold", fontsize=14.0)
    result_axis.add_patch(
        FancyBboxPatch(
            (0.15, 0.025),
            0.70,
            0.085,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor="#EAF7F1",
            edgecolor="#8BD0AA",
            linewidth=1.2,
        )
    )
    result_axis.text(
        0.50,
        0.067,
        f"{sum(check.passed for check in report.checks)}/{len(report.checks)} CHECKS PASS",
        ha="center",
        va="center",
        color=GREEN,
        fontsize=13.2,
        weight="bold",
    )
    result_axis.set_xlim(0.0, 1.0)
    result_axis.set_ylim(0.0, 1.0)

    figure.suptitle(
        "Task 7 · Particle in a one-dimensional box",
        fontsize=24,
        fontweight="bold",
        color=TEXT,
        y=0.965,
    )
    figure.text(
        0.5,
        0.875,
        "Infinite-wall boundary conditions create standing waves, discrete energies and unavoidable quantum uncertainty.",
        ha="center",
        color=MUTED,
        fontsize=13.0,
    )
    figure.text(
        0.055,
        0.025,
        "Electron · box width 1.00 nm · analytical solution independently checked by a 1600-point finite-difference eigensolver",
        color=MUTED,
        fontsize=10.0,
    )
    return figure


def _save_figure_pair(
    figure: Figure,
    output_directory: Path,
    base_name: str,
    configuration: Task07Configuration,
) -> tuple[Path, Path]:
    png_path = output_directory / f"{base_name}.png"
    svg_path = output_directory / f"{base_name}.svg"
    figure.savefig(
        png_path,
        dpi=configuration.figure_dpi,
        metadata={"Software": "BPhO Task 7 deterministic renderer"},
    )
    figure.savefig(
        svg_path,
        metadata={"Date": None, "Creator": "BPhO Task 7 deterministic renderer"},
    )
    plt.close(figure)
    return png_path, svg_path


def _verify_figure_files(
    paths: tuple[Path, ...],
    configuration: Task07Configuration,
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
                    if path.name == "task07_summary.png"
                    else (configuration.figure_width_px, configuration.figure_height_px)
                )
                if image.size != expected or image.format != "PNG":
                    raise ValueError(f"invalid PNG dimensions or format: {path.name}")
        else:
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
    if sum(path.stat().st_size for path in paths) > configuration.figure_size_budget_bytes:
        raise ValueError("figure package exceeds its size budget")


def generate_task07_figures(
    study: Task07StudyResult,
    report: Task07ValidationReport,
    output_directory: Path,
    configuration: Task07Configuration = DEFAULT_CONFIGURATION,
) -> tuple[Path, ...]:
    """Generate and verify all six approved PNG/SVG figure pairs."""

    _require_validated(study, report)
    if not isinstance(configuration, Task07Configuration):
        raise TypeError("configuration must be a Task07Configuration")
    _require_figure_font()
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    builders = (
        (FIGURE_BASE_NAMES[0], lambda: _make_energy_spectrum(study, configuration)),
        (FIGURE_BASE_NAMES[1], lambda: _make_probability_densities(study, configuration)),
        (FIGURE_BASE_NAMES[2], lambda: _make_wavefunctions_and_density(study, configuration)),
        (FIGURE_BASE_NAMES[3], lambda: _make_energy_level_wavefunctions(study, configuration)),
        (FIGURE_BASE_NAMES[4], lambda: _make_uncertainty_principle(study, configuration)),
        (FIGURE_BASE_NAMES[5], lambda: _make_summary(study, report, configuration)),
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
    "generate_task07_figures",
]
