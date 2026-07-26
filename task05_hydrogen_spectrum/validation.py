"""Independent structured validation for the complete Task 5 study."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from task05_hydrogen_spectrum.analysis import Task05StudyResult
from task05_hydrogen_spectrum.configuration import (
    DEFAULT_CONFIGURATION,
    Task05Configuration,
)
from task05_hydrogen_spectrum.constants import (
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    HC_EV_NM,
    PLANCK_CONSTANT_J_S,
    RYDBERG_CONSTANT_PER_M,
    SPEED_OF_LIGHT_M_S,
)
from task05_hydrogen_spectrum.reference import (
    reference_level_energy_ev,
    reference_series_limit_energy_ev,
    reference_series_limit_wavelength_nm,
    reference_transition_energy_ev,
    reference_transition_frequency_hz,
    reference_transition_wavelength_nm,
)
from task05_hydrogen_spectrum.transitions import (
    display_group_for_final,
    enumerate_transition_pairs,
    line_name_for_transition,
    series_name_for_final,
    spectral_region_for_wavelength_nm,
)


VALIDATION_SCHEMA_VERSION = "task05-validation-v1"

FROZEN_NAMED_LINE_ANCHORS: tuple[
    tuple[str, int, int, float, float], ...
] = (
    ("lyman_alpha", 2, 1, 10.204269842242885, 121.50227341101820),
    ("lyman_beta", 3, 1, 12.093949442658234, 102.51754319054661),
    ("h_alpha", 3, 2, 1.8896796004153491, 656.1122764194983),
    ("h_beta", 4, 2, 2.5510674605607213, 486.0090936440728),
    ("h_gamma", 5, 2, 2.857195555828008, 433.9366907536364),
    ("h_delta", 6, 2, 3.0234873606645586, 410.0701727621864),
)

FROZEN_SERIES_LIMIT_ANCHORS: tuple[tuple[int, float, float], ...] = (
    (1, 13.605693122990514, 91.12670505826365),
    (2, 3.4014232807476284, 364.5068202330546),
    (3, 1.5117436803322793, 820.1403455243729),
    (4, 0.8503558201869071, 1458.0272809322184),
    (5, 0.5442277249196206, 2278.1676264565913),
)


@dataclass(frozen=True)
class ValidationCheck:
    """One stable numerical or structural validation result."""

    name: str
    passed: bool
    observed: float
    expected: float
    unit: str
    comparison: str
    tolerance: float
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("validation check name must be non-empty text")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")
        for field_name in ("observed", "expected", "tolerance"):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
            object.__setattr__(self, field_name, value)
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative")
        for field_name in ("unit", "comparison", "explanation"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be non-empty text")


@dataclass(frozen=True)
class Task05ValidationReport:
    """Immutable ordered validation result for one Task 5 study."""

    schema_version: str
    checks: tuple[ValidationCheck, ...]

    def __post_init__(self) -> None:
        if self.schema_version != VALIDATION_SCHEMA_VERSION:
            raise ValueError("invalid validation schema version")
        checks = tuple(self.checks)
        if not checks or any(not isinstance(check, ValidationCheck) for check in checks):
            raise TypeError("checks must contain ValidationCheck records")
        names = tuple(check.name for check in checks)
        if len(set(names)) != len(names):
            raise ValueError("validation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[ValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _absolute_check(
    *,
    name: str,
    error: float,
    tolerance: float,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    normalized = abs(float(error))
    return ValidationCheck(
        name=name,
        passed=normalized <= tolerance,
        observed=normalized,
        expected=0.0,
        unit=unit,
        comparison="absolute_error_lte",
        tolerance=tolerance,
        explanation=explanation,
    )


def _exact_count_check(
    *,
    name: str,
    mismatches: int,
    explanation: str,
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=int(mismatches) == 0,
        observed=float(mismatches),
        expected=0.0,
        unit="count",
        comparison="exact_equal",
        tolerance=0.0,
        explanation=explanation,
    )


def _relative_error(observed: np.ndarray, expected: np.ndarray) -> float:
    return float(np.max(np.abs((observed - expected) / expected)))


def validate_task05(
    study: Task05StudyResult,
    configuration: Task05Configuration = DEFAULT_CONFIGURATION,
) -> Task05ValidationReport:
    """Return all pre-declared checks without mutating or repairing ``study``."""

    if not isinstance(study, Task05StudyResult):
        raise TypeError("study must be a Task05StudyResult")
    if not isinstance(configuration, Task05Configuration):
        raise TypeError("configuration must be a Task05Configuration")

    checks: list[ValidationCheck] = []

    expected_constants = (
        float("6.62607015e-34"),
        float("299792458"),
        float("1.602176634e-19"),
        float("10973731.568157"),
    )
    observed_constants = (
        PLANCK_CONSTANT_J_S,
        SPEED_OF_LIGHT_M_S,
        ELEMENTARY_CHARGE_C,
        RYDBERG_CONSTANT_PER_M,
    )
    checks.append(
        _exact_count_check(
            name="source_constants",
            mismatches=sum(
                observed != expected
                for observed, expected in zip(
                    observed_constants,
                    expected_constants,
                )
            ),
            explanation="Frozen source constants equal the declared decimal values.",
        )
    )

    expected_levels = np.arange(1, configuration.maximum_level + 1, dtype=np.int64)
    checks.append(
        _exact_count_check(
            name="level_enumeration",
            mismatches=int(
                study.levels_n.shape != expected_levels.shape
                or not np.array_equal(study.levels_n, expected_levels)
            ),
            explanation="Stored levels are the exact consecutive integers 1 through 10.",
        )
    )

    reference_levels = np.array(
        [reference_level_energy_ev(int(level)) for level in study.levels_n],
        dtype=np.float64,
    )
    checks.append(
        _absolute_check(
            name="level_energy_reference",
            error=float(np.max(np.abs(study.level_energy_ev - reference_levels))),
            tolerance=configuration.level_energy_tolerance_ev,
            unit="eV",
            explanation="Every level agrees with the independent Decimal Bohr reference.",
        )
    )
    checks.append(
        _absolute_check(
            name="level_joule_conversion",
            error=float(
                np.max(
                    np.abs(
                        study.level_energy_j
                        - study.level_energy_ev * ELECTRONVOLT_J
                    )
                )
            ),
            tolerance=configuration.level_energy_tolerance_ev * ELECTRONVOLT_J,
            unit="J",
            explanation="Level-energy joule values equal the eV values times one eV in joules.",
        )
    )
    level_order_violations = int(np.count_nonzero(np.diff(study.level_energy_ev) <= 0.0))
    level_order_violations += int(np.count_nonzero(study.level_energy_ev >= 0.0))
    checks.append(
        _exact_count_check(
            name="level_ordering",
            mismatches=level_order_violations,
            explanation="Bound levels are negative and strictly approach zero as n increases.",
        )
    )

    expected_pairs = enumerate_transition_pairs(configuration.maximum_level)
    observed_pairs = tuple(zip(study.initial_n.tolist(), study.final_n.tolist()))
    checks.append(
        _exact_count_check(
            name="transition_count",
            mismatches=abs(len(observed_pairs) - configuration.expected_transition_count),
            explanation="The finite study contains exactly 45 downward transitions.",
        )
    )
    checks.append(
        _exact_count_check(
            name="transition_pair_order",
            mismatches=sum(
                observed != expected
                for observed, expected in zip(observed_pairs, expected_pairs)
            )
            + abs(len(observed_pairs) - len(expected_pairs)),
            explanation="Transition pairs follow the frozen final-level-first order.",
        )
    )
    checks.append(
        _exact_count_check(
            name="transition_uniqueness",
            mismatches=len(observed_pairs) - len(set(observed_pairs)),
            explanation="No initial/final pair is duplicated.",
        )
    )

    difference_energy = study.initial_energy_ev - study.final_energy_ev
    checks.append(
        _absolute_check(
            name="transition_energy_difference",
            error=float(np.max(np.abs(study.photon_energy_ev - difference_energy))),
            tolerance=configuration.transition_energy_tolerance_ev,
            unit="eV",
            explanation="Positive photon energy equals initial minus final atomic energy.",
        )
    )
    reference_energy = np.array(
        [
            reference_transition_energy_ev(int(initial), int(final))
            for initial, final in observed_pairs
        ],
        dtype=np.float64,
    )
    checks.append(
        _absolute_check(
            name="transition_energy_reference",
            error=float(np.max(np.abs(study.photon_energy_ev - reference_energy))),
            tolerance=configuration.transition_energy_tolerance_ev,
            unit="eV",
            explanation="Every photon energy agrees with the independent Decimal reference.",
        )
    )
    checks.append(
        _absolute_check(
            name="photon_joule_conversion",
            error=float(
                np.max(
                    np.abs(
                        study.photon_energy_j
                        - study.photon_energy_ev * ELECTRONVOLT_J
                    )
                )
            ),
            tolerance=configuration.transition_energy_tolerance_ev
            * ELECTRONVOLT_J,
            unit="J",
            explanation="Photon joule values equal their eV values times one eV in joules.",
        )
    )
    physical_arrays = (
        study.photon_energy_ev,
        study.photon_energy_j,
        study.frequency_hz,
        study.wavelength_m,
        study.wavelength_nm,
    )
    physical_violations = sum(
        int(np.count_nonzero(~np.isfinite(array) | (array <= 0.0)))
        for array in physical_arrays
    )
    checks.append(
        _exact_count_check(
            name="positive_finite_emissions",
            mismatches=physical_violations,
            explanation="Every photon energy, frequency, and wavelength is positive and finite.",
        )
    )

    energy_wavelength_ratio = (
        study.photon_energy_ev * study.wavelength_nm / HC_EV_NM
    )
    checks.append(
        _absolute_check(
            name="energy_wavelength_identity",
            error=float(np.max(np.abs(energy_wavelength_ratio - 1.0))),
            tolerance=configuration.energy_wavelength_relative_tolerance,
            unit="dimensionless",
            explanation="All transitions satisfy E_gamma times lambda equals hc.",
        )
    )
    frequency_wavelength_ratio = (
        study.frequency_hz * study.wavelength_m / SPEED_OF_LIGHT_M_S
    )
    checks.append(
        _absolute_check(
            name="frequency_wavelength_identity",
            error=float(np.max(np.abs(frequency_wavelength_ratio - 1.0))),
            tolerance=configuration.frequency_wavelength_relative_tolerance,
            unit="dimensionless",
            explanation="All transitions satisfy frequency times wavelength equals c.",
        )
    )
    reference_wavelength = np.array(
        [
            reference_transition_wavelength_nm(int(initial), int(final))
            for initial, final in observed_pairs
        ],
        dtype=np.float64,
    )
    checks.append(
        _absolute_check(
            name="rydberg_wavelength_reference",
            error=_relative_error(study.wavelength_nm, reference_wavelength),
            tolerance=configuration.rydberg_wavelength_relative_tolerance,
            unit="dimensionless",
            explanation="Energy-derived wavelengths agree with the independent Rydberg form.",
        )
    )
    reference_frequency = np.array(
        [
            reference_transition_frequency_hz(int(initial), int(final))
            for initial, final in observed_pairs
        ],
        dtype=np.float64,
    )
    checks.append(
        _absolute_check(
            name="frequency_reference",
            error=_relative_error(study.frequency_hz, reference_frequency),
            tolerance=configuration.frequency_wavelength_relative_tolerance,
            unit="dimensionless",
            explanation="Energy-derived frequencies agree with the independent Rydberg form.",
        )
    )

    pair_to_index = {pair: index for index, pair in enumerate(observed_pairs)}
    for anchor_name, initial, final, energy_ev, wavelength_nm in FROZEN_NAMED_LINE_ANCHORS:
        index = pair_to_index[(initial, final)]
        observed = np.array(
            [study.photon_energy_ev[index], study.wavelength_nm[index]],
            dtype=np.float64,
        )
        expected = np.array([energy_ev, wavelength_nm], dtype=np.float64)
        checks.append(
            _absolute_check(
                name=f"named_line_{anchor_name}",
                error=_relative_error(observed, expected),
                tolerance=configuration.named_line_relative_tolerance,
                unit="dimensionless",
                explanation=f"The frozen ideal-model {anchor_name.replace('_', '-')} anchor agrees.",
            )
        )

    for final, energy_ev, wavelength_nm in FROZEN_SERIES_LIMIT_ANCHORS:
        index = int(np.where(study.series_limit_final_n == final)[0][0])
        observed = np.array(
            [
                study.series_limit_energy_ev[index],
                study.series_limit_wavelength_nm[index],
            ],
            dtype=np.float64,
        )
        expected = np.array([energy_ev, wavelength_nm], dtype=np.float64)
        independent = np.array(
            [
                reference_series_limit_energy_ev(final),
                reference_series_limit_wavelength_nm(final),
            ],
            dtype=np.float64,
        )
        error = max(_relative_error(observed, expected), _relative_error(observed, independent))
        checks.append(
            _absolute_check(
                name=f"series_limit_n{final}",
                error=error,
                tolerance=configuration.series_limit_relative_tolerance,
                unit="dimensionless",
                explanation=f"The n_f={final} analytical series limit agrees with both anchors.",
            )
        )

    convergence_violations = 0
    for final in range(1, configuration.highlighted_series_final_max + 1):
        mask = study.final_n == final
        convergence_violations += int(
            np.count_nonzero(np.diff(study.photon_energy_ev[mask]) <= 0.0)
        )
        convergence_violations += int(
            np.count_nonzero(np.diff(study.wavelength_nm[mask]) >= 0.0)
        )
        limit_index = final - 1
        convergence_violations += int(
            np.any(
                study.photon_energy_ev[mask]
                >= study.series_limit_energy_ev[limit_index]
            )
        )
        convergence_violations += int(
            np.any(
                study.wavelength_nm[mask]
                <= study.series_limit_wavelength_nm[limit_index]
            )
        )
    checks.append(
        _exact_count_check(
            name="series_convergence",
            mismatches=convergence_violations,
            explanation="Each named series approaches but never crosses its analytical limit.",
        )
    )

    label_mismatches = 0
    spectral_mismatches = 0
    for index, (initial, final) in enumerate(observed_pairs):
        expected_series = series_name_for_final(final)
        expected_group = display_group_for_final(final)
        expected_line = line_name_for_transition(initial, final)
        label_mismatches += int(study.series_names[index] != expected_series)
        label_mismatches += int(study.display_groups[index] != expected_group)
        label_mismatches += int(study.line_names[index] != expected_line)
        expected_region = spectral_region_for_wavelength_nm(
            float(study.wavelength_nm[index]),
            visible_min_nm=configuration.visible_min_nm,
            visible_max_nm=configuration.visible_max_nm,
        )
        spectral_mismatches += int(study.spectral_regions[index] != expected_region)
    checks.append(
        _exact_count_check(
            name="series_and_line_labels",
            mismatches=label_mismatches,
            explanation="Every final level and alpha--delta line has its declared label.",
        )
    )
    checks.append(
        _exact_count_check(
            name="spectral_classification",
            mismatches=spectral_mismatches,
            explanation="Every wavelength follows the exact 380--750 nm region convention.",
        )
    )

    return Task05ValidationReport(
        schema_version=VALIDATION_SCHEMA_VERSION,
        checks=tuple(checks),
    )


__all__ = [
    "FROZEN_NAMED_LINE_ANCHORS",
    "FROZEN_SERIES_LIMIT_ANCHORS",
    "Task05ValidationReport",
    "ValidationCheck",
    "VALIDATION_SCHEMA_VERSION",
    "validate_task05",
]
