"""Validated precision extension for Task 6 electron diffraction.

The official competition baseline remains non-relativistic.  This module adds
an explicitly secondary comparison using the relativistic energy-momentum
relation and reports the resulting first-order ring-radius shift.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task06_electron_diffraction.configuration import DEFAULT_CONFIGURATION
from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
)
from task06_electron_diffraction.models import electron_wavelength_m


FloatArray = NDArray[np.float64]
SCHEMA_VERSION = "task06-relativistic-extension-v1"


def _voltage_array(value: ArrayLike) -> FloatArray:
    raw = np.asarray(value)
    if np.issubdtype(raw.dtype, np.bool_) or not np.issubdtype(raw.dtype, np.number):
        raise TypeError("voltage_v must contain real numbers")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError("voltage_v must contain real numbers")
    voltage = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(voltage)):
        raise ValueError("voltage_v must be finite")
    if np.any(voltage < DEFAULT_CONFIGURATION.voltage_min_v) or np.any(
        voltage > DEFAULT_CONFIGURATION.voltage_max_v
    ):
        raise ValueError("voltage_v must be within 1000 to 5000 V inclusive")
    return voltage


def relativistic_momentum_kg_m_s(voltage_v: ArrayLike) -> FloatArray:
    """Return momentum from K(K + 2mc²) = p²c² for K = eV."""

    voltage = _voltage_array(voltage_v)
    kinetic_energy_j = ELEMENTARY_CHARGE_C * voltage
    rest_energy_j = ELECTRON_MASS_KG * SPEED_OF_LIGHT_M_S**2
    return np.asarray(
        np.sqrt(kinetic_energy_j * (kinetic_energy_j + 2.0 * rest_energy_j))
        / SPEED_OF_LIGHT_M_S,
        dtype=np.float64,
    )


def relativistic_wavelength_m(voltage_v: ArrayLike) -> FloatArray:
    """Return the relativistic de Broglie wavelength h/p."""

    return np.asarray(
        PLANCK_CONSTANT_J_S / relativistic_momentum_kg_m_s(voltage_v),
        dtype=np.float64,
    )


def first_order_radius_from_wavelength_m(
    wavelength_m: ArrayLike,
    spacing_m: float,
    tube_radius_m: float = DEFAULT_CONFIGURATION.tube_radius_m,
) -> FloatArray:
    """Return x = r sin(2φ), with φ = 2 asin(λ/2d), for first order."""

    wavelength = np.asarray(wavelength_m, dtype=np.float64)
    if not np.all(np.isfinite(wavelength)) or np.any(wavelength <= 0.0):
        raise ValueError("wavelength_m must be finite and positive")
    if not np.isfinite(spacing_m) or spacing_m <= 0.0:
        raise ValueError("spacing_m must be finite and positive")
    if not np.isfinite(tube_radius_m) or tube_radius_m <= 0.0:
        raise ValueError("tube_radius_m must be finite and positive")
    ratio = wavelength / (2.0 * spacing_m)
    if np.any(ratio > 1.0):
        raise ValueError("first order is outside the Bragg domain")
    phi = 2.0 * np.arcsin(ratio)
    return np.asarray(tube_radius_m * np.sin(2.0 * phi), dtype=np.float64)


def _records() -> list[dict[str, Any]]:
    config = DEFAULT_CONFIGURATION
    voltages = np.linspace(
        config.voltage_min_v,
        config.voltage_max_v,
        config.voltage_count,
        dtype=np.float64,
    )
    wavelength_nonrel = electron_wavelength_m(voltages)
    wavelength_rel = relativistic_wavelength_m(voltages)
    correction_percent = 100.0 * (wavelength_rel / wavelength_nonrel - 1.0)

    radius_data: dict[str, tuple[FloatArray, FloatArray]] = {}
    for spacing in config.spacings:
        radius_data[spacing.identifier] = (
            first_order_radius_from_wavelength_m(
                wavelength_nonrel, spacing.spacing_m, config.tube_radius_m
            ),
            first_order_radius_from_wavelength_m(
                wavelength_rel, spacing.spacing_m, config.tube_radius_m
            ),
        )

    records: list[dict[str, Any]] = []
    for index, voltage in enumerate(voltages):
        record: dict[str, Any] = {
            "voltage_v": int(round(float(voltage))),
            "voltage_kv": float(voltage / 1000.0),
            "wavelength_nonrel_pm": float(wavelength_nonrel[index] * 1.0e12),
            "wavelength_rel_pm": float(wavelength_rel[index] * 1.0e12),
            "wavelength_correction_percent": float(correction_percent[index]),
        }
        for spacing in config.spacings:
            radius_nonrel, radius_rel = radius_data[spacing.identifier]
            record[spacing.identifier] = {
                "radius_nonrel_mm": float(radius_nonrel[index] * 1.0e3),
                "radius_rel_mm": float(radius_rel[index] * 1.0e3),
                "radius_shift_um": float(
                    (radius_rel[index] - radius_nonrel[index]) * 1.0e6
                ),
            }
        records.append(record)
    return records


def validate_relativistic_evidence(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Recompute all extension quantities and return explicit validation checks."""

    records = evidence.get("records")
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    add(
        "schema",
        evidence.get("schema_version") == SCHEMA_VERSION,
        "The extension schema is explicitly versioned.",
    )
    if not isinstance(records, list) or len(records) != 401:
        add("voltage_grid", False, "The extension must contain 401 voltage records.")
        return checks

    voltage = np.asarray([row["voltage_v"] for row in records], dtype=np.float64)
    expected_voltage = np.arange(1000.0, 5000.0 + 10.0, 10.0)
    add(
        "voltage_grid",
        np.array_equal(voltage, expected_voltage),
        "Voltage runs from 1 to 5 kV in exact 10 V increments.",
    )

    nonrel = np.asarray(
        [row["wavelength_nonrel_pm"] for row in records], dtype=np.float64
    ) * 1.0e-12
    rel = np.asarray(
        [row["wavelength_rel_pm"] for row in records], dtype=np.float64
    ) * 1.0e-12
    expected_nonrel = electron_wavelength_m(voltage)
    expected_rel = relativistic_wavelength_m(voltage)
    add(
        "official_baseline_preserved",
        np.allclose(nonrel, expected_nonrel, rtol=5.0e-14, atol=0.0),
        "The official non-relativistic wavelength remains byte-for-value unchanged.",
    )
    add(
        "relativistic_wavelength",
        np.allclose(rel, expected_rel, rtol=5.0e-14, atol=0.0),
        "Every relativistic wavelength follows h/p with K(K+2mc²)=p²c².",
    )

    momentum = PLANCK_CONSTANT_J_S / rel
    kinetic = ELEMENTARY_CHARGE_C * voltage
    energy_lhs = (momentum * SPEED_OF_LIGHT_M_S) ** 2
    energy_rhs = kinetic * (
        kinetic + 2.0 * ELECTRON_MASS_KG * SPEED_OF_LIGHT_M_S**2
    )
    add(
        "energy_momentum_identity",
        np.allclose(energy_lhs, energy_rhs, rtol=2.0e-13, atol=0.0),
        "The generated wavelengths satisfy the relativistic energy-momentum identity.",
    )

    correction = np.asarray(
        [row["wavelength_correction_percent"] for row in records],
        dtype=np.float64,
    )
    expected_correction = 100.0 * (expected_rel / expected_nonrel - 1.0)
    add(
        "wavelength_correction",
        np.allclose(correction, expected_correction, rtol=2.0e-12, atol=2.0e-14)
        and np.all(correction < 0.0)
        and np.all(np.diff(correction) < 0.0),
        "Relativity shortens the wavelength, with a monotonic correction across 1–5 kV.",
    )

    for spacing in DEFAULT_CONFIGURATION.spacings:
        family = spacing.identifier
        nonrel_radius = np.asarray(
            [row[family]["radius_nonrel_mm"] for row in records], dtype=np.float64
        ) * 1.0e-3
        rel_radius = np.asarray(
            [row[family]["radius_rel_mm"] for row in records], dtype=np.float64
        ) * 1.0e-3
        shift = np.asarray(
            [row[family]["radius_shift_um"] for row in records], dtype=np.float64
        )
        expected_nonrel_radius = first_order_radius_from_wavelength_m(
            expected_nonrel, spacing.spacing_m
        )
        expected_rel_radius = first_order_radius_from_wavelength_m(
            expected_rel, spacing.spacing_m
        )
        add(
            f"{family}_exact_geometry",
            np.allclose(nonrel_radius, expected_nonrel_radius, rtol=5.0e-14, atol=0.0)
            and np.allclose(rel_radius, expected_rel_radius, rtol=5.0e-14, atol=0.0),
            f"Both {family} radius series retain the exact x=r sin(2φ) projection.",
        )
        add(
            f"{family}_radius_shift",
            np.allclose(
                shift,
                (expected_rel_radius - expected_nonrel_radius) * 1.0e6,
                rtol=2.0e-12,
                atol=2.0e-12,
            )
            and np.all(shift < 0.0),
            f"The {family} relativistic first-order ring is consistently inward.",
        )

    return checks


