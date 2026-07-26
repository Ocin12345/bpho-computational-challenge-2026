"""Validation-first transactional evidence generation for Task 6."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from task06_electron_diffraction.analysis import Task06StudyResult, build_task06_study
from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    Task06Configuration,
)
from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
)
from task06_electron_diffraction.plotting import (
    FIGURE_FILENAMES,
    generate_task06_figures,
)
from task06_electron_diffraction.reference import (
    reference_first_order_anchor,
    reference_fit_gradient_v_inv_sqrt,
    reference_maximum_bragg_order,
    reference_maximum_screen_order,
    reference_wavelength_m,
)
from task06_electron_diffraction.validation import (
    Task06ValidationReport,
    validate_task06,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task06"
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task06"
OUTPUT_SCHEMA_VERSION = "task06-data-v1"
MATHEMATICAL_SPECIFICATION_PATH = "task06_electron_diffraction/MATHEMATICAL_MODEL.md"

DATA_FILENAMES = (
    "voltage_sweep.csv",
    "diffraction_orders.csv",
    "validation_fits.csv",
    "reference_anchors.json",
    "validation_report.json",
    "manifest.json",
)


@dataclass(frozen=True)
class Task06GenerationResult:
    """Passing report and ordered outputs from one complete transaction."""

    report: Task06ValidationReport
    data_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task06ValidationReport) or not self.report.passed:
            raise ValueError("generation result requires a passing Task 6 report")
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


def _first_order_index(
    study: Task06StudyResult,
    voltage_index: int,
    spacing_index: int,
) -> int:
    matches = (
        (study.voltage_indices == voltage_index)
        & (study.spacing_indices == spacing_index)
        & (study.orders_n == 1)
    ).nonzero()[0]
    if matches.size != 1:
        raise ValueError("first-order record is missing or duplicated")
    return int(matches[0])


def _write_voltage_sweep(path: Path, study: Task06StudyResult) -> None:
    header: list[str] = [
        "voltage_v",
        "voltage_kv",
        "momentum_kg_m_s",
        "wavelength_m",
        "wavelength_pm",
    ]
    for spacing_id in study.spacing_ids:
        header.extend(
            [
                f"{spacing_id}_maximum_bragg_order",
                f"{spacing_id}_maximum_screen_order",
                f"{spacing_id}_n1_bragg_ratio_q",
                f"{spacing_id}_n1_phi_rad",
                f"{spacing_id}_n1_phi_deg",
                f"{spacing_id}_n1_photo_radius_m",
                f"{spacing_id}_n1_photo_radius_mm",
                f"{spacing_id}_n1_caliper_diameter_m",
                f"{spacing_id}_n1_caliper_diameter_mm",
            ]
        )

    rows: list[tuple[str, ...]] = []
    phi_degrees = study.phi_deg
    for voltage_index, voltage in enumerate(study.voltages_v):
        row: list[str] = [
            _format_float(voltage),
            _format_float(voltage / 1000.0),
            _format_float(study.momenta_kg_m_s[voltage_index]),
            _format_float(study.wavelengths_m[voltage_index]),
            _format_float(study.wavelengths_m[voltage_index] * 1.0e12),
        ]
        for spacing_index in range(study.spacings_m.size):
            record_index = _first_order_index(study, voltage_index, spacing_index)
            row.extend(
                [
                    str(int(study.maximum_bragg_orders[voltage_index, spacing_index])),
                    str(int(study.maximum_screen_orders[voltage_index, spacing_index])),
                    _format_float(study.bragg_ratios_q[record_index]),
                    _format_float(study.phi_rad[record_index]),
                    _format_float(phi_degrees[record_index]),
                    _format_float(study.photo_radii_m[record_index]),
                    _format_float(study.photo_radii_m[record_index] * 1.0e3),
                    _format_float(study.caliper_diameters_m[record_index]),
                    _format_float(study.caliper_diameters_m[record_index] * 1.0e3),
                ]
            )
        rows.append(tuple(row))
    _write_csv(path, tuple(header), rows)


def _write_diffraction_orders(path: Path, study: Task06StudyResult) -> None:
    theta_degrees = study.theta_deg
    phi_degrees = study.phi_deg
    header = (
        "voltage_index",
        "voltage_v",
        "voltage_kv",
        "spacing_index",
        "spacing_id",
        "spacing_label",
        "spacing_m",
        "spacing_nm",
        "order_n",
        "wavelength_m",
        "wavelength_pm",
        "bragg_ratio_q",
        "theta_rad",
        "theta_deg",
        "phi_rad",
        "phi_deg",
        "photo_radius_m",
        "photo_radius_mm",
        "caliper_diameter_m",
        "caliper_diameter_mm",
        "bragg_allowed",
        "screen_visible",
        "order_status",
    )
    rows = []
    for index in range(study.catalogue_size):
        voltage_index = int(study.voltage_indices[index])
        spacing_index = int(study.spacing_indices[index])
        voltage = float(study.voltages_v[voltage_index])
        spacing = float(study.spacings_m[spacing_index])
        wavelength = float(study.wavelengths_m[voltage_index])
        rows.append(
            (
                str(voltage_index),
                _format_float(voltage),
                _format_float(voltage / 1000.0),
                str(spacing_index),
                study.spacing_ids[spacing_index],
                study.spacing_labels[spacing_index],
                _format_float(spacing),
                _format_float(spacing * 1.0e9),
                str(int(study.orders_n[index])),
                _format_float(wavelength),
                _format_float(wavelength * 1.0e12),
                _format_float(study.bragg_ratios_q[index]),
                _format_float(study.theta_rad[index]),
                _format_float(theta_degrees[index]),
                _format_float(study.phi_rad[index]),
                _format_float(phi_degrees[index]),
                _format_float(study.photo_radii_m[index]),
                _format_float(study.photo_radii_m[index] * 1.0e3),
                _format_float(study.caliper_diameters_m[index]),
                _format_float(study.caliper_diameters_m[index] * 1.0e3),
                "true",
                "true" if bool(study.screen_visible_flags[index]) else "false",
                study.order_statuses[index],
            )
        )
    _write_csv(path, header, rows)


def _write_validation_fits(path: Path, study: Task06StudyResult) -> None:
    header = (
        "spacing_id",
        "fit_kind",
        "order_n",
        "point_count",
        "horizontal_variable",
        "vertical_variable",
        "constrained_gradient_v_inv_sqrt",
        "unconstrained_gradient_v_inv_sqrt",
        "unconstrained_intercept_v_inv_sqrt",
        "r_squared",
        "recovered_spacing_m",
        "recovered_spacing_nm",
        "maximum_absolute_residual_v_inv_sqrt",
    )
    rows = (
        (
            fit.spacing_id,
            fit.fit_kind,
            "" if fit.order_n is None else str(fit.order_n),
            str(fit.point_count),
            fit.horizontal_variable,
            fit.vertical_variable,
            _format_float(fit.constrained_gradient_v_inv_sqrt),
            _format_float(fit.unconstrained_gradient_v_inv_sqrt),
            _format_float(fit.unconstrained_intercept_v_inv_sqrt),
            _format_float(fit.r_squared),
            _format_float(fit.recovered_spacing_m),
            _format_float(fit.recovered_spacing_m * 1.0e9),
            _format_float(fit.maximum_absolute_residual_v_inv_sqrt),
        )
        for fit in study.first_order_fits + study.normalized_fits
    )
    _write_csv(path, header, rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _reference_anchor_payload(configuration: Task06Configuration) -> dict[str, object]:
    voltage_anchors: list[dict[str, object]] = []
    for voltage in (1000.0, 2000.0, 3000.0, 4000.0, 5000.0):
        spacing_anchors: list[dict[str, object]] = []
        for spacing in configuration.spacings:
            wavelength, phi, radius = reference_first_order_anchor(
                voltage,
                spacing.spacing_m,
                configuration.tube_radius_m,
            )
            spacing_anchors.append(
                {
                    "spacing_id": spacing.identifier,
                    "spacing_m": spacing.spacing_m,
                    "maximum_bragg_order": reference_maximum_bragg_order(
                        voltage,
                        spacing.spacing_m,
                    ),
                    "maximum_screen_order": reference_maximum_screen_order(
                        voltage,
                        spacing.spacing_m,
                    ),
                    "first_order_phi_rad": phi,
                    "first_order_photo_radius_m": radius,
                    "first_order_gradient_v_inv_sqrt": (
                        reference_fit_gradient_v_inv_sqrt(spacing.spacing_m)
                    ),
                }
            )
        voltage_anchors.append(
            {
                "voltage_v": voltage,
                "wavelength_m": reference_wavelength_m(voltage),
                "spacings": spacing_anchors,
            }
        )
    return {
        "schema_version": "task06-reference-v1",
        "reference_precision_decimal_digits": 60,
        "tube_radius_m": configuration.tube_radius_m,
        "voltage_anchors": voltage_anchors,
    }


def _validation_payload(report: Task06ValidationReport) -> dict[str, object]:
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


def _configuration_payload(configuration: Task06Configuration) -> dict[str, object]:
    return {
        "schema_version": configuration.schema_version,
        "voltage_min_v": configuration.voltage_min_v,
        "voltage_max_v": configuration.voltage_max_v,
        "voltage_step_v": configuration.voltage_step_v,
        "voltage_count": configuration.voltage_count,
        "tube_radius_m": configuration.tube_radius_m,
        "spacings": [
            {
                "identifier": spacing.identifier,
                "label": spacing.label,
                "spacing_m": spacing.spacing_m,
            }
            for spacing in configuration.spacings
        ],
    }


def _manifest_payload(
    study: Task06StudyResult,
    report: Task06ValidationReport,
    configuration: Task06Configuration,
    hashed_paths: tuple[Path, ...],
    temporary_root: Path,
) -> dict[str, object]:
    hashes = {
        str(path.relative_to(temporary_root)): _sha256(path)
        for path in hashed_paths
    }
    return {
        "schema_version": "task06-manifest-v1",
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "model": "non-relativistic de Broglie-Bragg electron diffraction",
        "study_digest": report.study_digest,
        "catalogue_size": study.catalogue_size,
        "forward_screen_count": study.forward_screen_count,
        "validation_check_count": len(report.checks),
        "validation_passed": report.passed,
        "constants": {
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "elementary_charge_c": ELEMENTARY_CHARGE_C,
            "electron_mass_kg": ELECTRON_MASS_KG,
        },
        "configuration": _configuration_payload(configuration),
        "geometry": {
            "photographic_radius": "x = r sin(2 phi)",
            "caliper_diameter": "y = 2 r sin(phi)",
            "forward_screen_condition": "sin(phi/2) <= 1/sqrt(2)",
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "expected_figure_filenames": list(FIGURE_FILENAMES),
        "sha256": hashes,
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
        "constant_source": "NIST 2022 CODATA central values",
    }


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _verify_prepared_data(
    data_paths: tuple[Path, ...],
    study: Task06StudyResult,
    configuration: Task06Configuration,
    temporary_root: Path,
) -> None:
    if tuple(path.name for path in data_paths) != DATA_FILENAMES:
        raise ValueError("data paths do not follow the frozen filename order")
    for path in data_paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty data artifact: {path.name}")
    with data_paths[0].open(encoding="utf-8", newline="") as handle:
        if len(list(csv.DictReader(handle))) != configuration.voltage_count:
            raise ValueError("voltage sweep CSV has the wrong row count")
    with data_paths[1].open(encoding="utf-8", newline="") as handle:
        if len(list(csv.DictReader(handle))) != study.catalogue_size:
            raise ValueError("diffraction order CSV has the wrong row count")
    with data_paths[2].open(encoding="utf-8", newline="") as handle:
        if len(list(csv.DictReader(handle))) != 2 * configuration.spacing_count:
            raise ValueError("fit CSV has the wrong row count")
    for path in data_paths[3:]:
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


def _commit_all(
    prepared: tuple[tuple[Path, Path], ...],
) -> None:
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


def generate_task06(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    figure_directory: Path = DEFAULT_FIGURE_DIRECTORY,
    configuration: Task06Configuration = DEFAULT_CONFIGURATION,
) -> Task06GenerationResult:
    """Build, validate, render, verify, and atomically replace Task 6 outputs."""

    if not isinstance(configuration, Task06Configuration):
        raise TypeError("configuration must be a Task06Configuration")
    data_output = Path(data_directory)
    figure_output = Path(figure_directory)
    data_output.mkdir(parents=True, exist_ok=True)
    figure_output.mkdir(parents=True, exist_ok=True)

    study = build_task06_study(configuration)
    report = validate_task06(study, configuration)
    if not report.passed:
        raise RuntimeError("Task 6 generation requires all validation checks to pass")

    with tempfile.TemporaryDirectory(prefix="task06-generation-") as temporary:
        temporary_root = Path(temporary)
        temporary_data = temporary_root / "data" / "task06"
        temporary_figures = temporary_root / "figures" / "task06"
        temporary_data.mkdir(parents=True)
        temporary_figures.mkdir(parents=True)

        _write_voltage_sweep(temporary_data / DATA_FILENAMES[0], study)
        _write_diffraction_orders(temporary_data / DATA_FILENAMES[1], study)
        _write_validation_fits(temporary_data / DATA_FILENAMES[2], study)
        _write_json(
            temporary_data / DATA_FILENAMES[3],
            _reference_anchor_payload(configuration),
        )
        _write_json(
            temporary_data / DATA_FILENAMES[4],
            _validation_payload(report),
        )
        figure_paths = generate_task06_figures(
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

        prepared = tuple(
            (temporary_data / filename, data_output / filename)
            for filename in DATA_FILENAMES
        ) + tuple(
            (temporary_figures / filename, figure_output / filename)
            for filename in FIGURE_FILENAMES
        )
        _commit_all(prepared)

    return Task06GenerationResult(
        report=report,
        data_paths=tuple(data_output / filename for filename in DATA_FILENAMES),
        figure_paths=tuple(figure_output / filename for filename in FIGURE_FILENAMES),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_DATA_DIRECTORY)
    parser.add_argument("--figure-directory", type=Path, default=DEFAULT_FIGURE_DIRECTORY)
    arguments = parser.parse_args(argv)
    result = generate_task06(arguments.data_directory, arguments.figure_directory)
    print(
        f"Task 6 generated {len(result.data_paths)} data files and "
        f"{len(result.figure_paths)} figure files; "
        f"{sum(check.passed for check in result.report.checks)}/"
        f"{len(result.report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DATA_FILENAMES",
    "DEFAULT_DATA_DIRECTORY",
    "DEFAULT_FIGURE_DIRECTORY",
    "Task06GenerationResult",
    "generate_task06",
    "main",
]
