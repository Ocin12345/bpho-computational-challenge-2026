"""Validated deterministic data generation for Task 3."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np

from task03_thermal_radiation.analysis import (
    EinsteinStudyResult,
    PlanckStudyResult,
    build_einstein_study,
    build_planck_study,
)
from task03_thermal_radiation.configuration import (
    DEFAULT_CONFIGURATION,
    Task03Configuration,
)
from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    EINSTEIN_DEBYE_FACTOR,
    MOLAR_GAS_CONSTANT_J_MOL_K,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
    STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
    WIEN_DISPLACEMENT_CONSTANT_M_K,
)
from task03_thermal_radiation.materials import (
    EinsteinMaterial,
    OFFICIAL_MATERIALS,
)
from task03_thermal_radiation.validation import (
    Task03ValidationReport,
    validate_task03,
)


DEFAULT_DATA_DIRECTORY = Path("data/task03")
DEFAULT_FIGURE_DIRECTORY = Path("figures/task03")
MATHEMATICAL_SPECIFICATION_PATH = (
    "task03_thermal_radiation/MATHEMATICAL_MODEL.md"
)
DATA_FILENAMES = (
    "planck_spectra.csv",
    "planck_validation.csv",
    "einstein_materials.csv",
    "einstein_heat_capacity.csv",
    "einstein_normalized.csv",
    "validation_report.json",
    "reproducibility_manifest.json",
)
FIGURE_FILENAMES = (
    "planck_spectra.png",
    "planck_spectra.svg",
    "planck_validation.png",
    "planck_validation.svg",
    "einstein_heat_capacity.png",
    "einstein_heat_capacity.svg",
    "einstein_normalized.png",
    "einstein_normalized.svg",
    "task03_summary.png",
    "task03_summary.svg",
)


@dataclass(frozen=True)
class Task03DataGenerationResult:
    """Validated report and ordered paths produced by one data-only run."""

    report: Task03ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task03ValidationReport):
            raise TypeError("report must be a Task03ValidationReport")
        if not self.report.passed:
            raise ValueError("generation result requires a passing report")
        paths = tuple(Path(path) for path in self.output_paths)
        if tuple(path.name for path in paths) != DATA_FILENAMES:
            raise ValueError("output_paths must follow the frozen file order")
        object.__setattr__(self, "output_paths", paths)


def _format_float(value: float) -> str:
    """Return a finite float with round-trip double-precision text."""

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("serialized numerical values must be finite")
    return format(normalized, ".17g")


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: Sequence[tuple[str, ...]],
) -> None:
    """Write one UTF-8 CSV with the frozen line-ending convention."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_planck_spectra(path: Path, result: PlanckStudyResult) -> None:
    rows = tuple(
        (
            _format_float(temperature),
            _format_float(wavelength),
            _format_float(result.spectral_exitance_w_m2_nm[t_index, w_index]),
        )
        for t_index, temperature in enumerate(result.temperatures_k)
        for w_index, wavelength in enumerate(result.wavelengths_nm)
    )
    _write_csv(
        path,
        (
            "temperature_k",
            "wavelength_nm",
            "spectral_exitance_w_m2_nm",
        ),
        rows,
    )


def _write_planck_validation(path: Path, result: PlanckStudyResult) -> None:
    rows = []
    for index, temperature in enumerate(result.temperatures_k):
        numerical_peak = result.numerical_peak_wavelength_m[index] * 1.0e9
        expected_peak = result.wien_peak_wavelength_m[index] * 1.0e9
        peak_error = abs(numerical_peak - expected_peak) / expected_peak
        numerical_exitance = result.numerical_integrated_exitance_w_m2[index]
        expected_exitance = result.stefan_boltzmann_exitance_w_m2[index]
        integral_error = (
            abs(numerical_exitance - expected_exitance) / expected_exitance
        )
        rows.append(
            (
                _format_float(temperature),
                _format_float(numerical_peak),
                _format_float(expected_peak),
                _format_float(peak_error),
                _format_float(numerical_exitance),
                _format_float(expected_exitance),
                _format_float(integral_error),
            )
        )
    _write_csv(
        path,
        (
            "temperature_k",
            "numerical_peak_nm",
            "wien_peak_nm",
            "peak_relative_error",
            "numerical_exitance_w_m2",
            "stefan_boltzmann_w_m2",
            "integral_relative_error",
        ),
        tuple(rows),
    )


