#!/usr/bin/env python3
"""Build the compact, browser-ready evidence bundle for Task 03.

The web page never invents benchmark values. This script reduces the validated
CSV outputs to a chart-friendly resolution while preserving their recorded
validation metrics and material constants.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "task03"
TARGET = ROOT / "site" / "data"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rounded(value: str, digits: int = 12) -> float:
    return round(float(value), digits)


def build_bundle() -> dict[str, object]:
    validation = json.loads(
        (SOURCE / "validation_report.json").read_text(encoding="utf-8")
    )
    planck_rows = read_csv("planck_spectra.csv")
    planck_validation = read_csv("planck_validation.csv")
    material_rows = read_csv("einstein_materials.csv")
    heat_rows = read_csv("einstein_heat_capacity.csv")
    normalized_rows = read_csv("einstein_normalized.csv")

    planck_by_temperature: dict[str, list[dict[str, float]]] = {}
    for temperature in (4000, 5000, 6000):
        series = [
            {
                "wavelength_nm": rounded(row["wavelength_nm"], 3),
                "exitance_w_m2_nm": float(
                    row["spectral_exitance_w_m2_nm"]
                ),
                "radiance_w_m2_sr_nm": (
                    float(row["spectral_exitance_w_m2_nm"]) / math.pi
                ),
            }
            for row in planck_rows
            if int(float(row["temperature_k"])) == temperature
            and int(round(float(row["wavelength_nm"]))) % 5 == 0
        ]
        planck_by_temperature[str(temperature)] = series

    heat_by_material: dict[str, list[dict[str, float]]] = {}
    for row in material_rows:
        symbol = row["symbol"]
        heat_by_material[symbol] = [
            {
                "temperature_k": rounded(point["temperature_k"], 3),
                "cv_j_mol_k": rounded(
                    point["molar_heat_capacity_j_mol_k"], 10
                ),
            }
            for point in heat_rows
            if point["symbol"] == symbol
            and int(round(float(point["temperature_k"]))) % 4 == 0
        ]

    normalized_by_material: dict[str, list[dict[str, float]]] = {}
    for material in material_rows:
        symbol = material["symbol"]
        material_curve = [
            row for row in normalized_rows if row["symbol"] == symbol
        ]
        normalized_by_material[symbol] = [
            {
                "reduced_temperature": rounded(
                    row["reduced_temperature"], 4
                ),
                "cv_over_3r": rounded(row["normalized_heat_capacity"], 12),
            }
            for index, row in enumerate(material_curve)
            if index % 5 == 0
        ]

    checks = validation["checks"]
    passed_checks = sum(1 for check in checks if check["passed"])

    return {
        "schema_version": 1,
        "task": "03",
        "generated_from": [
            "data/task03/planck_spectra.csv",
            "data/task03/planck_validation.csv",
            "data/task03/einstein_materials.csv",
            "data/task03/einstein_heat_capacity.csv",
            "data/task03/einstein_normalized.csv",
            "data/task03/validation_report.json",
        ],
        "constants": {
            "planck_j_s": 6.62607015e-34,
            "speed_of_light_m_s": 299792458.0,
            "boltzmann_j_k": 1.380649e-23,
            "gas_constant_j_mol_k": 8.31446261815324,
            "stefan_boltzmann_w_m2_k4": 5.6703744191844314e-8,
            "wien_displacement_m_k": 0.0028977719551851727,
        },
        "validation": {
            "passed": validation["passed"],
            "passed_checks": passed_checks,
            "total_checks": len(checks),
            "largest_planck_integral_relative_error": max(
                float(row["integral_relative_error"])
                for row in planck_validation
            ),
            "largest_wien_peak_relative_error": max(
                float(row["peak_relative_error"]) for row in planck_validation
            ),
            "normalized_collapse_max_absolute_difference": next(
                float(check["observed"])
                for check in checks
                if check["name"] == "einstein_normalized_collapse"
            ),
        },
        "planck": {
            "validation": [
                {
                    "temperature_k": int(float(row["temperature_k"])),
                    "numerical_peak_nm": rounded(row["numerical_peak_nm"], 5),
                    "wien_peak_nm": rounded(row["wien_peak_nm"], 9),
                    "peak_relative_error": float(row["peak_relative_error"]),
                    "numerical_exitance_w_m2": rounded(
                        row["numerical_exitance_w_m2"], 6
                    ),
                    "stefan_boltzmann_w_m2": rounded(
                        row["stefan_boltzmann_w_m2"], 6
                    ),
                    "numerical_radiance_w_m2_sr": rounded(
                        float(row["numerical_exitance_w_m2"]) / math.pi,
                        6,
                    ),
                    "stefan_boltzmann_radiance_w_m2_sr": rounded(
                        float(row["stefan_boltzmann_w_m2"]) / math.pi,
                        6,
                    ),
                    "integral_relative_error": float(
                        row["integral_relative_error"]
                    ),
                }
                for row in planck_validation
            ],
            "series": planck_by_temperature,
        },
        "einstein": {
            "high_temperature_limit_j_mol_k": 3.0 * 8.31446261815324,
            "materials": [
                {
                    "material": row["material"],
                    "symbol": row["symbol"],
                    "debye_temperature_k": rounded(
                        row["debye_temperature_k"], 3
                    ),
                    "einstein_temperature_k": rounded(
                        row["einstein_temperature_k"], 9
                    ),
                    "einstein_frequency_hz": rounded(
                        row["einstein_frequency_hz"], 3
                    ),
                    "official_frequency_1e13_hz": rounded(
                        row["official_frequency_1e13_hz"], 4
                    ),
                }
                for row in material_rows
            ],
            "series": heat_by_material,
            "normalized_series": normalized_by_material,
        },
    }


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle()
    json_text = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"
    (TARGET / "task-03-evidence.json").write_text(
        json_text, encoding="utf-8"
    )
    (TARGET / "task-03-evidence.js").write_text(
        "window.TASK03_EVIDENCE = " + json_text.rstrip() + ";\n",
        encoding="utf-8",
    )
    print(
        "Built Task 03 evidence: "
        f"{bundle['validation']['passed_checks']}/"
        f"{bundle['validation']['total_checks']} checks passed."
    )


if __name__ == "__main__":
    main()
