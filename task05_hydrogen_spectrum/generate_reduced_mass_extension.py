"""Generate separately validated browser evidence for the Task 5 extension."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import numpy as np

from task05_hydrogen_spectrum.analysis import build_task05_study
from task05_hydrogen_spectrum.constants import (
    HC_EV_NM,
    RYDBERG_CONSTANT_TEXT,
)
from task05_hydrogen_spectrum.reduced_mass_extension import (
    CONSTANT_SOURCE,
    ELECTRON_PROTON_MASS_RATIO,
    ELECTRON_PROTON_MASS_RATIO_TEXT,
    reduced_mass_factor,
    reduced_mass_transition_energy_ev,
    reduced_mass_transition_frequency_hz,
    reduced_mass_transition_wavelength_m,
)


JSON_FILENAME = "reduced_mass_validation.json"
CSV_FILENAME = "reduced_mass_transitions.csv"
SCHEMA_VERSION = "task05-reduced-mass-v1"
CHECK_TOLERANCE = 5.0e-13
FEATURED_PAIRS = ((2, 1), (3, 2), (4, 2), (5, 2), (6, 2))


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


def _line_label(line_name: str | None, initial_n: int, final_n: int) -> str:
    if line_name:
        return line_name
    return f"{initial_n}->{final_n}"


def build_reduced_mass_payload() -> dict[str, Any]:
    """Return the complete extension payload after independent checks pass."""

    study = build_task05_study()
    factor = reduced_mass_factor()
    corrected_energy = reduced_mass_transition_energy_ev(
        study.initial_n, study.final_n
    )
    corrected_frequency = reduced_mass_transition_frequency_hz(
        study.initial_n, study.final_n
    )
    corrected_wavelength_nm = (
        reduced_mass_transition_wavelength_m(study.initial_n, study.final_n)
        * 1.0e9
    )
    wavelength_shift_nm = corrected_wavelength_nm - study.wavelength_nm
    relative_shift = wavelength_shift_nm / study.wavelength_nm

    with localcontext() as context:
        context.prec = 50
        ratio_decimal = Decimal(ELECTRON_PROTON_MASS_RATIO_TEXT)
        factor_decimal = Decimal(1) / (Decimal(1) + ratio_decimal)
        h_alpha_factor = Decimal(1) / Decimal(4) - Decimal(1) / Decimal(9)
        ideal_h_alpha_nm = Decimal("1e9") / (
            Decimal(RYDBERG_CONSTANT_TEXT) * h_alpha_factor
        )
        corrected_h_alpha_nm = ideal_h_alpha_nm * (Decimal(1) + ratio_decimal)

    h_alpha_index = next(
        index
        for index, pair in enumerate(zip(study.initial_n, study.final_n))
        if tuple(int(value) for value in pair) == (3, 2)
    )
    energy_scaling_error = np.max(
        np.abs(corrected_energy / study.photon_energy_ev - factor)
    )
    frequency_scaling_error = np.max(
        np.abs(corrected_frequency / study.frequency_hz - factor)
    )
    wavelength_scaling_error = np.max(
        np.abs(corrected_wavelength_nm / study.wavelength_nm - 1.0 / factor)
    )
    identity_error = np.max(
        np.abs(corrected_energy * corrected_wavelength_nm / HC_EV_NM - 1.0)
    )

    checks = [
        _check("complete transition catalogue", float(study.initial_n.size), 45.0, 0.0),
        _check("Decimal reduced-mass factor", factor, float(factor_decimal), 5.0e-15),
        _check("factor is below ideal limit", float(factor < 1.0), 1.0, 0.0),
        _check("all corrected wavelengths are longer", float(np.all(wavelength_shift_nm > 0.0)), 1.0, 0.0),
        _check("all corrected energies are lower", float(np.all(corrected_energy < study.photon_energy_ev)), 1.0, 0.0),
        _check("all corrected frequencies are lower", float(np.all(corrected_frequency < study.frequency_hz)), 1.0, 0.0),
        _check("transition-independent relative wavelength shift", float(np.max(np.abs(relative_shift - ELECTRON_PROTON_MASS_RATIO))), 0.0, 5.0e-13),
        _check("energy scaling", float(energy_scaling_error), 0.0, 5.0e-15),
        _check("frequency scaling", float(frequency_scaling_error), 0.0, 5.0e-15),
        _check("wavelength scaling", float(wavelength_scaling_error), 0.0, 5.0e-15),
        _check("corrected photon identity", float(identity_error), 0.0, CHECK_TOLERANCE),
        _check("independent Decimal H-alpha wavelength", float(corrected_wavelength_nm[h_alpha_index]), float(corrected_h_alpha_nm), 5.0e-14),
    ]
    if not all(check["passed"] for check in checks):
        failed = ", ".join(check["name"] for check in checks if not check["passed"])
        raise RuntimeError(f"reduced-mass extension validation failed: {failed}")

    transitions = []
    for index in range(study.initial_n.size):
        initial = int(study.initial_n[index])
        final = int(study.final_n[index])
        transitions.append(
            {
                "index": index,
                "initial_n": initial,
                "final_n": final,
                "series_name": study.series_names[index],
                "line_name": study.line_names[index] or "",
                "display_label": _line_label(
                    study.line_names[index], initial, final
                ),
                "ideal_energy_ev": float(study.photon_energy_ev[index]),
                "corrected_energy_ev": float(corrected_energy[index]),
                "ideal_frequency_hz": float(study.frequency_hz[index]),
                "corrected_frequency_hz": float(corrected_frequency[index]),
                "ideal_wavelength_nm": float(study.wavelength_nm[index]),
                "corrected_wavelength_nm": float(corrected_wavelength_nm[index]),
                "wavelength_shift_nm": float(wavelength_shift_nm[index]),
                "wavelength_shift_pm": float(wavelength_shift_nm[index] * 1.0e3),
                "relative_shift": float(relative_shift[index]),
            }
        )

    featured = [
        transition
        for transition in transitions
        if (transition["initial_n"], transition["final_n"]) in FEATURED_PAIRS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "accepted_optional_extension",
        "model": "protium reduced-mass correction to ideal Bohr hydrogen",
        "baseline_model": "ideal stationary-nucleus Bohr hydrogen",
        "constant_source": CONSTANT_SOURCE,
        "constants": {
            "electron_proton_mass_ratio": ELECTRON_PROTON_MASS_RATIO,
            "reduced_mass_factor": factor,
            "rydberg_constant_per_m": float(RYDBERG_CONSTANT_TEXT),
            "hc_ev_nm": HC_EV_NM,
        },
        "equations": {
            "reduced_mass": "mu = m_e M / (m_e + M)",
            "scale_factor": "mu / m_e = 1 / (1 + m_e / M)",
            "wavelength": "lambda_M = lambda_infinity (1 + m_e / M)",
        },
        "scope": {
            "nucleus": "proton (protium)",
            "transition_count": len(transitions),
            "correction": "leading finite nuclear mass only",
            "does_not_model": [
                "line intensity",
                "transition probability",
                "linewidth",
                "fine or hyperfine structure",
                "Lamb shift",
                "literal electron trajectories",
            ],
        },
        "validation": {
            "passed": True,
            "check_count": len(checks),
            "checks": checks,
        },
        "featured_transitions": featured,
        "transitions": transitions,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _write_csv(path: Path, transitions: list[dict[str, Any]]) -> None:
    fieldnames = (
        "initial_n",
        "final_n",
        "series_name",
        "line_name",
        "ideal_energy_ev",
        "corrected_energy_ev",
        "ideal_frequency_hz",
        "corrected_frequency_hz",
        "ideal_wavelength_nm",
        "corrected_wavelength_nm",
        "wavelength_shift_nm",
        "wavelength_shift_pm",
        "relative_shift",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for transition in transitions:
            writer.writerow({name: transition[name] for name in fieldnames})


def generate_reduced_mass_evidence(directory: Path) -> tuple[Path, Path]:
    """Write the validated JSON and CSV transactionally."""

    output_directory = Path(directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    payload = build_reduced_mass_payload()
    with tempfile.TemporaryDirectory(
        dir=output_directory, prefix=".task05-reduced-mass-"
    ) as temporary:
        temporary_directory = Path(temporary)
        json_path = temporary_directory / JSON_FILENAME
        csv_path = temporary_directory / CSV_FILENAME
        _write_json(json_path, payload)
        _write_csv(csv_path, payload["transitions"])
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
        default=Path("data/task05"),
        help="directory for the separate extension evidence",
    )
    arguments = parser.parse_args(argv)
    paths = generate_reduced_mass_evidence(arguments.output_dir)
    print("Task 5 reduced-mass extension: 12/12 checks passed")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
