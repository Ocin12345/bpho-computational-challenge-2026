"""Pure vectorised equations for the Task 8 polarisation comparison."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral, Real
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import (
    DEGREES_PER_RADIAN,
    POLARISATION_PERIOD_DEG,
    PROBABILITY_MAXIMUM,
    PROBABILITY_MINIMUM,
    RADIANS_PER_DEGREE,
)


FloatArray = NDArray[np.float64]
SweepVariable = Literal["theta", "phi"]


@dataclass(frozen=True)
class DetectorProbabilities:
    """Probabilities for the orthogonal X and Y outcomes of one detector."""

    x: FloatArray
    y: FloatArray


@dataclass(frozen=True)
class MismatchComparison:
    """Classical and quantum match/mismatch results on a common shape."""

    classical_match: FloatArray
    classical_mismatch: FloatArray
    quantum_match: FloatArray
    quantum_mismatch: FloatArray
    signed_difference: FloatArray


@dataclass(frozen=True)
class AngleSweep:
    """One-dimensional detector-angle sweep and its calculated results."""

    variable: SweepVariable
    theta_deg: FloatArray
    phi_deg: FloatArray
    comparison: MismatchComparison


@dataclass(frozen=True)
class MismatchGrid:
    """Two-dimensional theta/phi grid and its calculated results."""

    theta_deg: FloatArray
    phi_deg: FloatArray
    comparison: MismatchComparison


def _real_array(value: ArrayLike, *, name: str) -> FloatArray:
    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(
        raw.dtype,
        np.complexfloating,
    ):
        raise TypeError(f"{name} must contain real numbers")
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def _real_scalar(value: Real, *, name: str) -> float:
    array = _real_array(value, name=name)
    if array.ndim != 0:
        raise TypeError(f"{name} must be a scalar")
    return float(array)


def _odd_point_count(value: Integral, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 3:
        raise ValueError(f"{name} must be at least 3")
    if normalized % 2 == 0:
        raise ValueError(f"{name} must be odd so zero degrees is sampled")
    return normalized


def _broadcast_angles(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    theta = _real_array(theta_deg, name="theta_deg")
    phi = _real_array(phi_deg, name="phi_deg")
    try:
        theta_b, phi_b = np.broadcast_arrays(theta, phi)
    except ValueError as exc:
        raise ValueError("theta_deg and phi_deg must be broadcast-compatible") from exc
    return (
        np.asarray(theta_b, dtype=np.float64),
        np.asarray(phi_b, dtype=np.float64),
    )


def _probability(
    value: ArrayLike,
    *,
    name: str,
    tolerance: float = DEFAULT_CONFIGURATION.probability_absolute_tolerance,
) -> FloatArray:
    array = _real_array(value, name=name)
    if np.any(array < PROBABILITY_MINIMUM - tolerance) or np.any(
        array > PROBABILITY_MAXIMUM + tolerance
    ):
        raise ArithmeticError(f"{name} fell outside the probability interval")
    return np.asarray(
        np.clip(array, PROBABILITY_MINIMUM, PROBABILITY_MAXIMUM),
        dtype=np.float64,
    )


def degrees_to_radians(angle_deg: ArrayLike) -> FloatArray:
    """Convert finite real angles from degrees to radians."""

    return np.asarray(
        _real_array(angle_deg, name="angle_deg") * RADIANS_PER_DEGREE,
        dtype=np.float64,
    )


def radians_to_degrees(angle_rad: ArrayLike) -> FloatArray:
    """Convert finite real angles from radians to degrees."""

    return np.asarray(
        _real_array(angle_rad, name="angle_rad") * DEGREES_PER_RADIAN,
        dtype=np.float64,
    )


def normalize_polarisation_angle_deg(angle_deg: ArrayLike) -> FloatArray:
    """Return the equivalent polarisation-axis angle in [-90, 90)."""

    angle = _real_array(angle_deg, name="angle_deg")
    return np.asarray(
        (angle + POLARISATION_PERIOD_DEG / 2.0) % POLARISATION_PERIOD_DEG
        - POLARISATION_PERIOD_DEG / 2.0,
        dtype=np.float64,
    )


def relative_detector_angle_deg(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> FloatArray:
    """Return the minimal signed B-minus-A detector-axis separation."""

    theta, phi = _broadcast_angles(theta_deg, phi_deg)
    return normalize_polarisation_angle_deg(phi - theta)


def detector_probabilities(angle_deg: ArrayLike) -> DetectorProbabilities:
    """Return Malus-law probabilities for a detector's X and Y outcomes."""

    angle_rad = degrees_to_radians(angle_deg)
    return DetectorProbabilities(
        x=_probability(np.square(np.cos(angle_rad)), name="x_probability"),
        y=_probability(np.square(np.sin(angle_rad)), name="y_probability"),
    )


