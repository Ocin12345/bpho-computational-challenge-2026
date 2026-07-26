"""Validation-first deterministic evidence generation for Task 5."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from task05_hydrogen_spectrum.analysis import Task05StudyResult, build_task05_study
from task05_hydrogen_spectrum.configuration import (
    DEFAULT_CONFIGURATION,
    Task05Configuration,
)
from task05_hydrogen_spectrum.constants import (
    ELEMENTARY_CHARGE_C,
    HC_EV_NM,
    PLANCK_CONSTANT_J_S,
    RYDBERG_CONSTANT_PER_M,
    RYDBERG_ENERGY_EV,
    SPEED_OF_LIGHT_M_S,
)
from task05_hydrogen_spectrum.transitions import SERIES_NAMES
from task05_hydrogen_spectrum.validation import (
    Task05ValidationReport,
    validate_task05,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "task05"
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task05"
OUTPUT_SCHEMA_VERSION = "task05-data-v1"
MATHEMATICAL_SPECIFICATION_PATH = "task05_hydrogen_spectrum/MATHEMATICAL_MODEL.md"

DATA_FILENAMES = (
    "energy_levels.csv",
    "emission_transitions.csv",
    "series_limits.csv",
    "validation_report.json",
    "reproducibility_manifest.json",
)

FIGURE_FILENAMES = (
    "photon_energy_vs_wavelength.png",
    "photon_energy_vs_wavelength.svg",
    "bohr_energy_level_diagram.png",
    "bohr_energy_level_diagram.svg",
    "balmer_visible_spectrum.png",
    "balmer_visible_spectrum.svg",
    "hydrogen_series_convergence.png",
    "hydrogen_series_convergence.svg",
    "hydrogen_validation.png",
    "hydrogen_validation.svg",
    "task05_summary.png",
    "task05_summary.svg",
)


@dataclass(frozen=True)
class Task05DataGenerationResult:
    """Passing report and ordered paths from one data transaction."""

    report: Task05ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task05ValidationReport) or not self.report.passed:
            raise ValueError("generation result requires a passing Task 5 report")
        paths = tuple(Path(path) for path in self.output_paths)
        if tuple(path.name for path in paths) != DATA_FILENAMES:
            raise ValueError("output_paths must follow the frozen file order")
        object.__setattr__(self, "output_paths", paths)


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


def _write_energy_levels(path: Path, study: Task05StudyResult) -> None:
    _write_csv(
        path,
        ("n", "energy_ev", "energy_j"),
        (
            (
                str(int(level)),
                _format_float(study.level_energy_ev[index]),
                _format_float(study.level_energy_j[index]),
            )
            for index, level in enumerate(study.levels_n)
        ),
    )


def _write_emission_transitions(path: Path, study: Task05StudyResult) -> None:
    header = (
        "initial_n",
        "final_n",
        "series_name",
        "display_group",
        "line_name",
        "initial_energy_ev",
        "final_energy_ev",
        "photon_energy_ev",
        "photon_energy_j",
        "frequency_hz",
        "wavelength_m",
        "wavelength_nm",
        "spectral_region",
    )
    rows = (
        (
            str(int(study.initial_n[index])),
            str(int(study.final_n[index])),
            study.series_names[index],
            study.display_groups[index],
            study.line_names[index] or "",
            _format_float(study.initial_energy_ev[index]),
            _format_float(study.final_energy_ev[index]),
            _format_float(study.photon_energy_ev[index]),
            _format_float(study.photon_energy_j[index]),
            _format_float(study.frequency_hz[index]),
            _format_float(study.wavelength_m[index]),
            _format_float(study.wavelength_nm[index]),
            study.spectral_regions[index],
        )
        for index in range(study.initial_n.size)
    )
    _write_csv(path, header, rows)


def _write_series_limits(path: Path, study: Task05StudyResult) -> None:
    _write_csv(
        path,
        (
            "final_n",
            "series_name",
            "limit_energy_ev",
            "limit_wavelength_m",
            "limit_wavelength_nm",
        ),
        (
            (
                str(int(final)),
                SERIES_NAMES[int(final)],
                _format_float(study.series_limit_energy_ev[index]),
                _format_float(study.series_limit_wavelength_m[index]),
                _format_float(study.series_limit_wavelength_nm[index]),
            )
            for index, final in enumerate(study.series_limit_final_n)
        ),
    )


def _validation_payload(report: Task05ValidationReport) -> dict[str, object]:
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
    configuration: Task05Configuration,
) -> dict[str, object]:
    return {
        field.name: getattr(configuration, field.name)
        for field in fields(configuration)
    }


def _manifest_payload(
    configuration: Task05Configuration,
) -> dict[str, object]:
    return {
        "schema_version": configuration.schema_version,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "model": "ideal stationary-nucleus Bohr hydrogen",
        "constants": {
            "planck_constant_j_s": PLANCK_CONSTANT_J_S,
            "speed_of_light_m_s": SPEED_OF_LIGHT_M_S,
            "elementary_charge_c": ELEMENTARY_CHARGE_C,
            "rydberg_constant_per_m": RYDBERG_CONSTANT_PER_M,
            "rydberg_energy_ev": RYDBERG_ENERGY_EV,
            "hc_ev_nm": HC_EV_NM,
        },
        "configuration": _configuration_payload(configuration),
        "transition_scope": {
            "minimum_level": 1,
            "maximum_level": configuration.maximum_level,
            "transition_count": configuration.expected_transition_count,
            "ordering": "final_n ascending, then initial_n ascending",
            "highlighted_series_final_max": (
                configuration.highlighted_series_final_max
            ),
        },
        "series_names": {
            str(final): name for final, name in sorted(SERIES_NAMES.items())
        },
        "units": {
            "energy_ev": "eV",
            "energy_j": "J",
            "frequency_hz": "Hz",
            "wavelength_m": "m",
            "wavelength_nm": "nm",
            "quantum_numbers": "dimensionless integer",
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "expected_figure_filenames": list(FIGURE_FILENAMES),
        "mathematical_specification": MATHEMATICAL_SPECIFICATION_PATH,
        "constant_source": "NIST 2022 CODATA central values",
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _prepare_data_files(
    directory: Path,
    study: Task05StudyResult,
    report: Task05ValidationReport,
    configuration: Task05Configuration,
) -> tuple[tuple[str, Path], ...]:
    writers = (
        (DATA_FILENAMES[0], lambda path: _write_energy_levels(path, study)),
        (DATA_FILENAMES[1], lambda path: _write_emission_transitions(path, study)),
        (DATA_FILENAMES[2], lambda path: _write_series_limits(path, study)),
        (
            DATA_FILENAMES[3],
            lambda path: _write_json(path, _validation_payload(report)),
        ),
        (
            DATA_FILENAMES[4],
            lambda path: _write_json(path, _manifest_payload(configuration)),
        ),
    )
    prepared: list[tuple[str, Path]] = []
    for filename, writer in writers:
        path = directory / filename
        writer(path)
        prepared.append((filename, path))
    return tuple(prepared)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _verify_prepared_data(
    prepared: tuple[tuple[str, Path], ...],
    configuration: Task05Configuration,
) -> None:
    if tuple(name for name, _ in prepared) != DATA_FILENAMES:
        raise ValueError("prepared data names do not match the frozen order")
    for filename, path in prepared:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"empty generated output: {filename}")

    with prepared[0][1].open(encoding="utf-8", newline="") as handle:
        level_rows = list(csv.DictReader(handle))
    if len(level_rows) != configuration.maximum_level:
        raise ValueError("energy level CSV has the wrong row count")

    with prepared[1][1].open(encoding="utf-8", newline="") as handle:
        transition_rows = list(csv.DictReader(handle))
    if len(transition_rows) != configuration.expected_transition_count:
        raise ValueError("transition CSV has the wrong row count")

    with prepared[2][1].open(encoding="utf-8", newline="") as handle:
        limit_rows = list(csv.DictReader(handle))
    if len(limit_rows) != configuration.highlighted_series_final_max:
        raise ValueError("series-limit CSV has the wrong row count")

    for _, path in prepared[3:]:
        with path.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=_reject_json_constant)

    total_bytes = sum(path.stat().st_size for _, path in prepared)
    if total_bytes > configuration.evidence_size_budget_bytes:
        raise ValueError("prepared numerical evidence exceeds its size budget")


def _replace_path(source: Path, destination: Path) -> None:
    os.replace(source, destination)


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


def _commit_prepared(
    prepared: tuple[tuple[str, Path], ...],
    output_directory: Path,
) -> tuple[Path, ...]:
    destinations = tuple(output_directory / filename for filename, _ in prepared)
    originals = {
        path: path.read_bytes() if path.exists() else None for path in destinations
    }
    replaced: list[Path] = []
    try:
        for (_, source), destination in zip(prepared, destinations):
            _replace_path(source, destination)
            replaced.append(destination)
    except Exception:
        for destination in reversed(replaced):
            _restore_path(destination, originals[destination])
        raise
    return destinations


def _require_matching_report(
    study: Task05StudyResult,
    report: Task05ValidationReport,
    configuration: Task05Configuration,
) -> None:
    if not isinstance(study, Task05StudyResult):
        raise TypeError("study must be a Task05StudyResult")
    if not isinstance(report, Task05ValidationReport):
        raise TypeError("report must be a Task05ValidationReport")
    if not report.passed:
        raise RuntimeError("Task 5 data generation requires a passing report")
    if report != validate_task05(study, configuration):
        raise ValueError("report does not exactly describe the supplied study")


def generate_task05_data(
    output_directory: Path = DEFAULT_DATA_DIRECTORY,
    *,
    configuration: Task05Configuration = DEFAULT_CONFIGURATION,
    study: Task05StudyResult | None = None,
    report: Task05ValidationReport | None = None,
) -> Task05DataGenerationResult:
    """Validate, prepare, verify, and atomically commit all numerical evidence."""

    if not isinstance(configuration, Task05Configuration):
        raise TypeError("configuration must be a Task05Configuration")
    normalized_study = build_task05_study(configuration) if study is None else study
    normalized_report = (
        validate_task05(normalized_study, configuration)
        if report is None
        else report
    )
    _require_matching_report(normalized_study, normalized_report, configuration)

    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=destination.parent,
        prefix=".task05-data-",
    ) as temporary:
        prepared = _prepare_data_files(
            Path(temporary),
            normalized_study,
            normalized_report,
            configuration,
        )
        _verify_prepared_data(prepared, configuration)
        output_paths = _commit_prepared(prepared, destination)
    return Task05DataGenerationResult(normalized_report, output_paths)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate validated Task 5 evidence")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="directory for CSV and JSON evidence",
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        default=DEFAULT_FIGURE_DIRECTORY,
        help="directory for PNG and SVG figures",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="generate numerical evidence without importing Matplotlib",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    study = build_task05_study()
    report = validate_task05(study)
    data_result = generate_task05_data(
        arguments.data_dir,
        study=study,
        report=report,
    )
    for path in data_result.output_paths:
        print(path)
    if not arguments.data_only:
        from task05_hydrogen_spectrum.plotting import generate_task05_figures

        figure_result = generate_task05_figures(
            arguments.figure_dir,
            study=study,
            report=report,
        )
        for path in figure_result.output_paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
