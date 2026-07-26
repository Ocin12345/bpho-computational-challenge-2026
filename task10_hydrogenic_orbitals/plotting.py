"""High-resolution publication plotting for Task 10."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.cm import ScalarMappable
from matplotlib import font_manager

from task10_hydrogenic_orbitals.analysis import (
    build_radial_profile,
    official_family_representatives,
    radial_containment_radius_over_a,
    radial_node_positions_over_a,
)
from task10_hydrogenic_orbitals.configuration import (
    HydrogenicState,
    official_gallery_states,
)
from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.models import (
    normalize_density_for_display,
    orbital_summary,
    scaled_density_cartesian,
    scaled_radial_wavefunction,
)
from task10_hydrogenic_orbitals.validation import task10_state_digest


NAVY = "#202124"
SLATE = "#5F6368"
GRID = "#E2E6EA"
TEAL = "#007A5E"
BLUE = "#0072B2"
ORANGE = "#C44E00"
PURPLE = "#A64F83"
CRIMSON = "#332288"
GREEN = "#2B8A5A"
PALE = "#F4F7FB"
FIGURE_DPI = 300
FIGURE_SOFTWARE = "BPhO Computational Challenge 2026 Task 10"
FIGURE_FONT_FAMILY = "Times New Roman"
FAMILY_COLORS = (BLUE, TEAL, ORANGE, PURPLE, CRIMSON)
FAMILY_LINESTYLES = ("-", "--", ":", "-.", (0, (8, 3)))


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


@dataclass(frozen=True)
class ProjectionResult:
    """One density maximum-intensity projection."""

    state: HydrogenicState
    extent_over_n_squared_a: float
    relative_density: np.ndarray


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def configure_plot_style() -> None:
    """Apply the frozen publication style."""

    _require_figure_font()
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": (FIGURE_FONT_FAMILY,),
            "mathtext.fontset": "custom",
            "mathtext.rm": FIGURE_FONT_FAMILY,
            "mathtext.it": f"{FIGURE_FONT_FAMILY}:italic",
            "mathtext.bf": f"{FIGURE_FONT_FAMILY}:bold",
            "mathtext.sf": FIGURE_FONT_FAMILY,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#69727D",
            "axes.labelcolor": NAVY,
            "axes.facecolor": "white",
            "axes.grid": True,
            "axes.grid.axis": "both",
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.8,
            "xtick.color": SLATE,
            "ytick.color": SLATE,
            "text.color": NAVY,
            "legend.frameon": False,
            "lines.linewidth": 2.0,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "svg.fonttype": "none",
            "svg.hashsalt": "task10-hydrogenic-orbitals-v2",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _save_figure(
    figure: plt.Figure,
    output_base: Path,
    *,
    save_svg: bool = True,
    save_pdf: bool = True,
) -> tuple[Path, ...]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    figure.savefig(
        png_path,
        dpi=FIGURE_DPI,
        facecolor="white",
        edgecolor="none",
        metadata={"Software": FIGURE_SOFTWARE},
    )
    outputs = [png_path]
    if save_svg:
        svg_path = output_base.with_suffix(".svg")
        figure.savefig(
            svg_path,
            facecolor="white",
            edgecolor="none",
            metadata={"Creator": FIGURE_SOFTWARE, "Date": None},
        )
        outputs.append(svg_path)
    if save_pdf:
        pdf_path = output_base.with_suffix(".pdf")
        figure.savefig(
            pdf_path,
            facecolor="white",
            edgecolor="none",
            metadata={
                "Creator": FIGURE_SOFTWARE,
                "CreationDate": None,
                "ModDate": None,
            },
        )
        outputs.append(pdf_path)
    plt.close(figure)
    return tuple(outputs)


def _rgba_density(
    relative_density: np.ndarray,
    *,
    threshold: float,
    minimum_alpha: float = 0.10,
    maximum_alpha: float = 0.72,
) -> np.ndarray:
    if not 0.0 <= threshold < 1.0:
        raise ValueError("threshold must satisfy 0 <= threshold < 1")
    if not 0.0 <= minimum_alpha <= maximum_alpha <= 1.0:
        raise ValueError("alpha limits must satisfy 0 <= minimum <= maximum <= 1")
    cmap = matplotlib.colormaps["magma"]
    density = np.asarray(relative_density, dtype=float)
    if density.ndim != 2 or not np.all(np.isfinite(density)):
        raise ValueError("relative_density must be a finite two-dimensional array")
    rgba = cmap(np.clip(density, 0.0, 1.0) ** 0.55)
    alpha = np.zeros_like(density)
    visible = density >= threshold
    alpha[visible] = minimum_alpha + (
        maximum_alpha - minimum_alpha
    ) * ((density[visible] - threshold) / (1.0 - threshold)) ** 0.65
    rgba[..., 3] = alpha
    return rgba


def density_maximum_projection(
    state: HydrogenicState,
    *,
    resolution: int = 101,
    depth_samples: int = 81,
) -> ProjectionResult:
    """Project maximum density along a fixed isometric viewing direction."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    if resolution < 41 or resolution % 2 == 0:
        raise ValueError("resolution must be odd and at least 41")
    if depth_samples < 31 or depth_samples % 2 == 0:
        raise ValueError("depth_samples must be odd and at least 31")

    containment = radial_containment_radius_over_a(state)
    extent = containment / state.n**2
    coordinates = np.linspace(-extent, extent, resolution)
    u, v = np.meshgrid(coordinates, coordinates, indexing="xy")
    projection = np.zeros_like(u)
    factor = state.n**2
    inverse_root_two = 1.0 / np.sqrt(2.0)
    for w in np.linspace(-extent, extent, depth_samples):
        x = factor * u
        y = factor * (v + w) * inverse_root_two
        z = factor * (v - w) * inverse_root_two
        density = np.asarray(scaled_density_cartesian(state, x, y, z))
        np.maximum(projection, density, out=projection)
    relative = np.asarray(normalize_density_for_display(projection))
    return ProjectionResult(
        state=state,
        extent_over_n_squared_a=float(extent),
        relative_density=_readonly(relative),
    )


