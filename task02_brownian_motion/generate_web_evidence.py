"""Build the bounded, source-backed evidence payload for the Task 2 website."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

try:
    from .brownian_motion import BrownianParameters
except ImportError:  # pragma: no cover - direct script execution
    from brownian_motion import BrownianParameters


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = PROJECT_ROOT / "task02_brownian_motion"
DEFAULT_OUTPUT = PROJECT_ROOT / "site" / "data" / "task-02-evidence.json"
DEFAULT_JAVASCRIPT_OUTPUT = (
    PROJECT_ROOT / "site" / "data" / "task-02-evidence.js"
)
ANALYSIS_REPORT = TASK_ROOT / "analysis" / "analysis_report.json"
BASELINE_MSD = TASK_ROOT / "analysis" / "baseline_msd.csv"
RUN_METRICS = TASK_ROOT / "analysis" / "run_metrics.csv"
VALIDATION_REPORT = TASK_ROOT / "validation" / "reference_validation.json"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def _bounded_series(
    rows: list[dict[str, str]],
    *,
    target_points: int = 241,
) -> list[dict[str, float]]:
    """Downsample a time series deterministically while retaining both ends."""

    if len(rows) <= target_points:
        selected = rows
    else:
        stride = math.ceil((len(rows) - 1) / (target_points - 1))
        selected = rows[::stride]
        if selected[-1] is not rows[-1]:
            selected.append(rows[-1])

    return [
        {
            "time_ps": _float(row, "time_ps"),
            "mean_x_nm": _float(row, "mean_x_nm"),
            "mean_y_nm": _float(row, "mean_y_nm"),
            "msd_nm2": _float(row, "msd_nm2"),
            "msd_ci_low_nm2": _float(row, "msd_ci_low_nm2"),
            "msd_ci_high_nm2": _float(row, "msd_ci_high_nm2"),
        }
        for row in selected
    ]


def build_payload() -> dict[str, Any]:
    analysis = _read_json(ANALYSIS_REPORT)
    validation = _read_json(VALIDATION_REPORT)
    if not analysis.get("passed") or not validation.get("passed"):
        raise RuntimeError("Task 2 source reports must pass before web export")

    baseline = next(
        summary
        for summary in analysis["summaries"]
        if summary["summary_id"] == "baseline_64"
    )
    baseline_rows = _read_csv(BASELINE_MSD)
    endpoint_rows = [
        row
        for row in _read_csv(RUN_METRICS)
        if row["configuration_id"] == "baseline"
    ]
    if len(endpoint_rows) != int(baseline["run_count"]):
        raise RuntimeError("baseline endpoint count does not match analysis report")

    parameters = BrownianParameters()
    fit_start = float(analysis["design"]["fit_start_ps"])
    fit_end = float(analysis["design"]["fit_end_ps"])

    return {
        "schema_version": 1,
        "model": "BPhO 2026 Task 2 collision-driven Brownian motion",
        "passed": True,
        "reference_parameters": {
            "n_small": parameters.n_small,
            "small_mass_kg": parameters.small_mass_kg,
            "large_mass_kg": parameters.large_mass_kg,
            "mass_ratio": parameters.large_mass_kg / parameters.small_mass_kg,
            "small_radius_nm": parameters.small_radius_nm,
            "large_radius_nm": parameters.large_radius_nm,
            "box_size_nm": parameters.box_size_nm,
            "gas_temperature_k": parameters.gas_temperature_k,
            "small_speed_nm_per_ps": parameters.small_speed_nm_per_ps,
            "knudsen_parameter": parameters.knudsen_parameter,
            "randomization_interval_ps": parameters.randomization_interval_ps,
            "restitution": parameters.restitution,
            "max_time_ps": parameters.max_time_ps,
            "time_step_ps": parameters.automatic_time_step_upper_bound_ps,
            "seed": parameters.seed,
        },
        "ensemble": {
            "run_count": int(baseline["run_count"]),
            "fit_window_ps": [fit_start, fit_end],
            "diffusion_coefficient_nm2_per_ps": baseline[
                "diffusion_coefficient_nm2_per_ps"
            ],
            "diffusion_ci_nm2_per_ps": [
                baseline["diffusion_ci_low_nm2_per_ps"],
                baseline["diffusion_ci_high_nm2_per_ps"],
            ],
            "msd_fit_slope_nm2_per_ps": baseline[
                "msd_fit_slope_nm2_per_ps"
            ],
            "msd_fit_intercept_nm2": baseline["msd_fit_intercept_nm2"],
            "msd_fit_r_squared": baseline["msd_fit_r_squared"],
            "final_mean_x_nm": baseline["final_mean_x_nm"],
            "final_mean_x_ci_nm": [
                baseline["final_mean_x_ci_low_nm"],
                baseline["final_mean_x_ci_high_nm"],
            ],
            "final_mean_y_nm": baseline["final_mean_y_nm"],
            "final_mean_y_ci_nm": [
                baseline["final_mean_y_ci_low_nm"],
                baseline["final_mean_y_ci_high_nm"],
            ],
            "final_rms_displacement_nm": baseline[
                "final_rms_displacement_nm"
            ],
            "series": _bounded_series(baseline_rows),
            "source_series_points": len(baseline_rows),
            "endpoints": [
                {
                    "seed": int(row["seed"]),
                    "x_nm": _float(row, "final_displacement_x_nm"),
                    "y_nm": _float(row, "final_displacement_y_nm"),
                }
                for row in endpoint_rows
            ],
        },
        "validation": {
            "minimum_observed_order": min(
                row["observed_order_from_previous"]
                for row in validation["controlled_convergence"]
                if row["observed_order_from_previous"] is not None
            ),
            "controlled_convergence": validation["controlled_convergence"],
            "reference_refinement": validation["reference_refinement"],
            "worst_normalized_collision_error": max(
                max(
                    row["maximum_normalized_momentum_error"],
                    row["maximum_normalized_restitution_error"],
                    row["maximum_normalized_energy_identity_error"],
                )
                for row in validation["reference_refinement"]
            ),
            "maximum_residual_penetration_nm": max(
                row["maximum_residual_penetration_nm"]
                for row in validation["reference_refinement"]
            ),
        },
        "scope": {
            "statement": (
                "The measured diffusion coefficient belongs to this finite, "
                "two-dimensional stochastic heat-bath model."
            ),
            "small_small_collisions": "not modelled explicitly",
            "walls": "reflective square boundary",
            "large_initial_velocity": "zero",
        },
        "provenance": {
            "analysis_report": str(ANALYSIS_REPORT.relative_to(PROJECT_ROOT)),
            "baseline_msd": str(BASELINE_MSD.relative_to(PROJECT_ROOT)),
            "run_metrics": str(RUN_METRICS.relative_to(PROJECT_ROOT)),
            "validation_report": str(
                VALIDATION_REPORT.relative_to(PROJECT_ROOT)
            ),
        },
    }


def write_payload(output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def write_javascript_payload(
    output: Path = DEFAULT_JAVASCRIPT_OUTPUT,
) -> Path:
    """Write the same evidence as a file:// compatible browser payload."""

    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        build_payload(),
        separators=(",", ":"),
        sort_keys=True,
    )
    output.write_text(
        f"window.TASK02_EVIDENCE = {serialized};\n",
        encoding="utf-8",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--javascript-output",
        type=Path,
        default=DEFAULT_JAVASCRIPT_OUTPUT,
    )
    arguments = parser.parse_args()
    output = write_payload(arguments.output.resolve())
    javascript_output = write_javascript_payload(
        arguments.javascript_output.resolve(),
    )
    print(f"Wrote {output}")
    print(f"Wrote {javascript_output}")


if __name__ == "__main__":
    main()
