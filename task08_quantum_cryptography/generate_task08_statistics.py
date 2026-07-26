"""Deterministic evidence generation for the Task 8 statistical extension."""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import (
    CLASSICAL_STREAM_SALT,
    QUANTUM_STREAM_SALT,
    UINT32_MAXIMUM,
    WILSON_95_Z,
)
from task08_quantum_cryptography.generate_task08 import (
    DEFAULT_DATA_DIRECTORY,
    REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
    _commit_all,
    _sha256,
    _write_json,
)
from task08_quantum_cryptography.statistical_validation import (
    StatisticalValidationReport,
    validate_task08_statistics,
)
from task08_quantum_cryptography.statistics import (
    FinitePhotonExperiment,
    FinitePhotonSample,
    mulberry32_uint32_sequence,
    mulberry32_uniform_sequence,
    simulate_finite_photon_experiment,
)


STATISTICS_DATA_FILENAMES = (
    "finite_photon_reference.json",
    "statistical_validation_report.json",
    "statistics_manifest.json",
)
STATISTICS_OUTPUT_SCHEMA_VERSION = "task08-statistics-data-v1"
STATISTICAL_SPECIFICATION_PATH = (
    "task08_quantum_cryptography/STATISTICAL_EXTENSION.md"
)

REFERENCE_EXPERIMENTS = (
    ("official_default", "Official -30/+30 degrees", -30.0, 30.0, 1_000, 2_026),
    ("aligned_zero", "Aligned at zero degrees", 0.0, 0.0, 1_000, 11),
    ("aligned_45", "Aligned at 45 degrees", 45.0, 45.0, 1_000, 42),
    (
        "maximum_positive_contrast",
        "Maximum positive contrast",
        -45.0,
        45.0,
        1_000,
        99,
    ),
    ("perpendicular", "Perpendicular axes", 0.0, 90.0, 1_000, 123),
    (
        "official_large_sample",
        "Official angles at maximum approved N",
        -30.0,
        30.0,
        100_000,
        2_026,
    ),
)


@dataclass(frozen=True)
class StatisticsGenerationResult:
    """Passing report and ordered statistical artifacts."""

    report: StatisticalValidationReport
    data_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, StatisticalValidationReport) or not self.report.passed:
            raise ValueError("generation result requires a passing statistical report")
        paths = tuple(Path(path) for path in self.data_paths)
        if tuple(path.name for path in paths) != STATISTICS_DATA_FILENAMES:
            raise ValueError("statistical data paths have the wrong order")
        object.__setattr__(self, "data_paths", paths)


def _sample_payload(sample: FinitePhotonSample) -> dict[str, object]:
    return {
        "model": sample.model,
        "stream_seed": sample.stream_seed,
        "photon_pairs": sample.photon_pairs,
        "mismatches": sample.mismatches,
        "matches": sample.matches,
        "theoretical_probability": sample.theoretical_probability,
        "observed_probability": sample.observed_probability,
        "expected_mismatches": sample.expected_mismatches,
        "standard_deviation_count": sample.standard_deviation_count,
        "standardized_residual": sample.standardized_residual,
        "wilson_interval": {
            "lower": sample.wilson_interval.lower,
            "upper": sample.wilson_interval.upper,
        },
    }


def _experiment_payload(
    identifier: str,
    label: str,
    experiment: FinitePhotonExperiment,
) -> dict[str, object]:
    return {
        "identifier": identifier,
        "label": label,
        "theta_deg": experiment.theta_deg,
        "phi_deg": experiment.phi_deg,
        "photon_pairs": experiment.photon_pairs,
        "seed": experiment.seed,
        "classical": _sample_payload(experiment.classical),
        "quantum": _sample_payload(experiment.quantum),
    }


