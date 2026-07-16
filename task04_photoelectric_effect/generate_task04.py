"""Validated deterministic evidence generation for Task 4."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from task04_photoelectric_effect.analysis import (
    Task04StudyResult,
    build_task04_study,
)
from task04_photoelectric_effect.configuration import (
    DEFAULT_CONFIGURATION,
    Task04Configuration,
)
from task04_photoelectric_effect.constants import (
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    HC_OVER_CHARGE_V_M,
    METRES_PER_NANOMETRE,
    NANOMETRES_PER_METRE,
    PLANCK_CONSTANT_J_S,
    PLANCK_OVER_CHARGE_V_S,
    SPEED_OF_LIGHT_M_S,
)
from task04_photoelectric_effect.materials import OFFICIAL_MATERIALS
from task04_photoelectric_effect.validation import (
    Task04ValidationReport,
    validate_task04,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task04"
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task04"
MATHEMATICAL_SPECIFICATION_PATH = (
    "task04_photoelectric_effect/MATHEMATICAL_MODEL.md"
)
OUTPUT_SCHEMA_VERSION = "task04-data-v1"
DATA_FILENAMES = (
    "material_cutoffs.csv",
    "stopping_voltage_frequency.csv",
    "stopping_voltage_wavelength.csv",
    "validation_report.json",
    "reproducibility_manifest.json",
)
FIGURE_FILENAMES = (
    "stopping_voltage_frequency.png",
    "stopping_voltage_frequency.svg",
    "stopping_voltage_wavelength.png",
    "stopping_voltage_wavelength.svg",
    "copper_threshold_explanation.png",
    "copper_threshold_explanation.svg",
    "photoelectric_validation.png",
    "photoelectric_validation.svg",
    "task04_summary.png",
    "task04_summary.svg",
)
ANIMATION_FILENAMES = (
    "photoelectric_demo.gif",
    "photoelectric_demo_storyboard.png",
)

_MATERIAL_HEADER = (
    "material",
    "symbol",
    "work_function_ev",
    "work_function_j",
    "cutoff_frequency_hz",
    "cutoff_wavelength_nm",
)
_FREQUENCY_HEADER = (
    "material",
    "symbol",
    "frequency_hz",
    "linear_stopping_voltage_v",
    "emission_possible",
    "physical_stopping_voltage_v",
)
_WAVELENGTH_HEADER = (
    "material",
    "symbol",
    "wavelength_nm",
    "linear_stopping_voltage_v",
    "emission_possible",
    "physical_stopping_voltage_v",
)


@dataclass(frozen=True)
class Task04DataGenerationResult:
    """Passing report and ordered paths from one data generation transaction."""

    report: Task04ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        """Protect result ordering and prevent failed evidence claims."""

        if not isinstance(self.report, Task04ValidationReport):
            raise TypeError("report must be a Task04ValidationReport")
        if not self.report.passed:
            raise ValueError("generation result requires a passing report")
        try:
            paths = tuple(Path(path) for path in self.output_paths)
        except TypeError as exc:
            raise TypeError("output_paths must be an iterable of paths") from exc
        if tuple(path.name for path in paths) != DATA_FILENAMES:
            raise ValueError("output_paths must follow the frozen file order")
        object.__setattr__(self, "output_paths", paths)


def _format_float(value: float) -> str:
    """Return finite round-trip text for one binary double."""

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("serialized numerical values must be finite")
    return format(normalized, ".17g")


def _format_source_work_function(value: float) -> str:
    """Preserve the one-decimal precision of the official source table."""

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("source work functions must be finite")
    return f"{normalized:.1f}"


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: Iterable[tuple[str, ...]],
) -> None:
    """Write one UTF-8 CSV with deterministic LF line endings."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_material_cutoffs(path: Path, study: Task04StudyResult) -> None:
    """Write the nine source records and their analytical cut-offs."""

    rows = (
        (
            material.name,
            material.symbol,
            _format_source_work_function(study.work_functions_ev[index]),
            _format_float(study.work_functions_j[index]),
            _format_float(study.cutoff_frequencies_hz[index]),
            _format_float(study.cutoff_wavelengths_nm[index]),
        )
        for index, material in enumerate(study.materials)
    )
    _write_csv(path, _MATERIAL_HEADER, rows)


def _write_stopping_voltage_frequency(
    path: Path,
    study: Task04StudyResult,
) -> None:
    """Write long-form frequency evidence in official material order."""

    rows = (
        (
            material.name,
            material.symbol,
            _format_float(frequency),
            _format_float(study.frequency_linear_voltage_v[m_index, f_index]),
            "true" if study.frequency_emission_mask[m_index, f_index] else "false",
            (
                _format_float(
                    study.frequency_physical_voltage_v[m_index, f_index]
                )
                if study.frequency_emission_mask[m_index, f_index]
                else ""
            ),
        )
        for m_index, material in enumerate(study.materials)
        for f_index, frequency in enumerate(study.frequency_hz)
    )
    _write_csv(path, _FREQUENCY_HEADER, rows)


