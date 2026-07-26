"""Validation-first transactional evidence generation for Task 7."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from task07_particle_in_box.analysis import Task07StudyResult, build_task07_study
from task07_particle_in_box.configuration import (
    DEFAULT_CONFIGURATION,
    Task07Configuration,
)
from task07_particle_in_box.constants import (
    ELECTRON_MASS_KG,
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    REDUCED_PLANCK_CONSTANT_J_S,
)
from task07_particle_in_box.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
    generate_task07_figures,
)
from task07_particle_in_box.reference import (
    reference_energy_j,
    reference_expected_position_squared_m2,
    reference_uncertainty_product_over_hbar,
)
from task07_particle_in_box.validation import (
    Task07ValidationReport,
    validate_task07,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task07"
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task07"
OUTPUT_SCHEMA_VERSION = "task07-data-v1"
MATHEMATICAL_SPECIFICATION_PATH = "task07_particle_in_box/MATHEMATICAL_MODEL.md"
OFFICIAL_REQUIREMENTS_PATH = "task07_particle_in_box/OFFICIAL_REQUIREMENTS.md"
OFFICIAL_SOURCE_URL = (
    "https://www.bpho.org.uk/bpho/computational-challenge/"
    "BPhO_ComPhys_Challenge_2026.zip"
)
OFFICIAL_SOURCE_PAGES = (48, 49)
OFFICIAL_ARCHIVE_SHA256 = (
    "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667"
)
OFFICIAL_QUANTUM_PDF_SHA256 = (
    "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6"
)
REPRODUCIBLE_BUILD_TIMESTAMP_UTC = "2026-01-01T00:00:00Z"

DATA_FILENAMES = (
    "energy_levels.csv",
    "stationary_states.csv",
    "expectation_values.csv",
    "numerical_eigenvalues.csv",
    "reference_anchors.json",
    "validation_report.json",
    "manifest.json",
)


@dataclass(frozen=True)
class Task07GenerationResult:
    """Passing report and ordered outputs from one complete transaction."""

    report: Task07ValidationReport
    data_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task07ValidationReport) or not self.report.passed:
            raise ValueError("generation result requires a passing Task 7 report")
        data_paths = tuple(Path(path) for path in self.data_paths)
        figure_paths = tuple(Path(path) for path in self.figure_paths)
        if tuple(path.name for path in data_paths) != DATA_FILENAMES:
            raise ValueError("data_paths must follow the frozen file order")
        if tuple(path.name for path in figure_paths) != FIGURE_FILENAMES:
            raise ValueError("figure_paths must follow the frozen file order")
        object.__setattr__(self, "data_paths", data_paths)
        object.__setattr__(self, "figure_paths", figure_paths)


def _format_float(value: float) -> str:
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("serialized values must be finite")
    return format(normalized, ".17g")


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: Iterable[tuple[str, ...]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_energy_levels(path: Path, study: Task07StudyResult) -> None:
    rows: list[tuple[str, ...]] = []
    for index, n in enumerate(study.quantum_numbers):
        if index + 1 < study.quantum_numbers.size:
            gap_j = float(study.energies_j[index + 1] - study.energies_j[index])
            gap_ev = float(study.energies_ev[index + 1] - study.energies_ev[index])
            gap_j_text = _format_float(gap_j)
            gap_ev_text = _format_float(gap_ev)
        else:
            gap_j_text = ""
            gap_ev_text = ""
        rows.append(
            (
                str(int(n)),
                _format_float(study.energies_j[index]),
                _format_float(study.energies_ev[index]),
                _format_float(study.energy_ratios[index]),
                gap_j_text,
                gap_ev_text,
            )
        )
    _write_csv(
        path,
        (
            "quantum_number_n",
            "energy_j",
            "energy_ev",
            "energy_over_ground",
            "gap_to_next_j",
            "gap_to_next_ev",
        ),
        rows,
    )


def _write_stationary_states(
    path: Path,
    study: Task07StudyResult,
    configuration: Task07Configuration,
) -> None:
    rows: list[tuple[str, ...]] = []
    for position_index, position in enumerate(study.positions_m):
        for state_index, n in enumerate(study.density_quantum_numbers):
            rows.append(
                (
                    str(position_index),
                    _format_float(position),
                    _format_float(position * 1.0e9),
                    _format_float(position / configuration.box_width_m),
                    str(int(n)),
                    _format_float(study.wavefunctions_m_neg_half[position_index, state_index]),
                    _format_float(
                        study.probability_densities_m_inv[position_index, state_index]
                    ),
                    _format_float(
                        configuration.box_width_m
                        * study.probability_densities_m_inv[position_index, state_index]
                    ),
                )
            )
    _write_csv(
        path,
        (
            "position_index",
            "position_m",
            "position_nm",
            "position_over_box_width",
            "quantum_number_n",
            "wavefunction_m_neg_half",
            "probability_density_m_inv",
            "box_width_times_density",
        ),
        rows,
    )


def _write_expectation_values(path: Path, study: Task07StudyResult) -> None:
    rows = (
        (
            str(int(study.quantum_numbers[index])),
            _format_float(study.expected_positions_m[index]),
            _format_float(study.expected_positions_squared_m2[index]),
            _format_float(study.position_uncertainties_m[index]),
            _format_float(study.expected_momenta_kg_m_s[index]),
            _format_float(study.expected_momenta_squared_kg2_m2_s2[index]),
            _format_float(study.momentum_uncertainties_kg_m_s[index]),
            _format_float(study.uncertainty_products_j_s[index]),
            _format_float(study.uncertainty_products_over_hbar[index]),
            _format_float(study.uncertainty_products_over_hbar[index] - 0.5),
        )
        for index in range(study.quantum_numbers.size)
    )
    _write_csv(
        path,
        (
            "quantum_number_n",
            "expected_x_m",
            "expected_x_squared_m2",
            "delta_x_m",
            "expected_p_kg_m_s",
            "expected_p_squared_kg2_m2_s2",
            "delta_p_kg_m_s",
            "delta_x_delta_p_j_s",
            "delta_x_delta_p_over_hbar",
            "margin_above_half_hbar",
        ),
        rows,
    )


def _write_numerical_eigenvalues(path: Path, study: Task07StudyResult) -> None:
    rows: list[tuple[str, ...]] = []
    finest_index = study.numerical_grid_sizes.size - 1
    for grid_index, grid_size in enumerate(study.numerical_grid_sizes):
        for state_index in range(study.numerical_energies_j.shape[1]):
            n = state_index + 1
            rows.append(
                (
                    str(int(grid_size)),
                    _format_float(study.numerical_grid_spacings_m[grid_index]),
                    str(n),
                    _format_float(study.numerical_energies_j[grid_index, state_index]),
                    _format_float(study.numerical_energies_j[grid_index, state_index] / ELECTRONVOLT_J),
                    _format_float(study.energies_j[state_index]),
                    _format_float(study.energies_ev[state_index]),
                    _format_float(study.numerical_relative_errors[grid_index, state_index]),
                    _format_float(study.numerical_convergence_orders[state_index]),
                    (
                        _format_float(study.numerical_overlaps[state_index])
                        if grid_index == finest_index
                        else ""
                    ),
                )
            )
    _write_csv(
        path,
        (
            "interior_point_count",
            "grid_spacing_m",
            "quantum_number_n",
            "numerical_energy_j",
            "numerical_energy_ev",
            "analytical_energy_j",
            "analytical_energy_ev",
            "relative_energy_error",
            "observed_convergence_order",
            "finest_grid_absolute_overlap",
        ),
        rows,
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _reference_anchor_payload(configuration: Task07Configuration) -> dict[str, object]:
    anchors = []
    for n in (1, 2, 4, 10):
        anchors.append(
            {
                "quantum_number_n": n,
                "energy_j": reference_energy_j(
                    n, configuration.particle_mass_kg, configuration.box_width_m
                ),
                "expected_x_squared_m2": reference_expected_position_squared_m2(
                    n, configuration.box_width_m
                ),
                "delta_x_delta_p_over_hbar": (
                    reference_uncertainty_product_over_hbar(n)
                ),
            }
        )
    return {
        "schema_version": "task07-reference-v1",
        "reference_precision_decimal_digits": 60,
        "particle_mass_kg": configuration.particle_mass_kg,
        "box_width_m": configuration.box_width_m,
        "anchors": anchors,
    }


def _validation_payload(report: Task07ValidationReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "study_digest": report.study_digest,
        "passed": report.passed,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "observed": check.observed,
                "expected": check.expected,
                "unit": check.unit,
                "comparison": check.comparison,
                "tolerance": check.tolerance,
                "explanation": check.explanation,
            }
            for check in report.checks
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _configuration_payload(configuration: Task07Configuration) -> dict[str, object]:
    return {
        "schema_version": configuration.schema_version,
        "particle_identifier": configuration.particle_identifier,
        "particle_label": configuration.particle_label,
        "particle_mass_kg": configuration.particle_mass_kg,
        "box_width_m": configuration.box_width_m,
        "maximum_quantum_number": configuration.maximum_quantum_number,
        "density_quantum_numbers": list(configuration.density_quantum_numbers),
        "position_point_count": configuration.position_point_count,
        "numerical_grid_sizes": list(configuration.numerical_grid_sizes),
        "numerical_state_count": configuration.numerical_state_count,
    }


def _manifest_payload(
    study: Task07StudyResult,
    report: Task07ValidationReport,
    configuration: Task07Configuration,
    hashed_paths: tuple[Path, ...],
    temporary_root: Path,
) -> dict[str, object]:
    hashes = {
        str(path.relative_to(temporary_root)): _sha256(path) for path in hashed_paths
    }
    return {
        "schema_version": "task07-manifest-v1",
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "model": "one-dimensional non-relativistic infinite square well",
        "study_digest": report.study_digest,
        "validation_check_count": len(report.checks),
        "validation_passed": report.passed,
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "constants": {
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "reduced_planck_constant_j_s": REDUCED_PLANCK_CONSTANT_J_S,
            "elementary_charge_c": ELEMENTARY_CHARGE_C,
            "electron_mass_kg": ELECTRON_MASS_KG,
        },
        "configuration": _configuration_payload(configuration),
        "equations": {
            "wavefunction": "psi_n = sqrt(2/a) sin(n pi x/a)",
            "energy": "E_n = n^2 pi^2 hbar^2/(2 m a^2)",
            "uncertainty": "Delta x Delta p/hbar = sqrt(n^2 pi^2/12 - 1/2)",
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "expected_figure_filenames": list(FIGURE_FILENAMES),
        "figure_font_family": FIGURE_FONT_FAMILY,
        "sha256": hashes,
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
        "official_requirements": OFFICIAL_REQUIREMENTS_PATH,
        "official_source": OFFICIAL_SOURCE_URL,
        "official_pages": list(OFFICIAL_SOURCE_PAGES),
        "official_source_sha256": {
            "BPhO_ComPhys_Challenge_2026.zip": OFFICIAL_ARCHIVE_SHA256,
            "BPhO CompPhys2026 Quantum.pdf": OFFICIAL_QUANTUM_PDF_SHA256,
        },
        "constant_source": "NIST 2022 CODATA central values and exact SI constants",
    }


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _verify_prepared_data(
    data_paths: tuple[Path, ...],
    study: Task07StudyResult,
    configuration: Task07Configuration,
    temporary_root: Path,
) -> None:
    if tuple(path.name for path in data_paths) != DATA_FILENAMES:
        raise ValueError("data paths do not follow the frozen filename order")
    for path in data_paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty data artifact: {path.name}")
    expected_rows = (
        configuration.maximum_quantum_number,
        configuration.position_point_count * len(configuration.density_quantum_numbers),
        configuration.maximum_quantum_number,
        len(configuration.numerical_grid_sizes) * configuration.numerical_state_count,
    )
    for path, row_count in zip(data_paths[:4], expected_rows):
        with path.open(encoding="utf-8", newline="") as handle:
            if len(list(csv.DictReader(handle))) != row_count:
                raise ValueError(f"{path.name} has the wrong row count")
    for path in data_paths[4:]:
        with path.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=_reject_json_constant)
    with data_paths[-1].open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    for relative_name, expected_hash in manifest["sha256"].items():
        if _sha256(temporary_root / relative_name) != expected_hash:
            raise ValueError(f"manifest hash mismatch for {relative_name}")
    if sum(path.stat().st_size for path in data_paths) > configuration.evidence_size_budget_bytes:
        raise ValueError("data package exceeds its size budget")


def _restore_path(destination: Path, content: bytes | None) -> None:
    if content is None:
        if destination.exists():
            destination.unlink()
        return
    with tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.name}.restore-",
        delete=False,
    ) as handle:
        restore_path = Path(handle.name)
        handle.write(content)
    os.replace(restore_path, destination)


def _commit_all(prepared: tuple[tuple[Path, Path], ...]) -> None:
    destinations = tuple(destination for _, destination in prepared)
    originals = {
        destination: destination.read_bytes() if destination.exists() else None
        for destination in destinations
    }
    replaced: list[Path] = []
    try:
        for source, destination in prepared:
            os.replace(source, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            _restore_path(destination, originals[destination])
        raise


def generate_task07(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    figure_directory: Path = DEFAULT_FIGURE_DIRECTORY,
    configuration: Task07Configuration = DEFAULT_CONFIGURATION,
) -> Task07GenerationResult:
    """Build, validate, render, verify and atomically replace Task 7 outputs."""

    if not isinstance(configuration, Task07Configuration):
        raise TypeError("configuration must be a Task07Configuration")
    started = time.perf_counter()
    data_output = Path(data_directory)
    figure_output = Path(figure_directory)
    data_output.mkdir(parents=True, exist_ok=True)
    figure_output.mkdir(parents=True, exist_ok=True)

    study_started = time.perf_counter()
    study = build_task07_study(configuration)
    study_runtime = time.perf_counter() - study_started
    if study_runtime > configuration.study_runtime_budget_s:
        raise RuntimeError("Task 7 study exceeded its runtime budget")
    report = validate_task07(study, configuration)
    if not report.passed:
        raise RuntimeError("Task 7 generation requires all validation checks to pass")

    with tempfile.TemporaryDirectory(prefix="task07-generation-") as temporary:
        temporary_root = Path(temporary)
        temporary_data = temporary_root / "data" / "task07"
        temporary_figures = temporary_root / "figures" / "task07"
        temporary_data.mkdir(parents=True)
        temporary_figures.mkdir(parents=True)

        _write_energy_levels(temporary_data / DATA_FILENAMES[0], study)
        _write_stationary_states(
            temporary_data / DATA_FILENAMES[1], study, configuration
        )
        _write_expectation_values(temporary_data / DATA_FILENAMES[2], study)
        _write_numerical_eigenvalues(temporary_data / DATA_FILENAMES[3], study)
        _write_json(
            temporary_data / DATA_FILENAMES[4],
            _reference_anchor_payload(configuration),
        )
        _write_json(
            temporary_data / DATA_FILENAMES[5],
            _validation_payload(report),
        )
        figure_paths = generate_task07_figures(
            study,
            report,
            temporary_figures,
            configuration,
        )
        pre_manifest_data = tuple(
            temporary_data / filename for filename in DATA_FILENAMES[:-1]
        )
        _write_json(
            temporary_data / DATA_FILENAMES[-1],
            _manifest_payload(
                study,
                report,
                configuration,
                pre_manifest_data + figure_paths,
                temporary_root,
            ),
        )
        data_paths = tuple(temporary_data / filename for filename in DATA_FILENAMES)
        _verify_prepared_data(data_paths, study, configuration, temporary_root)
        if time.perf_counter() - started > configuration.generation_runtime_budget_s:
            raise RuntimeError("Task 7 generation exceeded its runtime budget")

        prepared = tuple(
            (temporary_data / filename, data_output / filename)
            for filename in DATA_FILENAMES
        ) + tuple(
            (temporary_figures / filename, figure_output / filename)
            for filename in FIGURE_FILENAMES
        )
        _commit_all(prepared)

    return Task07GenerationResult(
        report=report,
        data_paths=tuple(data_output / filename for filename in DATA_FILENAMES),
        figure_paths=tuple(figure_output / filename for filename in FIGURE_FILENAMES),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_DATA_DIRECTORY)
    parser.add_argument("--figure-directory", type=Path, default=DEFAULT_FIGURE_DIRECTORY)
    arguments = parser.parse_args()
    result = generate_task07(arguments.data_directory, arguments.figure_directory)
    passed = sum(check.passed for check in result.report.checks)
    print(
        f"Task 7 generated {len(result.data_paths)} data files and "
        f"{len(result.figure_paths)} figure files; "
        f"{passed}/{len(result.report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