def _reference_payload(configuration: Task08Configuration) -> dict[str, object]:
    cases = []
    for identifier, label, theta, phi, photon_pairs, seed in REFERENCE_EXPERIMENTS:
        cases.append(
            _experiment_payload(
                identifier,
                label,
                simulate_finite_photon_experiment(
                    theta,
                    phi,
                    photon_pairs,
                    seed,
                    configuration=configuration,
                ),
            )
        )
    return {
        "schema_version": "task08-finite-photon-reference-v1",
        "generator": "Mulberry32 32-bit reproducible simulation only",
        "cryptographic_security": False,
        "wilson_z_95": WILSON_95_Z,
        "configuration": {
            "minimum_photon_pairs": configuration.simulation_minimum_photon_pairs,
            "maximum_photon_pairs": configuration.simulation_maximum_photon_pairs,
            "default_photon_pairs": configuration.simulation_default_photon_pairs,
            "default_seed": configuration.simulation_default_seed,
            "maximum_seed": UINT32_MAXIMUM,
            "classical_stream_salt": CLASSICAL_STREAM_SALT,
            "quantum_stream_salt": QUANTUM_STREAM_SALT,
        },
        "prng_reference": {
            "seed": 0,
            "uint32": list(mulberry32_uint32_sequence(0, 10)),
            "uniform": list(mulberry32_uniform_sequence(0, 10)),
        },
        "cases": cases,
    }


def _validation_payload(report: StatisticalValidationReport) -> dict[str, object]:
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
                "explanation": check.explanation,
            }
            for check in report.checks
        ],
    }


def _manifest_payload(
    report: StatisticalValidationReport,
    reference_path: Path,
    validation_path: Path,
    temporary_root: Path,
) -> dict[str, object]:
    return {
        "schema_version": "task08-statistics-manifest-v1",
        "output_schema_version": STATISTICS_OUTPUT_SCHEMA_VERSION,
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "validation_check_count": len(report.checks),
        "validation_passed": report.passed,
        "expected_data_filenames": list(STATISTICS_DATA_FILENAMES),
        "sha256": {
            str(reference_path.relative_to(temporary_root)): _sha256(reference_path),
            str(validation_path.relative_to(temporary_root)): _sha256(validation_path),
        },
        "statistical_specification": STATISTICAL_SPECIFICATION_PATH,
        "warning": "The seeded generator is reproducible, not cryptographically secure.",
    }


def _verify_prepared(paths: tuple[Path, ...], temporary_root: Path) -> None:
    if tuple(path.name for path in paths) != STATISTICS_DATA_FILENAMES:
        raise ValueError("statistical artifacts have the wrong filename order")
    payloads = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty statistical artifact: {path.name}")
        with path.open(encoding="utf-8") as handle:
            payloads.append(json.load(handle))
    reference, validation, manifest = payloads
    if len(reference.get("cases", [])) != len(REFERENCE_EXPERIMENTS):
        raise ValueError("finite-photon reference has the wrong case count")
    if not validation.get("passed") or len(validation.get("checks", [])) != 24:
        raise ValueError("serialized statistical validation did not pass 24 checks")
    if tuple(manifest.get("expected_data_filenames", ())) != STATISTICS_DATA_FILENAMES:
        raise ValueError("statistics manifest has the wrong filename order")
    for relative_name, expected_hash in manifest.get("sha256", {}).items():
        if _sha256(temporary_root / relative_name) != expected_hash:
            raise ValueError(f"statistics manifest hash mismatch for {relative_name}")


def generate_task08_statistics(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> StatisticsGenerationResult:
    """Validate, verify and atomically replace statistical evidence files."""

    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")
    destination_root = Path(data_directory)
    destination_root.mkdir(parents=True, exist_ok=True)
    report = validate_task08_statistics(configuration)
    if not report.passed:
        names = ", ".join(check.name for check in report.failed_checks)
        raise ValueError(f"statistical validation failed: {names}")

    with tempfile.TemporaryDirectory(
        dir=destination_root.parent,
        prefix=".task08-statistics-",
    ) as temporary:
        temporary_root = Path(temporary)
        paths = tuple(temporary_root / name for name in STATISTICS_DATA_FILENAMES)
        _write_json(paths[0], _reference_payload(configuration))
        _write_json(paths[1], _validation_payload(report))
        _write_json(
            paths[2],
            _manifest_payload(report, paths[0], paths[1], temporary_root),
        )
        _verify_prepared(paths, temporary_root)
        destinations = tuple(destination_root / path.name for path in paths)
        _commit_all(tuple(zip(paths, destinations)))

    return StatisticsGenerationResult(report=report, data_paths=destinations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate validated Task 8 finite-photon reference evidence."
    )
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="Output directory (default: data/task08)",
    )
    arguments = parser.parse_args(argv)
    result = generate_task08_statistics(arguments.data_directory)
    print(
        f"Task 8 statistics generated {len(result.data_paths)} data files; "
        f"{len(result.report.checks)}/{len(result.report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
