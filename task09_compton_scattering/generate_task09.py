"""Generate the deterministic, validated Task 9 kinematic data package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from task09_compton_scattering.analysis import (
    Task09StudyResult,
    build_task09_study,
)
from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.constants import (
    ELECTRON_COMPTON_WAVELENGTH_M,
    ELECTRON_MASS_KG,
    ELECTRON_REST_ENERGY_KEV,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
)
from task09_compton_scattering.reference import reference_kinematics
from task09_compton_scattering.validation import (
    Task09ValidationReport,
    validate_task09,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task09"
OUTPUT_SCHEMA_VERSION = "task09-output-v1"
REPRODUCIBLE_BUILD_TIMESTAMP_UTC = "2026-01-01T00:00:00Z"
MATHEMATICAL_SPECIFICATION_PATH = "task09_compton_scattering/MATHEMATICAL_MODEL.md"
OFFICIAL_REQUIREMENTS_PATH = "task09_compton_scattering/OFFICIAL_REQUIREMENTS.md"

DATA_FILENAMES = (
    "compton_angle_study.csv",
    "energy_summary.csv",
    "reference_anchors.json",
    "validation_report.json",
    "manifest.json",
)

ANGLE_STUDY_HEADER = (
    "energy_index",
    "angle_index",
    "incident_energy_kev",
    "theta_deg",
    "alpha",
    "incident_wavelength_m",
    "wavelength_shift_m",
    "fractional_wavelength_shift",
    "scattered_wavelength_m",
    "scattered_energy_kev",
    "electron_kinetic_energy_kev",
    "electron_gamma",
    "electron_beta",
    "electron_speed_m_s",
    "electron_pc_kev",
    "electron_recoil_angle_deg",
    "electron_recoil_direction_defined",
)

ENERGY_SUMMARY_HEADER = (
    "energy_index",
    "incident_energy_kev",
    "alpha",
    "incident_wavelength_pm",
    "maximum_fractional_wavelength_shift",
    "backscatter_scattered_energy_kev",
    "maximum_electron_kinetic_energy_kev",
    "maximum_electron_beta",
    "maximum_electron_speed_m_s",
    "electron_recoil_angle_at_90_deg",
    "forward_recoil_angle_limit_deg",
    "forward_recoil_direction_defined",
)


@dataclass(frozen=True)
class Task09GenerationResult:
    """Validated report and committed Task 9 data paths."""

    report: Task09ValidationReport
    data_paths: Tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task09ValidationReport):
            raise TypeError("report must be a Task09ValidationReport")
        paths = tuple(Path(path) for path in self.data_paths)
        if tuple(path.name for path in paths) != DATA_FILENAMES:
            raise ValueError("data_paths do not follow the frozen filename order")
        object.__setattr__(self, "data_paths", paths)


def _format_float(value: float) -> str:
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("CSV values must be finite")
    if normalized == 0.0:
        normalized = 0.0
    return format(normalized, ".17g")


def _write_csv(
    path: Path,
    header: Tuple[str, ...],
    rows: Iterable[Tuple[str, ...]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_angle_study(path: Path, study: Task09StudyResult) -> None:
    rows = (
        (
            str(energy_index),
            str(angle_index),
            _format_float(study.incident_energy_kev[energy_index, angle_index]),
            _format_float(study.theta_deg[energy_index, angle_index]),
            _format_float(study.alpha[energy_index, angle_index]),
            _format_float(study.incident_wavelength_m[energy_index, angle_index]),
            _format_float(study.wavelength_shift_m[energy_index, angle_index]),
            _format_float(
                study.fractional_wavelength_shift[energy_index, angle_index]
            ),
            _format_float(study.scattered_wavelength_m[energy_index, angle_index]),
            _format_float(study.scattered_energy_kev[energy_index, angle_index]),
            _format_float(
                study.electron_kinetic_energy_kev[energy_index, angle_index]
            ),
            _format_float(study.electron_gamma[energy_index, angle_index]),
            _format_float(study.electron_beta[energy_index, angle_index]),
            _format_float(study.electron_speed_m_s[energy_index, angle_index]),
            _format_float(study.electron_pc_kev[energy_index, angle_index]),
            _format_float(
                study.electron_recoil_angle_deg[energy_index, angle_index]
            ),
            (
                "true"
                if study.electron_recoil_direction_defined[energy_index, angle_index]
                else "false"
            ),
        )
        for energy_index in range(study.energy_count)
        for angle_index in range(study.angle_count)
    )
    _write_csv(path, ANGLE_STUDY_HEADER, rows)


def _write_energy_summary(
    path: Path,
    study: Task09StudyResult,
    configuration: Task09Configuration,
) -> None:
    right_angle_index = configuration.angle_point_count // 2
    rows = (
        (
            str(energy_index),
            _format_float(study.incident_energies_kev[energy_index]),
            _format_float(study.alpha[energy_index, 0]),
            _format_float(study.incident_wavelength_m[energy_index, 0] * 1.0e12),
            _format_float(study.fractional_wavelength_shift[energy_index, -1]),
            _format_float(study.scattered_energy_kev[energy_index, -1]),
            _format_float(study.electron_kinetic_energy_kev[energy_index, -1]),
            _format_float(study.electron_beta[energy_index, -1]),
            _format_float(study.electron_speed_m_s[energy_index, -1]),
            _format_float(
                study.electron_recoil_angle_deg[energy_index, right_angle_index]
            ),
            _format_float(study.electron_recoil_angle_deg[energy_index, 0]),
            (
                "true"
                if study.electron_recoil_direction_defined[energy_index, 0]
                else "false"
            ),
        )
        for energy_index in range(study.energy_count)
    )
    _write_csv(path, ENERGY_SUMMARY_HEADER, rows)


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _reference_anchor_payload(configuration: Task09Configuration) -> Dict[str, object]:
    anchors = []
    for energy in configuration.incident_energies_kev:
        for theta in (0.0, 90.0, 180.0):
            state = reference_kinematics(energy, theta)
            anchors.append(
                {
                    "incident_energy_kev": state.incident_energy_kev,
                    "theta_deg": state.theta_deg,
                    "fractional_wavelength_shift": (
                        state.fractional_wavelength_shift
                    ),
                    "scattered_energy_kev": state.scattered_energy_kev,
                    "electron_kinetic_energy_kev": (
                        state.electron_kinetic_energy_kev
                    ),
                    "electron_gamma": state.electron_gamma,
                    "electron_beta": state.electron_beta,
                    "electron_pc_kev": state.electron_pc_kev,
                    "electron_recoil_angle_deg": (
                        state.electron_recoil_angle_deg
                    ),
                    "electron_recoil_direction_defined": (
                        state.electron_recoil_direction_defined
                    ),
                }
            )
    return {
        "schema_version": "task09-reference-v1",
        "reference_route": (
            "dimensionless scattered-energy ratio plus independent momentum vector"
        ),
        "forward_endpoint_note": (
            "At theta=0 the stored 90-degree value is the continuous plotting limit; "
            "the direction-defined flag is false because electron momentum is zero."
        ),
        "anchors": anchors,
    }


def _validation_payload(report: Task09ValidationReport) -> Dict[str, object]:
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


def _configuration_payload(configuration: Task09Configuration) -> Dict[str, object]:
    return {
        "schema_version": configuration.schema_version,
        "incident_energies_kev": list(configuration.incident_energies_kev),
        "angle_minimum_deg": configuration.angle_minimum_deg,
        "angle_maximum_deg": configuration.angle_maximum_deg,
        "angle_point_count": configuration.angle_point_count,
        "angle_spacing_deg": configuration.angle_spacing_deg,
        "numerical_absolute_tolerance": (
            configuration.numerical_absolute_tolerance
        ),
        "numerical_relative_tolerance": (
            configuration.numerical_relative_tolerance
        ),
        "conservation_relative_tolerance": (
            configuration.conservation_relative_tolerance
        ),
        "evidence_size_budget_bytes": configuration.evidence_size_budget_bytes,
    }


def _manifest_payload(
    report: Task09ValidationReport,
    configuration: Task09Configuration,
    hashed_paths: Tuple[Path, ...],
    temporary_root: Path,
) -> Dict[str, object]:
    hashes = {
        str(path.relative_to(temporary_root)): _sha256(path) for path in hashed_paths
    }
    return {
        "schema_version": "task09-manifest-v1",
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "model": "relativistic free-electron Compton-scattering kinematics",
        "study_digest": report.study_digest,
        "validation_check_count": len(report.checks),
        "validation_passed": report.passed,
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "configuration": _configuration_payload(configuration),
        "constants": {
            "speed_of_light_m_s": SPEED_OF_LIGHT_M_S,
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "elementary_charge_c": ELEMENTARY_CHARGE_C,
            "electron_mass_kg": ELECTRON_MASS_KG,
            "electron_rest_energy_kev": ELECTRON_REST_ENERGY_KEV,
            "electron_compton_wavelength_m": ELECTRON_COMPTON_WAVELENGTH_M,
        },
        "equations": {
            "fractional_wavelength_shift": (
                "Delta lambda/lambda = E/(m_e c^2) (1 - cos theta)"
            ),
            "scattered_energy": (
                "E' = E/[1 + E/(m_e c^2) (1 - cos theta)]"
            ),
            "electron_speed": "beta = sqrt(1 - gamma^-2)",
            "electron_recoil_angle": (
                "phi = atan2(E' sin theta, E - E' cos theta)"
            ),
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "sha256": hashes,
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
        "official_requirements": OFFICIAL_REQUIREMENTS_PATH,
        "official_source": (
            "https://www.bpho.org.uk/bpho/computational-challenge/"
            "BPhO_ComPhys_Challenge_2026.zip"
        ),
        "constant_sources": [
            "https://www.bipm.org/en/measurement-units/si-defining-constants",
            "https://physics.nist.gov/cuu/pdf/wall_2022.pdf",
        ],
    }


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _verify_csv(
    path: Path,
    *,
    expected_header: Tuple[str, ...],
    expected_rows: int,
    integer_fields: Tuple[str, ...],
    boolean_fields: Tuple[str, ...],
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
                elif field_name in boolean_fields:
                    if text not in ("true", "false"):
                        raise ValueError(f"{path.name} contains an invalid boolean")
                elif not math.isfinite(float(text)):
                    raise ValueError(f"{path.name} contains a non-finite value")
        if row_count != expected_rows:
            raise ValueError(f"{path.name} has the wrong row count")


def _verify_prepared_data(
    data_paths: Tuple[Path, ...],
    report: Task09ValidationReport,
    study: Task09StudyResult,
    configuration: Task09Configuration,
    temporary_root: Path,
) -> None:
    if tuple(path.name for path in data_paths) != DATA_FILENAMES:
        raise ValueError("data paths do not follow the frozen filename order")
    for path in data_paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty data artifact: {path.name}")
    _verify_csv(
        data_paths[0],
        expected_header=ANGLE_STUDY_HEADER,
        expected_rows=study.row_count,
        integer_fields=("energy_index", "angle_index"),
        boolean_fields=("electron_recoil_direction_defined",),
    )
    _verify_csv(
        data_paths[1],
        expected_header=ENERGY_SUMMARY_HEADER,
        expected_rows=study.energy_count,
        integer_fields=("energy_index",),
        boolean_fields=("forward_recoil_direction_defined",),
    )
    for path in data_paths[2:]:
        with path.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=_reject_json_constant)
    with data_paths[2].open(encoding="utf-8") as handle:
        references = json.load(handle)
    if len(references.get("anchors", ())) != study.energy_count * 3:
        raise ValueError("reference anchor file has the wrong case count")
    with data_paths[3].open(encoding="utf-8") as handle:
        validation = json.load(handle)
    if not validation.get("passed") or len(validation.get("checks", ())) != len(
        report.checks
    ):
        raise ValueError("serialized validation report is incomplete or failed")
    with data_paths[-1].open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if tuple(manifest.get("expected_data_filenames", ())) != DATA_FILENAMES:
        raise ValueError("manifest has the wrong expected filename order")
    for relative_name, expected_hash in manifest["sha256"].items():
        if _sha256(temporary_root / relative_name) != expected_hash:
            raise ValueError(f"manifest hash mismatch for {relative_name}")
    if sum(path.stat().st_size for path in data_paths) > (
        configuration.evidence_size_budget_bytes
    ):
        raise ValueError("Task 9 data package exceeds its size budget")


def _restore_path(destination: Path, content: Optional[bytes]) -> None:
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


def _commit_all(prepared: Tuple[Tuple[Path, Path], ...]) -> None:
    destinations = tuple(destination for _, destination in prepared)
    originals = {
        destination: destination.read_bytes() if destination.exists() else None
        for destination in destinations
    }
    replaced = []
    try:
        for source, destination in prepared:
            os.replace(source, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            _restore_path(destination, originals[destination])
        raise


def generate_task09(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> Task09GenerationResult:
    """Build, validate, verify and atomically replace Task 9 data outputs."""

    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    started = time.perf_counter()
    data_output = Path(data_directory)
    data_output.mkdir(parents=True, exist_ok=True)

    study_started = time.perf_counter()
    study = build_task09_study(configuration)
    study_runtime = time.perf_counter() - study_started
    if study_runtime > configuration.study_runtime_budget_s:
        raise RuntimeError("Task 9 study exceeded its runtime budget")
    report = validate_task09(study, configuration)
    if not report.passed:
        raise RuntimeError("Task 9 generation requires every validation check to pass")

    with tempfile.TemporaryDirectory(prefix="task09-generation-") as temporary:
        temporary_root = Path(temporary)
        temporary_data = temporary_root / "data" / "task09"
        temporary_data.mkdir(parents=True)

        _write_angle_study(temporary_data / DATA_FILENAMES[0], study)
        _write_energy_summary(
            temporary_data / DATA_FILENAMES[1],
            study,
            configuration,
        )
        _write_json(
            temporary_data / DATA_FILENAMES[2],
            _reference_anchor_payload(configuration),
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
            study,
            configuration,
            temporary_root,
        )
        if time.perf_counter() - started > configuration.generation_runtime_budget_s:
            raise RuntimeError("Task 9 generation exceeded its runtime budget")

        prepared = tuple(
            (temporary_data / filename, data_output / filename)
            for filename in DATA_FILENAMES
        )
        _commit_all(prepared)

    return Task09GenerationResult(
        report=report,
        data_paths=tuple(data_output / filename for filename in DATA_FILENAMES),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_DATA_DIRECTORY)
    arguments = parser.parse_args()
    result = generate_task09(arguments.data_directory)
    passed = sum(check.passed for check in result.report.checks)
    print(
        f"Task 9 generated {len(result.data_paths)} data files; "
        f"{passed}/{len(result.report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
