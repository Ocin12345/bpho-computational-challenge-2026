"""Generate separate validated evidence for the Task 7 superposition lab."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION
from task07_particle_in_box.models import energy_ev
from task07_particle_in_box.superposition_extension import (
    beat_period_s,
    dimensionless_probability_density,
    energy_uncertainty_ev,
    expected_position_over_width,
    left_half_probability,
    mean_energy_ev,
)


JSON_FILENAME = "superposition_validation.json"
CSV_FILENAME = "superposition_phase_anchors.csv"
SCHEMA_VERSION = "task07-superposition-v1"
PHASES_RAD = np.linspace(0.0, 2.0 * np.pi, 17, dtype=np.float64)


def _relative_error(observed: float, expected: float) -> float:
    if expected == 0.0:
        return abs(observed)
    return abs(observed - expected) / abs(expected)


def _check(
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
) -> dict[str, Any]:
    return {
        "name": name,
        "observed": observed,
        "expected": expected,
        "tolerance": tolerance,
        "passed": math.isfinite(observed)
        and _relative_error(observed, expected) <= tolerance,
    }


def build_superposition_payload() -> dict[str, Any]:
    """Build all phase anchors and validation checks in memory."""

    configuration = DEFAULT_CONFIGURATION
    mass = configuration.particle_mass_kg
    width = configuration.box_width_m
    positions = np.linspace(0.0, 1.0, 4001, dtype=np.float64)
    densities = dimensionless_probability_density(
        positions[:, None], PHASES_RAD[None, :]
    )
    normalizations = np.trapezoid(densities, positions, axis=0)
    numerical_means = np.trapezoid(
        positions[:, None] * densities, positions, axis=0
    )
    left_mask = positions <= 0.5
    numerical_left = np.trapezoid(
        densities[left_mask], positions[left_mask], axis=0
    )
    analytical_means = expected_position_over_width(PHASES_RAD)
    analytical_left = left_half_probability(PHASES_RAD)
    energies = energy_ev(np.asarray([1, 2], dtype=np.int64), mass, width)
    period = beat_period_s(mass, width)
    mean_energy = mean_energy_ev(mass, width)
    energy_uncertainty = energy_uncertainty_ev(mass, width)

    checks = [
        _check("phase anchor count", float(PHASES_RAD.size), 17.0, 0.0),
        _check("density normalization", float(np.max(np.abs(normalizations - 1.0))), 0.0, 2.0e-12),
        _check("infinite-wall left boundary", float(np.max(np.abs(densities[0]))), 0.0, 2.0e-15),
        _check("infinite-wall right boundary", float(np.max(np.abs(densities[-1]))), 0.0, 2.0e-15),
        _check("non-negative density", float(np.min(densities) >= 0.0), 1.0, 0.0),
        _check("analytical mean position", float(np.max(np.abs(numerical_means - analytical_means))), 0.0, 2.0e-7),
        _check("analytical left probability", float(np.max(np.abs(numerical_left - analytical_left))), 0.0, 2.0e-7),
        _check("full-cycle density revival", float(np.max(np.abs(densities[:, 0] - densities[:, -1]))), 0.0, 2.0e-14),
        _check("half-cycle mirror symmetry", float(np.max(np.abs(densities[:, 0] - densities[::-1, 8]))), 0.0, 2.0e-14),
        _check("quarter-cycle centred mean", float(analytical_means[4]), 0.5, 2.0e-15),
        _check("energy expectation", mean_energy / float(energies[0]), 2.5, 2.0e-15),
        _check("energy uncertainty", energy_uncertainty / float(energies[0]), 1.5, 2.0e-15),
        _check("positive beat period", float(period > 0.0), 1.0, 0.0),
        _check("mean position remains inside box", float(np.all((analytical_means > 0.0) & (analytical_means < 1.0))), 1.0, 0.0),
    ]
    if not all(check["passed"] for check in checks):
        failed = ", ".join(check["name"] for check in checks if not check["passed"])
        raise RuntimeError(f"superposition validation failed: {failed}")

    anchors = []
    for index, phase in enumerate(PHASES_RAD):
        anchors.append(
            {
                "phase_index": index,
                "phase_rad": float(phase),
                "phase_deg": float(np.degrees(phase)),
                "time_fraction": float(phase / (2.0 * np.pi)),
                "time_fs": float(period * phase / (2.0 * np.pi) * 1.0e15),
                "expected_position_over_width": float(analytical_means[index]),
                "left_half_probability": float(analytical_left[index]),
                "normalization": float(normalizations[index]),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "accepted_optional_extension",
        "model": "equal coherent superposition of infinite-well states n=1 and n=2",
        "baseline_model": "stationary states in a one-dimensional infinite square well",
        "configuration": {
            "particle": "electron",
            "particle_mass_kg": mass,
            "box_width_m": width,
            "box_width_nm": width * 1.0e9,
            "states": [1, 2],
            "probabilities": [0.5, 0.5],
            "phase_anchor_count": len(anchors),
        },
        "derived": {
            "energy_1_ev": float(energies[0]),
            "energy_2_ev": float(energies[1]),
            "energy_gap_ev": float(energies[1] - energies[0]),
            "mean_energy_ev": mean_energy,
            "energy_uncertainty_ev": energy_uncertainty,
            "beat_period_s": period,
            "beat_period_fs": period * 1.0e15,
            "minimum_expected_position_over_width": float(np.min(analytical_means)),
            "maximum_expected_position_over_width": float(np.max(analytical_means)),
        },
        "equations": {
            "state": "Psi = (psi_1 + psi_2) / sqrt(2)",
            "relative_phase": "theta = (E_2 - E_1) t / hbar",
            "density": "a|Psi|^2 = sin^2(pi u) + sin^2(2 pi u) + 2 cos(theta) sin(pi u) sin(2 pi u)",
            "mean_position": "<x>/a = 1/2 - 16 cos(theta)/(9 pi^2)",
        },
        "scope": {
            "manual_phase_control": True,
            "does_not_model": [
                "measurement collapse",
                "decoherence",
                "finite walls",
                "particle trajectories",
                "interactions",
            ],
        },
        "validation": {
            "passed": True,
            "check_count": len(checks),
            "checks": checks,
        },
        "phase_anchors": anchors,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _write_csv(path: Path, anchors: list[dict[str, Any]]) -> None:
    fieldnames = tuple(anchors[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(anchors)


def generate_superposition_evidence(directory: Path) -> tuple[Path, Path]:
    """Write JSON and CSV extension evidence transactionally."""

    output_directory = Path(directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    payload = build_superposition_payload()
    with tempfile.TemporaryDirectory(
        dir=output_directory, prefix=".task07-superposition-"
    ) as temporary:
        temporary_directory = Path(temporary)
        json_path = temporary_directory / JSON_FILENAME
        csv_path = temporary_directory / CSV_FILENAME
        _write_json(json_path, payload)
        _write_csv(csv_path, payload["phase_anchors"])
        destinations = (
            output_directory / JSON_FILENAME,
            output_directory / CSV_FILENAME,
        )
        for source, destination in zip((json_path, csv_path), destinations):
            os.replace(source, destination)
    return destinations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/task07"),
    )
    arguments = parser.parse_args(argv)
    paths = generate_superposition_evidence(arguments.output_dir)
    print("Task 7 superposition extension: 14/14 checks passed")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
