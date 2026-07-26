"""Structured validation for the Task 8 finite-photon extension."""

from __future__ import annotations

import math
from dataclasses import dataclass

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import UINT32_MAXIMUM
from task08_quantum_cryptography.statistics import (
    advance_seed,
    binomial_mismatch_count,
    derived_stream_seed,
    mulberry32_uint32_sequence,
    mulberry32_uniform_sequence,
    simulate_finite_photon_experiment,
    wilson_interval,
)


STATISTICAL_VALIDATION_SCHEMA_VERSION = "task08-statistical-validation-v1"


@dataclass(frozen=True)
class StatisticalValidationCheck:
    """One machine-readable statistical acceptance check."""

    name: str
    passed: bool
    observed: float
    expected: float
    tolerance: float
    comparison: str
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("check name must be non-empty text")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")
        for field_name in ("observed", "expected", "tolerance"):
            normalized = float(getattr(self, field_name))
            if not math.isfinite(normalized):
                raise ValueError(f"{field_name} must be finite")
            object.__setattr__(self, field_name, normalized)
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative")
        if not self.comparison or not self.explanation:
            raise ValueError("comparison and explanation must be non-empty")


@dataclass(frozen=True)
class StatisticalValidationReport:
    """Complete statistical validation report."""

    schema_version: str
    checks: tuple[StatisticalValidationCheck, ...]

    def __post_init__(self) -> None:
        if self.schema_version != STATISTICAL_VALIDATION_SCHEMA_VERSION:
            raise ValueError("invalid statistical validation schema version")
        checks = tuple(self.checks)
        if not checks or any(
            not isinstance(check, StatisticalValidationCheck) for check in checks
        ):
            raise TypeError("checks must contain StatisticalValidationCheck records")
        names = tuple(check.name for check in checks)
        if len(names) != len(set(names)):
            raise ValueError("statistical validation check names must be unique")
        object.__setattr__(self, "checks", checks)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[StatisticalValidationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _exact(
    name: str,
    observed: float,
    expected: float,
    explanation: str,
) -> StatisticalValidationCheck:
    return StatisticalValidationCheck(
        name=name,
        passed=float(observed) == float(expected),
        observed=observed,
        expected=expected,
        tolerance=0.0,
        comparison="exact_equal",
        explanation=explanation,
    )


def _absolute(
    name: str,
    observed: float,
    expected: float,
    tolerance: float,
    explanation: str,
) -> StatisticalValidationCheck:
    error = abs(float(observed) - float(expected))
    return StatisticalValidationCheck(
        name=name,
        passed=error <= tolerance,
        observed=error,
        expected=0.0,
        tolerance=tolerance,
        comparison="absolute_error_lte",
        explanation=explanation,
    )


def _upper(
    name: str,
    observed: float,
    upper_bound: float,
    tolerance: float,
    explanation: str,
) -> StatisticalValidationCheck:
    value = float(observed)
    return StatisticalValidationCheck(
        name=name,
        passed=value <= upper_bound + tolerance,
        observed=value,
        expected=upper_bound,
        tolerance=tolerance,
        comparison="less_than_or_equal",
        explanation=explanation,
    )


def validate_task08_statistics(
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> StatisticalValidationReport:
    """Run the pre-declared deterministic statistical checks."""

    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")
    tolerance = configuration.cross_language_absolute_tolerance
    checks: list[StatisticalValidationCheck] = []

    golden = (1144304738, 1416247, 958946056, 627933444, 2007157716)
    observed_golden = mulberry32_uint32_sequence(0, len(golden))
    checks.append(
        _exact(
            "mulberry32_golden_sequence",
            sum(actual != expected for actual, expected in zip(observed_golden, golden)),
            0,
            "The first five unsigned outputs match the frozen Mulberry32 vector.",
        )
    )
    uniforms = mulberry32_uniform_sequence(0, 10_000)
    checks.append(
        _exact(
            "uniform_half_open_bounds",
            sum(not 0.0 <= value < 1.0 for value in uniforms),
            0,
            "Every generated uniform lies in the half-open interval [0, 1).",
        )
    )
    checks.append(
        _exact(
            "model_streams_distinct",
            int(
                derived_stream_seed(2026, "classical")
                == derived_stream_seed(2026, "quantum")
            ),
            0,
            "Classical and quantum draws use distinct salted streams.",
        )
    )
    checks.append(
        _exact(
            "seed_wraparound",
            advance_seed(UINT32_MAXIMUM),
            0,
            "Advancing the largest unsigned seed wraps to zero.",
        )
    )
    checks.append(
        _exact(
            "zero_probability_is_deterministic",
            binomial_mismatch_count(1_000, 0.0, 17),
            0,
            "A zero mismatch probability produces no mismatches.",
        )
    )
    checks.append(
        _exact(
            "unit_probability_is_deterministic",
            binomial_mismatch_count(1_000, 1.0, 17),
            1_000,
            "A unit mismatch probability produces one mismatch per pair.",
        )
    )

    official = simulate_finite_photon_experiment(-30, 30, 1_000, 2_026)
    checks.append(
        _absolute(
            "official_classical_theory",
            official.classical.theoretical_probability,
            3.0 / 8.0,
            tolerance,
            "The finite experiment retains the official classical probability.",
        )
    )
    checks.append(
        _absolute(
            "official_quantum_theory",
            official.quantum.theoretical_probability,
            3.0 / 4.0,
            tolerance,
            "The finite experiment retains the official quantum probability.",
        )
    )
    checks.append(
        _exact(
            "official_classical_seeded_count",
            official.classical.mismatches,
            363,
            "The default classical count is frozen for cross-language comparison.",
        )
    )
    checks.append(
        _exact(
            "official_quantum_seeded_count",
            official.quantum.mismatches,
            770,
            "The default quantum count is frozen for cross-language comparison.",
        )
    )
    checks.append(
        _exact(
            "classical_count_conservation",
            official.classical.mismatches + official.classical.matches,
            official.photon_pairs,
            "Classical matches and mismatches conserve the pair count.",
        )
    )
    checks.append(
        _exact(
            "quantum_count_conservation",
            official.quantum.mismatches + official.quantum.matches,
            official.photon_pairs,
            "Quantum matches and mismatches conserve the pair count.",
        )
    )
    checks.append(
        _absolute(
            "observed_rate_identity",
            max(
                abs(
                    sample.observed_probability
                    - sample.mismatches / sample.photon_pairs
                )
                for sample in (official.classical, official.quantum)
            ),
            0.0,
            tolerance,
            "Observed probability is exactly the mismatch fraction.",
        )
    )
    checks.append(
        _absolute(
            "expected_count_identity",
            max(
                abs(
                    sample.expected_mismatches
                    - sample.photon_pairs * sample.theoretical_probability
                )
                for sample in (official.classical, official.quantum)
            ),
            0.0,
            tolerance,
            "Expected mismatch count is N times the theoretical probability.",
        )
    )
    checks.append(
        _absolute(
            "binomial_standard_deviation_identity",
            max(
                abs(
                    sample.standard_deviation_count
                    - math.sqrt(
                        sample.photon_pairs
                        * sample.theoretical_probability
                        * (1.0 - sample.theoretical_probability)
                    )
                )
                for sample in (official.classical, official.quantum)
            ),
            0.0,
            tolerance,
            "Count spread uses the exact binomial standard deviation.",
        )
    )
    residual_errors = []
    for sample in (official.classical, official.quantum):
        expected_residual = (
            sample.mismatches - sample.expected_mismatches
        ) / sample.standard_deviation_count
        residual_errors.append(
            abs(float(sample.standardized_residual) - expected_residual)
        )
    checks.append(
        _absolute(
            "standardized_residual_identity",
            max(residual_errors),
            0.0,
            tolerance,
            "Each non-degenerate residual is measured in binomial standard deviations.",
        )
    )

    zero_interval = wilson_interval(0, 10)
    full_interval = wilson_interval(10, 10)
    checks.append(
        _absolute(
            "wilson_zero_count_reference",
            zero_interval.upper,
            0.2775327998628892,
            tolerance,
            "The zero-count Wilson upper limit matches its independent reference.",
        )
    )
    checks.append(
        _absolute(
            "wilson_full_count_reference",
            full_interval.lower,
            0.7224672001371107,
            tolerance,
            "The full-count Wilson lower limit matches its independent reference.",
        )
    )
    intervals = tuple(wilson_interval(count, 50) for count in range(51))
    checks.append(
        _exact(
            "wilson_intervals_bounded_and_ordered",
            sum(
                not 0.0 <= interval.lower <= interval.upper <= 1.0
                for interval in intervals
            ),
            0,
            "Wilson bounds remain ordered inside the probability range for every count.",
        )
    )
    checks.append(
        _exact(
            "wilson_intervals_contain_observed_fraction",
            sum(
                not interval.lower <= count / 50 <= interval.upper
                for count, interval in enumerate(intervals)
            ),
            0,
            "Every tested Wilson interval contains its observed fraction.",
        )
    )
    width_100 = wilson_interval(50, 100).upper - wilson_interval(50, 100).lower
    width_1000 = (
        wilson_interval(500, 1_000).upper - wilson_interval(500, 1_000).lower
    )
    checks.append(
        _upper(
            "wilson_width_shrinks_with_sample_size",
            width_1000,
            width_100,
            0.0,
            "At the same observed fraction, the interval narrows as N increases.",
        )
    )

    repeated = simulate_finite_photon_experiment(-30, 30, 1_000, 2_026)
    next_sample = simulate_finite_photon_experiment(-30, 30, 1_000, 2_027)
    checks.append(
        _exact(
            "same_seed_reproducible",
            int(repeated != official),
            0,
            "Repeating all inputs reproduces every sample field exactly.",
        )
    )
    checks.append(
        _exact(
            "next_seed_changes_sample",
            int(
                next_sample.classical.mismatches == official.classical.mismatches
                and next_sample.quantum.mismatches == official.quantum.mismatches
            ),
            0,
            "Advancing the displayed seed selects a new pair of samples.",
        )
    )
    large = simulate_finite_photon_experiment(-30, 30, 100_000, 2_026)
    checks.append(
        _upper(
            "large_reference_sample_within_five_sigma",
            max(
                abs(float(large.classical.standardized_residual)),
                abs(float(large.quantum.standardized_residual)),
            ),
            5.0,
            0.0,
            "The frozen large reference sample is not an extreme five-sigma outlier.",
        )
    )

    return StatisticalValidationReport(
        schema_version=STATISTICAL_VALIDATION_SCHEMA_VERSION,
        checks=tuple(checks),
    )


__all__ = [
    "STATISTICAL_VALIDATION_SCHEMA_VERSION",
    "StatisticalValidationCheck",
    "StatisticalValidationReport",
    "validate_task08_statistics",
]
