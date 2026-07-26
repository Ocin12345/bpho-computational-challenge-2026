"""Publication-quality figures built only from validated Task 6 records."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch
from PIL import Image

from task06_electron_diffraction.analysis import Task06StudyResult
from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    Task06Configuration,
)
from task06_electron_diffraction.validation import (
    Task06ValidationReport,
    task06_study_digest,
)


FIGURE_BASE_NAMES = (
    "electron_diffraction_rings",
    "ring_radius_vs_voltage",
    "straight_line_validation",
    "normalized_order_collapse",
    "wavelength_and_orders",
    "task06_summary",
)
FIGURE_FILENAMES = tuple(
    f"{base}.{extension}"
    for base in FIGURE_BASE_NAMES
    for extension in ("png", "svg")
)

TEXT_COLOUR = "#172033"
MUTED_TEXT = "#52627A"
GRID_COLOUR = "#CBD5E1"
FAMILY_COLOURS = ("#0072B2", "#D55E00")
FAMILY_SCREEN_COLOURS = ("#B7FF7A", "#61F5A1")
PASS_COLOUR = "#138A52"

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
    "svg.hashsalt": "bpho-task06-2026",
}


def _typeset_spacing_label(label: str) -> str:
    """Replace Unicode subscripts with portable mathtext for plot labels."""

    return label.replace("d₁", r"$d_1$").replace("d₂", r"$d_2$")


def _require_validated(
    study: Task06StudyResult,
    report: Task06ValidationReport,
) -> None:
    if not isinstance(study, Task06StudyResult):
        raise TypeError("study must be a Task06StudyResult")
    if not isinstance(report, Task06ValidationReport):
        raise TypeError("report must be a Task06ValidationReport")
    if not report.passed:
        raise RuntimeError("Task 6 figure generation requires a passing report")
    if report.study_digest != task06_study_digest(study):
        raise ValueError("report does not describe the supplied Task 6 study")


def _style_axes(axis: Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3.5, width=0.7)


def _figure_size(
    configuration: Task06Configuration,
    *,
    summary: bool = False,
) -> tuple[float, float]:
    width = configuration.summary_width_px if summary else configuration.figure_width_px
    height = configuration.summary_height_px if summary else configuration.figure_height_px
    return width / configuration.figure_dpi, height / configuration.figure_dpi


def _voltage_index(study: Task06StudyResult, voltage_v: float) -> int:
    matches = np.where(study.voltages_v == float(voltage_v))[0]
    if matches.size != 1:
        raise ValueError(f"voltage {voltage_v} V is not uniquely present")
    return int(matches[0])


def _screen_background(axis: Axes, radius_mm: float) -> None:
    coordinate = np.linspace(-radius_mm, radius_mm, 700, dtype=np.float64)
    xx, yy = np.meshgrid(coordinate, coordinate)
    radial = np.sqrt(np.square(xx) + np.square(yy)) / radius_mm
    inside = radial <= 1.0
    vignette = np.clip(1.0 - radial, 0.0, 1.0)
    centre = np.exp(-0.5 * np.square(radial / 0.055))
    image = np.zeros((coordinate.size, coordinate.size, 3), dtype=np.float64)
    image[..., 0] = inside * (0.006 + 0.025 * vignette + 0.30 * centre)
    image[..., 1] = inside * (0.045 + 0.19 * vignette + 0.92 * centre)
    image[..., 2] = inside * (0.018 + 0.055 * vignette + 0.40 * centre)
    axis.imshow(
        np.clip(image, 0.0, 1.0),
        extent=(-radius_mm, radius_mm, -radius_mm, radius_mm),
        origin="lower",
        interpolation="bilinear",
        zorder=0,
    )
    axis.add_patch(
        Circle(
            (0.0, 0.0),
            radius_mm,
            fill=False,
            edgecolor="#287C55",
            linewidth=1.2,
            alpha=0.9,
            zorder=1,
        )
    )


def _draw_screen_panel(
    axis: Axes,
    study: Task06StudyResult,
    configuration: Task06Configuration,
    voltage_v: float,
    *,
    compact: bool = False,
) -> None:
    voltage_index = _voltage_index(study, voltage_v)
    radius_mm = configuration.tube_radius_m * 1.0e3
    _screen_background(axis, radius_mm)
    for spacing_index in range(study.spacings_m.size):
        mask = (
            (study.voltage_indices == voltage_index)
            & (study.spacing_indices == spacing_index)
            & study.screen_visible_flags
        )
        rows = np.where(mask)[0]
        for row in rows:
            order = int(study.orders_n[row])
            ring_radius_mm = float(study.photo_radii_m[row] * 1.0e3)
            axis.add_patch(
                Circle(
                    (0.0, 0.0),
                    ring_radius_mm,
                    fill=False,
                    edgecolor=FAMILY_SCREEN_COLOURS[spacing_index],
                    linewidth=2.15 if order == 1 else 0.78,
                    linestyle="-" if spacing_index == 0 else (0, (4.0, 2.4)),
                    alpha=0.96 if order == 1 else 0.56,
                    zorder=3 if order == 1 else 2,
                )
            )
    axis.set_xlim(-radius_mm * 1.06, radius_mm * 1.06)
    axis.set_ylim(-radius_mm * 1.06, radius_mm * 1.06)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.grid(False)
    for spine in axis.spines.values():
        spine.set_visible(False)
    counts = study.maximum_screen_orders[voltage_index]
    first_order_values: list[float] = []
    for spacing_index in range(study.spacings_m.size):
        first = (
            (study.voltage_indices == voltage_index)
            & (study.spacing_indices == spacing_index)
            & (study.orders_n == 1)
        )
        first_order_values.append(float(study.photo_radii_m[first][0] * 1.0e3))
    axis.set_title(f"{voltage_v / 1000:.0f} kV", color=TEXT_COLOUR, pad=8)
    axis.text(
        0.5,
        0.025,
        (
            f"forward orders: {int(counts[0])} + {int(counts[1])}\n"
            f"$n=1$ radii: {first_order_values[0]:.1f} mm, "
            f"{first_order_values[1]:.1f} mm"
        ),
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=7.2 if compact else 9.0,
        color="#E8FFF0",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#07170E",
            "edgecolor": "#2A6B48",
            "alpha": 0.88,
        },
        zorder=5,
    )


def _make_ring_comparison(
    study: Task06StudyResult,
    configuration: Task06Configuration,
) -> Figure:
    figure, axes = plt.subplots(
        1,
        3,
        figsize=_figure_size(configuration),
        constrained_layout=True,
    )
    for axis, voltage in zip(axes, (1000.0, 3000.0, 5000.0)):
        _draw_screen_panel(axis, study, configuration, voltage)
    handles = (
        Line2D([0], [0], color=FAMILY_SCREEN_COLOURS[0], lw=2.2, label=_typeset_spacing_label(study.spacing_labels[0])),
        Line2D(
            [0],
            [0],
            color=FAMILY_SCREEN_COLOURS[1],
            lw=2.2,
            linestyle=(0, (4.0, 2.4)),
            label=_typeset_spacing_label(study.spacing_labels[1]),
        ),
    )
    figure.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.915))
    figure.suptitle(
        "Forward-screen electron-diffraction rings",
        fontsize=17,
        fontweight="bold",
        color=TEXT_COLOUR,
        y=0.992,
    )
    figure.text(
        0.5,
        0.008,
        "Exact spherical projection $x=r\\sin(2\\phi)$; line brightness and width are schematic, not predicted intensity.",
        ha="center",
        color=MUTED_TEXT,
        fontsize=10.5,
    )
    return figure


def _make_radius_voltage(
    study: Task06StudyResult,
    configuration: Task06Configuration,
) -> Figure:
    figure, axes = plt.subplots(
        1,
        2,
        figsize=_figure_size(configuration),
        sharey=True,
        constrained_layout=True,
    )
    for spacing_index, axis in enumerate(axes):
        maximum_order = int(np.max(study.maximum_screen_orders[:, spacing_index]))
        normalization = Normalize(vmin=1, vmax=maximum_order)
        colour_map = plt.get_cmap("viridis")
        for order in range(1, maximum_order + 1):
            mask = (
                (study.spacing_indices == spacing_index)
                & (study.orders_n == order)
                & study.screen_visible_flags
            )
            if not np.any(mask):
                continue
            voltage = study.voltages_v[study.voltage_indices[mask]] / 1000.0
            radius = study.photo_radii_m[mask] * 1000.0
            axis.plot(
                voltage,
                radius,
                color=colour_map(normalization(order)),
                linewidth=2.2 if order == 1 else 0.9,
                alpha=1.0 if order == 1 else 0.78,
            )
        axis.set_xlim(1.0, 5.0)
        axis.set_ylim(0.0, configuration.tube_radius_m * 1000.0 * 1.04)
        axis.set_xlabel("Accelerating voltage, $V$ (kV)")
        axis.set_title(_typeset_spacing_label(study.spacing_labels[spacing_index]))
        axis.text(
            0.03,
            0.97,
            f"forward-screen orders $n=1$–{maximum_order}",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9.5,
            color=MUTED_TEXT,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.82,
            },
        )
        _style_axes(axis)
        colour_bar = figure.colorbar(
            plt.cm.ScalarMappable(norm=normalization, cmap=colour_map),
            ax=axis,
            pad=0.02,
            fraction=0.045,
        )
        colour_bar.set_label("Diffraction order, $n$")
        colour_bar.set_ticks(sorted(set((1, maximum_order // 2, maximum_order))))
    axes[0].set_ylabel("Photographic ring radius, $x$ (mm)")
    figure.suptitle(
        "Exact projected ring radius across the 1–5 kV sweep",
        fontsize=18,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    return figure


def _make_straight_line_validation(
    study: Task06StudyResult,
    configuration: Task06Configuration,
) -> Figure:
    figure, axis = plt.subplots(
        figsize=_figure_size(configuration),
        constrained_layout=True,
    )
    for spacing_index, fit in enumerate(study.first_order_fits):
        mask = (study.spacing_indices == spacing_index) & (study.orders_n == 1)
        x = study.bragg_ratios_q[mask]
        voltage = study.voltages_v[study.voltage_indices[mask]]
        y = 1.0 / np.sqrt(voltage)
        line_x = np.linspace(0.0, float(np.max(x)) * 1.04, 300)
        axis.plot(
            line_x,
            fit.constrained_gradient_v_inv_sqrt * line_x,
            color=FAMILY_COLOURS[spacing_index],
            linewidth=2.6,
            label=(
                f"{_typeset_spacing_label(study.spacing_labels[spacing_index])}: "
                f"$d_{{fit}}={fit.recovered_spacing_m * 1e9:.6f}$ nm"
            ),
        )
        displayed = np.arange(0, x.size, 50, dtype=int)
        if displayed[-1] != x.size - 1:
            displayed = np.append(displayed, x.size - 1)
        axis.scatter(
            x[displayed],
            y[displayed],
            s=54,
            color=FAMILY_COLOURS[spacing_index],
            edgecolor="white",
            linewidth=0.9,
            zorder=3,
        )
        axis.text(
            float(np.max(x)) * 0.72,
            float(np.max(y)) * (0.80 if spacing_index == 0 else 0.54),
            (
                f"$k={fit.constrained_gradient_v_inv_sqrt:.9f}$ "
                "$\\mathrm{V^{-1/2}}$\n"
                f"$R^2={fit.r_squared:.12f}$"
            ),
            color=FAMILY_COLOURS[spacing_index],
            fontsize=10.5,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#D5DEE9"},
        )
    axis.set_xlim(left=0.0)
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel(r"$\sin(\phi/2)$")
    axis.set_ylabel(r"$1/\sqrt{V}$ ($\mathrm{V^{-1/2}}$)")
    axis.set_title(
        r"Official Task 6a check: $1/\sqrt{V}$ versus $\sin(\phi/2)$",
        pad=14,
    )
    axis.legend(loc="upper left", fontsize=10.5)
    axis.text(
        0.98,
        0.04,
        "Markers shown every 0.5 kV; fits use all 401 voltages.\n"
        r"$d=nhk/[2\sqrt{2m_\mathrm{e}e}]$, with $n=1$.",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=10.2,
        color=MUTED_TEXT,
    )
    _style_axes(axis)
    return figure


def _make_normalized_collapse(
    study: Task06StudyResult,
    configuration: Task06Configuration,
) -> Figure:
    figure, axis = plt.subplots(
        figsize=_figure_size(configuration),
        constrained_layout=True,
    )
    for spacing_index, fit in enumerate(study.normalized_fits):
        family = study.spacing_indices == spacing_index
        shown = family & (study.voltage_indices % 10 == 0)
        x = study.bragg_ratios_q[shown]
        voltage = study.voltages_v[study.voltage_indices[shown]]
        y = study.orders_n[shown].astype(np.float64) / np.sqrt(voltage)
        axis.scatter(
            x,
            y,
            s=11,
            alpha=0.23,
            color=FAMILY_COLOURS[spacing_index],
            edgecolors="none",
            label=(
                f"{_typeset_spacing_label(study.spacing_labels[spacing_index])} "
                f"({fit.point_count:,} fitted records)"
            ),
        )
        line_x = np.linspace(0.0, 1.0, 400)
        axis.plot(
            line_x,
            fit.constrained_gradient_v_inv_sqrt * line_x,
            color=FAMILY_COLOURS[spacing_index],
            linewidth=2.5,
        )
    axis.set_xlim(0.0, 1.02)
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel(r"$\sin(\phi/2)$")
    axis.set_ylabel(r"$n/\sqrt{V}$ ($\mathrm{V^{-1/2}}$)")
    axis.set_title("All diffraction orders collapse onto one line per spacing")
    axis.legend(loc="upper left", fontsize=10.5)
    axis.text(
        0.98,
        0.04,
        "Markers shown every 100 V; fits use every Bragg-allowed record.\n"
        "Normalization by $n$ removes the order-dependent gradient.",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=10.2,
        color=MUTED_TEXT,
    )
    _style_axes(axis)
    return figure


def _make_wavelength_orders(
    study: Task06StudyResult,
    configuration: Task06Configuration,
) -> Figure:
    figure, axes = plt.subplots(
        1,
        2,
        figsize=_figure_size(configuration),
        constrained_layout=True,
    )
    voltage_kv = study.voltages_v / 1000.0
    wavelength_pm = study.wavelengths_m * 1.0e12
    axes[0].plot(voltage_kv, wavelength_pm, color="#5B3CC4", linewidth=2.8)
    axes[0].scatter(
        [voltage_kv[0], voltage_kv[-1]],
        [wavelength_pm[0], wavelength_pm[-1]],
        s=62,
        color="#5B3CC4",
        edgecolor="white",
        linewidth=0.9,
        zorder=3,
    )
    axes[0].annotate(
        f"{wavelength_pm[0]:.3f} pm",
        (voltage_kv[0], wavelength_pm[0]),
        xytext=(1.28, wavelength_pm[0] - 1.5),
        arrowprops={"arrowstyle": "->", "color": MUTED_TEXT},
    )
    axes[0].annotate(
        f"{wavelength_pm[-1]:.3f} pm",
        (voltage_kv[-1], wavelength_pm[-1]),
        xytext=(4.05, wavelength_pm[-1] + 4.2),
        arrowprops={"arrowstyle": "->", "color": MUTED_TEXT},
    )
    axes[0].set_xlabel("Accelerating voltage, $V$ (kV)")
    axes[0].set_ylabel("Electron wavelength, $\lambda$ (pm)")
    axes[0].set_title(
        "de Broglie wavelength\n" + r"$\lambda\propto V^{-1/2}$",
        fontsize=13.5,
        pad=9,
    )
    _style_axes(axes[0])

    for spacing_index in range(study.spacings_m.size):
        colour = FAMILY_COLOURS[spacing_index]
        axes[1].step(
            voltage_kv,
            study.maximum_bragg_orders[:, spacing_index],
            where="post",
            color=colour,
            linewidth=2.0,
            label=f"{_typeset_spacing_label(study.spacing_labels[spacing_index])}: Bragg maximum",
        )
        axes[1].step(
            voltage_kv,
            study.maximum_screen_orders[:, spacing_index],
            where="post",
            color=colour,
            linewidth=1.8,
            linestyle="--",
            label=f"{_typeset_spacing_label(study.spacing_labels[spacing_index])}: forward screen",
        )
    axes[1].set_xlabel("Accelerating voltage, $V$ (kV)")
    axes[1].set_ylabel("Maximum integer order")
    axes[1].set_title(
        "Maximum diffraction orders\nBragg allowed vs forward screen",
        fontsize=13.5,
        pad=9,
    )
    axes[1].legend(loc="upper left", fontsize=8.9)
    axes[1].set_ylim(bottom=0.0)
    _style_axes(axes[1])
    return figure


def _make_summary(
    study: Task06StudyResult,
    report: Task06ValidationReport,
    configuration: Task06Configuration,
) -> Figure:
    figure = plt.figure(
        figsize=_figure_size(configuration, summary=True),
        constrained_layout=True,
    )
    grid = figure.add_gridspec(2, 2, width_ratios=(0.9, 1.45), height_ratios=(1.0, 0.62))
    screen_axis = figure.add_subplot(grid[:, 0])
    validation_axis = figure.add_subplot(grid[0, 1])
    result_axis = figure.add_subplot(grid[1, 1])

    _draw_screen_panel(screen_axis, study, configuration, 3000.0, compact=True)
    screen_axis.set_title("Geometric rings at 3 kV", fontsize=12.5, color=TEXT_COLOUR)

    for spacing_index, fit in enumerate(study.first_order_fits):
        mask = (study.spacing_indices == spacing_index) & (study.orders_n == 1)
        x = study.bragg_ratios_q[mask]
        y = 1.0 / np.sqrt(study.voltages_v[study.voltage_indices[mask]])
        shown = np.arange(0, x.size, 50, dtype=int)
        validation_axis.scatter(
            x[shown],
            y[shown],
            s=25,
            color=FAMILY_COLOURS[spacing_index],
            edgecolor="white",
            linewidth=0.5,
        )
        line_x = np.linspace(0.0, float(np.max(x)) * 1.04, 200)
        validation_axis.plot(
            line_x,
            fit.constrained_gradient_v_inv_sqrt * line_x,
            color=FAMILY_COLOURS[spacing_index],
            linewidth=2.0,
            label=f"{_typeset_spacing_label(study.spacing_labels[spacing_index])} → {fit.recovered_spacing_m * 1e9:.3f} nm",
        )
    validation_axis.set_xlabel(r"$\sin(\phi/2)$", fontsize=9.5)
    validation_axis.set_ylabel(r"$1/\sqrt{V}$ ($\mathrm{V^{-1/2}}$)", fontsize=9.5)
    validation_axis.set_title("Required straight-line validation", fontsize=12.5)
    validation_axis.legend(fontsize=7.4, loc="upper left")
    validation_axis.tick_params(labelsize=8)
    _style_axes(validation_axis)

    result_axis.axis("off")
    result_axis.set_xlim(0.0, 1.0)
    result_axis.set_ylim(0.0, 1.0)
    cards = (
        (0.02, 0.56, 0.29, 0.34, "Voltage sweep", "1–5 kV\n401 values", "#EEF2FF"),
        (0.35, 0.56, 0.29, 0.34, "Order catalogue", f"{study.catalogue_size:,} Bragg\n{study.forward_screen_count:,} forward", "#ECFDF5"),
        (0.68, 0.56, 0.29, 0.34, "Validation", f"{sum(c.passed for c in report.checks)}/{len(report.checks)} checks\npassed", "#FFF7ED"),
    )
    for x0, y0, width, height, heading, value, face in cards:
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
        result_axis.text(x0 + 0.02, y0 + height - 0.09, heading, fontsize=8.6, color=MUTED_TEXT, weight="bold")
        result_axis.text(x0 + 0.02, y0 + 0.08, value, fontsize=11.0, color=TEXT_COLOUR, weight="bold")
    result_axis.text(
        0.02,
        0.35,
        r"$\lambda=h/\sqrt{2m_\mathrm{e}eV}$   ·   $2d\sin\theta=n\lambda$   ·   $\phi=2\theta$   ·   $x=r\sin(2\phi)$",
        fontsize=10.0,
        color=TEXT_COLOUR,
        weight="bold",
    )
    result_axis.text(
        0.02,
        0.13,
        "The model predicts ring positions only. Ring brightness is schematic; no structure factor or detector-response data were supplied.",
        fontsize=8.9,
        color=MUTED_TEXT,
        wrap=True,
    )

    figure.suptitle(
        "Task 6 · Electron diffraction from graphite",
        fontsize=20,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    return figure


def _save_figure_pair(
    figure: Figure,
    output_directory: Path,
    base_name: str,
    configuration: Task06Configuration,
) -> tuple[Path, Path]:
    png_path = output_directory / f"{base_name}.png"
    svg_path = output_directory / f"{base_name}.svg"
    figure.savefig(
        png_path,
        dpi=configuration.figure_dpi,
        metadata={"Software": "BPhO Task 6 deterministic renderer"},
    )
    figure.savefig(
        svg_path,
        metadata={"Date": None, "Creator": "BPhO Task 6 deterministic renderer"},
    )
    plt.close(figure)
    return png_path, svg_path


def _verify_figure_files(
    paths: tuple[Path, ...],
    configuration: Task06Configuration,
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
                    if path.name == "task06_summary.png"
                    else (configuration.figure_width_px, configuration.figure_height_px)
                )
                if image.size != expected or image.format != "PNG":
                    raise ValueError(f"invalid PNG dimensions or format: {path.name}")
        else:
            root = ET.parse(path).getroot()
            if not root.tag.endswith("svg"):
                raise ValueError(f"invalid SVG root: {path.name}")
    if sum(path.stat().st_size for path in paths) > configuration.figure_size_budget_bytes:
        raise ValueError("figure package exceeds its size budget")


def generate_task06_figures(
    study: Task06StudyResult,
    report: Task06ValidationReport,
    output_directory: Path,
    configuration: Task06Configuration = DEFAULT_CONFIGURATION,
) -> tuple[Path, ...]:
    """Generate and verify all six approved PNG/SVG figure pairs."""

    _require_validated(study, report)
    if not isinstance(configuration, Task06Configuration):
        raise TypeError("configuration must be a Task06Configuration")
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    builders = (
        (FIGURE_BASE_NAMES[0], lambda: _make_ring_comparison(study, configuration)),
        (FIGURE_BASE_NAMES[1], lambda: _make_radius_voltage(study, configuration)),
        (FIGURE_BASE_NAMES[2], lambda: _make_straight_line_validation(study, configuration)),
        (FIGURE_BASE_NAMES[3], lambda: _make_normalized_collapse(study, configuration)),
        (FIGURE_BASE_NAMES[4], lambda: _make_wavelength_orders(study, configuration)),
        (FIGURE_BASE_NAMES[5], lambda: _make_summary(study, report, configuration)),
    )
    generated: list[Path] = []
    with plt.rc_context(PLOT_STYLE):
        for base_name, builder in builders:
            generated.extend(
                _save_figure_pair(
                    builder(),
                    directory,
                    base_name,
                    configuration,
                )
            )
    paths = tuple(generated)
    _verify_figure_files(paths, configuration)
    return paths


__all__ = [
    "FIGURE_BASE_NAMES",
    "FIGURE_FILENAMES",
    "generate_task06_figures",
]
