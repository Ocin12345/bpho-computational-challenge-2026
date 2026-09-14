"""Generate accepted browser evidence for the Task 3 Debye extension."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from task03_thermal_radiation.constants import (
    EINSTEIN_DEBYE_FACTOR,
    MOLAR_GAS_CONSTANT_J_MOL_K,
)
from task03_thermal_radiation.debye_extension import (
    debye_low_temperature_heat_capacity,
    debye_molar_heat_capacity,
)
from task03_thermal_radiation.materials import OFFICIAL_MATERIALS
from task03_thermal_radiation.models import einstein_molar_heat_capacity


DEFAULT_OUTPUT = Path("site/data/task-03-debye-validation.json")


def _relative_error(observed: float, expected: float) -> float:
    return abs(observed - expected) / abs(expected)


def generate_payload() -> dict[str, object]:
    gas_constant = MOLAR_GAS_CONSTANT_J_MOL_K
    three_r = 3.0 * gas_constant
    ratios = np.concatenate((np.array([0.0]), np.linspace(0.01, 2.5, 250)))
    debye = debye_molar_heat_capacity(ratios, 1.0)
    einstein = einstein_molar_heat_capacity(ratios, EINSTEIN_DEBYE_FACTOR)
    low_temperature = debye_low_temperature_heat_capacity(ratios, 1.0)

    convergence_ratios = np.array([0.02, 0.05, 0.1, 0.25, 1.0, 2.5])
    convergence_160 = debye_molar_heat_capacity(
        convergence_ratios,
        1.0,
        quadrature_order=160,
    )
    convergence_320 = debye_molar_heat_capacity(
        convergence_ratios,
        1.0,
        quadrature_order=320,
    )
    convergence_error = float(
        np.max(np.abs(convergence_160 - convergence_320) / three_r)
    )

    low_ratio = 0.02
    low_exact = float(debye_molar_heat_capacity(low_ratio, 1.0))
    low_asymptote = float(debye_low_temperature_heat_capacity(low_ratio, 1.0))
    low_error = _relative_error(low_exact, low_asymptote)

    high_ratio = 100.0
    high_exact = float(debye_molar_heat_capacity(high_ratio, 1.0) / three_r)
    high_series = (
        1.0
        - 1.0 / (20.0 * high_ratio**2)
        + 1.0 / (560.0 * high_ratio**4)
    )
    high_error = _relative_error(high_exact, high_series)

    positive = ratios > 0.0
    model_gap_positive = bool(np.all(debye[positive] > einstein[positive]))
    bounded_monotonic = bool(
        np.all(debye >= 0.0)
        and np.all(debye <= three_r)
        and np.all(np.diff(debye) >= -1e-12)
    )

    diagnostics = []
    for ratio in (0.02, 0.05, 0.1, 0.25, 1.0, 2.0):
        debye_value = float(debye_molar_heat_capacity(ratio, 1.0))
        einstein_value = float(
            einstein_molar_heat_capacity(ratio, EINSTEIN_DEBYE_FACTOR)
        )
        diagnostics.append(
            {
                "temperature_over_debye_temperature": ratio,
                "debye_over_3r": debye_value / three_r,
                "einstein_over_3r": einstein_value / three_r,
                "debye_to_einstein_ratio": debye_value
                / max(einstein_value, np.finfo(float).tiny),
            }
        )

    curve = []
    for ratio, debye_value, einstein_value, low_value in zip(
        ratios,
        debye,
        einstein,
        low_temperature,
    ):
        curve.append(
            {
                "temperature_over_debye_temperature": float(ratio),
                "debye_over_3r": float(debye_value / three_r),
                "einstein_over_3r": float(einstein_value / three_r),
                "low_temperature_cubic_over_3r": (
                    float(low_value / three_r) if ratio <= 0.14 else None
                ),
            }
        )

    checks = {
        "zero_temperature_limit": bool(debye[0] == 0.0 and einstein[0] == 0.0),
        "debye_bounded_and_monotonic": bounded_monotonic,
        "debye_exceeds_einstein_on_displayed_domain": model_gap_positive,
        "low_temperature_cubic_relative_error": low_error,
        "high_temperature_series_relative_error": high_error,
        "quadrature_convergence_over_3r": convergence_error,
    }
    accepted = bool(
        checks["zero_temperature_limit"]
        and checks["debye_bounded_and_monotonic"]
        and checks["debye_exceeds_einstein_on_displayed_domain"]
        and low_error < 1e-10
        and high_error < 1e-12
        and convergence_error < 1e-11
    )

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted": accepted,
        "extension": "Einstein--Debye molar heat-capacity comparison",
        "normalization": {
            "temperature": "T / theta_D",
            "heat_capacity": "C_V / (3R)",
            "einstein_temperature_over_debye_temperature": EINSTEIN_DEBYE_FACTOR,
            "gas_constant_j_mol_k": gas_constant,
        },
        "materials": [
            {
                "name": material.name,
                "symbol": material.symbol,
                "debye_temperature_k": material.debye_temperature_k,
                "einstein_temperature_k": (
                    EINSTEIN_DEBYE_FACTOR * material.debye_temperature_k
                ),
            }
            for material in OFFICIAL_MATERIALS
        ],
        "curve": curve,
        "diagnostics": diagnostics,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = generate_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Task 3 Debye validation written to {args.output}: "
        f"{'PASS' if payload['accepted'] else 'FAIL'}"
    )
    return 0 if payload["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
