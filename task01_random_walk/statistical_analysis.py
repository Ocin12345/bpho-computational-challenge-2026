"""Formal statistical validation for BPhO Task 1 random walks."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from matplotlib.ticker import ScalarFormatter
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
Z_95 = 1.959963984540054
DEFAULT_STEP_COUNTS = (10, 20, 50, 100, 200, 500, 1_000, 2_000)
DEFAULT_VALIDATION_STEM = Path("figures/task01/statistical_validation")
DEFAULT_ENDPOINT_STEM = Path("figures/task01/endpoint_distribution")
DEFAULT_CSV_PATH = Path("data/task01/statistical_results.csv")


@dataclass(frozen=True)
class StepStatistics:
    """Measured and theoretical quantities for one value of N."""

    n_steps: int
    n_walks: int
    step_size: float
    mean_x: float
    mean_y: float
    standard_error_x: float
    standard_error_y: float
    variance_x: float
    variance_y: float
    mean_squared_displacement: float
    standard_error_msd: float

    @property
    def theoretical_coordinate_variance(self) -> float:
        """Theoretical value Ns^2/2 for either coordinate variance."""

        return self.n_steps * self.step_size**2 / 2.0

    @property
    def theoretical_msd(self) -> float:
        """Theoretical mean squared displacement Ns^2."""

        return self.n_steps * self.step_size**2

    @property
    def msd_ratio(self) -> float:
        """Measured mean squared displacement divided by theory."""

        return self.mean_squared_displacement / self.theoretical_msd

    @property
    def variance_ratio_x(self) -> float:
        """Measured x variance divided by theory."""

        return self.variance_x / self.theoretical_coordinate_variance

    @property
    def variance_ratio_y(self) -> float:
        """Measured y variance divided by theory."""

        return self.variance_y / self.theoretical_coordinate_variance

    @property
    def normalized_mean_x(self) -> float:
        """Mean x divided by the theoretical endpoint standard deviation."""

        return self.mean_x / np.sqrt(self.theoretical_coordinate_variance)

    @property
    def normalized_mean_y(self) -> float:
        """Mean y divided by the theoretical endpoint standard deviation."""

        return self.mean_y / np.sqrt(self.theoretical_coordinate_variance)


@dataclass(frozen=True)
class StatisticalAnalysisResult:
    """Statistics across step counts plus endpoints for one reference N."""

    statistics: tuple[StepStatistics, ...]
    reference_n_steps: int
    reference_endpoints: FloatArray
    seed: int | None


def _positive_integer(value: int, name: str, *, minimum: int = 1) -> int:
    """Validate a positive integer used by the statistical analysis."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return int(value)


