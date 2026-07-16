"""Publication-quality figures built only from validated Task 3 results."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from task03_thermal_radiation.analysis import (
    EinsteinStudyResult,
    PlanckStudyResult,
)
from task03_thermal_radiation.constants import MOLAR_GAS_CONSTANT_J_MOL_K
from task03_thermal_radiation.generate_task03 import (
    DEFAULT_FIGURE_DIRECTORY,
    FIGURE_FILENAMES,
)
from task03_thermal_radiation.validation import (
    Task03ValidationReport,
    validate_task03,
)


FIGURE_DPI = 180
REGULAR_FIGURE_SIZE_IN = (8.4, 5.2)
WIDE_FIGURE_SIZE_IN = (10.4, 5.2)
SUMMARY_FIGURE_SIZE_IN = (2400 / FIGURE_DPI, 1350 / FIGURE_DPI)

PLANCK_COLOURS = ("#3B4CC0", "#E68613", "#B40426")
MATERIAL_COLOURS = (
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#D55E00",
    "#56B4E9",
    "#222222",
)
VALIDATION_COLOURS = ("#0072B2", "#D55E00")
PASS_COLOUR = "#14804A"
GRID_COLOUR = "#CBD5E1"
TEXT_COLOUR = "#172033"

PLOT_STYLE: dict[str, object] = {
    "font.family": "DejaVu Sans",
    "font.size": 10.0,
    "axes.titlesize": 13.0,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "axes.labelcolor": TEXT_COLOUR,
    "axes.edgecolor": "#64748B",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID_COLOUR,
    "grid.alpha": 0.6,
    "grid.linewidth": 0.7,
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "legend.frameon": False,
    "legend.fontsize": 9.0,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.edgecolor": "white",
    "svg.hashsalt": "bpho-task03-2026",
}


@dataclass(frozen=True)
class Task03FigureGenerationResult:
    """Passing validation report and ordered paths from one figure run."""

    report: Task03ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task03ValidationReport):
            raise TypeError("report must be a Task03ValidationReport")
        if not self.report.passed:
            raise ValueError("figure generation requires a passing report")
        paths = tuple(Path(path) for path in self.output_paths)
        if tuple(path.name for path in paths) != FIGURE_FILENAMES:
            raise ValueError("output_paths must follow the frozen figure order")
        object.__setattr__(self, "output_paths", paths)


def _require_validated(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Task03ValidationReport:
    report = validate_task03(planck_result, einstein_result)
    if not report.passed:
        failed_names = ", ".join(check.name for check in report.failures)
        raise RuntimeError(
            "Task 3 figure generation refused because validation failed: "
            f"{failed_names}"
        )
    return report


def _style_axes(axis: Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3.5, width=0.7)


def _plot_planck_spectra(
    axis: Axes,
    result: PlanckStudyResult,
    *,
    compact: bool = False,
) -> None:
    axis.axvspan(
        380.0,
        750.0,
        color="#FDE68A",
        alpha=0.30,
        linewidth=0.0,
        label="Visible range",
        zorder=0,
    )
    for index, (temperature, colour) in enumerate(
        zip(result.temperatures_k, PLANCK_COLOURS)
    ):
        axis.plot(
            result.wavelengths_nm,
            result.spectral_exitance_w_m2_nm[index],
            color=colour,
            linewidth=2.1 if compact else 2.4,
            label=f"{temperature:.0f} K",
        )
        peak_nm = result.numerical_peak_wavelength_m[index] * 1.0e9
        peak_height = np.interp(
            peak_nm,
            result.wavelengths_nm,
            result.spectral_exitance_w_m2_nm[index],
        )
        axis.scatter(
            [peak_nm],
            [peak_height],
            s=27 if compact else 36,
            color=colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
    axis.set_xlim(
        result.configuration.planck_display_min_nm,
        result.configuration.planck_display_max_nm,
    )
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel("Wavelength, $\\lambda$ (nm)")
    axis.set_ylabel("Spectral exitance (W m$^{-2}$ nm$^{-1}$)")
    axis.set_title("Planck black-body spectra")
    axis.legend(ncol=2 if compact else 1, loc="upper right")
    _style_axes(axis)


def _planck_errors(
    result: PlanckStudyResult,
) -> tuple[np.ndarray, np.ndarray]:
    peak_errors = np.abs(
        result.numerical_peak_wavelength_m - result.wien_peak_wavelength_m
    ) / result.wien_peak_wavelength_m
    integral_errors = np.abs(
        result.numerical_integrated_exitance_w_m2
        - result.stefan_boltzmann_exitance_w_m2
    ) / result.stefan_boltzmann_exitance_w_m2
    return peak_errors, integral_errors


def _validation_panel(
    axis: Axes,
    temperatures: np.ndarray,
    errors: np.ndarray,
    tolerance: float,
    *,
    title: str,
    series_label: str,
    colour: str,
) -> None:
    percent_errors = errors * 100.0
    tolerance_percent = tolerance * 100.0
    axis.semilogy(
        temperatures,
        percent_errors,
        marker="o",
        markersize=6.0,
        linewidth=2.0,
        color=colour,
        label=series_label,
    )
    axis.axhline(
        tolerance_percent,
        color="#64748B",
        linestyle="--",
        linewidth=1.4,
        label=f"Tolerance ({tolerance_percent:g}%)",
    )
    positive_values = percent_errors[percent_errors > 0.0]
    lower = max(float(np.min(positive_values)) / 3.0, 1.0e-8)
    axis.set_ylim(lower, tolerance_percent * 2.2)
    axis.set_xticks(temperatures)
    axis.set_xlabel("Temperature (K)")
    axis.set_ylabel("Absolute relative error (%)")
    axis.set_title(title)
    axis.legend(loc="best")
    _style_axes(axis)


def _plot_einstein_heat_capacity(
    axis: Axes,
    result: EinsteinStudyResult,
    *,
    compact: bool = False,
) -> None:
    for index, (material, colour) in enumerate(
        zip(result.materials, MATERIAL_COLOURS)
    ):
        axis.plot(
            result.temperatures_k,
            result.molar_heat_capacity_j_mol_k[index],
            color=colour,
            linewidth=1.8 if compact else 2.0,
            label=f"{material.symbol}  ($T_E$={result.einstein_temperatures_k[index]:.0f} K)",
        )
    dulong_petit = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K
    axis.axhline(
        dulong_petit,
        color="#64748B",
        linestyle="--",
        linewidth=1.5,
        label="$3R$ Dulong–Petit limit",
    )
    axis.set_xlim(
        result.configuration.einstein_temperature_min_k,
        result.configuration.einstein_temperature_max_k,
    )
    axis.set_ylim(0.0, dulong_petit * 1.08)
    axis.set_xlabel("Temperature, $T$ (K)")
    axis.set_ylabel("Molar heat capacity (J mol$^{-1}$ K$^{-1}$)")
    axis.set_title("Einstein heat-capacity model")
    axis.legend(ncol=2, loc="lower right", fontsize=7.8 if compact else 8.4)
    _style_axes(axis)


def _plot_normalized_curves(axis: Axes, result: EinsteinStudyResult) -> None:
    line_styles = ("-", "--", "-.", ":", "-", "--", "-.")
    for index, (material, colour, line_style) in enumerate(
        zip(result.materials, MATERIAL_COLOURS, line_styles)
    ):
        axis.plot(
            result.reduced_temperatures,
            result.normalized_heat_capacity[index],
            color=colour,
            linestyle=line_style,
            linewidth=2.0,
            alpha=0.86,
            label=material.symbol,
        )
    axis.set_xlim(
        result.configuration.einstein_reduced_temperature_min,
        result.configuration.einstein_reduced_temperature_max,
    )
    axis.set_ylim(0.0, 1.035)
    axis.set_xlabel("Reduced temperature, $T/T_E$")
    axis.set_ylabel("Normalized heat capacity, $C_V/(3R)$")
    axis.set_title("Universal Einstein curve")
    axis.legend(ncol=2, loc="lower right")
    _style_axes(axis)


def _build_planck_spectra_figure(result: PlanckStudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_FIGURE_SIZE_IN)
        _plot_planck_spectra(axis, result)
        figure.text(
            0.12,
            0.96,
            "Peak markers shift to shorter wavelength as temperature rises.",
            ha="left",
            va="top",
            color="#475569",
            fontsize=9.2,
        )
        figure.subplots_adjust(left=0.12, right=0.97, bottom=0.14, top=0.88)
        return figure


def _build_planck_validation_figure(result: PlanckStudyResult) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=WIDE_FIGURE_SIZE_IN,
            sharex=True,
        )
        peak_errors, integral_errors = _planck_errors(result)
        _validation_panel(
            axes[0],
            result.temperatures_k,
            peak_errors,
            result.configuration.wien_peak_relative_tolerance,
            title="Wien displacement law",
            series_label="Numerical peak",
            colour=VALIDATION_COLOURS[0],
        )
        _validation_panel(
            axes[1],
            result.temperatures_k,
            integral_errors,
            result.configuration.stefan_boltzmann_relative_tolerance,
            title="Stefan–Boltzmann law",
            series_label="Integrated spectrum",
            colour=VALIDATION_COLOURS[1],
        )
        figure.suptitle(
            "Independent validation of the Planck calculation",
            fontsize=15,
            fontweight="bold",
            color=TEXT_COLOUR,
        )
        figure.text(
            0.5,
            0.915,
            "All numerical errors lie below the pre-declared tolerances.",
            ha="center",
            va="center",
            color="#475569",
            fontsize=9.5,
        )
        figure.subplots_adjust(
            left=0.09,
            right=0.98,
            bottom=0.15,
            top=0.82,
            wspace=0.27,
        )
        return figure


def _build_einstein_heat_capacity_figure(
    result: EinsteinStudyResult,
) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axis = plt.subplots(figsize=REGULAR_FIGURE_SIZE_IN)
        _plot_einstein_heat_capacity(axis, result)
        figure.text(
            0.12,
            0.96,
            "Higher Einstein temperature delays the approach to the classical limit.",
            ha="left",
            va="top",
            color="#475569",
            fontsize=9.2,
        )
        figure.subplots_adjust(left=0.12, right=0.97, bottom=0.14, top=0.88)
        return figure


def _build_einstein_normalized_figure(
    result: EinsteinStudyResult,
) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(
            1,
            2,
            figsize=WIDE_FIGURE_SIZE_IN,
            gridspec_kw={"width_ratios": (1.65, 1.0)},
        )
        _plot_normalized_curves(axes[0], result)

        deviations = np.max(
            np.abs(
                result.normalized_heat_capacity
                - result.normalized_heat_capacity[0]
            ),
            axis=1,
        )
        display_floor = 1.0e-18
        displayed = np.maximum(deviations, display_floor)
        symbols = [material.symbol for material in result.materials]
        axes[1].scatter(
            symbols,
            displayed,
            s=58,
            color=MATERIAL_COLOURS,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        axes[1].axhline(
            result.configuration.einstein_normalized_collapse_tolerance,
            color="#64748B",
            linestyle="--",
            linewidth=1.5,
            label="Collapse tolerance",
        )
        axes[1].set_yscale("log")
        axes[1].set_ylim(
            display_floor / 2.0,
            result.configuration.einstein_normalized_collapse_tolerance * 8.0,
        )
        axes[1].set_xlabel("Material")
        axes[1].set_ylabel("Maximum difference from Au")
        axes[1].set_title("Numerical collapse check")
        axes[1].legend(loc="upper right")
        axes[1].text(
            0.04,
            0.10,
            "Au difference = 0 (shown at display floor)",
            transform=axes[1].transAxes,
            ha="left",
            va="bottom",
            fontsize=7.8,
            color="#64748B",
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.82,
                "pad": 1.5,
            },
        )
        _style_axes(axes[1])

        figure.suptitle(
            "Einstein scaling removes the material dependence",
            fontsize=15,
            fontweight="bold",
            color=TEXT_COLOUR,
        )
        figure.text(
            0.5,
            0.915,
            "All seven solids coincide when both axes are normalized by $T_E$ and $3R$.",
            ha="center",
            va="center",
            color="#475569",
            fontsize=9.5,
        )
        figure.subplots_adjust(
            left=0.09,
            right=0.98,
            bottom=0.15,
            top=0.82,
            wspace=0.30,
        )
        return figure


def _build_summary_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
    report: Task03ValidationReport,
) -> Figure:
    with matplotlib.rc_context(PLOT_STYLE):
        figure, axes = plt.subplots(2, 2, figsize=SUMMARY_FIGURE_SIZE_IN)
        _plot_planck_spectra(axes[0, 0], planck_result, compact=True)
        _plot_einstein_heat_capacity(
            axes[0, 1],
            einstein_result,
            compact=True,
        )

        peak_errors, integral_errors = _planck_errors(planck_result)
        axes[1, 0].semilogy(
            planck_result.temperatures_k,
            peak_errors * 100.0,
            marker="o",
            linewidth=2.0,
            color=VALIDATION_COLOURS[0],
            label="Wien peak error",
        )
        axes[1, 0].semilogy(
            planck_result.temperatures_k,
            integral_errors * 100.0,
            marker="s",
            linewidth=2.0,
            color=VALIDATION_COLOURS[1],
            label="Integrated-exitance error",
        )
        axes[1, 0].axhline(
            planck_result.configuration.wien_peak_relative_tolerance * 100.0,
            color=VALIDATION_COLOURS[0],
            linestyle="--",
            linewidth=1.1,
            alpha=0.75,
            label="Wien tolerance",
        )
        axes[1, 0].axhline(
            planck_result.configuration.stefan_boltzmann_relative_tolerance
            * 100.0,
            color=VALIDATION_COLOURS[1],
            linestyle="--",
            linewidth=1.1,
            alpha=0.75,
            label="Integral tolerance",
        )
        axes[1, 0].set_xticks(planck_result.temperatures_k)
        axes[1, 0].set_xlabel("Temperature (K)")
        axes[1, 0].set_ylabel("Absolute relative error (%)")
        axes[1, 0].set_title("Numerical checks against analytic laws")
        axes[1, 0].legend(ncol=2, fontsize=7.5, loc="best")
        _style_axes(axes[1, 0])

        _plot_normalized_curves(axes[1, 1], einstein_result)
        axes[1, 1].text(
            0.04,
            0.93,
            f"PASS  •  {len(report.checks)}/{len(report.checks)} checks",
            transform=axes[1, 1].transAxes,
            ha="left",
            va="top",
            fontsize=9.0,
            fontweight="bold",
            color=PASS_COLOUR,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#E8F5EE",
                "edgecolor": "#8ED1AC",
                "linewidth": 0.8,
            },
        )

        figure.suptitle(
            "Task 3 — Planck radiation and Einstein heat capacity",
            fontsize=19,
            fontweight="bold",
            color=TEXT_COLOUR,
            y=0.975,
        )
        figure.text(
            0.5,
            0.925,
            "Deterministic models • SI units • independently validated limiting laws",
            ha="center",
            va="center",
            color="#475569",
            fontsize=10.5,
        )
        figure.subplots_adjust(
            left=0.075,
            right=0.98,
            bottom=0.075,
            top=0.865,
            wspace=0.22,
            hspace=0.38,
        )
        return figure


def create_planck_spectra_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Figure:
    """Return the validated principal Planck-spectrum figure."""

    _require_validated(planck_result, einstein_result)
    return _build_planck_spectra_figure(planck_result)


def create_planck_validation_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Figure:
    """Return the validated Wien and Stefan--Boltzmann error figure."""

    _require_validated(planck_result, einstein_result)
    return _build_planck_validation_figure(planck_result)


def create_einstein_heat_capacity_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Figure:
    """Return the validated principal Einstein heat-capacity figure."""

    _require_validated(planck_result, einstein_result)
    return _build_einstein_heat_capacity_figure(einstein_result)


def create_einstein_normalized_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Figure:
    """Return the validated universal-curve and collapse-check figure."""

    _require_validated(planck_result, einstein_result)
    return _build_einstein_normalized_figure(einstein_result)


def create_task03_summary_figure(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
) -> Figure:
    """Return the validated 16:9 presentation summary figure."""

    report = _require_validated(planck_result, einstein_result)
    return _build_summary_figure(planck_result, einstein_result, report)


def _save_figure(figure: Figure, path: Path) -> None:
    file_format = path.suffix.removeprefix(".").lower()
    if file_format == "png":
        metadata = {"Software": "BPhO Computational Challenge 2026"}
    elif file_format == "svg":
        metadata = {
            "Creator": "BPhO Computational Challenge 2026",
            "Date": None,
        }
    else:  # pragma: no cover - frozen writers only use PNG and SVG
        raise ValueError(f"unsupported figure format: {file_format}")
    try:
        # The SVG backend reads svg.hashsalt at serialization time.
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
            # Matplotlib writes spaces before line breaks inside path data.
            # They are semantically irrelevant but fail repository whitespace
            # checks, so normalize them without changing the rendered vector.
            original = path.read_text(encoding="utf-8")
            normalized = "\n".join(
                line.rstrip() for line in original.splitlines()
            ) + "\n"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(normalized)
    finally:
        plt.close(figure)


def _atomic_write_figures(
    output_directory: Path,
    writers: tuple[tuple[str, Callable[[Path], None]], ...],
) -> tuple[Path, ...]:
    if output_directory.exists() and not output_directory.is_dir():
        raise NotADirectoryError(f"output path is not a directory: {output_directory}")
    output_directory.mkdir(parents=True, exist_ok=True)

    destinations = tuple(output_directory / name for name, _ in writers)
    for destination in destinations:
        if destination.exists() and destination.is_dir():
            raise IsADirectoryError(
                f"output destination is a directory: {destination}"
            )

    temporary_paths: list[Path] = []
    try:
        for (filename, writer), destination in zip(writers, destinations):
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.stem}.",
                suffix=destination.suffix,
                dir=output_directory,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_paths.append(temporary_path)
            writer(temporary_path)
            if temporary_path.stat().st_size == 0:
                raise RuntimeError(f"empty figure output: {filename}")
            temporary_path.chmod(0o644)

        for temporary_path, destination in zip(temporary_paths, destinations):
            temporary_path.replace(destination)
        return destinations
    finally:
        for temporary_path in temporary_paths:
            if temporary_path.exists():
                temporary_path.unlink()


def write_task03_figures(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
    output_directory: str | os.PathLike[str] = DEFAULT_FIGURE_DIRECTORY,
) -> Task03FigureGenerationResult:
    """Validate results, then atomically write five PNG/SVG figure pairs."""

    report = _require_validated(planck_result, einstein_result)
    factories: tuple[Callable[[], Figure], ...] = (
        lambda: _build_planck_spectra_figure(planck_result),
        lambda: _build_planck_validation_figure(planck_result),
        lambda: _build_einstein_heat_capacity_figure(einstein_result),
        lambda: _build_einstein_normalized_figure(einstein_result),
        lambda: _build_summary_figure(planck_result, einstein_result, report),
    )
    factory_by_stem = {
        stem: factory
        for stem, factory in zip(
            (
                "planck_spectra",
                "planck_validation",
                "einstein_heat_capacity",
                "einstein_normalized",
                "task03_summary",
            ),
            factories,
        )
    }
    writers = tuple(
        (
            filename,
            lambda path, factory=factory_by_stem[Path(filename).stem]: (
                _save_figure(factory(), path)
            ),
        )
        for filename in FIGURE_FILENAMES
    )
    output_paths = _atomic_write_figures(Path(output_directory), writers)
    return Task03FigureGenerationResult(
        report=report,
        output_paths=output_paths,
    )


__all__ = [
    "FIGURE_DPI",
    "MATERIAL_COLOURS",
    "PLANCK_COLOURS",
    "PLOT_STYLE",
    "Task03FigureGenerationResult",
    "create_einstein_heat_capacity_figure",
    "create_einstein_normalized_figure",
    "create_planck_spectra_figure",
    "create_planck_validation_figure",
    "create_task03_summary_figure",
    "write_task03_figures",
]