def _write_einstein_materials(path: Path, result: EinsteinStudyResult) -> None:
    rows = tuple(
        (
            material.name,
            material.symbol,
            _format_float(material.debye_temperature_k),
            _format_float(result.einstein_temperatures_k[index]),
            _format_float(result.einstein_frequencies_hz[index]),
            f"{material.official_frequency_1e13_hz:.4f}",
        )
        for index, material in enumerate(result.materials)
    )
    _write_csv(
        path,
        (
            "material",
            "symbol",
            "debye_temperature_k",
            "einstein_temperature_k",
            "einstein_frequency_hz",
            "official_frequency_1e13_hz",
        ),
        rows,
    )


def _write_einstein_heat_capacity(
    path: Path,
    result: EinsteinStudyResult,
) -> None:
    rows = tuple(
        (
            material.name,
            material.symbol,
            _format_float(temperature),
            _format_float(result.molar_heat_capacity_j_mol_k[m_index, t_index]),
        )
        for m_index, material in enumerate(result.materials)
        for t_index, temperature in enumerate(result.temperatures_k)
    )
    _write_csv(
        path,
        (
            "material",
            "symbol",
            "temperature_k",
            "molar_heat_capacity_j_mol_k",
        ),
        rows,
    )


def _write_einstein_normalized(
    path: Path,
    result: EinsteinStudyResult,
) -> None:
    rows = tuple(
        (
            material.name,
            material.symbol,
            _format_float(reduced_temperature),
            _format_float(result.normalized_heat_capacity[m_index, t_index]),
        )
        for m_index, material in enumerate(result.materials)
        for t_index, reduced_temperature in enumerate(
            result.reduced_temperatures
        )
    )
    _write_csv(
        path,
        (
            "material",
            "symbol",
            "reduced_temperature",
            "normalized_heat_capacity",
        ),
        rows,
    )


def _validation_payload(report: Task03ValidationReport) -> dict[str, object]:
    """Return the frozen JSON-compatible validation schema."""

    return {
        "schema_version": report.schema_version,
        "passed": report.passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "observed": check.observed,
                "expected": check.expected,
                "tolerance": check.tolerance,
                "comparison": check.comparison,
                "unit": check.unit,
                "explanation": check.explanation,
            }
            for check in report.checks
        ],
    }


def _configuration_payload(
    configuration: Task03Configuration,
) -> dict[str, object]:
    """Return every immutable configuration field in declaration order."""

    payload: dict[str, object] = {}
    for field in fields(configuration):
        value = getattr(configuration, field.name)
        payload[field.name] = list(value) if isinstance(value, tuple) else value
    return payload


def _material_payload(material: EinsteinMaterial) -> dict[str, object]:
    return {
        "name": material.name,
        "symbol": material.symbol,
        "debye_temperature_k": material.debye_temperature_k,
        "official_frequency_1e13_hz": material.official_frequency_1e13_hz,
    }


