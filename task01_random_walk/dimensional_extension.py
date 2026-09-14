"""Dimension-comparison extension for BPhO Computational Challenge Task 1.

The official task is two-dimensional.  This module keeps the fixed-step,
isotropic model but evaluates it in one, two, and three spatial dimensions.
For every dimension the exact identity is

    E[|R_N|^2] = N s^2,

while each Cartesian component has variance ``N s^2 / d``.  The radial
endpoint distribution changes with dimension even though the RMS law does
not.  These routines provide deterministic reference calculations for the
browser extension and deliberately contain no presentation code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
SUPPORTED_DIMENSIONS = (1, 2, 3)


@dataclass(frozen=True)
class DimensionalWalk:
    """One exact fixed-step walk in ``dimension`` spatial dimensions."""

    dimension: int
    n_steps: int
    step_size: float
    seed: int | None
    displacements: FloatArray
    positions: FloatArray

    @property
    def step_lengths(self) -> FloatArray:
        """Euclidean length of every microscopic step."""

        return np.linalg.norm(self.displacements, axis=1)

    @property
    def final_distance(self) -> float:
        """Euclidean distance of the final point from the origin."""

        return float(np.linalg.norm(self.positions[-1]))


@dataclass(frozen=True)
class ScalingPoint:
    """Ensemble estimate at one step count."""

    n_steps: int
    mean_squared_displacement: float
    msd_standard_error: float
    rms_displacement: float
    rms_standard_error: float


@dataclass(frozen=True)
class DimensionStudy:
    """Distribution and scaling evidence for one spatial dimension."""

    dimension: int
    n_walks: int
    step_size: float
    seed: int
    checkpoints: tuple[int, ...]
    normalized_radii: FloatArray
    scaling: tuple[ScalingPoint, ...]
    slope: float
    slope_standard_error: float
    exponent: float
    exponent_standard_error: float
    mean_endpoint: FloatArray


def _validate_dimension(dimension: int) -> int:
    if isinstance(dimension, (bool, np.bool_)) or not isinstance(
        dimension, (int, np.integer)
    ):
        raise TypeError("dimension must be an integer")
    dimension = int(dimension)
    if dimension not in SUPPORTED_DIMENSIONS:
        raise ValueError("dimension must be 1, 2, or 3")
    return dimension


def _validate_positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _validate_step_size(step_size: float) -> float:
    if isinstance(step_size, (bool, np.bool_)) or not isinstance(
        step_size, (int, float, np.integer, np.floating)
    ):
        raise TypeError("step_size must be a real number")
    step_size = float(step_size)
    if not np.isfinite(step_size) or step_size <= 0.0:
        raise ValueError("step_size must be finite and greater than zero")
    return step_size


def _validate_seed(seed: int | None) -> int | None:
    if seed is None:
        return None
    if isinstance(seed, (bool, np.bool_)) or not isinstance(
        seed, (int, np.integer)
    ):
        raise TypeError("seed must be a non-negative integer or None")
    seed = int(seed)
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return seed


def sample_isotropic_steps(
    rng: np.random.Generator,
    count: int,
    dimension: int,
    step_size: float = 1.0,
) -> FloatArray:
    """Sample exact isotropic vectors of fixed Euclidean length.

    In one dimension isotropy means equal probabilities for ``+s`` and
    ``-s``.  In two dimensions the azimuth is uniform.  In three dimensions
    both azimuth and ``cos(polar angle)`` are uniform, which avoids the polar
    clustering produced by sampling the polar angle itself uniformly.
    """

    count = _validate_positive_integer(count, "count")
    dimension = _validate_dimension(dimension)
    step_size = _validate_step_size(step_size)

    if dimension == 1:
        signs = rng.integers(0, 2, size=count, dtype=np.int8) * 2 - 1
        return step_size * signs.astype(np.float64)[:, None]

    azimuth = rng.uniform(0.0, 2.0 * np.pi, size=count)
    if dimension == 2:
        return step_size * np.column_stack(
            (np.cos(azimuth), np.sin(azimuth))
        )

    cosine_polar = rng.uniform(-1.0, 1.0, size=count)
    radial_xy = np.sqrt(np.maximum(0.0, 1.0 - cosine_polar**2))
    return step_size * np.column_stack(
        (
            radial_xy * np.cos(azimuth),
            radial_xy * np.sin(azimuth),
            cosine_polar,
        )
    )


def simulate_dimensional_walk(
    n_steps: int,
    step_size: float,
    dimension: int,
    *,
    seed: int | None = None,
) -> DimensionalWalk:
    """Simulate one exact isotropic walk in one, two, or three dimensions."""

    n_steps = _validate_positive_integer(n_steps, "n_steps")
    step_size = _validate_step_size(step_size)
    dimension = _validate_dimension(dimension)
    seed = _validate_seed(seed)
    rng = np.random.default_rng(seed)
    displacements = sample_isotropic_steps(
        rng, n_steps, dimension, step_size
    )
    positions = np.empty((n_steps + 1, dimension), dtype=np.float64)
    positions[0] = 0.0
    positions[1:] = np.cumsum(displacements, axis=0)
    return DimensionalWalk(
        dimension=dimension,
        n_steps=n_steps,
        step_size=step_size,
        seed=seed,
        displacements=displacements,
        positions=positions,
    )


def default_checkpoints(max_steps: int) -> tuple[int, ...]:
    """Return seven approximately geometric checkpoints ending at max_steps."""

    max_steps = _validate_positive_integer(max_steps, "max_steps")
    fractions = (1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2, 3 / 4, 1)
    values = {max(4, min(max_steps, int(round(max_steps * f)))) for f in fractions}
    values.add(max_steps)
    return tuple(sorted(values))


def theoretical_normalized_radial_density(
    normalized_radius: FloatArray | Iterable[float], dimension: int
) -> FloatArray:
    """Large-N density of q = |R|/(s sqrt(N)) for dimension 1, 2, or 3."""

    dimension = _validate_dimension(dimension)
    q = np.asarray(normalized_radius, dtype=np.float64)
    if np.any(~np.isfinite(q)) or np.any(q < 0.0):
        raise ValueError("normalized radii must be finite and non-negative")
    if dimension == 1:
        return np.sqrt(2.0 / np.pi) * np.exp(-0.5 * q**2)
    if dimension == 2:
        return 2.0 * q * np.exp(-(q**2))
    return (
        np.sqrt(2.0 / np.pi)
        * 3.0
        * np.sqrt(3.0)
        * q**2
        * np.exp(-1.5 * q**2)
    )


def _fit_through_origin(x: FloatArray, y: FloatArray) -> tuple[float, float]:
    denominator = float(np.dot(x, x))
    slope = float(np.dot(x, y) / denominator)
    residuals = y - slope * x
    degrees_of_freedom = max(1, len(x) - 1)
    residual_variance = float(np.dot(residuals, residuals) / degrees_of_freedom)
    standard_error = float(np.sqrt(residual_variance / denominator))
    return slope, standard_error


def _fit_power_law(step_counts: FloatArray, rms: FloatArray) -> tuple[float, float]:
    x = np.log(step_counts)
    y = np.log(rms)
    design = np.column_stack((np.ones_like(x), x))
    coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ coefficients
    degrees_of_freedom = max(1, len(x) - 2)
    residual_variance = float(np.dot(residuals, residuals) / degrees_of_freedom)
    covariance = residual_variance * np.linalg.inv(design.T @ design)
    return float(coefficients[1]), float(np.sqrt(covariance[1, 1]))


def run_dimension_study(
    dimension: int,
    *,
    n_walks: int = 6_000,
    max_steps: int = 800,
    step_size: float = 1.0,
    seed: int = 2026,
    checkpoints: Iterable[int] | None = None,
) -> DimensionStudy:
    """Run an exact endpoint and RMS-scaling study without storing trajectories."""

    dimension = _validate_dimension(dimension)
    n_walks = _validate_positive_integer(n_walks, "n_walks")
    max_steps = _validate_positive_integer(max_steps, "max_steps")
    step_size = _validate_step_size(step_size)
    validated_seed = _validate_seed(seed)
    assert validated_seed is not None

    checkpoint_values = (
        default_checkpoints(max_steps)
        if checkpoints is None
        else tuple(sorted({_validate_positive_integer(v, "checkpoint") for v in checkpoints}))
    )
    if not checkpoint_values or checkpoint_values[-1] != max_steps:
        raise ValueError("checkpoints must include max_steps")
    if checkpoint_values[-1] > max_steps:
        raise ValueError("checkpoints cannot exceed max_steps")

    rng = np.random.default_rng(validated_seed)
    positions = np.zeros((n_walks, dimension), dtype=np.float64)
    checkpoint_set = set(checkpoint_values)
    points: list[ScalingPoint] = []

    for step in range(1, max_steps + 1):
        positions += sample_isotropic_steps(rng, n_walks, dimension, step_size)
        if step not in checkpoint_set:
            continue
        squared_radius = np.einsum("ij,ij->i", positions, positions)
        mean_msd = float(np.mean(squared_radius))
        msd_se = float(np.std(squared_radius, ddof=1) / np.sqrt(n_walks))
        rms = float(np.sqrt(mean_msd))
        rms_se = float(msd_se / (2.0 * max(rms, np.finfo(float).tiny)))
        points.append(
            ScalingPoint(
                n_steps=step,
                mean_squared_displacement=mean_msd,
                msd_standard_error=msd_se,
                rms_displacement=rms,
                rms_standard_error=rms_se,
            )
        )

    step_counts = np.array([point.n_steps for point in points], dtype=np.float64)
    normalized_rms = np.array(
        [point.rms_displacement / step_size for point in points], dtype=np.float64
    )
    slope, slope_se = _fit_through_origin(np.sqrt(step_counts), normalized_rms)
    exponent, exponent_se = _fit_power_law(step_counts, normalized_rms)
    normalized_radii = np.linalg.norm(positions, axis=1) / (
        step_size * np.sqrt(max_steps)
    )

    return DimensionStudy(
        dimension=dimension,
        n_walks=n_walks,
        step_size=step_size,
        seed=validated_seed,
        checkpoints=checkpoint_values,
        normalized_radii=normalized_radii,
        scaling=tuple(points),
        slope=slope,
        slope_standard_error=slope_se,
        exponent=exponent,
        exponent_standard_error=exponent_se,
        mean_endpoint=np.mean(positions, axis=0),
    )