def _positive_float(value: float, name: str) -> float:
    """Validate a positive finite floating-point parameter."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def simulate_endpoints(
    n_walks: int,
    n_steps: int,
    step_size: float,
    *,
    rng: np.random.Generator,
    batch_size: int = 1_000,
) -> FloatArray:
    """Simulate endpoints efficiently without storing complete trajectories."""

    n_walks = _positive_integer(n_walks, "n_walks", minimum=2)
    n_steps = _positive_integer(n_steps, "n_steps")
    batch_size = _positive_integer(batch_size, "batch_size")
    step_size = _positive_float(step_size, "step_size")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")

    endpoints = np.empty((n_walks, 2), dtype=np.float64)
    for start in range(0, n_walks, batch_size):
        stop = min(start + batch_size, n_walks)
        angles = rng.uniform(0.0, 2.0 * np.pi, size=(stop - start, n_steps))
        endpoints[start:stop, 0] = step_size * np.cos(angles).sum(axis=1)
        endpoints[start:stop, 1] = step_size * np.sin(angles).sum(axis=1)

    return endpoints


def analyse_endpoints(
    endpoints: FloatArray,
    n_steps: int,
    step_size: float,
) -> StepStatistics:
    """Calculate endpoint means, variances, MSD, and standard errors."""

    n_steps = _positive_integer(n_steps, "n_steps")
    step_size = _positive_float(step_size, "step_size")
    endpoints = np.asarray(endpoints, dtype=np.float64)
    if endpoints.ndim != 2 or endpoints.shape[1] != 2:
        raise ValueError("endpoints must have shape (n_walks, 2)")
    n_walks = _positive_integer(len(endpoints), "n_walks", minimum=2)
    if not np.all(np.isfinite(endpoints)):
        raise ValueError("all endpoints must be finite")

    x = endpoints[:, 0]
    y = endpoints[:, 1]
    squared_displacements = np.sum(endpoints**2, axis=1)
    variance_x = float(np.var(x, ddof=1))
    variance_y = float(np.var(y, ddof=1))

    return StepStatistics(
        n_steps=n_steps,
        n_walks=n_walks,
        step_size=step_size,
        mean_x=float(np.mean(x)),
        mean_y=float(np.mean(y)),
        standard_error_x=float(np.sqrt(variance_x / n_walks)),
        standard_error_y=float(np.sqrt(variance_y / n_walks)),
        variance_x=variance_x,
        variance_y=variance_y,
        mean_squared_displacement=float(np.mean(squared_displacements)),
        standard_error_msd=float(
            np.std(squared_displacements, ddof=1) / np.sqrt(n_walks)
        ),
    )


def run_statistical_analysis(
    step_counts: Sequence[int] = DEFAULT_STEP_COUNTS,
    *,
    n_walks: int = 50_000,
    step_size: float = 1.0,
    seed: int | None = 2026,
    reference_n_steps: int = 1_000,
    batch_size: int = 1_000,
) -> StatisticalAnalysisResult:
    """Run reproducible, independent endpoint experiments for several N values."""

    n_walks = _positive_integer(n_walks, "n_walks", minimum=2)
    step_size = _positive_float(step_size, "step_size")
    batch_size = _positive_integer(batch_size, "batch_size")
    if seed is not None:
        seed = _positive_integer(seed, "seed", minimum=0)

    validated_counts = tuple(
        sorted({_positive_integer(value, "step count") for value in step_counts})
    )
    if not validated_counts:
        raise ValueError("step_counts must contain at least one value")
    reference_n_steps = _positive_integer(reference_n_steps, "reference_n_steps")
    if reference_n_steps not in validated_counts:
        raise ValueError("reference_n_steps must be included in step_counts")

    seed_sequence = np.random.SeedSequence(seed)
    child_sequences = seed_sequence.spawn(len(validated_counts))
    statistics: list[StepStatistics] = []
    reference_endpoints: FloatArray | None = None

    for n_steps, child_sequence in zip(validated_counts, child_sequences):
        endpoints = simulate_endpoints(
            n_walks,
            n_steps,
            step_size,
            rng=np.random.default_rng(child_sequence),
            batch_size=batch_size,
        )
        statistics.append(analyse_endpoints(endpoints, n_steps, step_size))
        if n_steps == reference_n_steps:
            reference_endpoints = endpoints

    if reference_endpoints is None:
        raise RuntimeError("reference endpoint simulation was not produced")

    return StatisticalAnalysisResult(
        statistics=tuple(statistics),
        reference_n_steps=reference_n_steps,
        reference_endpoints=reference_endpoints,
        seed=seed,
    )


def _weighted_msd_slope(
    statistics: Sequence[StepStatistics],
) -> tuple[float, float]:
    """Fit MSD = slope*N through the origin using inverse-variance weights."""

    n_steps = np.array([item.n_steps for item in statistics], dtype=np.float64)
    msd = np.array(
        [item.mean_squared_displacement for item in statistics], dtype=np.float64
    )
    errors = np.array(
        [item.standard_error_msd for item in statistics], dtype=np.float64
    )
    weights = 1.0 / errors**2
    denominator = float(np.sum(weights * n_steps**2))
    slope = float(np.sum(weights * n_steps * msd) / denominator)
    slope_error = float(np.sqrt(1.0 / denominator))
    return slope, slope_error


def create_validation_figure(result: StatisticalAnalysisResult) -> Figure:
    """Create a four-panel comparison between simulation and theory."""

    statistics = result.statistics
    n_steps = np.array([item.n_steps for item in statistics], dtype=np.float64)
    measured_msd = np.array(
        [item.mean_squared_displacement for item in statistics], dtype=np.float64
    )
    msd_errors = np.array(
        [Z_95 * item.standard_error_msd for item in statistics], dtype=np.float64
    )
    theoretical_msd = np.array(
        [item.theoretical_msd for item in statistics], dtype=np.float64
    )
    msd_ratios = measured_msd / theoretical_msd
    ratio_errors = msd_errors / theoretical_msd
    normalized_mean_x = np.array(
        [item.normalized_mean_x for item in statistics], dtype=np.float64
    )
    normalized_mean_y = np.array(
        [item.normalized_mean_y for item in statistics], dtype=np.float64
    )
    normalized_mean_error_x = np.array(
        [
            Z_95
            * item.standard_error_x
            / np.sqrt(item.theoretical_coordinate_variance)
            for item in statistics
        ],
        dtype=np.float64,
    )
    normalized_mean_error_y = np.array(
        [
            Z_95
            * item.standard_error_y
            / np.sqrt(item.theoretical_coordinate_variance)
            for item in statistics
        ],
        dtype=np.float64,
    )
    variance_ratio_x = np.array(
        [item.variance_ratio_x for item in statistics], dtype=np.float64
    )
    variance_ratio_y = np.array(
        [item.variance_ratio_y for item in statistics], dtype=np.float64
    )

    figure, axes = plt.subplots(2, 2, figsize=(13.0, 9.5))
    figure.patch.set_facecolor("white")
    figure.subplots_adjust(
        left=0.08,
        right=0.98,
        bottom=0.08,
        top=0.86,
        hspace=0.28,
        wspace=0.18,
    )
    figure.suptitle(
        "Statistical validation of the two-dimensional random walk",
        fontsize=19,
        fontweight="bold",
        color="#0f172a",
        y=0.975,
    )
    figure.text(
        0.5,
        0.925,
        (
            f"{statistics[0].n_walks:,} independent walks per N   |   "
            f"s = {statistics[0].step_size:g}   |   master seed = {result.seed}"
        ),
        ha="center",
        fontsize=10.5,
        color="#475569",
    )

    for axis in axes.flat:
        axis.set_facecolor("#f8fafc")
        axis.grid(True, color="#cbd5e1", linewidth=0.65, alpha=0.55)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color("#94a3b8")
        axis.spines["bottom"].set_color("#94a3b8")
        axis.tick_params(colors="#334155", labelsize=9)
        axis.set_xscale("log")
        axis.set_xticks(n_steps)
        axis.xaxis.set_major_formatter(ScalarFormatter())

    axis = axes[0, 0]
    axis.errorbar(
        n_steps,
        measured_msd,
        yerr=msd_errors,
        fmt="o",
        color="#2563eb",
        ecolor="#93c5fd",
        capsize=3,
        markersize=5,
        label="Simulation (95% CI)",
        zorder=3,
    )
    axis.plot(
        n_steps,
        theoretical_msd,
        color="#dc2626",
        linewidth=1.8,
        label=r"Theory: $\langle r^2\rangle=Ns^2$",
    )
    axis.set_yscale("log")
    axis.set_title("A. Mean squared displacement", loc="left", fontweight="bold")
    axis.set_xlabel("Number of steps, N")
    axis.set_ylabel(r"$\langle r^2\rangle$")
    slope, slope_error = _weighted_msd_slope(statistics)
    axis.text(
        0.04,
        0.96,
        (
            "Weighted fit through origin\n"
            f"slope = {slope:.5f} ± {Z_95 * slope_error:.5f} (95% CI)\n"
            f"theory = {statistics[0].step_size**2:.5f}"
        ),
        transform=axis.transAxes,
        va="top",
        fontsize=8.8,
        color="#334155",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "#cbd5e1",
            "alpha": 0.94,
        },
    )
    axis.legend(fontsize=8.5, frameon=True)

    axis = axes[0, 1]
    axis.errorbar(
        n_steps,
        msd_ratios,
        yerr=ratio_errors,
        fmt="o-",
        color="#2563eb",
        ecolor="#93c5fd",
        capsize=3,
        markersize=4.5,
        label="Simulation/theory",
    )
    axis.axhline(1.0, color="#dc2626", linewidth=1.5, label="Exact agreement")
    ratio_extent = max(float(np.max(np.abs(msd_ratios - 1.0) + ratio_errors)), 0.02)
    axis.set_ylim(1.0 - 1.25 * ratio_extent, 1.0 + 1.25 * ratio_extent)
    axis.set_title("B. Relative MSD agreement", loc="left", fontweight="bold")
    axis.set_xlabel("Number of steps, N")
    axis.set_ylabel(r"$\langle r^2\rangle/(Ns^2)$")
    axis.legend(fontsize=8.5, frameon=True)

    axis = axes[1, 0]
    axis.errorbar(
        n_steps,
        normalized_mean_x,
        yerr=normalized_mean_error_x,
        fmt="o-",
        color="#2563eb",
        ecolor="#93c5fd",
        capsize=3,
        markersize=4.5,
        label="x coordinate",
    )
    axis.errorbar(
        n_steps,
        normalized_mean_y,
        yerr=normalized_mean_error_y,
        fmt="s-",
        color="#ea580c",
        ecolor="#fdba74",
        capsize=3,
        markersize=4.5,
        label="y coordinate",
    )
    axis.axhline(0.0, color="#334155", linewidth=1.2, label="Theory: zero")
    mean_extent = max(
        float(
            np.max(
                np.concatenate(
                    (
                        np.abs(normalized_mean_x) + normalized_mean_error_x,
                        np.abs(normalized_mean_y) + normalized_mean_error_y,
                    )
                )
            )
        ),
        0.025,
    )
    axis.set_ylim(-1.2 * mean_extent, 1.2 * mean_extent)
    axis.set_title("C. Test for directional bias", loc="left", fontweight="bold")
    axis.set_xlabel("Number of steps, N")
    axis.set_ylabel("Mean coordinate / theoretical standard deviation")
    axis.legend(fontsize=8.5, frameon=True)

    axis = axes[1, 1]
    axis.plot(
        n_steps,
        variance_ratio_x,
        "o-",
        color="#2563eb",
        markersize=4.5,
        label="x variance",
    )
    axis.plot(
        n_steps,
        variance_ratio_y,
        "s-",
        color="#ea580c",
        markersize=4.5,
        label="y variance",
    )
    axis.axhline(1.0, color="#dc2626", linewidth=1.5, label="Theory")
    variance_extent = max(
        float(
            np.max(
                np.abs(np.concatenate((variance_ratio_x, variance_ratio_y)) - 1.0)
            )
        ),
        0.02,
    )
    axis.set_ylim(1.0 - 1.25 * variance_extent, 1.0 + 1.25 * variance_extent)
    axis.set_title("D. Coordinate variance", loc="left", fontweight="bold")
    axis.set_xlabel("Number of steps, N")
    axis.set_ylabel(r"Measured variance / $(Ns^2/2)$")
    axis.legend(fontsize=8.5, frameon=True)

    return figure


def _radial_quantile(n_steps: int, step_size: float, probability: float) -> float:
    """Large-N Rayleigh approximation for a radial containment quantile."""

    return float(step_size * np.sqrt(-n_steps * np.log1p(-probability)))


def create_endpoint_distribution_figure(
    result: StatisticalAnalysisResult,
) -> Figure:
    """Plot the endpoint cloud and theoretical radial containment circles."""

    endpoints = result.reference_endpoints
    reference_statistics = next(
        item
        for item in result.statistics
        if item.n_steps == result.reference_n_steps
    )
    radius_50 = _radial_quantile(
        result.reference_n_steps,
        reference_statistics.step_size,
        0.50,
    )
    radius_95 = _radial_quantile(
        result.reference_n_steps,
        reference_statistics.step_size,
        0.95,
    )
    radii = np.linalg.norm(endpoints, axis=1)
    measured_50 = float(np.mean(radii <= radius_50))
    measured_95 = float(np.mean(radii <= radius_95))

    figure, axis = plt.subplots(figsize=(10.5, 8.0), layout="constrained")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("#f8fafc")
    density = axis.hexbin(
        endpoints[:, 0],
        endpoints[:, 1],
        gridsize=62,
        mincnt=1,
        bins="log",
        cmap="magma",
        linewidths=0.0,
        zorder=2,
    )
    colour_bar = figure.colorbar(density, ax=axis, pad=0.025, shrink=0.88)
    colour_bar.set_label("Endpoint count per hexagon (log colour scale)")
    colour_bar.outline.set_edgecolor("#94a3b8")

    circle_50 = Circle(
        (0.0, 0.0),
        radius_50,
        fill=False,
        color="#38bdf8",
        linewidth=1.8,
        linestyle=(0, (5, 3)),
        label=f"Theory: 50% within r = {radius_50:.2f}",
        zorder=4,
    )
    circle_95 = Circle(
        (0.0, 0.0),
        radius_95,
        fill=False,
        color="#22c55e",
        linewidth=1.8,
        linestyle=(0, (8, 3)),
        label=f"Theory: 95% within r = {radius_95:.2f}",
        zorder=4,
    )
    axis.add_patch(circle_50)
    axis.add_patch(circle_95)
    axis.scatter(
        0.0,
        0.0,
        s=80,
        color="white",
        edgecolor="#0f172a",
        linewidth=1.5,
        marker="o",
        label="Origin",
        zorder=5,
    )

    limit = max(float(np.max(np.abs(endpoints))), 1.08 * radius_95) * 1.04
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    axis.set_aspect("equal", adjustable="box")
    axis.axhline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.axvline(0.0, color="#94a3b8", linewidth=0.8, alpha=0.65, zorder=0)
    axis.grid(True, color="#cbd5e1", linewidth=0.65, alpha=0.45, zorder=0)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#94a3b8")
    axis.spines["bottom"].set_color("#94a3b8")

    axis.set_title(
        "Endpoint distribution and isotropy",
        loc="left",
        fontsize=17,
        fontweight="bold",
        color="#0f172a",
        pad=25,
    )
    axis.text(
        0.0,
        1.015,
        (
            f"{len(endpoints):,} independent walks   |   "
            f"N = {result.reference_n_steps:,}   |   "
            f"s = {reference_statistics.step_size:g}   |   seed = {result.seed}"
        ),
        transform=axis.transAxes,
        fontsize=10.5,
        color="#475569",
        va="bottom",
    )
    axis.set_xlabel("Final x position (distance units)", fontsize=11)
    axis.set_ylabel("Final y position (distance units)", fontsize=11)
    axis.legend(
        loc="upper right",
        frameon=True,
        facecolor="white",
        edgecolor="#cbd5e1",
        framealpha=0.94,
        fontsize=9,
    )
    axis.text(
        0.025,
        0.975,
        (
            f"Observed inside 50% circle: {100.0 * measured_50:.2f}%\n"
            f"Observed inside 95% circle: {100.0 * measured_95:.2f}%"
        ),
        transform=axis.transAxes,
        va="top",
        fontsize=9.5,
        color="#334155",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "#cbd5e1",
            "alpha": 0.94,
        },
    )

    return figure


def _save_figure(
    figure: Figure,
    output_stem: str | Path,
    *,
    title: str,
    dpi: int,
) -> tuple[Path, Path]:
    """Save one figure in high-resolution PNG and vector SVG formats."""

    if dpi <= 0:
        raise ValueError("dpi must be greater than zero")
    output_stem = Path(output_stem)
    if output_stem.suffix:
        output_stem = output_stem.with_suffix("")
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_stem.with_suffix(".png")
    svg_path = output_stem.with_suffix(".svg")
    try:
        figure.savefig(
            png_path,
            dpi=dpi,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": title},
        )
        figure.savefig(
            svg_path,
            facecolor="white",
            bbox_inches="tight",
            metadata={"Title": title},
        )
    finally:
        plt.close(figure)
    return png_path, svg_path


def save_analysis_figures(
    result: StatisticalAnalysisResult,
    *,
    validation_stem: str | Path = DEFAULT_VALIDATION_STEM,
    endpoint_stem: str | Path = DEFAULT_ENDPOINT_STEM,
    dpi: int = 240,
) -> tuple[Path, Path, Path, Path]:
    """Save both statistical figures in PNG and SVG formats."""

    validation_png, validation_svg = _save_figure(
        create_validation_figure(result),
        validation_stem,
        title="BPhO Task 1: statistical validation",
        dpi=dpi,
    )
    endpoint_png, endpoint_svg = _save_figure(
        create_endpoint_distribution_figure(result),
        endpoint_stem,
        title="BPhO Task 1: endpoint distribution",
        dpi=dpi,
    )
    return validation_png, validation_svg, endpoint_png, endpoint_svg


def save_statistics_csv(
    result: StatisticalAnalysisResult,
    output_path: str | Path = DEFAULT_CSV_PATH,
) -> Path:
    """Save all measured and theoretical values in a reproducible CSV file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "n_steps",
        "n_walks",
        "step_size",
        "mean_x",
        "mean_y",
        "ci95_half_width_x",
        "ci95_half_width_y",
        "variance_x",
        "variance_y",
        "theoretical_coordinate_variance",
        "mean_squared_displacement",
        "ci95_half_width_msd",
        "theoretical_msd",
        "msd_ratio",
    )
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in result.statistics:
            writer.writerow(
                {
                    "n_steps": item.n_steps,
                    "n_walks": item.n_walks,
                    "step_size": item.step_size,
                    "mean_x": item.mean_x,
                    "mean_y": item.mean_y,
                    "ci95_half_width_x": Z_95 * item.standard_error_x,
                    "ci95_half_width_y": Z_95 * item.standard_error_y,
                    "variance_x": item.variance_x,
                    "variance_y": item.variance_y,
                    "theoretical_coordinate_variance": (
                        item.theoretical_coordinate_variance
                    ),
                    "mean_squared_displacement": item.mean_squared_displacement,
                    "ci95_half_width_msd": Z_95 * item.standard_error_msd,
                    "theoretical_msd": item.theoretical_msd,
                    "msd_ratio": item.msd_ratio,
                }
            )
    return output_path


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for the statistical analysis."""

    parser = argparse.ArgumentParser(
        description="Run the formal statistical validation for BPhO Task 1."
    )
    parser.add_argument("--walks", type=int, default=50_000)
    parser.add_argument("--step-size", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--batch-size", type=int, default=1_000)
    parser.add_argument(
        "--step-counts",
        type=int,
        nargs="+",
        default=list(DEFAULT_STEP_COUNTS),
    )
    parser.add_argument("--reference-steps", type=int, default=1_000)
    parser.add_argument("--dpi", type=int, default=240)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the analysis, save evidence files, and print a compact summary."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = run_statistical_analysis(
            args.step_counts,
            n_walks=args.walks,
            step_size=args.step_size,
            seed=args.seed,
            reference_n_steps=args.reference_steps,
            batch_size=args.batch_size,
        )
        figure_paths = save_analysis_figures(result, dpi=args.dpi)
        csv_path = save_statistics_csv(result)
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    print("N       <r^2> measured    Ns^2 theory    ratio")
    for item in result.statistics:
        print(
            f"{item.n_steps:4d}    {item.mean_squared_displacement:14.6f}    "
            f"{item.theoretical_msd:11.6f}    {item.msd_ratio:7.5f}"
        )
    slope, slope_error = _weighted_msd_slope(result.statistics)
    print(
        f"Weighted MSD slope: {slope:.6f} ± {Z_95 * slope_error:.6f} "
        f"(95% CI); theory = {args.step_size**2:.6f}"
    )
    for path in (*figure_paths, csv_path):
        print(f"Saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