def _manifest_payload(
    configuration: Task03Configuration,
    materials: tuple[EinsteinMaterial, ...],
) -> dict[str, object]:
    """Return deterministic provenance without machine-specific metadata."""

    return {
        "schema_version": configuration.schema_version,
        "constants": {
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "speed_of_light_m_s": SPEED_OF_LIGHT_M_S,
            "boltzmann_constant_j_k": BOLTZMANN_CONSTANT_J_K,
            "molar_gas_constant_j_mol_k": MOLAR_GAS_CONSTANT_J_MOL_K,
            "stefan_boltzmann_constant_w_m2_k4": (
                STEFAN_BOLTZMANN_CONSTANT_W_M2_K4
            ),
            "wien_displacement_constant_m_k": (
                WIEN_DISPLACEMENT_CONSTANT_M_K
            ),
            "einstein_debye_factor": EINSTEIN_DEBYE_FACTOR,
        },
        "configuration": _configuration_payload(configuration),
        "official_materials": [
            _material_payload(material) for material in materials
        ],
        "expected_output_filenames": list(DATA_FILENAMES),
        "expected_figure_filenames": list(FIGURE_FILENAMES),
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        handle.write("\n")


def _atomic_write_outputs(
    output_directory: Path,
    writers: tuple[tuple[str, Callable[[Path], None]], ...],
) -> tuple[Path, ...]:
    """Prepare every temporary sibling, then replace destinations in order."""

    if output_directory.exists() and not output_directory.is_dir():
        raise NotADirectoryError(f"output path is not a directory: {output_directory}")
    output_directory.mkdir(parents=True, exist_ok=True)

    temporary_paths: list[Path] = []
    destinations = tuple(output_directory / name for name, _ in writers)
    try:
        for (filename, writer), destination in zip(writers, destinations):
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{filename}.",
                suffix=".tmp",
                dir=output_directory,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_paths.append(temporary_path)
            writer(temporary_path)
            temporary_path.chmod(0o644)
            if destination.exists() and destination.is_dir():
                raise IsADirectoryError(
                    f"output destination is a directory: {destination}"
                )

        for temporary_path, destination in zip(
            temporary_paths,
            destinations,
        ):
            temporary_path.replace(destination)
        return destinations
    finally:
        for temporary_path in temporary_paths:
            if temporary_path.exists():
                temporary_path.unlink()


def write_task03_data(
    planck_result: PlanckStudyResult,
    einstein_result: EinsteinStudyResult,
    output_directory: str | os.PathLike[str] = DEFAULT_DATA_DIRECTORY,
) -> Task03DataGenerationResult:
    """Validate completed studies and atomically write all numerical evidence."""

    report = validate_task03(planck_result, einstein_result)
    if not report.passed:
        failed_names = ", ".join(check.name for check in report.failures)
        raise RuntimeError(
            "Task 3 data generation refused because validation failed: "
            f"{failed_names}"
        )

    output_path = Path(output_directory)
    writers: tuple[tuple[str, Callable[[Path], None]], ...] = (
        (
            DATA_FILENAMES[0],
            lambda path: _write_planck_spectra(path, planck_result),
        ),
        (
            DATA_FILENAMES[1],
            lambda path: _write_planck_validation(path, planck_result),
        ),
        (
            DATA_FILENAMES[2],
            lambda path: _write_einstein_materials(path, einstein_result),
        ),
        (
            DATA_FILENAMES[3],
            lambda path: _write_einstein_heat_capacity(path, einstein_result),
        ),
        (
            DATA_FILENAMES[4],
            lambda path: _write_einstein_normalized(path, einstein_result),
        ),
        (
            DATA_FILENAMES[5],
            lambda path: _write_json(path, _validation_payload(report)),
        ),
        (
            DATA_FILENAMES[6],
            lambda path: _write_json(
                path,
                _manifest_payload(
                    einstein_result.configuration,
                    einstein_result.materials,
                ),
            ),
        ),
    )
    output_paths = _atomic_write_outputs(output_path, writers)
    return Task03DataGenerationResult(
        report=report,
        output_paths=output_paths,
    )


def generate_task03_data(
    output_directory: str | os.PathLike[str] = DEFAULT_DATA_DIRECTORY,
    configuration: Task03Configuration = DEFAULT_CONFIGURATION,
    materials: tuple[EinsteinMaterial, ...] = OFFICIAL_MATERIALS,
) -> Task03DataGenerationResult:
    """Build, validate, and serialize both Task 3 studies."""

    planck_result = build_planck_study(configuration)
    einstein_result = build_einstein_study(configuration, materials)
    return write_task03_data(
        planck_result,
        einstein_result,
        output_directory,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run validated data and optional figure generation."""

    parser = argparse.ArgumentParser(
        description="Generate validated Task 3 numerical evidence.",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="write CSV and JSON evidence without importing Matplotlib",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="destination directory for CSV and JSON files",
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        default=DEFAULT_FIGURE_DIRECTORY,
        help="destination directory for PNG and SVG figures",
    )
    arguments = parser.parse_args(argv)

    planck_result = build_planck_study()
    einstein_result = build_einstein_study()
    result = write_task03_data(
        planck_result,
        einstein_result,
        arguments.data_dir,
    )
    print(f"Python {platform.python_version()}; NumPy {np.__version__}")
    if arguments.data_only:
        print("Task 3 Stage 8: validated data generation")
    else:
        print("Task 3 Stage 9: validated data and figure generation")
    for path in result.output_paths:
        print(path)
    if not arguments.data_only:
        # This local import is intentional: --data-only must not load Matplotlib.
        from task03_thermal_radiation.plotting import write_task03_figures

        figure_result = write_task03_figures(
            planck_result,
            einstein_result,
            arguments.figure_dir,
        )
        for path in figure_result.output_paths:
            print(path)
    print(f"Validation checks: {len(result.report.checks)}")
    if arguments.data_only:
        print("Task 3 data generation: PASS")
    else:
        print("Task 3 complete generation: PASS")
    return 0


__all__ = [
    "DATA_FILENAMES",
    "DEFAULT_DATA_DIRECTORY",
    "DEFAULT_FIGURE_DIRECTORY",
    "FIGURE_FILENAMES",
    "MATHEMATICAL_SPECIFICATION_PATH",
    "Task03DataGenerationResult",
    "generate_task03_data",
    "main",
    "write_task03_data",
]


if __name__ == "__main__":
    raise SystemExit(main())
