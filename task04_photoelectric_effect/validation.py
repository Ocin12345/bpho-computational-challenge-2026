"""Independent, immutable validation reports for Task 4."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from numbers import Real
import numpy as np

import task04_photoelectric_effect.constants as constants
from task04_photoelectric_effect.analysis import Task04StudyResult
from task04_photoelectric_effect.configuration import (
    DEFAULT_CONFIGURATION,
    Task04Configuration,
)
from task04_photoelectric_effect.materials import OFFICIAL_MATERIALS
from task04_photoelectric_effect.reference import (
    reference_common_gradient_v_s,
    reference_cutoff_frequency_hz,
    reference_cutoff_wavelength_nm,
    reference_voltage_at_frequency_v,
    reference_voltage_at_wavelength_v,
)


_CHECK_NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
_FAILURE_SENTINEL = 1.0e300
_REFERENCE_MATERIALS = (
    ("Silver", "Ag", 4.3),
    ("Aluminium", "Al", 4.3),
    ("Gold", "Au", 5.1),
    ("Copper", "Cu", 4.7),
    ("Tin", "Sn", 4.4),
    ("Lead", "Pb", 4.3),
    ("Tungsten", "W", 4.5),
    ("Nickel", "Ni", 4.6),
    ("Sodium", "Na", 2.4),
)


def _finite_real(value: Real, *, name: str, non_negative: bool = False) -> float:
    """Normalize one finite scalar used in a validation record."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if non_negative and normalized < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _non_empty_text(value: str, *, name: str) -> str:
    """Require meaningful text without silently rewriting it."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


@dataclass(frozen=True)
class ValidationCheck:
    """One deterministic scientific validation result."""

    name: str
    passed: bool
    observed: float
    expected: float
    unit: str
    comparison: str
    tolerance: float
    explanation: str

    def __post_init__(self) -> None:
        """Validate the complete machine-readable check contract."""

        name = _non_empty_text(self.name, name="name")
        if _CHECK_NAME.fullmatch(name) is None:
            raise ValueError("name must use lowercase snake_case")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a bool")
        object.__setattr__(
            self,
            "observed",
            _finite_real(self.observed, name="observed"),
        )
        object.__setattr__(
            self,
            "expected",
            _finite_real(self.expected, name="expected"),
        )
        object.__setattr__(
            self,
            "tolerance",
            _finite_real(
                self.tolerance,
                name="tolerance",
                non_negative=True,
            ),
        )
        for field_name in ("unit", "comparison", "explanation"):
            object.__setattr__(
                self,
                field_name,
                _non_empty_text(getattr(self, field_name), name=field_name),
            )


@dataclass(frozen=True)
class Task04ValidationReport:
    """Immutable ordered collection of all Stage 6 checks."""

    schema_version: str
    checks: tuple[ValidationCheck, ...]

    def __post_init__(self) -> None:
        """Freeze checks and enforce a deterministic report schema."""

        if not isinstance(self.schema_version, str):
            raise TypeError("schema_version must be text")
        if self.schema_version != "task04-v1":
            raise ValueError("schema_version must be 'task04-v1'")
        try:
            checks = tuple(self.checks)
        except TypeError as exc:
            raise TypeError("checks must be an iterable of ValidationCheck") from exc
        if not checks:
            raise ValueError("checks must not be empty")
        if any(not isinstance(check, ValidationCheck) for check in checks):
            raise TypeError("checks must contain only ValidationCheck records")
        names = tuple(check.name for check in checks)
        if len(names) != len(set(names)):
            raise ValueError("validation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        """Return ``True`` only when every required check passed."""

        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[ValidationCheck, ...]:
        """Return failed checks in their original stable order."""

        return tuple(check for check in self.checks if not check.passed)


def _error_check(
    name: str,
    error: Real,
    tolerance: Real,
    *,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    """Build a check whose observed value is a non-negative error."""

    observed = _finite_real(error, name=f"{name} error", non_negative=True)
    threshold = _finite_real(
        tolerance,
        name=f"{name} tolerance",
        non_negative=True,
    )
    return ValidationCheck(
        name=name,
        passed=observed <= threshold,
        observed=observed,
        expected=0.0,
        unit=unit,
        comparison="absolute_error_lte",
        tolerance=threshold,
        explanation=explanation,
    )


def _exact_check(
    name: str,
    mismatches: int,
    *,
    explanation: str,
) -> ValidationCheck:
    """Build an exact-equality check from a mismatch count."""

    return ValidationCheck(
        name=name,
        passed=mismatches == 0,
        observed=float(mismatches),
        expected=0.0,
        unit="count",
        comparison="exact_equal",
        tolerance=0.0,
        explanation=explanation,
    )


def _relative_check(
    name: str,
    observed: Real,
    expected: Real,
    tolerance: Real,
    *,
    unit: str,
    explanation: str,
) -> ValidationCheck:
    """Build a relative-error check while retaining the measured value."""

    measured = _finite_real(observed, name=f"{name} observed")
    target = _finite_real(expected, name=f"{name} expected")
    threshold = _finite_real(
        tolerance,
        name=f"{name} tolerance",
        non_negative=True,
    )
    denominator = abs(target)
    relative_error = (
        abs(measured - target) / denominator
        if denominator > 0.0
        else abs(measured - target)
    )
    return ValidationCheck(
        name=name,
        passed=relative_error <= threshold,
        observed=measured,
        expected=target,
        unit=unit,
        comparison="relative_error_lte",
        tolerance=threshold,
        explanation=explanation,
    )


def _max_abs_error(actual: np.ndarray, expected: np.ndarray) -> float:
    """Return maximum absolute error, or a finite sentinel on shape failure."""

    if actual.shape != expected.shape:
        return _FAILURE_SENTINEL
    difference = np.abs(actual - expected)
    if not np.all(np.isfinite(difference)):
        return _FAILURE_SENTINEL
    return float(np.max(difference, initial=0.0))


def _physical_error(actual: np.ndarray, expected: np.ndarray) -> float:
    """Compare arrays while treating the exact NaN domain as scientific data."""

    if actual.shape != expected.shape:
        return _FAILURE_SENTINEL
    actual_nan = np.isnan(actual)
    expected_nan = np.isnan(expected)
    if not np.array_equal(actual_nan, expected_nan):
        return _FAILURE_SENTINEL
    active = ~expected_nan
    if np.any(~np.isfinite(actual[active])):
        return _FAILURE_SENTINEL
    return _max_abs_error(actual[active], expected[active])


def _array_equal_with_nan(first: np.ndarray, second: np.ndarray) -> bool:
    """Return exact equality for numerical arrays with matching NaNs."""

    if first.dtype == np.bool_ or second.dtype == np.bool_:
        return bool(np.array_equal(first, second))
    return bool(np.array_equal(first, second, equal_nan=True))


def _material_index(study: Task04StudyResult) -> dict[str, int]:
    """Map every unique study symbol to its row index."""

    return {material.symbol: index for index, material in enumerate(study.materials)}


def _official_row_or_none(
    study: Task04StudyResult,
    symbol_to_index: dict[str, int],
    symbol: str,
) -> int | None:
    """Return a safe row only when one official symbol is present."""

    index = symbol_to_index.get(symbol)
    if index is None or index >= study.work_functions_ev.size:
        return None
    return index


def _source_checks(study: Task04StudyResult) -> list[ValidationCheck]:
    """Check exact constants, official sources, and stored joule conversion."""

    expected_constants = (
        float("6.62607015e-34"),
        float("1.602176634e-19"),
        float("299792458"),
        float("1e-9"),
        float("1e9"),
    )
    actual_constants = (
        constants.PLANCK_CONSTANT_J_S,
        constants.ELEMENTARY_CHARGE_C,
        constants.SPEED_OF_LIGHT_M_S,
        constants.METRES_PER_NANOMETRE,
        constants.NANOMETRES_PER_METRE,
    )
    constant_mismatches = sum(
        actual != expected
        for actual, expected in zip(actual_constants, expected_constants)
    )
    constant_mismatches += int(
        constants.ELECTRONVOLT_J != expected_constants[1]
    )
    constant_mismatches += int(
        constants.PLANCK_OVER_CHARGE_V_S
        != expected_constants[0] / expected_constants[1]
    )
    constant_mismatches += int(
        constants.HC_OVER_CHARGE_V_M
        != expected_constants[0] * expected_constants[2] / expected_constants[1]
    )

    official_records = tuple(
        (material.name, material.symbol, material.work_function_ev)
        for material in OFFICIAL_MATERIALS
    )
    study_records = tuple(
        (material.name, material.symbol, material.work_function_ev)
        for material in study.materials
    )
    expected_work = np.array(
        [record[2] for record in _REFERENCE_MATERIALS],
        dtype=np.float64,
    )
    source_mismatches = int(official_records != _REFERENCE_MATERIALS)
    source_mismatches += int(study_records != _REFERENCE_MATERIALS)
    source_mismatches += int(
        not np.array_equal(study.work_functions_ev, expected_work)
    )

    expected_joules = (
        study.work_functions_ev * float("1.602176634e-19")
    )
    return [
        _exact_check(
            "exact_constants",
            constant_mismatches,
            explanation=(
                "Exact SI constants and derived conversions match the frozen "
                "definitions."
            ),
        ),
        _exact_check(
            "official_material_table",
            source_mismatches,
            explanation=(
                "Official and stored material order, names, symbols, and work "
                "functions match the source slide."
            ),
        ),
        _error_check(
            "work_function_joules",
            _max_abs_error(study.work_functions_j, expected_joules),
            0.0,
            unit="J",
            explanation=(
                "Stored joule values equal each electronvolt work function "
                "multiplied by the exact elementary charge."
            ),
        ),
    ]


def _grid_checks(
    study: Task04StudyResult,
    configuration: Task04Configuration,
) -> list[ValidationCheck]:
    """Check exact grids and permitted finiteness semantics."""

    expected_frequency = configuration.frequency_start_hz + np.arange(
        configuration.frequency_points,
        dtype=np.float64,
    ) * configuration.frequency_step_hz
    expected_wavelength_nm = configuration.wavelength_start_nm + np.arange(
        configuration.wavelength_points,
        dtype=np.float64,
    ) * configuration.wavelength_step_nm
    expected_wavelength_m = expected_wavelength_nm * float("1e-9")

    frequency_nonfinite = int(np.count_nonzero(~np.isfinite(study.frequency_hz)))
    frequency_nonfinite += int(
        np.count_nonzero(~np.isfinite(study.cutoff_frequencies_hz))
    )
    frequency_nonfinite += int(
        np.count_nonzero(~np.isfinite(study.frequency_linear_voltage_v))
    )
    frequency_nonfinite += int(
        np.count_nonzero(
            ~np.isfinite(
                study.frequency_physical_voltage_v[
                    study.frequency_emission_mask
                ]
            )
        )
    )

    wavelength_nonfinite = int(np.count_nonzero(~np.isfinite(study.wavelength_m)))
    wavelength_nonfinite += int(np.count_nonzero(~np.isfinite(study.wavelength_nm)))
    wavelength_nonfinite += int(
        np.count_nonzero(~np.isfinite(study.cutoff_wavelengths_nm))
    )
    wavelength_nonfinite += int(
        np.count_nonzero(~np.isfinite(study.wavelength_linear_voltage_v))
    )
    wavelength_nonfinite += int(
        np.count_nonzero(
            ~np.isfinite(
                study.wavelength_physical_voltage_v[
                    study.wavelength_emission_mask
                ]
            )
        )
    )

    return [
        _exact_check(
            "frequency_grid",
            int(not np.array_equal(study.frequency_hz, expected_frequency)),
            explanation=(
                "Frequency grid matches the frozen inclusive start, interval, "
                "count, and endpoint exactly."
            ),
        ),
        _exact_check(
            "wavelength_grid",
            int(not np.array_equal(study.wavelength_nm, expected_wavelength_nm))
            + int(not np.array_equal(study.wavelength_m, expected_wavelength_m)),
            explanation=(
                "Metre and nanometre wavelength grids match the frozen "
                "inclusive specification exactly."
            ),
        ),
        _exact_check(
            "frequency_finiteness",
            frequency_nonfinite,
            explanation=(
                "Frequency metadata, signed curves, and active physical values "
                "are finite."
            ),
        ),
        _exact_check(
            "wavelength_finiteness",
            wavelength_nonfinite,
            explanation=(
                "Wavelength metadata, signed curves, and active physical values "
                "are finite."
            ),
        ),
    ]


def _identity_and_gradient_checks(
    study: Task04StudyResult,
    configuration: Task04Configuration,
) -> tuple[list[ValidationCheck], np.ndarray, np.ndarray]:
    """Calculate independent whole-grid targets and their first checks."""

    reference_gradient = reference_common_gradient_v_s()
    reference_hc_over_e_v_nm = (
        reference_voltage_at_wavelength_v(1.0, 1.0) + 1.0
    )
    expected_frequency = (
        reference_gradient * study.frequency_hz[np.newaxis, :]
        - study.work_functions_ev[:, np.newaxis]
    )
    expected_wavelength = (
        reference_hc_over_e_v_nm / study.wavelength_nm[np.newaxis, :]
        - study.work_functions_ev[:, np.newaxis]
    )

    measured_gradients = np.diff(
        study.frequency_linear_voltage_v,
        axis=1,
    ) / np.diff(study.frequency_hz)[np.newaxis, :]
    if np.all(np.isfinite(measured_gradients)):
        gradient_relative_error = float(
            np.max(
                np.abs(measured_gradients - reference_gradient)
                / abs(reference_gradient),
                initial=0.0,
            )
        )
    else:
        gradient_relative_error = _FAILURE_SENTINEL

    checks = [
        _error_check(
            "frequency_energy_identity",
            _max_abs_error(
                study.frequency_linear_voltage_v,
                expected_frequency,
            ),
            configuration.energy_identity_tolerance_ev,
            unit="eV",
            explanation=(
                "Every frequency point independently satisfies eV = hf - W "
                "when numerical electronvolt and volt values are compared."
            ),
        ),
        _error_check(
            "wavelength_energy_identity",
            _max_abs_error(
                study.wavelength_linear_voltage_v,
                expected_wavelength,
            ),
            configuration.energy_identity_tolerance_ev,
            unit="eV",
            explanation=(
                "Every wavelength point independently satisfies "
                "eV = hc/lambda - W."
            ),
        ),
        _error_check(
            "common_frequency_gradient",
            gradient_relative_error,
            configuration.gradient_relative_tolerance,
            unit="dimensionless",
            explanation=(
                "Every numerical frequency gradient agrees with the "
                "independent Decimal value h/e."
            ),
        ),
    ]
    return checks, expected_frequency, expected_wavelength


def _cutoff_checks(
    study: Task04StudyResult,
    configuration: Task04Configuration,
    symbol_to_index: dict[str, int],
) -> tuple[list[ValidationCheck], np.ndarray, np.ndarray]:
    """Check every official frequency and wavelength cut-off independently."""

    expected_frequency = np.array(
        [reference_cutoff_frequency_hz(record[2]) for record in _REFERENCE_MATERIALS],
        dtype=np.float64,
    )
    expected_wavelength = np.array(
        [reference_cutoff_wavelength_nm(record[2]) for record in _REFERENCE_MATERIALS],
        dtype=np.float64,
    )
    checks: list[ValidationCheck] = []
    for official_index, (_, symbol, _) in enumerate(_REFERENCE_MATERIALS):
        row = _official_row_or_none(study, symbol_to_index, symbol)
        observed = (
            float(study.cutoff_frequencies_hz[row])
            if row is not None
            else 0.0
        )
        checks.append(
            _relative_check(
                f"cutoff_frequency_{symbol.lower()}",
                observed,
                expected_frequency[official_index],
                configuration.cutoff_relative_tolerance,
                unit="Hz",
                explanation=(
                    f"{symbol} threshold frequency agrees with independent "
                    "Decimal eW/h."
                ),
            )
        )
    for official_index, (_, symbol, _) in enumerate(_REFERENCE_MATERIALS):
        row = _official_row_or_none(study, symbol_to_index, symbol)
        observed = (
            float(study.cutoff_wavelengths_nm[row])
            if row is not None
            else 0.0
        )
        checks.append(
            _relative_check(
                f"cutoff_wavelength_{symbol.lower()}",
                observed,
                expected_wavelength[official_index],
                configuration.cutoff_relative_tolerance,
                unit="nm",
                explanation=(
                    f"{symbol} threshold wavelength agrees with independent "
                    "Decimal hc/(eW)."
                ),
            )
        )
    return checks, expected_frequency, expected_wavelength


def _threshold_errors(
    study: Task04StudyResult,
    symbol_to_index: dict[str, int],
) -> tuple[float, float]:
    """Evaluate independent equations at the stored analytical cut-offs."""

    frequency_errors: list[float] = []
    wavelength_errors: list[float] = []
    for _, symbol, work_function_ev in _REFERENCE_MATERIALS:
        row = _official_row_or_none(study, symbol_to_index, symbol)
        if row is None:
            return _FAILURE_SENTINEL, _FAILURE_SENTINEL
        frequency_errors.append(
            abs(
                reference_voltage_at_frequency_v(
                    float(study.cutoff_frequencies_hz[row]),
                    work_function_ev,
                )
            )
        )
        wavelength_errors.append(
            abs(
                reference_voltage_at_wavelength_v(
                    float(study.cutoff_wavelengths_nm[row]),
                    work_function_ev,
                )
            )
        )
    return max(frequency_errors, default=0.0), max(wavelength_errors, default=0.0)


def _domain_checks(
    study: Task04StudyResult,
    configuration: Task04Configuration,
    expected_frequency_linear: np.ndarray,
    expected_wavelength_linear: np.ndarray,
    expected_cutoff_frequency: np.ndarray,
    expected_cutoff_wavelength: np.ndarray,
    symbol_to_index: dict[str, int],
) -> list[ValidationCheck]:
    """Check thresholds, masks, physical values, bounds, and monotonicity."""

    threshold_frequency_error, threshold_wavelength_error = _threshold_errors(
        study,
        symbol_to_index,
    )
    expected_frequency_mask = (
        study.frequency_hz[np.newaxis, :]
        >= expected_cutoff_frequency[:, np.newaxis]
    )
    expected_wavelength_mask = (
        study.wavelength_nm[np.newaxis, :]
        <= expected_cutoff_wavelength[:, np.newaxis]
    )
    frequency_mask_mismatches = (
        int(np.count_nonzero(study.frequency_emission_mask != expected_frequency_mask))
        if study.frequency_emission_mask.shape == expected_frequency_mask.shape
        else max(study.frequency_emission_mask.size, expected_frequency_mask.size)
    )
    wavelength_mask_mismatches = (
        int(
            np.count_nonzero(
                study.wavelength_emission_mask != expected_wavelength_mask
            )
        )
        if study.wavelength_emission_mask.shape == expected_wavelength_mask.shape
        else max(study.wavelength_emission_mask.size, expected_wavelength_mask.size)
    )
    expected_frequency_physical = np.where(
        expected_frequency_mask,
        np.maximum(expected_frequency_linear, 0.0),
        np.nan,
    )
    expected_wavelength_physical = np.where(
        expected_wavelength_mask,
        np.maximum(expected_wavelength_linear, 0.0),
        np.nan,
    )

    frequency_active = study.frequency_physical_voltage_v[
        study.frequency_emission_mask
    ]
    wavelength_active = study.wavelength_physical_voltage_v[
        study.wavelength_emission_mask
    ]
    frequency_bound_error = (
        max(0.0, -float(np.min(frequency_active)))
        if frequency_active.size and np.all(np.isfinite(frequency_active))
        else _FAILURE_SENTINEL
    )
    wavelength_bound_error = (
        max(0.0, -float(np.min(wavelength_active)))
        if wavelength_active.size and np.all(np.isfinite(wavelength_active))
        else _FAILURE_SENTINEL
    )
    frequency_decrease = np.diff(study.frequency_linear_voltage_v, axis=1)
    wavelength_increase = np.diff(study.wavelength_linear_voltage_v, axis=1)
    frequency_monotonic_error = (
        max(0.0, -float(np.min(frequency_decrease)))
        if frequency_decrease.size and np.all(np.isfinite(frequency_decrease))
        else _FAILURE_SENTINEL
    )
    wavelength_monotonic_error = (
        max(0.0, float(np.max(wavelength_increase)))
        if wavelength_increase.size and np.all(np.isfinite(wavelength_increase))
        else _FAILURE_SENTINEL
    )

    return [
        _error_check(
            "threshold_frequency_voltage",
            threshold_frequency_error,
            configuration.threshold_voltage_tolerance_v,
            unit="V",
            explanation=(
                "Independent frequency equations give zero voltage at every "
                "stored frequency cut-off."
            ),
        ),
        _error_check(
            "threshold_wavelength_voltage",
            threshold_wavelength_error,
            configuration.threshold_voltage_tolerance_v,
            unit="V",
            explanation=(
                "Independent wavelength equations give zero voltage at every "
                "stored wavelength cut-off."
            ),
        ),
        _exact_check(
            "frequency_emission_mask",
            frequency_mask_mismatches,
            explanation=(
                "Frequency emission mask exactly follows f greater than or "
                "equal to each independent cut-off."
            ),
        ),
        _exact_check(
            "wavelength_emission_mask",
            wavelength_mask_mismatches,
            explanation=(
                "Wavelength emission mask exactly follows lambda less than or "
                "equal to each independent cut-off."
            ),
        ),
        _error_check(
            "frequency_physical_voltage",
            _physical_error(
                study.frequency_physical_voltage_v,
                expected_frequency_physical,
            ),
            configuration.boundary_clamp_tolerance_v,
            unit="V",
            explanation=(
                "Frequency physical voltage equals the independent signed "
                "result in-domain and is NaN outside it."
            ),
        ),
        _error_check(
            "wavelength_physical_voltage",
            _physical_error(
                study.wavelength_physical_voltage_v,
                expected_wavelength_physical,
            ),
            configuration.boundary_clamp_tolerance_v,
            unit="V",
            explanation=(
                "Wavelength physical voltage equals the independent signed "
                "result in-domain and is NaN outside it."
            ),
        ),
        _error_check(
            "frequency_physical_bounds",
            frequency_bound_error,
            configuration.physical_bound_slack_v,
            unit="V",
            explanation=(
                "All active frequency-domain stopping voltages are finite and "
                "non-negative within boundary slack."
            ),
        ),
        _error_check(
            "wavelength_physical_bounds",
            wavelength_bound_error,
            configuration.physical_bound_slack_v,
            unit="V",
            explanation=(
                "All active wavelength-domain stopping voltages are finite and "
                "non-negative within boundary slack."
            ),
        ),
        _error_check(
            "frequency_monotonicity",
            frequency_monotonic_error,
            configuration.monotonic_slack_v,
            unit="V",
            explanation=(
                "Signed stopping voltage never decreases as frequency rises "
                "beyond numerical slack."
            ),
        ),
        _error_check(
            "wavelength_monotonicity",
            wavelength_monotonic_error,
            configuration.monotonic_slack_v,
            unit="V",
            explanation=(
                "Signed stopping voltage never increases as vacuum wavelength "
                "rises beyond numerical slack."
            ),
        ),
    ]


def _duplicate_mismatches(
    study: Task04StudyResult,
    symbol_to_index: dict[str, int],
) -> int:
    """Count unequal results among Ag, Al, and Pb."""

    rows = [symbol_to_index.get(symbol) for symbol in ("Ag", "Al", "Pb")]
    if any(row is None for row in rows):
        return 1
    baseline = int(rows[0])
    mismatch_count = 0
    for row_value in rows[1:]:
        row = int(row_value)
        for field_name in (
            "work_functions_ev",
            "work_functions_j",
            "cutoff_frequencies_hz",
            "cutoff_wavelengths_nm",
            "frequency_linear_voltage_v",
            "frequency_emission_mask",
            "frequency_physical_voltage_v",
            "wavelength_linear_voltage_v",
            "wavelength_emission_mask",
            "wavelength_physical_voltage_v",
        ):
            values = getattr(study, field_name)
            mismatch_count += int(
                not _array_equal_with_nan(
                    np.asarray(values[baseline]),
                    np.asarray(values[row]),
                )
            )
    return mismatch_count


def _ordering_mismatches(
    study: Task04StudyResult,
    symbol_to_index: dict[str, int],
) -> int:
    """Check pairwise threshold ordering against official work functions."""

    mismatch_count = 0
    for first_position, (_, first_symbol, first_work) in enumerate(
        _REFERENCE_MATERIALS
    ):
        first_row = symbol_to_index.get(first_symbol)
        if first_row is None:
            mismatch_count += 1
            continue
        for _, second_symbol, second_work in _REFERENCE_MATERIALS[
            first_position + 1 :
        ]:
            second_row = symbol_to_index.get(second_symbol)
            if second_row is None:
                mismatch_count += 1
                continue
            first_frequency = study.cutoff_frequencies_hz[first_row]
            second_frequency = study.cutoff_frequencies_hz[second_row]
            first_wavelength = study.cutoff_wavelengths_nm[first_row]
            second_wavelength = study.cutoff_wavelengths_nm[second_row]
            if first_work == second_work:
                correct = (
                    first_frequency == second_frequency
                    and first_wavelength == second_wavelength
                )
            elif first_work < second_work:
                correct = (
                    first_frequency < second_frequency
                    and first_wavelength > second_wavelength
                )
            else:
                correct = (
                    first_frequency > second_frequency
                    and first_wavelength < second_wavelength
                )
            mismatch_count += int(not correct)
    return mismatch_count


def _coordinate_error(study: Task04StudyResult) -> float:
    """Compare both stored coordinate forms after independent f = c/lambda."""

    converted_frequency = float("299792458") / study.wavelength_m
    if (
        np.any(converted_frequency < study.frequency_hz[0])
        or np.any(converted_frequency > study.frequency_hz[-1])
    ):
        return _FAILURE_SENTINEL
    maximum_error = 0.0
    for row in range(len(study.materials)):
        interpolated = np.interp(
            converted_frequency,
            study.frequency_hz,
            study.frequency_linear_voltage_v[row],
        )
        error = _max_abs_error(
            interpolated,
            study.wavelength_linear_voltage_v[row],
        )
        maximum_error = max(maximum_error, error)
    return maximum_error


def _anchor_error(
    study: Task04StudyResult,
    symbol_to_index: dict[str, int],
    *,
    frequency: bool,
) -> float:
    """Return the largest independent error at one frozen scalar anchor."""

    grid = study.frequency_hz if frequency else study.wavelength_nm
    anchor = 1.5e15 if frequency else 200.0
    matches = np.flatnonzero(grid == anchor)
    if matches.size != 1:
        return _FAILURE_SENTINEL
    column = int(matches[0])
    errors: list[float] = []
    for _, symbol, work_function_ev in _REFERENCE_MATERIALS:
        row = symbol_to_index.get(symbol)
        if row is None:
            return _FAILURE_SENTINEL
        expected = (
            reference_voltage_at_frequency_v(anchor, work_function_ev)
            if frequency
            else reference_voltage_at_wavelength_v(anchor, work_function_ev)
        )
        actual = (
            study.frequency_linear_voltage_v[row, column]
            if frequency
            else study.wavelength_linear_voltage_v[row, column]
        )
        errors.append(abs(float(actual) - expected))
    return max(errors, default=0.0)


def _relationship_checks(
    study: Task04StudyResult,
    configuration: Task04Configuration,
    symbol_to_index: dict[str, int],
) -> list[ValidationCheck]:
    """Check duplicates, ordering, coordinate conversion, and anchors."""

    return [
        _exact_check(
            "duplicate_materials",
            _duplicate_mismatches(study, symbol_to_index),
            explanation=(
                "Ag, Al, and Pb have exactly identical ideal results because "
                "the official table gives each 4.3 eV."
            ),
        ),
        _exact_check(
            "cutoff_ordering",
            _ordering_mismatches(study, symbol_to_index),
            explanation=(
                "Higher work function always gives higher frequency cut-off "
                "and shorter wavelength cut-off; equal work functions coincide."
            ),
        ),
        _error_check(
            "frequency_wavelength_consistency",
            _coordinate_error(study),
            configuration.coordinate_consistency_tolerance_v,
            unit="V",
            explanation=(
                "Frequency and wavelength signed curves agree after independent "
                "vacuum conversion f = c/lambda."
            ),
        ),
        _error_check(
            "frequency_anchor",
            _anchor_error(study, symbol_to_index, frequency=True),
            configuration.anchor_tolerance_v,
            unit="V",
            explanation=(
                "Every metal agrees with the independent Decimal voltage at "
                "1.5e15 Hz."
            ),
        ),
        _error_check(
            "wavelength_anchor",
            _anchor_error(study, symbol_to_index, frequency=False),
            configuration.anchor_tolerance_v,
            unit="V",
            explanation=(
                "Every metal agrees with the independent Decimal voltage at "
                "200 nm."
            ),
        ),
    ]


def validate_task04(
    study: Task04StudyResult,
    configuration: Task04Configuration = DEFAULT_CONFIGURATION,
) -> Task04ValidationReport:
    """Return the complete deterministic 43-check validation report."""

    if not isinstance(study, Task04StudyResult):
        raise TypeError("study must be a Task04StudyResult")
    if not isinstance(configuration, Task04Configuration):
        raise TypeError("configuration must be a Task04Configuration")

    symbol_to_index = _material_index(study)
    checks: list[ValidationCheck] = []
    checks.extend(_source_checks(study))
    checks.extend(_grid_checks(study, configuration))
    identity_checks, expected_frequency_linear, expected_wavelength_linear = (
        _identity_and_gradient_checks(study, configuration)
    )
    checks.extend(identity_checks)
    cutoff_checks, _, _ = (
        _cutoff_checks(study, configuration, symbol_to_index)
    )
    checks.extend(cutoff_checks)
    study_cutoff_frequency = np.array(
        [
            reference_cutoff_frequency_hz(material.work_function_ev)
            for material in study.materials
        ],
        dtype=np.float64,
    )
    study_cutoff_wavelength = np.array(
        [
            reference_cutoff_wavelength_nm(material.work_function_ev)
            for material in study.materials
        ],
        dtype=np.float64,
    )
    checks.extend(
        _domain_checks(
            study,
            configuration,
            expected_frequency_linear,
            expected_wavelength_linear,
            study_cutoff_frequency,
            study_cutoff_wavelength,
            symbol_to_index,
        )
    )
    checks.extend(_relationship_checks(study, configuration, symbol_to_index))
    if len(checks) != 43:
        raise RuntimeError(f"validation schema drifted to {len(checks)} checks")
    return Task04ValidationReport(
        schema_version=configuration.schema_version,
        checks=tuple(checks),
    )


__all__ = [
    "Task04ValidationReport",
    "ValidationCheck",
    "validate_task04",
]
