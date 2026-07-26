"""Transactional deterministic data generation for Task 10."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from task10_hydrogenic_orbitals.analysis import (
    build_radial_profile,
    distinct_radial_states,
    official_family_representatives,
    radial_node_positions_over_a,
    supported_states,
)
from task10_hydrogenic_orbitals.configuration import (
    HydrogenicState,
    official_gallery_states,
)
from task10_hydrogenic_orbitals.constants import (
    CODATA_2022_SOURCE,
    CONSTANTS,
    SI_DEFINING_CONSTANTS_SOURCE,
)
from task10_hydrogenic_orbitals.models import (
    orbital_summary,
    real_spherical_harmonic,
    scaled_density_cartesian,
)
from task10_hydrogenic_orbitals.reference import (
    analytic_1s_scaled_density,
    analytic_2pz_scaled_density,
    analytic_2s_scaled_density,
)
from task10_hydrogenic_orbitals.validation import (
    Task10ValidationReport,
    validate_task10,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "data/task10"
REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00Z"
OUTPUT_SCHEMA_VERSION = "task10-output-v1"
MANIFEST_SCHEMA_VERSION = "task10-manifest-v1"
DATA_FILENAMES = (
    "orbital_state_catalog.csv",
    "official_gallery.csv",
    "radial_profiles.csv",
    "radial_nodes.csv",
    "reference_anchors.json",
    "validation_report.json",
    "manifest.json",
)


@dataclass(frozen=True)
class Task10GenerationResult:
    """Committed Task 10 data package."""

    output_directory: Path
    files: tuple[Path, ...]
    validation_report: Task10ValidationReport


def _format_float(value: float) -> str:
    return format(float(value), ".17g")


def _write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _state_row(state: HydrogenicState) -> dict[str, object]:
    summary = orbital_summary(state)
    return {
        "n": state.n,
        "l": state.l,
        "m": state.m,
        "family": state.family,
        "atomic_number": state.atomic_number,
        "mass_number": state.mass_number,
        "label": state.label,
        "energy_ev": _format_float(summary.energy_ev),
        "effective_bohr_radius_angstrom": _format_float(
            summary.effective_bohr_radius_angstrom
        ),
        "reduced_mass_ratio": _format_float(summary.reduced_mass_ratio),
        "radial_nodes": summary.radial_nodes,
        "angular_nodes": summary.angular_nodes,
        "degeneracy": summary.degeneracy,
        "parity": summary.parity,
        "orientation": _orientation_label(state.l, state.m),
    }


def _orientation_label(l: int, m: int) -> str:
    labels = {
        (0, 0): "spherical",
        (1, 1): "p_x",
        (1, -1): "p_y",
        (1, 0): "p_z",
        (2, 2): "d_x2-y2",
        (2, -2): "d_xy",
        (2, 1): "d_xz",
        (2, -1): "d_yz",
        (2, 0): "d_z2",
    }
    if (l, m) in labels:
        return labels[(l, m)]
    if m < 0:
        return f"real sine tesseral |m|={abs(m)}"
    if m > 0:
        return f"real cosine tesseral m={m}"
    return f"axial tesseral l={l}"


def _write_state_catalog(path: Path) -> None:
    fieldnames = tuple(_state_row(HydrogenicState(1, 0, 0)).keys())
    _write_csv(path, fieldnames, (_state_row(state) for state in supported_states()))


def _write_official_gallery(path: Path) -> None:
    fieldnames = tuple(_state_row(HydrogenicState(1, 0, 0)).keys())
    _write_csv(
        path,
        fieldnames,
        (_state_row(state) for state in official_gallery_states()),
    )


def _write_radial_profiles(path: Path) -> None:
    fieldnames = (
        "label",
        "n",
        "l",
        "m",
        "sample_index",
        "radius_over_a",
        "radius_over_n_squared_a",
        "scaled_radial_wavefunction",
        "scaled_radial_probability",
        "cumulative_probability",
        "containment_target",
        "extent_over_a",
    )

    def rows() -> Iterable[dict[str, object]]:
        for state in official_family_representatives():
            profile = build_radial_profile(state)
            for index in range(len(profile.radius_over_a)):
                yield {
                    "label": state.label,
                    "n": state.n,
                    "l": state.l,
                    "m": state.m,
                    "sample_index": index,
                    "radius_over_a": _format_float(
                        profile.radius_over_a[index]
                    ),
                    "radius_over_n_squared_a": _format_float(
                        profile.radius_over_n_squared_a[index]
                    ),
                    "scaled_radial_wavefunction": _format_float(
                        profile.scaled_radial_wavefunction[index]
                    ),
                    "scaled_radial_probability": _format_float(
                        profile.scaled_radial_probability[index]
                    ),
                    "cumulative_probability": _format_float(
                        profile.cumulative_probability[index]
                    ),
                    "containment_target": _format_float(
                        profile.containment_target
                    ),
                    "extent_over_a": _format_float(profile.extent_over_a),
                }

    _write_csv(path, fieldnames, rows())


def _write_radial_nodes(path: Path) -> None:
    fieldnames = (
        "n",
        "l",
        "family",
        "node_index",
        "radius_over_a",
        "radius_over_n_squared_a",
    )

    def rows() -> Iterable[dict[str, object]]:
        for state in distinct_radial_states():
            nodes = radial_node_positions_over_a(state)
            for index, radius in enumerate(nodes, start=1):
                yield {
                    "n": state.n,
                    "l": state.l,
                    "family": state.family,
                    "node_index": index,
                    "radius_over_a": _format_float(radius),
                    "radius_over_n_squared_a": _format_float(
                        radius / state.n**2
                    ),
                }

    _write_csv(path, fieldnames, rows())


def _reference_anchor_payload() -> dict[str, object]:
    hydrogen_ground = HydrogenicState(1, 0, 0)
    hydrogen_3d = HydrogenicState(3, 2, 0)
    carbon_3d = HydrogenicState(3, 2, 0, 6, 12)
    ground_summary = orbital_summary(hydrogen_ground)
    return {
        "schema_version": "task10-reference-anchors-v1",
        "coordinate_convention": {
            "polar": "vartheta in [0, pi]",
            "azimuth": "varphi in (-pi, pi]",
            "cartesian": [
                "x = r sin(vartheta) cos(varphi)",
                "y = r sin(vartheta) sin(varphi)",
                "z = r cos(vartheta)",
            ],
        },
        "hydrogen_1s": {
            "reduced_mass_ratio": ground_summary.reduced_mass_ratio,
            "effective_bohr_radius_angstrom": (
                ground_summary.effective_bohr_radius_angstrom
            ),
            "energy_ev": ground_summary.energy_ev,
            "scaled_density_at_origin": float(
                scaled_density_cartesian(hydrogen_ground, 0.0, 0.0, 0.0)
            ),
            "analytic_scaled_density_at_origin": (
                analytic_1s_scaled_density(0.0)
            ),
        },
        "hydrogen_3d": {
            "energy_ev": orbital_summary(hydrogen_3d).energy_ev,
            "radial_nodes": hydrogen_3d.radial_node_count,
            "angular_nodes": hydrogen_3d.angular_node_count,
        },
        "carbon12_3d": {
            "atomic_number": 6,
            "mass_number": 12,
            "energy_ev": orbital_summary(carbon_3d).energy_ev,
            "effective_bohr_radius_angstrom": (
                orbital_summary(carbon_3d).effective_bohr_radius_angstrom
            ),
        },
        "analytic_densities": {
            "one_s_r_over_a_2": analytic_1s_scaled_density(2.0),
            "two_s_r_over_a_2_node": analytic_2s_scaled_density(2.0),
            "two_pz_r_over_a_2_axis": analytic_2pz_scaled_density(2.0, 0.0),
            "two_pz_r_over_a_2_equator": analytic_2pz_scaled_density(
                2.0, 0.5 * np.pi
            ),
        },
        "real_harmonic_orientation": {
            "p_x_on_x_axis": float(
                real_spherical_harmonic(1, 1, 0.5 * np.pi, 0.0)
            ),
            "p_y_on_y_axis": float(
                real_spherical_harmonic(1, -1, 0.5 * np.pi, 0.5 * np.pi)
            ),
            "p_z_on_z_axis": float(
                real_spherical_harmonic(1, 0, 0.0, 0.0)
            ),
        },
    }


def _validation_payload(report: Task10ValidationReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "passed": report.passed,
        "state_digest": report.state_digest,
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "maximum_error": check.maximum_error,
                "tolerance": check.tolerance,
                "detail": check.detail,
            }
            for check in report.checks
        ],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_payload(
    directory: Path,
    report: Task10ValidationReport,
) -> dict[str, object]:
    data_files = DATA_FILENAMES[:-1]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "reproducible_build_timestamp_utc": REPRODUCIBLE_TIMESTAMP,
        "model": "normalized real hydrogenic Coulomb eigenstates",
        "official_source": (
            "https://www.bpho.org.uk/bpho/computational-challenge/"
            "BPhO_ComPhys_Challenge_2026.zip"
        ),
        "official_pages": [62, 76],
        "constant_sources": [
            CODATA_2022_SOURCE,
            SI_DEFINING_CONSTANTS_SOURCE,
        ],
        "constants": {
            "electron_mass_kg": CONSTANTS.electron_mass_kg,
            "atomic_mass_constant_kg": CONSTANTS.atomic_mass_constant_kg,
            "bohr_radius_m": CONSTANTS.bohr_radius_m,
            "hartree_energy_ev": CONSTANTS.hartree_energy_ev,
            "elementary_charge_c": CONSTANTS.elementary_charge_c,
        },
        "domain": {
            "n": [1, 8],
            "l": "0 <= l < n",
            "m": "-l <= m <= l",
            "atomic_number": [1, 20],
            "mass_number": "Z <= A <= 3Z",
            "official_gallery": "1s, 2p, 3d, 4f, 5g; every m",
        },
        "visualization_contract": {
            "default_display_threshold": 0.15,
            "threshold_affects_normalization": False,
            "radial_profile_containment": 0.9995,
            "radial_profile_points": 1201,
        },
        "validation": {
            "passed": report.passed,
            "check_count": len(report.checks),
            "state_digest": report.state_digest,
        },
        "expected_data_filenames": list(DATA_FILENAMES),
        "sha256": {
            f"data/task10/{name}": _sha256(directory / name)
            for name in data_files
        },
    }


def _count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def _verify_prepared(directory: Path) -> None:
    for name in DATA_FILENAMES:
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing or empty generated file: {name}")
    expected_rows = {
        "orbital_state_catalog.csv": 204,
        "official_gallery.csv": 25,
        "radial_profiles.csv": 5 * 1201,
        "radial_nodes.csv": 84,
    }
    for name, expected in expected_rows.items():
        observed = _count_csv_rows(directory / name)
        if observed != expected:
            raise AssertionError(f"{name}: expected {expected} rows, found {observed}")

    report = json.loads((directory / "validation_report.json").read_text())
    if report.get("passed") is not True or len(report.get("checks", [])) != 22:
        raise AssertionError("generated validation report is not a passing 22-check report")

    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("expected_data_filenames") != list(DATA_FILENAMES):
        raise AssertionError("generated manifest has the wrong file inventory")
    for relative_name, digest in manifest.get("sha256", {}).items():
        path = directory / Path(relative_name).name
        if _sha256(path) != digest:
            raise AssertionError(f"manifest digest mismatch: {relative_name}")


def _restore_path(path: Path, content: bytes | None) -> None:
    if content is None:
        path.unlink(missing_ok=True)
    else:
        path.write_bytes(content)


def _commit_all(
    prepared: tuple[tuple[Path, Path], ...],
    *,
    replace: Callable[[os.PathLike[str], os.PathLike[str]], None] = os.replace,
) -> None:
    backups = {
        destination: destination.read_bytes() if destination.exists() else None
        for _, destination in prepared
    }
    replaced: list[Path] = []
    try:
        for source, destination in prepared:
            replace(source, destination)
            replaced.append(destination)
    except Exception:
        for destination in replaced:
            _restore_path(destination, backups[destination])
        raise


def generate_task10(
    output_directory: Path = DEFAULT_OUTPUT_DIRECTORY,
) -> Task10GenerationResult:
    """Generate, verify and atomically commit the Task 10 data package."""

    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    report = validate_task10()
    if not report.passed:
        failed = ", ".join(check.name for check in report.failed_checks)
        raise RuntimeError(f"Task 10 scientific validation failed: {failed}")

    with tempfile.TemporaryDirectory(
        prefix=".task10-build-",
        dir=output_directory.parent,
    ) as temporary_name:
        temporary_directory = Path(temporary_name)
        _write_state_catalog(temporary_directory / DATA_FILENAMES[0])
        _write_official_gallery(temporary_directory / DATA_FILENAMES[1])
        _write_radial_profiles(temporary_directory / DATA_FILENAMES[2])
        _write_radial_nodes(temporary_directory / DATA_FILENAMES[3])
        _write_json(
            temporary_directory / DATA_FILENAMES[4],
            _reference_anchor_payload(),
        )
        _write_json(
            temporary_directory / DATA_FILENAMES[5],
            _validation_payload(report),
        )
        _write_json(
            temporary_directory / DATA_FILENAMES[6],
            _manifest_payload(temporary_directory, report),
        )
        _verify_prepared(temporary_directory)

        prepared = tuple(
            (temporary_directory / name, output_directory / name)
            for name in DATA_FILENAMES
        )
        _commit_all(prepared)

    return Task10GenerationResult(
        output_directory=output_directory,
        files=tuple(output_directory / name for name in DATA_FILENAMES),
        validation_report=report,
    )


def main() -> int:
    result = generate_task10()
    print(
        f"Task 10 generated {len(result.files)} data files; "
        f"{len(result.validation_report.checks)}/"
        f"{len(result.validation_report.checks)} validation checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
