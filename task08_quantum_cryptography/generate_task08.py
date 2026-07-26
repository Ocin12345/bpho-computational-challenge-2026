"""Validation-first transactional evidence generation for Task 8."""

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

from task08_quantum_cryptography.analysis import (
    Task08StudyResult,
    build_task08_study,
)
from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import POLARISATION_PERIOD_DEG
from task08_quantum_cryptography.reference import (
    REFERENCE_CASES,
    reference_classical_mismatch,
    reference_quantum_mismatch,
)
from task08_quantum_cryptography.validation import (
    Task08ValidationReport,
    validate_task08,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task08"
OUTPUT_SCHEMA_VERSION = "task08-data-v1"
MATHEMATICAL_SPECIFICATION_PATH = "task08_quantum_cryptography/MATHEMATICAL_MODEL.md"
OFFICIAL_REQUIREMENTS_PATH = "task08_quantum_cryptography/OFFICIAL_REQUIREMENTS.md"
OFFICIAL_SOURCE_URL = (
    "https://www.bpho.org.uk/bpho/computational-challenge/"
    "BPhO_ComPhys_Challenge_2026.zip"
)
OFFICIAL_SOURCE_PAGES = (53, 54, 55, 56, 57, 58)
OFFICIAL_ARCHIVE_SHA256 = (
    "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667"
)
OFFICIAL_QUANTUM_PDF_SHA256 = (
    "7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6"
)
REPRODUCIBLE_BUILD_TIMESTAMP_UTC = "2026-01-01T00:00:00Z"

DATA_FILENAMES = (
    "angle_sweep.csv",
    "mismatch_grid.csv",
    "reference_cases.json",
    "validation_report.json",
    "manifest.json",
)

ANGLE_SWEEP_HEADER = (
    "theta_deg",
    "phi_deg",
    "relative_angle_deg",
    "detector_a_x_probability",
    "detector_a_y_probability",
    "detector_b_x_probability",
    "detector_b_y_probability",
    "classical_match_probability",
    "classical_mismatch_probability",
    "quantum_match_probability",
    "quantum_mismatch_probability",
    "quantum_minus_classical",
    "classical_mismatch_percent",
    "quantum_mismatch_percent",
    "difference_percentage_points",
)

MISMATCH_GRID_HEADER = (
    "theta_index",
    "phi_index",
    "theta_deg",
    "phi_deg",
    "relative_angle_deg",
    "classical_match_probability",
    "classical_mismatch_probability",
    "quantum_match_probability",
    "quantum_mismatch_probability",
    "quantum_minus_classical",
)


@dataclass(frozen=True)
class Task08GenerationResult:
    """Passing report and ordered data outputs from one transaction."""

    report: Task08ValidationReport
    data_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task08ValidationReport) or not self.report.passed:
            raise ValueError("generation result requires a passing Task 8 report")
        paths = tuple(Path(path) for path in self.data_paths)
        if tuple(path.name for path in paths) != DATA_FILENAMES:
            raise ValueError("data_paths must follow the frozen file order")
        object.__setattr__(self, "data_paths", paths)


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


def _write_angle_sweep(path: Path, study: Task08StudyResult) -> None:
    rows = (
        (
            _format_float(study.sweep_theta_deg[index]),
            _format_float(study.sweep_phi_deg[index]),
            _format_float(study.sweep_relative_angle_deg[index]),
            _format_float(study.sweep_detector_a_x[index]),
            _format_float(study.sweep_detector_a_y[index]),
            _format_float(study.sweep_detector_b_x[index]),
            _format_float(study.sweep_detector_b_y[index]),
            _format_float(study.sweep_classical_match[index]),
            _format_float(study.sweep_classical_mismatch[index]),
            _format_float(study.sweep_quantum_match[index]),
            _format_float(study.sweep_quantum_mismatch[index]),
            _format_float(study.sweep_signed_difference[index]),
            _format_float(100.0 * study.sweep_classical_mismatch[index]),
            _format_float(100.0 * study.sweep_quantum_mismatch[index]),
            _format_float(100.0 * study.sweep_signed_difference[index]),
        )
        for index in range(study.sweep_point_count)
    )
    _write_csv(path, ANGLE_SWEEP_HEADER, rows)