def classical_match_probability(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> FloatArray:
    """Return the official independent classical match probability."""

    theta, phi = _broadcast_angles(theta_deg, phi_deg)
    detector_a = detector_probabilities(theta)
    detector_b = detector_probabilities(phi)
    return _probability(
        detector_a.x * detector_b.x + detector_a.y * detector_b.y,
        name="classical_match_probability",
    )


def classical_mismatch_probability(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> FloatArray:
    """Return the classical mismatch probability stated by Task 8."""

    return _probability(
        1.0 - classical_match_probability(theta_deg, phi_deg),
        name="classical_mismatch_probability",
    )


def quantum_match_probability(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> FloatArray:
    """Return the quantum match probability after measurement collapse."""

    delta_rad = degrees_to_radians(relative_detector_angle_deg(theta_deg, phi_deg))
    return _probability(
        np.square(np.cos(delta_rad)),
        name="quantum_match_probability",
    )


def quantum_mismatch_probability(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> FloatArray:
    """Return sin^2(phi-theta), the Task 8 quantum mismatch probability."""

    delta_rad = degrees_to_radians(relative_detector_angle_deg(theta_deg, phi_deg))
    return _probability(
        np.square(np.sin(delta_rad)),
        name="quantum_mismatch_probability",
    )


def mismatch_comparison(
    theta_deg: ArrayLike,
    phi_deg: ArrayLike,
) -> MismatchComparison:
    """Return all primary classical/quantum comparison quantities."""

    theta, phi = _broadcast_angles(theta_deg, phi_deg)
    classical_match = classical_match_probability(theta, phi)
    classical_mismatch = _probability(
        1.0 - classical_match,
        name="classical_mismatch_probability",
    )
    quantum_match = quantum_match_probability(theta, phi)
    quantum_mismatch = quantum_mismatch_probability(theta, phi)
    return MismatchComparison(
        classical_match=classical_match,
        classical_mismatch=classical_mismatch,
        quantum_match=quantum_match,
        quantum_mismatch=quantum_mismatch,
        signed_difference=np.asarray(
            quantum_mismatch - classical_mismatch,
            dtype=np.float64,
        ),
    )


def probability_percent(probability: ArrayLike) -> FloatArray:
    """Convert a validated probability to percentage points."""

    try:
        validated = _probability(probability, name="probability")
    except ArithmeticError as exc:
        raise ValueError("probability must lie within [0, 1]") from exc
    return np.asarray(
        100.0 * validated,
        dtype=np.float64,
    )


def angle_samples(
    point_count: Integral | None = None,
    *,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> FloatArray:
    """Return an inclusive symmetric display-angle sample containing zero."""

    count = _odd_point_count(
        configuration.sweep_point_count if point_count is None else point_count,
        name="point_count",
    )
    return np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        count,
        dtype=np.float64,
    )


def angle_sweep(
    fixed_angle_deg: Real,
    *,
    variable: SweepVariable = "phi",
    point_count: Integral | None = None,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> AngleSweep:
    """Sweep theta or phi while holding the other detector angle fixed."""

    if variable not in ("theta", "phi"):
        raise ValueError("variable must be either 'theta' or 'phi'")
    fixed = _real_scalar(fixed_angle_deg, name="fixed_angle_deg")
    if not configuration.angle_minimum_deg <= fixed <= configuration.angle_maximum_deg:
        raise ValueError("fixed_angle_deg must lie within the display range")
    samples = angle_samples(point_count, configuration=configuration)
    fixed_values = np.full(samples.shape, fixed, dtype=np.float64)
    if variable == "theta":
        theta, phi = samples, fixed_values
    else:
        theta, phi = fixed_values, samples
    return AngleSweep(
        variable=variable,
        theta_deg=theta,
        phi_deg=phi,
        comparison=mismatch_comparison(theta, phi),
    )


def _grid_axis(
    value: ArrayLike | None,
    *,
    name: str,
    configuration: Task08Configuration,
) -> FloatArray:
    if value is None:
        return angle_samples(
            configuration.heatmap_point_count,
            configuration=configuration,
        )
    axis = _real_array(value, name=name)
    if axis.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if axis.size == 0:
        raise ValueError(f"{name} must not be empty")
    if np.any(axis < configuration.angle_minimum_deg) or np.any(
        axis > configuration.angle_maximum_deg
    ):
        raise ValueError(f"{name} must lie within the display range")
    return axis


def mismatch_grid(
    theta_deg: ArrayLike | None = None,
    phi_deg: ArrayLike | None = None,
    *,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> MismatchGrid:
    """Return a theta-by-phi mesh suitable for heatmaps and evidence data."""

    theta_axis = _grid_axis(
        theta_deg,
        name="theta_deg",
        configuration=configuration,
    )
    phi_axis = _grid_axis(
        phi_deg,
        name="phi_deg",
        configuration=configuration,
    )
    theta_mesh, phi_mesh = np.meshgrid(theta_axis, phi_axis, indexing="ij")
    return MismatchGrid(
        theta_deg=np.asarray(theta_mesh, dtype=np.float64),
        phi_deg=np.asarray(phi_mesh, dtype=np.float64),
        comparison=mismatch_comparison(theta_mesh, phi_mesh),
    )


__all__ = [
    "AngleSweep",
    "DetectorProbabilities",
    "MismatchComparison",
    "MismatchGrid",
    "angle_samples",
    "angle_sweep",
    "classical_match_probability",
    "classical_mismatch_probability",
    "degrees_to_radians",
    "detector_probabilities",
    "mismatch_comparison",
    "mismatch_grid",
    "normalize_polarisation_angle_deg",
    "probability_percent",
    "quantum_match_probability",
    "quantum_mismatch_probability",
    "radians_to_degrees",
    "relative_detector_angle_deg",
]