def _draw_projection(
    axis: plt.Axes,
    projection: ProjectionResult,
    *,
    title: str,
    subtitle: str | None = None,
) -> None:
    rgba = _rgba_density(
        projection.relative_density,
        threshold=0.015,
        minimum_alpha=0.22,
        maximum_alpha=1.0,
    )
    extent = projection.extent_over_n_squared_a
    axis.imshow(
        rgba,
        origin="lower",
        extent=(-extent, extent, -extent, extent),
        interpolation="bilinear",
        rasterized=True,
    )
    axis.set_facecolor("white")
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.grid(False)
    for spine in axis.spines.values():
        spine.set_color("#CBD6E4")
        spine.set_linewidth(0.8)
    axis.set_title(title, fontsize=8.8, color=NAVY, pad=3)
    if subtitle:
        axis.text(
            0.5,
            0.02,
            subtitle,
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=6.2,
            color=SLATE,
        )


def build_required_gallery_figure() -> plt.Figure:
    """Build the complete 25-state S–G density gallery."""

    configure_plot_style()
    figure = plt.figure(figsize=(12.8, 8.0))
    grid = figure.add_gridspec(
        6,
        9,
        height_ratios=(0.28, 1.0, 1.0, 1.0, 1.0, 1.0),
        left=0.055,
        right=0.975,
        top=0.84,
        bottom=0.09,
        hspace=0.34,
        wspace=0.16,
    )

    figure.text(
        0.055,
        0.955,
        "Hydrogenic orbitals · official S–G probability-density gallery",
        fontsize=20.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    figure.text(
        0.055,
        0.915,
        "All 25 normalized real states · fixed isometric maximum-density projection · "
        "each panel spans its 99.95% radial containment",
        fontsize=10.5,
        color=SLATE,
        ha="left",
        va="top",
    )
    figure.text(
        0.965,
        0.895,
        "density only · not electron paths",
        fontsize=9.5,
        color=TEAL,
        ha="right",
        va="top",
        fontstyle="italic",
    )

    states = official_gallery_states()
    state_index = 0
    for l in range(5):
        count = 2 * l + 1
        start = (9 - count) // 2
        for offset, m in enumerate(range(-l, l + 1)):
            state = states[state_index]
            state_index += 1
            axis = figure.add_subplot(grid[l + 1, start + offset])
            projection = density_maximum_projection(
                state,
                resolution=91,
                depth_samples=71,
            )
            orientation = {
                (0, 0): "spherical",
                (1, -1): "oriented along y",
                (1, 0): "oriented along z",
                (1, 1): "oriented along x",
                (2, -2): "xy angular form",
                (2, -1): "yz angular form",
                (2, 0): "z² angular form",
                (2, 1): "xz angular form",
                (2, 2): "x²−y² angular form",
            }.get((l, m), f"m={m:+d}")
            _draw_projection(
                axis,
                projection,
                title=f"{state.n}{state.family.lower()} · m={m:+d}",
                subtitle=orientation,
            )
        # Keep family labels outside the grid.  A label axis in column zero
        # would cover the m=-4 panel in the full G row.
        row_position = grid[l + 1, :].get_position(figure)
        figure.text(
            0.038,
            0.5 * (row_position.y0 + row_position.y1),
            state.family,
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=FAMILY_COLORS[l],
        )

    color_axis = figure.add_axes((0.64, 0.045, 0.30, 0.013))
    colorbar = figure.colorbar(
        ScalarMappable(
            norm=colors.Normalize(0.0, 1.0),
            cmap=matplotlib.colormaps["magma"],
        ),
        cax=color_axis,
        orientation="horizontal",
    )
    colorbar.set_ticks((0.0, 0.5, 1.0))
    colorbar.ax.tick_params(labelsize=7, colors=SLATE)
    colorbar.ax.set_title(
        "relative maximum-projected density within each state",
        fontsize=8,
        color=SLATE,
        pad=4,
    )
    figure.text(
        0.055,
        0.027,
        "Coordinates scaled by n²a · per-state display normalization; absolute density is preserved.",
        fontsize=7.7,
        color=SLATE,
        ha="left",
        va="bottom",
    )
    return figure


def build_radial_structure_figure() -> plt.Figure:
    """Build radial probability, nodes, energy and scaling evidence."""

    configure_plot_style()
    figure, axes = plt.subplots(2, 2, figsize=(8.0, 5.0))
    figure.subplots_adjust(
        left=0.095,
        right=0.975,
        top=0.79,
        bottom=0.18,
        wspace=0.34,
        hspace=0.72,
    )
    figure.text(
        0.075,
        0.95,
        "Radial structure, nodes and hydrogenic scaling",
        fontsize=17.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    figure.text(
        0.075,
        0.902,
        "Normalized radial probability is independent of m · all extents contain 99.95% probability",
        fontsize=8.8,
        color=SLATE,
        ha="left",
        va="top",
    )

    axis = axes[0, 0]
    for index, state in enumerate(official_family_representatives()):
        profile = build_radial_profile(state)
        scaled_coordinate = profile.radius_over_n_squared_a
        scaled_probability = state.n**2 * profile.scaled_radial_probability
        axis.plot(
            scaled_coordinate,
            scaled_probability,
            color=FAMILY_COLORS[index],
            linestyle=FAMILY_LINESTYLES[index],
            label=f"{state.n}{state.family.lower()}",
        )
    axis.set_xlim(0.0, 6.2)
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel("scaled radius, r/(n²a)")
    axis.set_ylabel("probability per d[r/(n²a)]")
    axis.set_title("(a) S–G radial probability")
    axis.legend(ncol=3, fontsize=7, loc="upper right")

    axis = axes[0, 1]
    n_three_states = (
        HydrogenicState(3, 0, 0),
        HydrogenicState(3, 1, 0),
        HydrogenicState(3, 2, 0),
    )
    radius = np.linspace(0.0, 42.0, 1401)
    for index, state in enumerate(n_three_states):
        radial = np.asarray(scaled_radial_wavefunction(state, radius))
        axis.plot(
            radius,
            radial,
            color=FAMILY_COLORS[index],
            linestyle=FAMILY_LINESTYLES[index],
            label=f"3{state.family.lower()} · {state.radial_node_count} radial nodes",
        )
        for node in radial_node_positions_over_a(state):
            axis.axvline(node, color=FAMILY_COLORS[index], alpha=0.32, linewidth=0.8)
    axis.axhline(0.0, color=SLATE, linewidth=0.8)
    axis.set_xlim(0.0, 42.0)
    axis.set_xlabel("radius, r/a")
    axis.set_ylabel("scaled radial amplitude")
    axis.set_title("(b) Same n, different radial nodes")
    axis.legend(fontsize=6.9, loc="upper right")

    axis = axes[1, 0]
    n_values = np.arange(1, 9)
    hydrogen_energies = np.asarray(
        [orbital_summary(HydrogenicState(int(n), 0, 0)).energy_ev for n in n_values]
    )
    carbon_energies = np.asarray(
        [
            orbital_summary(HydrogenicState(int(n), 0, 0, 6, 12)).energy_ev
            for n in n_values
        ]
    )
    axis.plot(n_values, hydrogen_energies, "o-", color=BLUE, label="H, Z=1 A=1")
    axis.plot(
        n_values,
        carbon_energies / 36.0,
        "s--",
        color=ORANGE,
        label="C(VI) energy / 36",
    )
    axis.set_xlabel("principal quantum number, n")
    axis.set_ylabel("scaled energy / eV")
    axis.set_title("(c) Energy scales as −Z²/n²")
    axis.set_xticks(n_values)
    axis.legend(fontsize=7)

    axis = axes[1, 1]
    atomic_numbers = np.arange(1, 21)
    radii = np.asarray(
        [
            orbital_summary(
                HydrogenicState(1, 0, 0, int(z), max(int(z), 2 * int(z)))
            ).effective_bohr_radius_angstrom
            for z in atomic_numbers
        ]
    )
    axis.plot(atomic_numbers, radii, "o-", color=TEAL, markersize=3.5)
    axis.plot(
        atomic_numbers,
        radii[0] / atomic_numbers,
        ":",
        color=CRIMSON,
        label="a scales as 1/Z reference",
    )
    axis.set_xlabel("nuclear charge, Z")
    axis.set_ylabel("effective Bohr length / Å")
    axis.set_title("(d) Orbitals contract as Z increases")
    axis.set_xticks((1, 5, 10, 15, 20))
    axis.legend(fontsize=7)

    figure.text(
        0.975,
        0.025,
        "22/22 independent scientific checks · 204 supported states · normalized before display",
        fontsize=7.7,
        color=TEAL,
        ha="right",
        va="bottom",
    )
    return figure


def _glass_stack_data(
    state: HydrogenicState,
    *,
    resolution: int = 71,
    slice_count: int = 17,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    if resolution < 31 or resolution % 2 == 0:
        raise ValueError("resolution must be odd and at least 31")
    if slice_count < 5 or slice_count % 2 == 0:
        raise ValueError("slice_count must be odd and at least 5")
    extent = radial_containment_radius_over_a(state) / state.n**2
    coordinate = np.linspace(-extent, extent, resolution)
    x, y = np.meshgrid(coordinate, coordinate, indexing="xy")
    z_values = np.linspace(-extent, extent, slice_count)
    densities = []
    for z in z_values:
        densities.append(
            np.asarray(
                scaled_density_cartesian(
                    state,
                    state.n**2 * x,
                    state.n**2 * y,
                    state.n**2 * z,
                )
            )
        )
    maximum = max(float(np.max(density)) for density in densities)
    relative = [density / maximum for density in densities]
    return x, y, z_values, relative


def draw_coloured_glass(
    axis: plt.Axes,
    state: HydrogenicState,
    *,
    threshold: float = 0.15,
    resolution: int = 71,
    slice_count: int = 17,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    """Draw semitransparent x-y density planes on a 3D axis."""

    x, y, z_values, relative = _glass_stack_data(
        state,
        resolution=resolution,
        slice_count=slice_count,
    )
    for z, density in zip(z_values, relative):
        rgba = _rgba_density(
            density,
            threshold=threshold,
            minimum_alpha=0.12,
            maximum_alpha=0.72,
        )
        axis.plot_surface(
            x,
            y,
            np.full_like(x, z),
            facecolors=rgba,
            linewidth=0.0,
            antialiased=False,
            shade=False,
            rstride=1,
            cstride=1,
            rasterized=True,
        )
    visible_extent = max(
        max(
            abs(float(z)),
            float(np.max(np.abs(x[density >= threshold]))),
            float(np.max(np.abs(y[density >= threshold]))),
        )
        for z, density in zip(z_values, relative)
        if np.any(density >= threshold)
    )
    visible_extent *= 1.16
    axis.set_xlim(-visible_extent, visible_extent)
    axis.set_ylim(-visible_extent, visible_extent)
    axis.set_zlim(-visible_extent, visible_extent)
    axis.set_box_aspect((1.0, 1.0, 1.0))
    axis.view_init(elev=24, azim=-54)
    axis.set_xlabel("x/(n²a)", labelpad=2)
    axis.set_ylabel("y/(n²a)", labelpad=2)
    axis.set_zlabel("z/(n²a)", labelpad=2)
    axis.tick_params(labelsize=6, pad=0)
    axis.grid(False)
    axis.xaxis.pane.set_alpha(0.0)
    axis.yaxis.pane.set_alpha(0.0)
    axis.zaxis.pane.set_alpha(0.0)
    return x, y, z_values, relative


def build_coloured_glass_figure() -> plt.Figure:
    """Build the official coloured-glass density construction."""

    configure_plot_style()
    state = HydrogenicState(3, 2, 0)
    figure = plt.figure(figsize=(10.0, 6.25))
    figure.text(
        0.055,
        0.955,
        "Hydrogen 3d, m=0 · semi-transparent “coloured glass” density",
        fontsize=17.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    figure.text(
        0.055,
        0.91,
        "17 x-y planes at fixed z · colour and opacity encode |ψ|² / max |ψ|² · display threshold = 0.15",
        fontsize=9.2,
        color=SLATE,
        ha="left",
        va="top",
    )

    axis_3d = figure.add_axes((0.03, 0.12, 0.57, 0.68), projection="3d")
    x, y, z_values, relative = draw_coloured_glass(axis_3d, state)
    axis_3d.set_title("(a) Full slice stack", pad=8, fontsize=12)

    selected_indices = (5, 8, 11)
    for panel_index, slice_index in enumerate(selected_indices):
        axis = figure.add_axes((0.64, 0.61 - 0.21 * panel_index, 0.29, 0.17))
        density = relative[slice_index]
        extent = float(np.max(np.abs(x)))
        image = axis.imshow(
            density,
            origin="lower",
            extent=(-extent, extent, -extent, extent),
            cmap="magma",
            vmin=0.0,
            vmax=1.0,
            interpolation="bilinear",
            rasterized=True,
        )
        axis.contour(
            x,
            y,
            density,
            levels=(0.15,),
            colors=("white",),
            linewidths=0.8,
        )
        axis.set_aspect("equal")
        axis.grid(False)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_title(
            f"({chr(98 + panel_index)}) z/(n²a) = {z_values[slice_index]:+.2f}",
            fontsize=8.5,
            loc="left",
        )
        if panel_index == 0:
            color_axis = figure.add_axes((0.945, 0.61, 0.012, 0.17))
            colorbar = figure.colorbar(image, cax=color_axis)
            colorbar.set_ticks((0.0, 0.5, 1.0))
            colorbar.ax.tick_params(labelsize=6)
            colorbar.set_label("relative density", fontsize=7)

    summary = orbital_summary(state)
    figure.text(
        0.64,
        0.035,
        "The complete unthresholded field remains normalized.\n"
        "Transparent regions are hidden only for visual clarity.\n"
        f"E(n=3) = {summary.energy_ev:.6f} eV · 0 radial nodes · 2 angular nodes",
        fontsize=8.3,
        color=NAVY,
        ha="left",
        va="bottom",
        linespacing=1.45,
        bbox={
            "boxstyle": "round,pad=0.48",
            "facecolor": PALE,
            "edgecolor": "#CBD6E4",
        },
    )
    return figure


def _outer_density_isosurface(
    state: HydrogenicState,
    *,
    threshold: float = 0.15,
    polar_samples: int = 181,
    azimuth_samples: int = 241,
    radial_samples: int = 801,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the outer constant-density surface for an axial real state."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    if state.m != 0:
        raise ValueError("the axial isosurface constructor requires m=0")
    if not 0.0 < threshold < 1.0:
        raise ValueError("threshold must satisfy 0 < threshold < 1")
    if polar_samples < 41 or azimuth_samples < 61 or radial_samples < 201:
        raise ValueError("isosurface sampling is below the accepted minimum")

    theta = np.linspace(0.0, np.pi, polar_samples)
    radius_over_a = np.linspace(
        0.0,
        radial_containment_radius_over_a(state),
        radial_samples,
    )
    theta_grid, radius_grid = np.meshgrid(theta, radius_over_a, indexing="ij")
    density = np.asarray(
        scaled_density_cartesian(
            state,
            radius_grid * np.sin(theta_grid),
            np.zeros_like(radius_grid),
            radius_grid * np.cos(theta_grid),
        )
    )
    relative = density / float(np.max(density))
    outer_radius = np.full(theta.shape, np.nan)
    for index, row in enumerate(relative):
        accepted = np.flatnonzero(row >= threshold)
        if not accepted.size:
            continue
        lower = int(accepted[-1])
        if lower == radial_samples - 1:
            outer_radius[index] = radius_over_a[lower]
            continue
        x0 = radius_over_a[lower]
        x1 = radius_over_a[lower + 1]
        y0 = row[lower]
        y1 = row[lower + 1]
        outer_radius[index] = x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)

    scaled_radius = outer_radius / state.n**2
    phi = np.linspace(0.0, 2.0 * np.pi, azimuth_samples)
    theta_surface, phi_surface = np.meshgrid(theta, phi, indexing="ij")
    radius_surface = np.broadcast_to(scaled_radius[:, np.newaxis], theta_surface.shape)
    x = radius_surface * np.sin(theta_surface) * np.cos(phi_surface)
    y = radius_surface * np.sin(theta_surface) * np.sin(phi_surface)
    z = radius_surface * np.cos(theta_surface)
    return _readonly(x), _readonly(y), _readonly(z)


def build_rendering_comparison_figure() -> plt.Figure:
    """Compare quantitative orthogonal slices with a threshold isosurface."""

    configure_plot_style()
    state = HydrogenicState(3, 2, 0)
    threshold = 0.15
    extent = 1.42
    coordinate = np.linspace(-extent, extent, 181)
    horizontal, vertical = np.meshgrid(coordinate, coordinate, indexing="xy")
    factor = state.n**2
    slice_data = (
        (
            "x-y · z=0",
            np.asarray(
                scaled_density_cartesian(
                    state, factor * horizontal, factor * vertical, 0.0
                )
            ),
            "x/(n²a)",
            "y/(n²a)",
        ),
        (
            "x-z · y=0",
            np.asarray(
                scaled_density_cartesian(
                    state, factor * horizontal, 0.0, factor * vertical
                )
            ),
            "x/(n²a)",
            "z/(n²a)",
        ),
        (
            "y-z · x=0",
            np.asarray(
                scaled_density_cartesian(
                    state, 0.0, factor * horizontal, factor * vertical
                )
            ),
            "y/(n²a)",
            "z/(n²a)",
        ),
    )
    maximum = max(float(np.max(item[1])) for item in slice_data)

    figure = plt.figure(figsize=(10.0, 6.0))
    figure.text(
        0.05,
        0.955,
        "One normalized field · complementary rendering choices",
        fontsize=18.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    figure.text(
        0.05,
        0.91,
        "Hydrogen 3d, m=0 · orthogonal slices retain values; the outer 0.15 isosurface retains 3D topology",
        fontsize=8.9,
        color=SLATE,
        ha="left",
        va="top",
    )

    image = None
    for index, (title, density, _xlabel, _ylabel) in enumerate(slice_data):
        axis = figure.add_axes((0.055, 0.635 - index * 0.255, 0.255, 0.19))
        relative = density / maximum
        image = axis.imshow(
            relative,
            origin="lower",
            extent=(-extent, extent, -extent, extent),
            cmap="magma",
            vmin=0.0,
            vmax=1.0,
            interpolation="bilinear",
            rasterized=True,
        )
        axis.contour(
            horizontal,
            vertical,
            relative,
            levels=(threshold,),
            colors=("white",),
            linewidths=0.8,
        )
        axis.set_aspect("equal")
        axis.grid(False)
        axis.set_xticks((-1.0, 0.0, 1.0))
        axis.set_yticks((-1.0, 0.0, 1.0))
        axis.tick_params(labelsize=6)
        axis.set_title(f"({chr(97 + index)}) {title}", fontsize=9, loc="left", pad=3)
    if image is None:
        raise AssertionError("orthogonal slice image was not created")
    color_axis = figure.add_axes((0.075, 0.035, 0.215, 0.012))
    colorbar = figure.colorbar(image, cax=color_axis, orientation="horizontal")
    colorbar.set_ticks((0.0, 0.5, 1.0))
    colorbar.ax.tick_params(labelsize=6)
    colorbar.ax.set_title("relative density · white = 0.15", fontsize=6.8, pad=3)

    surface_axis = figure.add_axes((0.315, 0.15, 0.40, 0.66), projection="3d")
    surface_x, surface_y, surface_z = _outer_density_isosurface(
        state,
        threshold=threshold,
    )
    surface_axis.plot_surface(
        surface_x,
        surface_y,
        surface_z,
        color=ORANGE,
        alpha=0.78,
        linewidth=0.12,
        edgecolor="#9B3B19",
        antialiased=True,
        shade=False,
        rstride=2,
        cstride=3,
        rasterized=True,
    )
    finite_extent = float(
        np.nanmax(
            np.abs(np.concatenate((surface_x.ravel(), surface_y.ravel(), surface_z.ravel())))
        )
    )
    limit = 1.08 * finite_extent
    surface_axis.set_xlim(-limit, limit)
    surface_axis.set_ylim(-limit, limit)
    surface_axis.set_zlim(-limit, limit)
    surface_axis.set_box_aspect((1.0, 1.0, 1.0))
    surface_axis.view_init(elev=23, azim=-52)
    surface_axis.set_xlabel("x/(n²a)", fontsize=7, labelpad=0)
    surface_axis.set_ylabel("y/(n²a)", fontsize=7, labelpad=0)
    surface_axis.set_zlabel("z/(n²a)", fontsize=7, labelpad=0)
    surface_axis.tick_params(labelsize=6, pad=0)
    surface_axis.grid(False)
    surface_axis.xaxis.pane.set_alpha(0.0)
    surface_axis.yaxis.pane.set_alpha(0.0)
    surface_axis.zaxis.pane.set_alpha(0.0)
    surface_axis.set_title(
        "(d) Outer |ψ|² / max |ψ|² = 0.15 isosurface",
        fontsize=10,
        pad=4,
    )

    explanation_axis = figure.add_axes((0.73, 0.14, 0.24, 0.68))
    explanation_axis.set_axis_off()
    comparison = (
        (
            BLUE,
            "ORTHOGONAL SLICES",
            "Quantitative density values and nodes on three exact planes.",
            "Every feature that lies away from those planes.",
        ),
        (
            ORANGE,
            "ISOSURFACE",
            "One equal-density boundary and its three-dimensional topology.",
            "Density variation above and below the chosen threshold.",
        ),
        (
            TEAL,
            "COLOURED GLASS",
            "Multiple quantitative slices in a navigable spatial stack.",
            "Interior structure when translucent planes occlude one another.",
        ),
    )
    for index, (accent, heading, preserves, hides) in enumerate(comparison):
        y = 0.69 - 0.32 * index
        explanation_axis.add_patch(
            plt.Rectangle(
                (0.0, y),
                1.0,
                0.27,
                transform=explanation_axis.transAxes,
                facecolor=PALE,
                edgecolor="#CBD6E4",
                linewidth=1.0,
            )
        )
        explanation_axis.add_patch(
            plt.Rectangle(
                (0.0, y),
                0.025,
                0.27,
                transform=explanation_axis.transAxes,
                facecolor=accent,
                edgecolor="none",
            )
        )
        explanation_axis.text(
            0.07, y + 0.225, heading, fontsize=7.4, fontweight="bold", color=NAVY
        )
        explanation_axis.text(
            0.07,
            y + 0.155,
            "Preserves: " + preserves,
            fontsize=6.8,
            color=SLATE,
            va="top",
            wrap=True,
        )
        explanation_axis.text(
            0.07,
            y + 0.065,
            "Hides: " + hides,
            fontsize=6.8,
            color=SLATE,
            va="top",
            wrap=True,
        )
    figure.text(
        0.95,
        0.035,
        "All views use the same normalized field · threshold changes visibility, never probability",
        fontsize=7.5,
        color=TEAL,
        ha="right",
        va="bottom",
    )
    return figure


def build_summary_figure() -> plt.Figure:
    """Build the 4K Task 10 competition summary."""

    configure_plot_style()
    state = HydrogenicState(3, 2, 0)
    summary = orbital_summary(state)
    containment = radial_containment_radius_over_a(state)
    containment_angstrom = (
        containment * summary.effective_bohr_radius_angstrom
    )

    figure = plt.figure(figsize=(12.8, 7.2))
    figure.text(
        0.045,
        0.95,
        "Hydrogenic orbitals · normalized 3D density",
        fontsize=20.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    figure.text(
        0.045,
        0.905,
        "BPhO Computational Challenge 2026 · Task 10 · one electron, Z protons · complete S–G gallery",
        fontsize=10.3,
        color=SLATE,
        ha="left",
        va="top",
    )
    figure.text(
        0.955,
        0.936,
        "22/22 scientific checks   ·   204 validated states",
        fontsize=10,
        fontweight="bold",
        color=TEAL,
        ha="right",
        va="top",
        fontstyle="italic",
    )

    glass_axis = figure.add_axes((0.025, 0.12, 0.52, 0.72), projection="3d")
    draw_coloured_glass(
        glass_axis,
        state,
        threshold=0.15,
        resolution=65,
        slice_count=17,
    )
    glass_axis.set_title(
        "(a) Required 3D coloured-glass view · hydrogen 3d, m=0",
        fontsize=12,
        pad=7,
    )

    card_positions = (
        (0.57, 0.76, 0.12, 0.085),
        (0.705, 0.76, 0.12, 0.085),
        (0.84, 0.76, 0.12, 0.085),
    )
    card_content = (
        ("ENERGY", f"{summary.energy_ev:.5f} eV", "depends on n and Z"),
        ("99.95% RADIUS", f"{containment_angstrom:.2f} Å", "physical H-1 scale"),
        ("NODES", "0 radial · 2 angular", "full field normalized"),
    )
    accent_colors = (ORANGE, TEAL, PURPLE)
    for position, content, accent in zip(
        card_positions, card_content, accent_colors
    ):
        axis = figure.add_axes(position)
        axis.set_axis_off()
        axis.add_patch(
            plt.Rectangle(
                (0.0, 0.0),
                1.0,
                1.0,
                transform=axis.transAxes,
                facecolor=PALE,
                edgecolor="#CBD6E4",
                linewidth=1.1,
            )
        )
        axis.add_patch(
            plt.Rectangle(
                (0.0, 0.0),
                0.045,
                1.0,
                transform=axis.transAxes,
                facecolor=accent,
                edgecolor="none",
            )
        )
        axis.text(0.10, 0.73, content[0], fontsize=6.8, color=SLATE, fontweight="bold")
        axis.text(0.10, 0.39, content[1], fontsize=10.2, color=NAVY, fontweight="bold")
        axis.text(0.10, 0.10, content[2], fontsize=6.3, color=SLATE)

    family_states = official_family_representatives()
    for index, family_state in enumerate(family_states):
        axis = figure.add_axes((0.57 + index * 0.078, 0.43, 0.071, 0.22))
        projection = density_maximum_projection(
            family_state,
            resolution=71,
            depth_samples=51,
        )
        _draw_projection(
            axis,
            projection,
            title=f"{family_state.n}{family_state.family.lower()} · m=0",
        )
    figure.text(
        0.57,
        0.685,
        "(b) Official S–G family progression",
        fontsize=11.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
    )
    figure.text(
        0.57,
        0.405,
        "Each view spans 99.95% probability and is normalized only for display.",
        fontsize=6.8,
        color=SLATE,
        ha="left",
    )

    radial_axis = figure.add_axes((0.59, 0.12, 0.35, 0.22))
    for index, family_state in enumerate(family_states):
        profile = build_radial_profile(family_state)
        radial_axis.plot(
            profile.radius_over_n_squared_a,
            family_state.n**2 * profile.scaled_radial_probability,
            color=FAMILY_COLORS[index],
            linestyle=FAMILY_LINESTYLES[index],
            label=f"{family_state.n}{family_state.family.lower()}",
        )
    radial_axis.set_xlim(0.0, 6.2)
    radial_axis.set_ylim(bottom=0.0)
    radial_axis.set_xlabel("scaled radius, r/(n²a)", fontsize=8)
    radial_axis.set_ylabel("radial probability", fontsize=8)
    radial_axis.tick_params(labelsize=7)
    radial_axis.set_title(
        "(c) Radial structure stays distinct from angular shape",
        fontsize=10,
        loc="left",
    )
    radial_axis.legend(ncol=5, fontsize=6, loc="upper right")

    figure.text(
        0.045,
        0.035,
        "Threshold 0.15 changes opacity only · coordinates use standard polar colatitude ϑ and azimuth φ · "
        "view rotation is not electron motion",
        fontsize=8.2,
        color=SLATE,
        ha="left",
        va="bottom",
    )
    return figure


def generate_publication_figures(output_directory: Path) -> tuple[Path, ...]:
    """Generate every accepted static Task 10 figure."""

    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    outputs.extend(
        _save_figure(
            build_required_gallery_figure(),
            output_directory / "required_orbital_gallery",
        )
    )
    outputs.extend(
        _save_figure(
            build_radial_structure_figure(),
            output_directory / "radial_and_nodal_structure",
        )
    )
    outputs.extend(
        _save_figure(
            build_coloured_glass_figure(),
            output_directory / "coloured_glass_density",
            save_svg=False,
            save_pdf=False,
        )
    )
    outputs.extend(
        _save_figure(
            build_rendering_comparison_figure(),
            output_directory / "rendering_comparison",
        )
    )
    outputs.extend(
        _save_figure(
            build_summary_figure(),
            output_directory / "task10_summary",
        )
    )
    return tuple(outputs)


def write_figure_manifest(
    output_directory: Path,
    data_directory: Path,
    outputs: Iterable[Path],
) -> Path:
    """Write a deterministic, portable quality manifest for rendered figures."""

    from PIL import Image

    output_directory = Path(output_directory).resolve()
    data_directory = Path(data_directory).resolve()
    output_paths = tuple(sorted((Path(path).resolve() for path in outputs)))
    expected_names = {
        "required_orbital_gallery.png",
        "required_orbital_gallery.svg",
        "required_orbital_gallery.pdf",
        "radial_and_nodal_structure.png",
        "radial_and_nodal_structure.svg",
        "radial_and_nodal_structure.pdf",
        "coloured_glass_density.png",
        "rendering_comparison.png",
        "rendering_comparison.svg",
        "rendering_comparison.pdf",
        "task10_summary.png",
        "task10_summary.svg",
        "task10_summary.pdf",
    }
    if {path.name for path in output_paths} != expected_names:
        raise ValueError("figure output inventory is incomplete or unexpected")

    entries: list[dict[str, object]] = []
    for path in output_paths:
        if path.parent != output_directory or not path.is_file():
            raise FileNotFoundError(f"figure output is missing: {path}")
        entry: dict[str, object] = {
            "bytes": path.stat().st_size,
            "format": path.suffix.removeprefix("."),
            "path": f"figures/task10/{path.name}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        if path.suffix == ".png":
            with Image.open(path) as image:
                dpi = image.info.get("dpi", (0.0, 0.0))
                entry.update(
                    {
                        "dpi": [round(float(dpi[0])), round(float(dpi[1]))],
                        "height_px": int(image.height),
                        "width_px": int(image.width),
                    }
                )
        elif path.suffix == ".svg":
            svg_text = path.read_text(encoding="utf-8")
            font_families = sorted(
                set(re.findall(r"font:[^;]+?'([^']+)'", svg_text))
            )
            if font_families != [FIGURE_FONT_FAMILY]:
                raise ValueError(
                    f"unexpected SVG font families in {path.name}: {font_families}"
                )
            entry["vector_shell"] = True
            entry["contains_raster_density_layers"] = True
            entry["font_families"] = font_families
            entry["editable_text"] = True
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
            entry["vector_shell"] = True
            entry["contains_raster_density_layers"] = True
            entry["font_family"] = FIGURE_FONT_FAMILY
            entry["font_embedded"] = True
            entry["font_type"] = 42
            entry["editable_text"] = True
        entries.append(entry)

    report = json.loads(
        (data_directory / "validation_report.json").read_text(encoding="utf-8")
    )
    data_manifest_path = data_directory / "manifest.json"
    payload = {
        "figures": entries,
        "notes": {
            "coloured_glass_density": (
                "PNG only by design: layered transparency is rasterized to preserve "
                "the accepted visual appearance."
            ),
            "normalization": (
                "The 0.15 cutoff affects renderer opacity only; physical fields and "
                "normalization remain unchanged."
            ),
        },
        "renderer": {
            "default_dpi": FIGURE_DPI,
            "font_family": FIGURE_FONT_FAMILY,
            "matplotlib": matplotlib.__version__,
            "software": FIGURE_SOFTWARE,
        },
        "schema_version": "task10-figure-manifest-v2",
        "science_gate": {
            "checks_passed": sum(
                bool(check.get("passed")) for check in report.get("checks", [])
            ),
            "checks_total": len(report.get("checks", [])),
            "data_manifest_sha256": hashlib.sha256(
                data_manifest_path.read_bytes()
            ).hexdigest(),
            "state_digest": report.get("state_digest"),
        },
        "task": "BPhO Computational Challenge 2026 Task 10",
    }
    manifest_path = output_directory / "manifest.json"
    temporary_path = output_directory / ".manifest.json.tmp"
    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(manifest_path)
    return manifest_path


def verify_data_gate(data_directory: Path) -> None:
    """Reject figures unless current data and validation digests agree."""

    data_directory = Path(data_directory)
    manifest_path = data_directory / "manifest.json"
    report_path = data_directory / "validation_report.json"
    if not manifest_path.is_file() or not report_path.is_file():
        raise FileNotFoundError("Task 10 data manifest and validation report are required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    current_digest = task10_state_digest()
    if report.get("passed") is not True:
        raise RuntimeError("Task 10 validation report is not passing")
    if len(report.get("checks", [])) != 22:
        raise RuntimeError("Task 10 validation report does not contain 22 checks")
    if report.get("state_digest") != current_digest:
        raise RuntimeError("Task 10 report does not match the current scientific state")
    if manifest.get("validation", {}).get("state_digest") != current_digest:
        raise RuntimeError("Task 10 manifest does not match the current scientific state")