def _write_mismatch_grid(path: Path, study: Task08StudyResult) -> None:
    rows = (
        (
            str(theta_index),
            str(phi_index),
            _format_float(study.grid_theta_deg[theta_index, phi_index]),
            _format_float(study.grid_phi_deg[theta_index, phi_index]),
            _format_float(study.grid_relative_angle_deg[theta_index, phi_index]),
            _format_float(study.grid_classical_match[theta_index, phi_index]),
            _format_float(study.grid_classical_mismatch[theta_index, phi_index]),
            _format_float(study.grid_quantum_match[theta_index, phi_index]),
            _format_float(study.grid_quantum_mismatch[theta_index, phi_index]),
            _format_float(study.grid_signed_difference[theta_index, phi_index]),
        )
        for theta_index in range(study.grid_shape[0])
        for phi_index in range(study.grid_shape[1])
    )
    _write_csv(path, MISMATCH_GRID_HEADER, rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _fraction_payload(value: object) -> dict[str, object]:
    from fractions import Fraction

    if not isinstance(value, Fraction):
        raise TypeError("value must be a Fraction")
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def _reference_cases_payload() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for case in REFERENCE_CASES:
        cases.append(
            {
                "identifier": case.identifier,
                "label": case.label,
                "theta_deg": case.theta_deg,
                "phi_deg": case.phi_deg,
                "classical_mismatch": _fraction_payload(case.classical_mismatch),
                "quantum_mismatch": _fraction_payload(case.quantum_mismatch),
                "signed_difference": _fraction_payload(case.signed_difference),
                "double_angle_classical_reference": reference_classical_mismatch(
                    case.theta_deg,
                    case.phi_deg,
                ),
                "double_angle_quantum_reference": reference_quantum_mismatch(
                    case.theta_deg,
                    case.phi_deg,
                ),
            }
        )
    return {
        "schema_version": "task08-reference-v1",
        "classical_reference_equation": (
            "P_C(mismatch) = (1 - cos(2 theta) cos(2 phi))/2"
        ),
        "quantum_reference_equation": (
            "P_Q(mismatch) = (1 - cos(2(phi - theta)))/2"
        ),
        "cases": cases,
    }


def _validation_payload(report: Task08ValidationReport) -> dict[str, object]:
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


def _configuration_payload(configuration: Task08Configuration) -> dict[str, object]:
    return {
        "schema_version": configuration.schema_version,
        "angle_minimum_deg": configuration.angle_minimum_deg,
        "angle_maximum_deg": configuration.angle_maximum_deg,
        "angle_step_deg": configuration.angle_step_deg,
        "official_theta_deg": configuration.official_theta_deg,
        "official_phi_deg": configuration.official_phi_deg,
        "sweep_point_count": configuration.sweep_point_count,
        "sweep_spacing_deg": configuration.sweep_spacing_deg,
        "heatmap_point_count": configuration.heatmap_point_count,
        "heatmap_spacing_deg": configuration.heatmap_spacing_deg,
        "reference_absolute_tolerance": configuration.reference_absolute_tolerance,
        "evidence_size_budget_bytes": configuration.evidence_size_budget_bytes,
    }


def _manifest_payload(
    report: Task08ValidationReport,
    configuration: Task08Configuration,
    hashed_paths: tuple[Path, ...],
    temporary_root: Path,
) -> dict[str, object]:
    hashes = {
        str(path.relative_to(temporary_root)): _sha256(path) for path in hashed_paths
    }
    return {
        "schema_version": "task08-manifest-v1",
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "model": "classical and quantum entangled-photon detector mismatch",
        "study_digest": report.study_digest,
        "validation_check_count": len(report.checks),
        "validation_passed": report.passed,
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "configuration": _configuration_payload(configuration),
        "constants": {
            "polarisation_period_deg": POLARISATION_PERIOD_DEG,
        },
        "equations": {
            "classical_mismatch": (
                "1 - cos(theta)^2 cos(phi)^2 - sin(theta)^2 sin(phi)^2"
            ),
            "quantum_mismatch": "sin(phi - theta)^2",
            "signed_difference": "quantum mismatch - classical mismatch",
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "sha256": hashes,
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
        "official_requirements": OFFICIAL_REQUIREMENTS_PATH,
        "official_source": OFFICIAL_SOURCE_URL,
        "official_pages": list(OFFICIAL_SOURCE_PAGES),
        "official_source_sha256": {
            "BPhO_ComPhys_Challenge_2026.zip": OFFICIAL_ARCHIVE_SHA256,
            "BPhO CompPhys2026 Quantum.pdf": OFFICIAL_QUANTUM_PDF_SHA256,
        },
    }


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _verify_csv(
    path: Path,
    *,
    expected_header: tuple[str, ...],
    expected_rows: int,
    integer_fields: tuple[str, ...] = (),
) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise ValueError(f"{path.name} has the wrong header")
        row_count = 0
        for row in reader:
            row_count += 1
            for field_name, text in row.items():
                if field_name in integer_fields:
                    int(text)
                    continue
                value = float(text)
                if not math.isfinite(value):
                    raise ValueError(f"{path.name} contains a non-finite value")
        if row_count != expected_rows:
            raise ValueError(f"{path.name} has the wrong row count")


def _verify_prepared_data(
    data_paths: tuple[Path, ...],
    report: Task08ValidationReport,
    configuration: Task08Configuration,
    temporary_root: Path,
) -> None:
    if tuple(path.name for path in data_paths) != DATA_FILENAMES:
        raise ValueError("data paths do not follow the frozen filename order")
    for path in data_paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty data artifact: {path.name}")

    _verify_csv(
        data_paths[0],
        expected_header=ANGLE_SWEEP_HEADER,
        expected_rows=configuration.sweep_point_count,
    )
    _verify_csv(
        data_paths[1],
        expected_header=MISMATCH_GRID_HEADER,
        expected_rows=configuration.heatmap_point_count**2,
        integer_fields=("theta_index", "phi_index"),
    )
    for path in data_paths[2:]:
        with path.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=_reject_json_constant)

    with data_paths[3].open(encoding="utf-8") as handle:
        validation_payload = json.load(handle)
    if not validation_payload.get("passed"):
        raise ValueError("serialized validation report did not pass")
    if len(validation_payload.get("checks", [])) != len(report.checks):
        raise ValueError("serialized validation report has the wrong check count")

    with data_paths[-1].open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if tuple(manifest.get("expected_data_filenames", ())) != DATA_FILENAMES:
        raise ValueError("manifest has the wrong expected filename order")
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


def generate_task08(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> Task08GenerationResult:
    """Build, validate, verify and atomically replace Task 8 data outputs."""

    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")
    started = time.perf_counter()
    data_output = Path(data_directory)
    data_output.mkdir(parents=True, exist_ok=True)

    study_started = time.perf_counter()
    study = build_task08_study(configuration)
    study_runtime = time.perf_counter() - study_started
    if study_runtime > configuration.study_runtime_budget_s:
        raise RuntimeError("Task 8 study exceeded its runtime budget")
    report = validate_task08(study, configuration)
    if not report.passed:
        raise RuntimeError("Task 8 generation requires every validation check to pass")

    with tempfile.TemporaryDirectory(prefix="task08-generation-") as temporary:
        temporary_root = Path(temporary)
        temporary_data = temporary_root / "data" / "task08"
        temporary_data.mkdir(parents=True)

        _write_angle_sweep(temporary_data / DATA_FILENAMES[0], study)
        _write_mismatch_grid(temporary_data / DATA_FILENAMES[1], study)
        _write_json(
            temporary_data / DATA_FILENAMES[2],
            _reference_cases_payload(),
        )
        _write_json(
            temporary_data / DATA_FILENAMES[3],
            _validation_payload(report),
        )
        pre_manifest_paths = tuple(
            temporary_data / filename for filename in DATA_FILENAMES[:-1]
        )
        _write_json(
            temporary_data / DATA_FILENAMES[-1],
            _manifest_payload(
                report,
                configuration,
                pre_manifest_paths,
                temporary_root,
            ),
        )
        data_paths = tuple(temporary_data / filename for filename in DATA_FILENAMES)
        _verify_prepared_data(
            data_paths,
            report,
            configuration,
            temporary_root,
        )
        if time.perf_counter() - started > configuration.generation_runtime_budget_s:
            raise RuntimeError("Task 8 generation exceeded its runtime budget")

        prepared = tuple(
            (temporary_data / filename, data_output / filename)
            for filename in DATA_FILENAMES
        )
        _commit_all(prepared)

    return Task08GenerationResult(
        report=report,
        data_paths=tuple(data_output / filename for filename in DATA_FILENAMES),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_DATA_DIRECTORY)
    arguments = parser.parse_args()
    result = generate_task08(arguments.data_directory)
    passed = sum(check.passed for check in result.report.checks)
    print(
        f"Task 8 generated {len(result.data_paths)} data files; "
        f"{passed}/{len(result.report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
