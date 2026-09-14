"""Uncertainty-aware photoelectric inference extension for Task 4.

The official task predicts stopping voltage from a supplied work function.
This extension solves the inverse problem: infer Planck's constant and the
work function from noisy stopping-voltage measurements using weighted least
squares, then check bias and confidence-interval coverage with a seeded Monte
Carlo study.

The historical cross-check uses the nine ``slope in volt-frequencies`` values
from Table II of R. A. Millikan, Physical Review 7, 355-388 (1916), DOI
10.1103/PhysRev.7.355.  Those nine values are historical measurements.  The
``simulate_photoelectric_measurements`` function, by contrast, is explicitly
synthetic and exists to test the recovery pipeline under controlled noise.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task04_photoelectric_effect.constants import (
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    PLANCK_OVER_CHARGE_V_S,
)


FloatArray = NDArray[np.float64]

MILLIKAN_1916_SLOPES_V_S = 1.0e-15 * np.asarray(
    [4.11, 4.14, 4.10, 4.12, 4.24, 3.98, 4.04, 4.24, 4.21],
    dtype=np.float64,
)


@dataclass(frozen=True)
class PhotoelectricFit:
    """Weighted line fit and propagated physical parameters."""

    slope_v_s: float
    intercept_v: float
    slope_standard_error_v_s: float
    intercept_standard_error_v: float
    covariance_v2_s: float
    planck_constant_j_s: float
    planck_standard_error_j_s: float
    work_function_ev: float
    work_function_standard_error_ev: float
    reduced_chi_squared: float
    residuals_v: FloatArray


@dataclass(frozen=True)
class RecoveryStudy:
    """Seeded repeated-experiment diagnostics."""

    experiment_count: int
    mean_planck_constant_j_s: float
    relative_planck_bias: float
    planck_rmse_j_s: float
    planck_95_percent_coverage: float
    mean_work_function_ev: float
    work_function_bias_ev: float
    work_function_95_percent_coverage: float


def _measurement_arrays(
    frequency_hz: ArrayLike,
    stopping_voltage_v: ArrayLike,
    voltage_sigma_v: ArrayLike,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    frequency = np.asarray(frequency_hz, dtype=np.float64)
    voltage = np.asarray(stopping_voltage_v, dtype=np.float64)
    sigma = np.asarray(voltage_sigma_v, dtype=np.float64)
    try:
        frequency, voltage, sigma = np.broadcast_arrays(frequency, voltage, sigma)
    except ValueError as exc:
        raise ValueError("measurement arrays must be broadcast-compatible") from exc
    if frequency.ndim != 1 or frequency.size < 3:
        raise ValueError("at least three one-dimensional measurements are required")
    if np.any(~np.isfinite(frequency)) or np.any(frequency <= 0.0):
        raise ValueError("frequency_hz must be finite and positive")
    if np.any(~np.isfinite(voltage)):
        raise ValueError("stopping_voltage_v must be finite")
    if np.any(~np.isfinite(sigma)) or np.any(sigma <= 0.0):
        raise ValueError("voltage_sigma_v must be finite and positive")
    if float(np.ptp(frequency)) == 0.0:
        raise ValueError("frequencies must span more than one value")
    return (
        np.asarray(frequency, dtype=np.float64),
        np.asarray(voltage, dtype=np.float64),
        np.asarray(sigma, dtype=np.float64),
    )


def fit_photoelectric_measurements(
    frequency_hz: ArrayLike,
    stopping_voltage_v: ArrayLike,
    voltage_sigma_v: ArrayLike,
) -> PhotoelectricFit:
    """Fit ``V_stop = (h/e) f - phi/e`` with full covariance propagation."""

    frequency, voltage, sigma = _measurement_arrays(
        frequency_hz, stopping_voltage_v, voltage_sigma_v
    )
    # Centre and scale frequency so the normal equations remain well
    # conditioned despite frequencies of order 10^15 Hz.
    centre = float(np.mean(frequency))
    scale = float(np.ptp(frequency))
    normalized_frequency = (frequency - centre) / scale
    design = np.column_stack((normalized_frequency, np.ones_like(frequency)))
    weighted_design = design / sigma[:, None]
    weighted_voltage = voltage / sigma
    coefficients, _, rank, _ = np.linalg.lstsq(
        weighted_design, weighted_voltage, rcond=None
    )
    if rank != 2:
        raise RuntimeError("weighted design matrix is rank deficient")
    covariance_normalized = np.linalg.inv(weighted_design.T @ weighted_design)
    normalized_slope, normalized_intercept = coefficients
    slope = float(normalized_slope / scale)
    intercept = float(normalized_intercept - normalized_slope * centre / scale)
    jacobian = np.asarray(
        [[1.0 / scale, 0.0], [-centre / scale, 1.0]], dtype=np.float64
    )
    covariance = jacobian @ covariance_normalized @ jacobian.T
    predicted = slope * frequency + intercept
    residuals = np.asarray(voltage - predicted, dtype=np.float64)
    residuals.setflags(write=False)
    dof = frequency.size - 2
    return PhotoelectricFit(
        slope_v_s=slope,
        intercept_v=intercept,
        slope_standard_error_v_s=float(np.sqrt(covariance[0, 0])),
        intercept_standard_error_v=float(np.sqrt(covariance[1, 1])),
        covariance_v2_s=float(covariance[0, 1]),
        planck_constant_j_s=slope * ELEMENTARY_CHARGE_C,
        planck_standard_error_j_s=(
            float(np.sqrt(covariance[0, 0])) * ELEMENTARY_CHARGE_C
        ),
        work_function_ev=-intercept,
        work_function_standard_error_ev=float(np.sqrt(covariance[1, 1])),
        reduced_chi_squared=float(np.sum((residuals / sigma) ** 2) / dof),
        residuals_v=residuals,
    )


def simulate_photoelectric_measurements(
    frequency_hz: ArrayLike,
    *,
    work_function_ev: float = 2.4,
    voltage_sigma_v: float = 0.02,
    seed: int = 2026,
) -> tuple[FloatArray, FloatArray]:
    """Generate a labelled synthetic stopping-voltage experiment."""

    frequency = np.asarray(frequency_hz, dtype=np.float64)
    if frequency.ndim != 1 or frequency.size < 3:
        raise ValueError("frequency_hz must contain at least three points")
    work_function = float(work_function_ev)
    sigma = float(voltage_sigma_v)
    if not np.isfinite(work_function) or work_function <= 0.0:
        raise ValueError("work_function_ev must be positive")
    if not np.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("voltage_sigma_v must be positive")
    expected = PLANCK_OVER_CHARGE_V_S * frequency - work_function
    if np.any(expected < 0.0):
        raise ValueError("all simulated frequencies must lie above threshold")
    measured = expected + np.random.default_rng(seed).normal(0.0, sigma, frequency.size)
    uncertainty = np.full(frequency.shape, sigma, dtype=np.float64)
    return np.asarray(measured, dtype=np.float64), uncertainty


def run_recovery_study(
    *,
    experiment_count: int = 500,
    work_function_ev: float = 2.4,
    voltage_sigma_v: float = 0.02,
    seed: int = 2026,
) -> RecoveryStudy:
    """Measure estimator bias and nominal 95% interval coverage."""

    if isinstance(experiment_count, bool) or int(experiment_count) < 30:
        raise ValueError("experiment_count must be an integer of at least 30")
    count = int(experiment_count)
    frequencies = np.linspace(6.2e14, 1.15e15, 12, dtype=np.float64)
    rng = np.random.default_rng(seed)
    planck = np.empty(count, dtype=np.float64)
    planck_error = np.empty(count, dtype=np.float64)
    work = np.empty(count, dtype=np.float64)
    work_error = np.empty(count, dtype=np.float64)
    expected = PLANCK_OVER_CHARGE_V_S * frequencies - work_function_ev
    sigma = np.full(frequencies.shape, voltage_sigma_v, dtype=np.float64)
    for index in range(count):
        observed = expected + rng.normal(0.0, voltage_sigma_v, frequencies.size)
        fitted = fit_photoelectric_measurements(frequencies, observed, sigma)
        planck[index] = fitted.planck_constant_j_s
        planck_error[index] = fitted.planck_standard_error_j_s
        work[index] = fitted.work_function_ev
        work_error[index] = fitted.work_function_standard_error_ev
    return RecoveryStudy(
        experiment_count=count,
        mean_planck_constant_j_s=float(np.mean(planck)),
        relative_planck_bias=float(np.mean(planck) / PLANCK_CONSTANT_J_S - 1.0),
        planck_rmse_j_s=float(
            np.sqrt(np.mean((planck - PLANCK_CONSTANT_J_S) ** 2))
        ),
        planck_95_percent_coverage=float(
            np.mean(np.abs(planck - PLANCK_CONSTANT_J_S) <= 1.96 * planck_error)
        ),
        mean_work_function_ev=float(np.mean(work)),
        work_function_bias_ev=float(np.mean(work) - work_function_ev),
        work_function_95_percent_coverage=float(
            np.mean(np.abs(work - work_function_ev) <= 1.96 * work_error)
        ),
    )


def millikan_1916_planck_estimate() -> tuple[float, float, float]:
    """Return mean h, its standard error, and relative modern difference.

    Millikan reported an unweighted mean, so this reproduces that treatment.
    The conversion to SI uses today's exact elementary charge and is therefore
    not numerically identical to Millikan's 1916 conversion from electrostatic
    units.
    """

    mean_slope = float(np.mean(MILLIKAN_1916_SLOPES_V_S))
    slope_sem = float(
        np.std(MILLIKAN_1916_SLOPES_V_S, ddof=1)
        / np.sqrt(MILLIKAN_1916_SLOPES_V_S.size)
    )
    planck = mean_slope * ELEMENTARY_CHARGE_C
    planck_sem = slope_sem * ELEMENTARY_CHARGE_C
    return planck, planck_sem, planck / PLANCK_CONSTANT_J_S - 1.0


__all__ = [
    "MILLIKAN_1916_SLOPES_V_S",
    "PhotoelectricFit",
    "RecoveryStudy",
    "fit_photoelectric_measurements",
    "millikan_1916_planck_estimate",
    "run_recovery_study",
    "simulate_photoelectric_measurements",
]
