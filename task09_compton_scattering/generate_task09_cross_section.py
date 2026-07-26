"""Generate the separate validated Klein–Nishina extension package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np

from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.constants import (
    BARN_M2,
    CLASSICAL_ELECTRON_RADIUS_M,
    ELECTRON_REST_ENERGY_KEV,
    THOMSON_CROSS_SECTION_M2,
)
from task09_compton_scattering.cross_section import (
    KleinNishinaStudy,
    build_klein_nishina_study,
)
from task09_compton_scattering.cross_section_reference import (
    reference_total_cross_section_m2,
)
from task09_compton_scattering.cross_section_validation import (
    CrossSectionValidationReport,
    validate_cross_section_study,
)
from task09_compton_scattering.generate_task09 import (
    DEFAULT_DATA_DIRECTORY,
    REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
    _commit_all,
    _format_float,
    _sha256,
)
from task09_compton_scattering.models import angle_samples


CROSS_SECTION_FILENAMES = (
    "klein_nishina_study.csv",
    "klein_nishina_summary.csv",
    "cross_section_validation_report.json",
    "cross_section_manifest.json",
)

CROSS_SECTION_STUDY_HEADER = (
    "energy_index",
    "angle_index",
    "incident_energy_kev",
    "theta_deg",
    "scattered_to_incident_energy_ratio",
    "differential_cross_section_m2_sr",
    "differential_cross_section_barn_sr",
    "relative_differential_cross_section",
    "theta_density_m2_rad",
    "theta_pdf_rad_inv",
    "total_cross_section_m2",
    "total_cross_section_barn",
)

CROSS_SECTION_SUMMARY_HEADER = (
    "energy_index",
    "incident_energy_kev",
    "alpha",
    "analytical_total_cross_section_barn",
    "quadrature_total_cross_section_barn",
    "quadrature_relative_error",
    "forward_hemisphere_probability",
    "modal_polar_angle_deg",
    "mean_polar_angle_deg",
)


@dataclass(frozen=True)
class CrossSectionGenerationResult:
    """Validated extension report and committed output paths."""

    report: CrossSectionValidationReport
    data_paths: Tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, CrossSectionValidationReport):
            raise TypeError("report must be a CrossSectionValidationReport")
        paths = tuple(Path(path) for path in self.data_paths)
        if tuple(path.name for path in paths) != CROSS_SECTION_FILENAMES:
            raise ValueError("extension paths do not follow the frozen filename order")
        object.__setattr__(self, "data_paths", paths)


def _write_csv(
    path: Path,
    header: Tuple[str, ...],
    rows: Iterable[Tuple[str, ...]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_study(path: Path, study: KleinNishinaStudy) -> None:
    energy_count, angle_count = study.incident_energy_kev.shape
    rows = (
        (
            str(energy_index),
            str(angle_index),
            _format_float(study.incident_energy_kev[energy_index, angle_index]),
            _format_float(study.theta_deg[energy_index, angle_index]),
            _format_float(
                study.scattered_to_incident_energy_ratio[energy_index, angle_index]
            ),
            _format_float(
                study.differential_cross_section_m2_sr[energy_index, angle_index]
            ),
            _format_float(
                study.differential_cross_section_barn_sr[energy_index, angle_index]
            ),
            _format_float(
                study.relative_differential_cross_section[energy_index, angle_index]
            ),
            _format_float(study.theta_density_m2_rad[energy_index, angle_index]),
            _format_float(study.theta_pdf_rad_inv[energy_index, angle_index]),
            _format_float(study.total_cross_section_m2[energy_index, angle_index]),
            _format_float(study.total_cross_section_barn[energy_index, angle_index]),
        )
        for energy_index in range(energy_count)
        for angle_index in range(angle_count)
    )
    _write_csv(path, CROSS_SECTION_STUDY_HEADER, rows)


def _summary_rows(
    study: KleinNishinaStudy,
    configuration: Task09Configuration,
) -> Iterable[Tuple[str, ...]]:
    theta_axis = study.theta_deg[0]
    theta_rad = np.radians(theta_axis)
    right_angle_index = configuration.angle_point_count // 2
    for energy_index, energy in enumerate(configuration.incident_energies_kev):
        analytical = float(study.total_cross_section_m2[energy_index, 0])
        quadrature = reference_total_cross_section_m2(
            energy,
            configuration.cross_section_quadrature_order,
        )
        pdf = study.theta_pdf_rad_inv[energy_index]
        forward_probability = float(
            np.trapezoid(
                pdf[: right_angle_index + 1],
                theta_rad[: right_angle_index + 1],
            )
        )
        modal_angle = float(theta_axis[int(np.argmax(pdf))])
        mean_angle = float(np.trapezoid(theta_axis * pdf, theta_rad))
        yield (
            str(energy_index),
            _format_float(energy),
            _format_float(energy / ELECTRON_REST_ENERGY_KEV),
            _format_float(analytical / BARN_M2),
            _format_float(quadrature / BARN_M2),
            _format_float((analytical - quadrature) / quadrature),
            _format_float(forward_probability),
            _format_float(modal_angle),
            _format_float(mean_angle),
        )


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _validation_payload(report: CrossSectionValidationReport) -> Dict[str, object]:
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


def _manifest_payload(
    report: CrossSectionValidationReport,
    configuration: Task09Configuration,
    hashed_paths: Tuple[Path, ...],
    temporary_root: Path,
) -> Dict[str, object]:
    return {
        "schema_version": "task09-cross-section-manifest-v1",
        "model": "unpolarized free-electron Klein-Nishina angular weighting",
        "scope": "optional extension; separate from the three official kinematic curves",
        "study_digest": report.study_digest,
        "validation_passed": report.passed,
        "validation_check_count": len(report.checks),
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "configuration": {
            "incident_energies_kev": list(configuration.incident_energies_kev),
            "angle_point_count": configuration.angle_point_count,
            "angle_spacing_deg": configuration.angle_spacing_deg,
            "quadrature_order": configuration.cross_section_quadrature_order,
        },
        "constants": {
            "classical_electron_radius_m": CLASSICAL_ELECTRON_RADIUS_M,
            "thomson_cross_section_m2": THOMSON_CROSS_SECTION_M2,
            "barn_m2": BARN_M2,
        },
        "equation": (
            "d sigma/d Omega = r_e^2/2 (E'/E)^2 "
            "[E'/E + E/E' - sin(theta)^2]"
        ),
        "expected_filenames": list(CROSS_SECTION_FILENAMES),
        "sha256": {
            str(path.relative_to(temporary_root)): _sha256(path)
            for path in hashed_paths
        },
        "extension_decision": "task09_compton_scattering/EXTENSION_DECISION.md",
        "reference_sources": [
            "https://physics.nist.gov/PhysRefData/Xcom/Text/chap2.html",
            "https://doi.org/10.1007/BF01366453",
        ],
    }


def _verify_csv(
    path: Path,
    expected_header: Tuple[str, ...],
    expected_rows: int,
) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise ValueError(f"{path.name} has the wrong header")
        rows = list(reader)
    if len(rows) != expected_rows:
        raise ValueError(f"{path.name} has the wrong row count")
    for row in rows:
        for field_name, text in row.items():
            if field_name in ("energy_index", "angle_index"):
                int(text)
            elif not math.isfinite(float(text)):
                raise ValueError(f"{path.name} contains a non-finite value")


def _verify_prepared(
    paths: Tuple[Path, ...],
    report: CrossSectionValidationReport,
    configuration: Task09Configuration,
    temporary_root: Path,
) -> None:
    if tuple(path.name for path in paths) != CROSS_SECTION_FILENAMES:
        raise ValueError("extension paths have the wrong filename order")
    if any(not path.is_file() or path.stat().st_size == 0 for path in paths):
        raise ValueError("extension package contains a missing or empty file")
    _verify_csv(
        paths[0],
        CROSS_SECTION_STUDY_HEADER,
        len(configuration.incident_energies_kev) * configuration.angle_point_count,
    )
    _verify_csv(
        paths[1],
        CROSS_SECTION_SUMMARY_HEADER,
        len(configuration.incident_energies_kev),
    )
    for path in paths[2:]:
        with path.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON token is forbidden: {value}")
            ))
    with paths[2].open(encoding="utf-8") as handle:
        validation = json.load(handle)
    if not validation.get("passed") or len(validation.get("checks", ())) != len(
        report.checks
    ):
        raise ValueError("serialized extension validation is incomplete")
    with paths[-1].open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if tuple(manifest.get("expected_filenames", ())) != CROSS_SECTION_FILENAMES:
        raise ValueError("extension manifest has the wrong filename order")
    for relative_name, expected_hash in manifest["sha256"].items():
        if _sha256(temporary_root / relative_name) != expected_hash:
            raise ValueError(f"extension manifest mismatch for {relative_name}")
    if sum(path.stat().st_size for path in paths) > configuration.evidence_size_budget_bytes:
        raise ValueError("extension package exceeds the evidence size budget")


def generate_task09_cross_section(
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> CrossSectionGenerationResult:
    """Build, validate, verify and atomically replace extension outputs."""

    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    started = time.perf_counter()
    output = Path(data_directory)
    output.mkdir(parents=True, exist_ok=True)
    study = build_klein_nishina_study(
        np.asarray(configuration.incident_energies_kev)[:, None],
        angle_samples(configuration.angle_point_count, configuration=configuration)[
            None, :
        ],
    )
    report = validate_cross_section_study(study, configuration)
    if not report.passed:
        raise RuntimeError("extension generation requires every check to pass")

    with tempfile.TemporaryDirectory(prefix="task09-cross-section-") as temporary:
        temporary_root = Path(temporary)
        temporary_data = temporary_root / "data" / "task09"
        temporary_data.mkdir(parents=True)
        _write_study(temporary_data / CROSS_SECTION_FILENAMES[0], study)
        _write_csv(
            temporary_data / CROSS_SECTION_FILENAMES[1],
            CROSS_SECTION_SUMMARY_HEADER,
            _summary_rows(study, configuration),
        )
        _write_json(
            temporary_data / CROSS_SECTION_FILENAMES[2],
            _validation_payload(report),
        )
        pre_manifest = tuple(
            temporary_data / filename for filename in CROSS_SECTION_FILENAMES[:-1]
        )
        _write_json(
            temporary_data / CROSS_SECTION_FILENAMES[-1],
            _manifest_payload(report, configuration, pre_manifest, temporary_root),
        )
        paths = tuple(
            temporary_data / filename for filename in CROSS_SECTION_FILENAMES
        )
        _verify_prepared(paths, report, configuration, temporary_root)
        if time.perf_counter() - started > configuration.generation_runtime_budget_s:
            raise RuntimeError("extension generation exceeded its runtime budget")
        _commit_all(
            tuple(
                (temporary_data / filename, output / filename)
                for filename in CROSS_SECTION_FILENAMES
            )
        )
    return CrossSectionGenerationResult(
        report=report,
        data_paths=tuple(output / filename for filename in CROSS_SECTION_FILENAMES),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_DATA_DIRECTORY)
    arguments = parser.parse_args()
    result = generate_task09_cross_section(arguments.data_directory)
    passed = sum(check.passed for check in result.report.checks)
    print(
        f"Task 9 Klein–Nishina extension generated {len(result.data_paths)} files; "
        f"{passed}/{len(result.report.checks)} checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
