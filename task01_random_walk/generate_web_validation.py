"""Generate the reproducible browser-validation dataset for Task 1."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from task01_random_walk.statistical_analysis import Z_95, simulate_endpoints


DEFAULT_STATISTICS_PATH = Path("data/task01/statistical_results.csv")
DEFAULT_OUTPUT_PATH = Path("site/data/task-01-validation.json")


def _positive_integer(value: int, name: str, minimum: int = 1) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return int(value)


def _read_msd_statistics(path: str | Path) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    with Path(path).open(newline="", encoding="utf-8") as input_file:
        for raw in csv.DictReader(input_file):
            rows.append(
                {
                    "n_steps": int(raw["n_steps"]),
                    "n_walks": int(raw["n_walks"]),
                    "step_size": float(raw["step_size"]),
                    "mean_squared_displacement": float(
                        raw["mean_squared_displacement"]
                    ),
                    "ci95_half_width_msd": float(
                        raw["ci95_half_width_msd"]
                    ),
                    "theoretical_msd": float(raw["theoretical_msd"]),
                    "msd_ratio": float(raw["msd_ratio"]),
                    "mean_x": float(raw["mean_x"]),
                    "mean_y": float(raw["mean_y"]),
                }
            )
    if len(rows) < 2:
        raise ValueError("MSD statistics must contain at least two step counts")
    return rows


def _weighted_msd_coefficient(
    rows: list[dict[str, float | int]],
) -> tuple[float, float]:
    n_steps = np.asarray([row["n_steps"] for row in rows], dtype=np.float64)
    msd = np.asarray(
        [row["mean_squared_displacement"] for row in rows],
        dtype=np.float64,
    )
    standard_errors = np.asarray(
        [row["ci95_half_width_msd"] / Z_95 for row in rows],
        dtype=np.float64,
    )
    weights = 1.0 / standard_errors**2
    denominator = float(np.sum(weights * n_steps**2))
    coefficient = float(np.sum(weights * n_steps * msd) / denominator)
    coefficient_error = float(np.sqrt(1.0 / denominator))
    return coefficient, Z_95 * coefficient_error


def _angular_evidence(
    rng: np.random.Generator,
    *,
    sample_count: int,
    bin_count: int,
) -> dict[str, Any]:
    angles = rng.uniform(0.0, 2.0 * np.pi, size=sample_count)
    counts, edges = np.histogram(
        angles,
        bins=bin_count,
        range=(0.0, 2.0 * np.pi),
    )
    expected = sample_count / bin_count
    maximum_relative_deviation = float(
        np.max(np.abs(counts - expected)) / expected
    )
    return {
        "sample_count": sample_count,
        "bin_count": bin_count,
        "expected_per_bin": expected,
        "maximum_relative_deviation": maximum_relative_deviation,
        "bins": [
            {
                "start_radians": float(edges[index]),
                "end_radians": float(edges[index + 1]),
                "count": int(counts[index]),
            }
            for index in range(bin_count)
        ],
    }


def _radial_evidence(
    rng: np.random.Generator,
    *,
    n_walks: int,
    n_steps: int,
    step_size: float,
    bin_count: int,
    batch_size: int,
) -> dict[str, Any]:
    endpoints = simulate_endpoints(
        n_walks,
        n_steps,
        step_size,
        rng=rng,
        batch_size=batch_size,
    )
    radii = np.linalg.norm(endpoints, axis=1)
    theoretical_scale_squared = n_steps * step_size**2
    radius_50 = float(
        step_size * np.sqrt(-n_steps * np.log(1.0 - 0.50))
    )
    radius_95 = float(
        step_size * np.sqrt(-n_steps * np.log(1.0 - 0.95))
    )
    observed_50 = float(np.mean(radii <= radius_50))
    observed_95 = float(np.mean(radii <= radius_95))
    theoretical_upper = float(
        step_size * np.sqrt(-n_steps * np.log(1.0 - 0.9999))
    )
    upper = max(float(np.max(radii)), theoretical_upper)
    counts, edges = np.histogram(radii, bins=bin_count, range=(0.0, upper))
    cdf = 1.0 - np.exp(-(edges**2) / theoretical_scale_squared)
    expected_counts = n_walks * np.diff(cdf)

    return {
        "n_walks": n_walks,
        "n_steps": n_steps,
        "step_size": step_size,
        "radius_50": radius_50,
        "radius_95": radius_95,
        "observed_fraction_50": observed_50,
        "observed_fraction_95": observed_95,
        "bins": [
            {
                "start_radius": float(edges[index]),
                "end_radius": float(edges[index + 1]),
                "count": int(counts[index]),
                "rayleigh_expected_count": float(expected_counts[index]),
            }
            for index in range(bin_count)
        ],
    }


def build_validation_payload(
    *,
    statistics_path: str | Path = DEFAULT_STATISTICS_PATH,
    seed: int = 2026,
    angle_samples: int = 250_000,
    angle_bins: int = 24,
    radial_walks: int = 50_000,
    radial_steps: int = 1_000,
    radial_bins: int = 34,
    step_size: float = 1.0,
    batch_size: int = 1_000,
) -> dict[str, Any]:
    """Build all deterministic evidence needed by the browser charts."""

    seed = _positive_integer(seed, "seed", minimum=0)
    angle_samples = _positive_integer(angle_samples, "angle_samples", minimum=2)
    angle_bins = _positive_integer(angle_bins, "angle_bins", minimum=4)
    radial_walks = _positive_integer(radial_walks, "radial_walks", minimum=2)
    radial_steps = _positive_integer(radial_steps, "radial_steps")
    radial_bins = _positive_integer(radial_bins, "radial_bins", minimum=4)
    batch_size = _positive_integer(batch_size, "batch_size")
    step_size = float(step_size)
    if not np.isfinite(step_size) or step_size <= 0.0:
        raise ValueError("step_size must be finite and greater than zero")

    msd_rows = _read_msd_statistics(statistics_path)
    coefficient, coefficient_ci95 = _weighted_msd_coefficient(msd_rows)
    seed_sequence = np.random.SeedSequence(seed)
    angle_seed, radial_seed = seed_sequence.spawn(2)

    return {
        "schema_version": 1,
        "model": "Two-dimensional isotropic fixed-step random walk",
        "seed": seed,
        "provenance": {
            "simulation": "task01_random_walk.statistical_analysis",
            "statistics_csv": str(Path(statistics_path)),
            "angles_exact": True,
            "endpoints_exact": True,
        },
        "angular": _angular_evidence(
            np.random.default_rng(angle_seed),
            sample_count=angle_samples,
            bin_count=angle_bins,
        ),
        "msd": {
            "weighted_coefficient": coefficient,
            "weighted_coefficient_ci95": coefficient_ci95,
            "theoretical_coefficient": step_size**2,
            "maximum_absolute_ratio_error": max(
                abs(float(row["msd_ratio"]) - 1.0) for row in msd_rows
            ),
            "rows": msd_rows,
        },
        "radial": _radial_evidence(
            np.random.default_rng(radial_seed),
            n_walks=radial_walks,
            n_steps=radial_steps,
            step_size=step_size,
            bin_count=radial_bins,
            batch_size=batch_size,
        ),
    }


def save_validation_payload(
    payload: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Task 1 browser-validation data."
    )
    parser.add_argument("--statistics", type=Path, default=DEFAULT_STATISTICS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--angle-samples", type=int, default=250_000)
    parser.add_argument("--radial-walks", type=int, default=50_000)
    parser.add_argument("--radial-steps", type=int, default=1_000)
    return parser


def main() -> int:
    arguments = build_argument_parser().parse_args()
    payload = build_validation_payload(
        statistics_path=arguments.statistics,
        seed=arguments.seed,
        angle_samples=arguments.angle_samples,
        radial_walks=arguments.radial_walks,
        radial_steps=arguments.radial_steps,
    )
    output_path = save_validation_payload(payload, arguments.output)
    print(
        "Task 1 browser validation data written: "
        f"{output_path} "
        f"({payload['angular']['sample_count']:,} angles, "
        f"{payload['radial']['n_walks']:,} exact endpoints)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