def _write_stopping_voltage_wavelength(
    path: Path,
    study: Task04StudyResult,
) -> None:
    """Write long-form wavelength evidence in official material order."""

    rows = (
        (
            material.name,
            material.symbol,
            _format_float(wavelength),
            _format_float(study.wavelength_linear_voltage_v[m_index, w_index]),
            "true" if study.wavelength_emission_mask[m_index, w_index] else "false",
            (
                _format_float(
                    study.wavelength_physical_voltage_v[m_index, w_index]
                )
                if study.wavelength_emission_mask[m_index, w_index]
                else ""
            ),
        )
        for m_index, material in enumerate(study.materials)
        for w_index, wavelength in enumerate(study.wavelength_nm)
    )
    _write_csv(path, _WAVELENGTH_HEADER, rows)


def _validation_payload(report: Task04ValidationReport) -> dict[str, object]:
    """Return the complete JSON-compatible validation schema."""

    return {
        "schema_version": report.schema_version,
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


def _configuration_payload(
    configuration: Task04Configuration,
) -> dict[str, object]:
    """Return every immutable configuration field in declaration order."""

    return {
        field.name: getattr(configuration, field.name)
        for field in fields(configuration)
    }


def _manifest_payload(
    configuration: Task04Configuration,
) -> dict[str, object]:
    """Return complete portable provenance without generated measurements."""

    return {
        "schema_version": configuration.schema_version,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "constants": {
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "elementary_charge_c": ELEMENTARY_CHARGE_C,
            "speed_of_light_m_s": SPEED_OF_LIGHT_M_S,
            "electronvolt_j": ELECTRONVOLT_J,
            "planck_over_charge_v_s": PLANCK_OVER_CHARGE_V_S,
            "hc_over_charge_v_m": HC_OVER_CHARGE_V_M,
            "metres_per_nanometre": METRES_PER_NANOMETRE,
            "nanometres_per_metre": NANOMETRES_PER_METRE,
        },
        "configuration": _configuration_payload(configuration),
        "tolerances": {
            field.name: getattr(configuration, field.name)
            for field in fields(configuration)
            if "tolerance" in field.name or "slack" in field.name
        },
        "units": {
            "work_function_ev": "eV",
            "work_function_j": "J",
            "cutoff_frequency_hz": "Hz",
            "cutoff_wavelength_nm": "nm",
            "frequency_hz": "Hz",
            "wavelength_nm": "nm",
            "linear_stopping_voltage_v": "V",
            "physical_stopping_voltage_v": "V",
            "emission_possible": "boolean",
        },
        "material_source": "BPhO CompPhys2026 Quantum, slide 28",
        "official_materials": [
            {
                "name": material.name,
                "symbol": material.symbol,
                "work_function_ev": material.work_function_ev,
            }
            for material in OFFICIAL_MATERIALS
        ],
        "expected_data_filenames": list(DATA_FILENAMES),
        "expected_figure_filenames": list(FIGURE_FILENAMES),
        "optional_animation_filenames": list(ANIMATION_FILENAMES),
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """Write sorted, indented, finite JSON with one final LF."""

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        handle.write("\n")


def _reject_json_constant(value: str) -> None:
    """Reject non-standard NaN and infinity tokens during verification."""

    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _verify_csv(
    path: Path,
    expected_header: tuple[str, ...],
    expected_rows: int,
) -> None:
    """Parse and semantically verify one prepared CSV artifact."""

    content = path.read_bytes()
    if not content.endswith(b"\n") or b"\r\n" in content:
        raise ValueError(f"CSV line endings are invalid: {path.name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise ValueError(f"CSV header is invalid: {path.name}")
        row_count = 0
        for row in reader:
            row_count += 1
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV row width is invalid: {path.name}")
            if not row["material"] or not row["symbol"]:
                raise ValueError(f"CSV material identity is empty: {path.name}")
            for field_name, value in row.items():
                if field_name in ("material", "symbol", "emission_possible"):
                    continue
                if field_name == "physical_stopping_voltage_v" and value == "":
                    continue
                if not math.isfinite(float(value)):
                    raise ValueError(
                        f"CSV contains a non-finite value: {path.name}"
                    )
            if "emission_possible" in row:
                emission = row["emission_possible"]
                physical = row["physical_stopping_voltage_v"]
                if emission not in ("true", "false"):
                    raise ValueError(f"CSV boolean is invalid: {path.name}")
                if (emission == "true") != (physical != ""):
                    raise ValueError(
                        f"CSV physical-domain field is invalid: {path.name}"
                    )
        if row_count != expected_rows:
            raise ValueError(
                f"CSV row count is invalid for {path.name}: {row_count}"
            )


def _verify_json(path: Path, *, validation_report: bool) -> None:
    """Parse one prepared JSON artifact and check its top-level schema."""

    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or "\r\n" in text:
        raise ValueError(f"JSON line endings are invalid: {path.name}")
    payload = json.loads(text, parse_constant=_reject_json_constant)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path.name}")
    if validation_report:
        if set(payload) != {"schema_version", "passed", "checks"}:
            raise ValueError("validation report JSON schema is invalid")
        if payload["passed"] is not True or len(payload["checks"]) != 43:
            raise ValueError("validation report JSON does not pass 43 checks")
    else:
        if payload.get("output_schema_version") != OUTPUT_SCHEMA_VERSION:
            raise ValueError("reproducibility manifest schema is invalid")
        if payload.get("expected_data_filenames") != list(DATA_FILENAMES):
            raise ValueError("reproducibility manifest filenames are invalid")


def _verify_prepared_outputs(
    prepared: tuple[tuple[str, Path], ...],
    configuration: Task04Configuration,
) -> None:
    """Verify every temporary artifact before any destination is changed."""

    if tuple(filename for filename, _ in prepared) != DATA_FILENAMES:
        raise ValueError("prepared output names do not match the frozen order")
    verifiers: tuple[Callable[[Path], None], ...] = (
        lambda path: _verify_csv(path, _MATERIAL_HEADER, 9),
        lambda path: _verify_csv(
            path,
            _FREQUENCY_HEADER,
            9 * configuration.frequency_points,
        ),
        lambda path: _verify_csv(
            path,
            _WAVELENGTH_HEADER,
            9 * configuration.wavelength_points,
        ),
        lambda path: _verify_json(path, validation_report=True),
        lambda path: _verify_json(path, validation_report=False),
    )
    for (_, path), verifier in zip(prepared, verifiers):
        verifier(path)
    total_bytes = sum(path.stat().st_size for _, path in prepared)
    if total_bytes > configuration.evidence_size_budget_bytes:
        raise ValueError(
            "prepared evidence exceeds the configured size budget: "
            f"{total_bytes} bytes"
        )


def _replace_path(source: Path, destination: Path) -> None:
    """Atomically replace one path; isolated for transaction-failure tests."""

    os.replace(source, destination)


def _unused_sibling(path: Path, *, suffix: str) -> Path:
    """Reserve and release one unique sibling name for a later atomic move."""

    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=suffix,
        dir=path.parent,
    )
    os.close(descriptor)
    sibling = Path(name)
    sibling.unlink()
    return sibling


def _restore_transaction(
    installed: list[Path],
    backups: list[tuple[Path, Path]],
) -> None:
    """Remove new destinations and restore every pre-transaction file."""

    rollback_errors: list[OSError] = []
    for destination in reversed(installed):
        try:
            if destination.exists():
                destination.unlink()
        except OSError as exc:
            rollback_errors.append(exc)
    for destination, backup in reversed(backups):
        try:
            if backup.exists():
                _replace_path(backup, destination)
        except OSError as exc:
            rollback_errors.append(exc)
    if rollback_errors:
        raise RuntimeError("Task 4 output rollback failed") from rollback_errors[0]


def _atomic_write_outputs(
    output_directory: Path,
    writers: tuple[tuple[str, Callable[[Path], None]], ...],
    configuration: Task04Configuration,
) -> tuple[Path, ...]:
    """Prepare, verify, and atomically install all files with full rollback."""

    if output_directory.exists() and not output_directory.is_dir():
        raise NotADirectoryError(
            f"output path is not a directory: {output_directory}"
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    destinations = tuple(output_directory / name for name, _ in writers)
    for destination in destinations:
        if destination.exists() and destination.is_dir():
            raise IsADirectoryError(
                f"output destination is a directory: {destination}"
            )

    temporary_paths: list[Path] = []
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for filename, writer in writers:
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

        prepared = tuple(
            (filename, temporary_path)
            for (filename, _), temporary_path in zip(writers, temporary_paths)
        )
        _verify_prepared_outputs(prepared, configuration)

        for destination in destinations:
            if destination.exists():
                backup = _unused_sibling(destination, suffix=".bak")
                _replace_path(destination, backup)
                backups.append((destination, backup))

        for temporary_path, destination in zip(
            temporary_paths,
            destinations,
        ):
            _replace_path(temporary_path, destination)
            installed.append(destination)
        return destinations
    except Exception:
        _restore_transaction(installed, backups)
        raise
    finally:
        for path in temporary_paths:
            if path.exists():
                path.unlink()
        for _, backup in backups:
            if backup.exists():
                backup.unlink()


def write_task04_data(
    study: Task04StudyResult,
    output_directory: str | os.PathLike[str] = DEFAULT_DATA_DIRECTORY,
    configuration: Task04Configuration = DEFAULT_CONFIGURATION,
) -> Task04DataGenerationResult:
    """Validate one completed study before transactionally writing evidence."""

    report = validate_task04(study, configuration)
    if not report.passed:
        failed_names = ", ".join(check.name for check in report.failed_checks)
        raise RuntimeError(
            "Task 4 data generation refused because validation failed: "
            f"{failed_names}"
        )

    output_path = Path(output_directory)
    writers: tuple[tuple[str, Callable[[Path], None]], ...] = (
        (
            DATA_FILENAMES[0],
            lambda path: _write_material_cutoffs(path, study),
        ),
        (
            DATA_FILENAMES[1],
            lambda path: _write_stopping_voltage_frequency(path, study),
        ),
        (
            DATA_FILENAMES[2],
            lambda path: _write_stopping_voltage_wavelength(path, study),
        ),
        (
            DATA_FILENAMES[3],
            lambda path: _write_json(path, _validation_payload(report)),
        ),
        (
            DATA_FILENAMES[4],
            lambda path: _write_json(path, _manifest_payload(configuration)),
        ),
    )
    output_paths = _atomic_write_outputs(
        output_path,
        writers,
        configuration,
    )
    return Task04DataGenerationResult(
        report=report,
        output_paths=output_paths,
    )


def generate_task04_data(
    output_directory: str | os.PathLike[str] = DEFAULT_DATA_DIRECTORY,
    configuration: Task04Configuration = DEFAULT_CONFIGURATION,
) -> Task04DataGenerationResult:
    """Build, validate, and serialize the complete Task 4 study."""

    if not isinstance(configuration, Task04Configuration):
        raise TypeError("configuration must be a Task04Configuration")
    study = build_task04_study(configuration=configuration)
    return write_task04_data(study, output_directory, configuration)


def main(argv: Sequence[str] | None = None) -> int:
    """Run validated data generation without loading plotting dependencies."""

    parser = argparse.ArgumentParser(
        description="Generate validated Task 4 numerical evidence.",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="write CSV and JSON evidence without importing Matplotlib",
    )
    parser.add_argument(
        "--with-animation",
        action="store_true",
        help="also write the optional GIF and four-panel storyboard",
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
    if arguments.data_only and arguments.with_animation:
        parser.error("--with-animation cannot be combined with --data-only")

    study = build_task04_study()
    result = write_task04_data(study, arguments.data_dir)
    if arguments.data_only:
        print("Task 4 Stage 7: validated numerical evidence")
    elif arguments.with_animation:
        print("Task 4 Stage 10: validated evidence, figures and animation")
    else:
        print("Task 4 Stage 8: validated evidence and figures")
    for path in result.output_paths:
        print(path)
    if not arguments.data_only:
        # Local import is required: --data-only must not load Matplotlib.
        from task04_photoelectric_effect.plotting import write_task04_figures

        figure_result = write_task04_figures(
            study,
            result.report,
            arguments.figure_dir,
        )
        for path in figure_result.output_paths:
            print(path)
        if arguments.with_animation:
            from task04_photoelectric_effect.animation import (
                write_task04_animation,
            )

            animation_result = write_task04_animation(
                study,
                result.report,
                arguments.figure_dir,
            )
            for path in animation_result.output_paths:
                print(path)
    print(f"Validation checks: {len(result.report.checks)}")
    if arguments.data_only:
        print("Task 4 data generation: PASS")
    elif arguments.with_animation:
        print("Task 4 complete generation with animation: PASS")
    else:
        print("Task 4 complete generation: PASS")
    return 0


__all__ = [
    "ANIMATION_FILENAMES",
    "DATA_FILENAMES",
    "DEFAULT_DATA_DIRECTORY",
    "DEFAULT_FIGURE_DIRECTORY",
    "FIGURE_FILENAMES",
    "MATHEMATICAL_SPECIFICATION_PATH",
    "OUTPUT_SCHEMA_VERSION",
    "Task04DataGenerationResult",
    "generate_task04_data",
    "main",
    "write_task04_data",
]


if __name__ == "__main__":
    raise SystemExit(main())
