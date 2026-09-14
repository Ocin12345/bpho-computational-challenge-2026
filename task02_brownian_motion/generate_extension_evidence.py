"""Generate deterministic website evidence for the Task 2 hard-disc extension."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from task02_brownian_motion.brownian_motion import BrownianParameters, run_simulation
from task02_brownian_motion.small_particle_extension import (
    resolve_small_small_collisions,
    run_hard_disc_simulation,
)


DEFAULT_OUTPUT = Path("site/data/task-02-extension-evidence.json")


def _controlled_collision_evidence(seed: int, count: int = 2_000) -> dict[str, float | int]:
    rng = np.random.default_rng(seed)
    maximum_momentum_error = 0.0
    maximum_energy_error = 0.0
    maximum_penetration = 0.0
    impulses = 0
    radius = 0.16
    mass = BrownianParameters().small_mass_kg

    for _ in range(count):
        angle = rng.uniform(0.0, 2.0 * np.pi)
        normal = np.array([np.cos(angle), np.sin(angle)])
        positions = np.vstack((np.zeros(2), 1.9 * radius * normal))
        centre_velocity = rng.normal(0.0, 0.3, size=2)
        tangent = np.array([-normal[1], normal[0]])
        relative_tangent = rng.normal(0.0, 0.3)
        approach_speed = rng.uniform(0.05, 1.0)
        velocities = np.vstack(
            (
                centre_velocity + 0.5 * approach_speed * normal - 0.5 * relative_tangent * tangent,
                centre_velocity - 0.5 * approach_speed * normal + 0.5 * relative_tangent * tangent,
            )
        )
        report = resolve_small_small_collisions(
            positions,
            velocities,
            radius_nm=radius,
            mass_kg=mass,
            restitution=1.0,
            clearance_nm=1.0e-9 * radius,
        )
        impulses += report.impulses_applied
        maximum_momentum_error = max(
            maximum_momentum_error,
            report.maximum_normalized_momentum_error,
        )
        maximum_energy_error = max(
            maximum_energy_error,
            report.maximum_normalized_energy_error,
        )
        maximum_penetration = max(
            maximum_penetration,
            report.maximum_residual_penetration_nm,
        )

    return {
        "sample_count": count,
        "impulses_applied": impulses,
        "maximum_normalized_momentum_error": maximum_momentum_error,
        "maximum_normalized_energy_error": maximum_energy_error,
        "maximum_residual_penetration_nm": maximum_penetration,
    }


def _sample_path(times: np.ndarray, positions: np.ndarray, count: int = 96) -> dict[str, list[float]]:
    indices = np.unique(
        np.rint(np.linspace(0, len(times) - 1, min(count, len(times)))).astype(int)
    )
    start = positions[0]
    displacement = positions[indices] - start
    return {
        "time_ps": times[indices].astype(float).tolist(),
        "x_nm": displacement[:, 0].astype(float).tolist(),
        "y_nm": displacement[:, 1].astype(float).tolist(),
    }


def generate_payload(*, seed: int = 2026) -> dict[str, object]:
    parameters = BrownianParameters(
        n_small=64,
        box_size_nm=8.0,
        max_time_ps=12.0,
        max_collision_passes=32,
        seed=seed,
    )
    baseline = run_simulation(parameters, max_frames=96)
    hard_disc = run_hard_disc_simulation(parameters, max_frames=96)
    controlled = _controlled_collision_evidence(seed ^ 0xA5A5A5A5)
    baseline_times = baseline.time_grid.times_ps
    hard_times = hard_disc.times_ps

    checks = {
        "controlled_momentum_error_below_1e-12": controlled[
            "maximum_normalized_momentum_error"
        ]
        < 1.0e-12,
        "controlled_energy_error_below_1e-12": controlled[
            "maximum_normalized_energy_error"
        ]
        < 1.0e-12,
        "hard_disc_energy_drift_below_1e-12": abs(
            hard_disc.relative_kinetic_energy_drift
        )
        < 1.0e-12,
        "hard_disc_has_gas_collisions": hard_disc.total_small_small_impulses > 0,
        "hard_disc_has_no_direction_resets": hard_disc.direction_resets == 0,
        "baseline_has_direction_resets": baseline.diagnostics.total_direction_resets > 0,
    }
    accepted = all(checks.values())
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted": accepted,
        "model": "Task 2 mutually exclusive heat-bath comparison",
        "parameters": {
            "n_small": parameters.n_small,
            "box_size_nm": parameters.box_size_nm,
            "duration_ps": parameters.max_time_ps,
            "small_radius_nm": parameters.small_radius_nm,
            "large_radius_nm": parameters.large_radius_nm,
            "mass_ratio": parameters.large_mass_kg / parameters.small_mass_kg,
            "temperature_k": parameters.gas_temperature_k,
            "seed": seed,
        },
        "controlled_collisions": controlled,
        "checks": checks,
        "modes": {
            "random_reset": {
                "label": "Random direction bath",
                "direction_resets": baseline.diagnostics.total_direction_resets,
                "small_small_impulses": 0,
                "small_large_contacts": baseline.diagnostics.total_contacts,
                "path": _sample_path(baseline_times, baseline.large_positions_nm),
            },
            "hard_disc": {
                "label": "Explicit hard-disc bath",
                "direction_resets": hard_disc.direction_resets,
                "small_small_contacts": hard_disc.total_small_small_contacts,
                "small_small_impulses": hard_disc.total_small_small_impulses,
                "small_large_contacts": hard_disc.total_small_large_contacts,
                "relative_kinetic_energy_drift": hard_disc.relative_kinetic_energy_drift,
                "maximum_normalized_momentum_error": hard_disc.maximum_normalized_momentum_error,
                "maximum_normalized_energy_error": hard_disc.maximum_normalized_energy_error,
                "path": _sample_path(hard_times, hard_disc.tracer_positions_nm),
            },
        },
        "scope": [
            "The baseline has direction resets and no small-small collisions.",
            "The hard-disc extension has small-small collisions and no direction resets.",
            "The extension test bed uses 64 gas particles so exact pair contacts remain interactive.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = generate_payload(seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Task 2 extension evidence written to {args.output}: "
        f"{'PASS' if payload['accepted'] else 'FAIL'}"
    )
    return 0 if payload["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
