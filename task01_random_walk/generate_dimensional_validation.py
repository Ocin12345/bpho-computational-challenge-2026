"""Generate accepted browser evidence for the Task 1 dimension extension."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from task01_random_walk.dimensional_extension import (
    run_dimension_study,
    theoretical_normalized_radial_density,
)


DEFAULT_OUTPUT = Path("site/data/task-01-dimensions-validation.json")
DIMENSION_LABELS = {1: "One dimension", 2: "Two dimensions", 3: "Three dimensions"}


def _serialise_study(study: object, bin_count: int = 36) -> dict[str, object]:
    dimension = int(study.dimension)  # type: ignore[attr-defined]
    radii = study.normalized_radii  # type: ignore[attr-defined]
    edges = np.linspace(0.0, 3.6, bin_count + 1)
    density, _ = np.histogram(radii, bins=edges, density=True)
    centres = 0.5 * (edges[:-1] + edges[1:])
    theory = theoretical_normalized_radial_density(centres, dimension)
    slope_ci = 1.96 * study.slope_standard_error  # type: ignore[attr-defined]
    exponent_ci = 1.96 * study.exponent_standard_error  # type: ignore[attr-defined]

    scaling = [
        {
            "n_steps": point.n_steps,
            "mean_squared_displacement": point.mean_squared_displacement,
            "msd_standard_error": point.msd_standard_error,
            "rms_displacement": point.rms_displacement,
            "rms_standard_error": point.rms_standard_error,
        }
        for point in study.scaling  # type: ignore[attr-defined]
    ]
    final_point = study.scaling[-1]  # type: ignore[attr-defined]
    theory_msd = final_point.n_steps * study.step_size**2  # type: ignore[attr-defined]

    return {
        "dimension": dimension,
        "label": DIMENSION_LABELS[dimension],
        "mean_endpoint": study.mean_endpoint.tolist(),  # type: ignore[attr-defined]
        "distribution": {
            "variable": "q = |R| / (s sqrt(N))",
            "bin_edges": edges.tolist(),
            "bin_centres": centres.tolist(),
            "density": density.tolist(),
            "theory_density": theory.tolist(),
            "sample_count": len(radii),
        },
        "scaling": scaling,
        "fit": {
            "model": "r_RMS / s = a sqrt(N)",
            "slope": study.slope,  # type: ignore[attr-defined]
            "slope_standard_error": study.slope_standard_error,  # type: ignore[attr-defined]
            "slope_ci95_half_width": slope_ci,
            "power_model": "r_RMS / s = A N^alpha",
            "exponent": study.exponent,  # type: ignore[attr-defined]
            "exponent_standard_error": study.exponent_standard_error,  # type: ignore[attr-defined]
            "exponent_ci95_half_width": exponent_ci,
        },
        "checks": {
            "final_msd_relative_error": (
                final_point.mean_squared_displacement - theory_msd
            )
            / theory_msd,
            "slope_difference_from_unity": study.slope - 1.0,  # type: ignore[attr-defined]
            "exponent_difference_from_half": study.exponent - 0.5,  # type: ignore[attr-defined]
        },
    }


def generate_payload(
    *, n_walks: int, max_steps: int, step_size: float, seed: int
) -> dict[str, object]:
    dimensions = []
    for dimension in (1, 2, 3):
        study = run_dimension_study(
            dimension,
            n_walks=n_walks,
            max_steps=max_steps,
            step_size=step_size,
            seed=(seed + dimension * 0x9E3779B1) & 0xFFFFFFFF,
        )
        dimensions.append(_serialise_study(study))

    accepted = all(
        abs(item["checks"]["final_msd_relative_error"]) < 0.04  # type: ignore[index]
        and abs(item["fit"]["slope"] - 1.0) < 0.035  # type: ignore[index,operator]
        and abs(item["fit"]["exponent"] - 0.5) < 0.035  # type: ignore[index,operator]
        for item in dimensions
    )
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted": accepted,
        "model": "Exact isotropic fixed-step random walks in 1D, 2D and 3D",
        "parameters": {
            "n_walks": n_walks,
            "max_steps": max_steps,
            "step_size": step_size,
            "master_seed": seed,
        },
        "invariants": {
            "mean_squared_displacement": "E[|R_N|^2] = N s^2",
            "rms_displacement": "r_RMS = s sqrt(N)",
            "coordinate_variance": "Var(X_j) = N s^2 / d",
        },
        "dimensions": dimensions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--walks", type=int, default=12_000)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--step-size", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = generate_payload(
        n_walks=args.walks,
        max_steps=args.max_steps,
        step_size=args.step_size,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Task 1 dimensional validation written to {args.output}: "
        f"{'PASS' if payload['accepted'] else 'FAIL'}"
    )
    return 0 if payload["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