def build_relativistic_evidence() -> dict[str, Any]:
    """Build the deterministic extension evidence and its validation report."""

    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "secondary precision extension; official baseline preserved",
        "formulae": {
            "official_nonrelativistic": "lambda = h / sqrt(2 m_e e V)",
            "relativistic": "lambda = h c / sqrt(e V (e V + 2 m_e c^2))",
            "photographic_radius": "x = r sin(2 phi)",
        },
        "configuration": {
            "voltage_min_v": 1000,
            "voltage_max_v": 5000,
            "voltage_step_v": 10,
            "tube_radius_m": DEFAULT_CONFIGURATION.tube_radius_m,
            "spacings_m": {
                spacing.identifier: spacing.spacing_m
                for spacing in DEFAULT_CONFIGURATION.spacings
            },
        },
        "records": _records(),
    }
    checks = validate_relativistic_evidence(evidence)
    evidence["validation"] = {
        "passed": all(check["passed"] for check in checks),
        "check_count": len(checks),
        "checks": checks,
    }
    if not evidence["validation"]["passed"]:
        raise RuntimeError("Task 6 relativistic extension validation failed")
    return evidence


def write_relativistic_evidence(path: Path) -> Path:
    """Write deterministic JSON only after the complete extension validates."""

    evidence = build_relativistic_evidence()
    payload = json.dumps(
        evidence,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)
    return path


def corrupted_copy(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return a deliberately corrupted copy for focused failure tests."""

    copy = deepcopy(evidence)
    copy["records"][0]["wavelength_rel_pm"] *= 1.01
    copy.pop("validation", None)
    return copy


__all__ = [
    "SCHEMA_VERSION",
    "build_relativistic_evidence",
    "corrupted_copy",
    "first_order_radius_from_wavelength_m",
    "relativistic_momentum_kg_m_s",
    "relativistic_wavelength_m",
    "validate_relativistic_evidence",
    "write_relativistic_evidence",
]
