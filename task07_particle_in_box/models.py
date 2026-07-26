"""Pure analytical equations for the one-dimensional infinite square well."""

from __future__ import annotations

from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task07_particle_in_box.constants import (
    ELECTRONVOLT_J,
    REDUCED_PLANCK_CONSTANT_J_S,
)


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
IntegerArray = NDArray[np.int64]


def _real_array(
    value: ArrayLike,
    *,
    name: str,
    positive: bool = False,
) -> FloatArray:
    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(
        raw.dtype, np.complexfloating
    ):
        raise TypeError(f"{name} must contain real numbers")
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    if positive and np.any(array <= 0.0):
        raise ValueError(f"{name} must be greater than zero")
    return array


def _positive_integer_array(value: ArrayLike, *, name: str) -> IntegerArray:
    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain integers, not booleans")
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.integer):
        raise TypeError(f"{name} must contain integers")
    array = np.asarray(value, dtype=np.int64)
    if np.any(array < 1):
        raise ValueError(f"{name} must be positive")
    return array


def _positive_scalar(value: Real, *, name: str) -> float:
    array = _real_array(value, name=name, positive=True)
    if array.ndim != 0:
        raise TypeError(f"{name} must be a scalar")
    return float(array)


def energy_j(
    quantum_number: ArrayLike,
    particle_mass_kg: Real,
    box_width_m: Real,
) -> FloatArray:
    """Return exact energy eigenvalues in joules."""

    n = _positive_integer_array(quantum_number, name="quantum_number")
    mass = _positive_scalar(particle_mass_kg, name="particle_mass_kg")
    width = _positive_scalar(box_width_m, name="box_width_m")
    return np.asarray(
        np.square(n.astype(np.float64))
        * np.pi**2
        * REDUCED_PLANCK_CONSTANT_J_S**2
        / (2.0 * mass * width**2),
        dtype=np.float64,
    )


def energy_ev(
    quantum_number: ArrayLike,
    particle_mass_kg: Real,
    box_width_m: Real,
) -> FloatArray:
    """Return exact energy eigenvalues in electronvolts."""

    return np.asarray(
        energy_j(quantum_number, particle_mass_kg, box_width_m) / ELECTRONVOLT_J,
        dtype=np.float64,
    )


def spatial_wavefunction_m_neg_half(
    position_m: ArrayLike,
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    """Return normalized spatial eigenfunctions, with zero outside the box."""

    position = _real_array(position_m, name="position_m")
    n = _positive_integer_array(quantum_number, name="quantum_number")
    width = _positive_scalar(box_width_m, name="box_width_m")
    try:
        position_b, n_b = np.broadcast_arrays(position, n)
    except ValueError as exc:
        raise ValueError("position_m and quantum_number must be broadcast-compatible") from exc
    inside = (position_b >= 0.0) & (position_b <= width)
    values = np.zeros(position_b.shape, dtype=np.float64)
    values[inside] = np.sqrt(2.0 / width) * np.sin(
        n_b[inside].astype(np.float64) * np.pi * position_b[inside] / width
    )
    return values


def probability_density_m_inv(
    position_m: ArrayLike,
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    """Return the Born probability density |psi|^2."""

    wavefunction = spatial_wavefunction_m_neg_half(
        position_m,
        quantum_number,
        box_width_m,
    )
    return np.asarray(np.square(wavefunction), dtype=np.float64)


def time_dependent_wavefunction_m_neg_half(
    position_m: ArrayLike,
    time_s: ArrayLike,
    quantum_number: ArrayLike,
    particle_mass_kg: Real,
    box_width_m: Real,
) -> ComplexArray:
    """Return psi_n(x,t), whose time factor is a unit-modulus phase."""

    spatial = spatial_wavefunction_m_neg_half(
        position_m,
        quantum_number,
        box_width_m,
    )
    time = _real_array(time_s, name="time_s")
    energies = energy_j(quantum_number, particle_mass_kg, box_width_m)
    try:
        spatial_b, time_b, energies_b = np.broadcast_arrays(spatial, time, energies)
    except ValueError as exc:
        raise ValueError("position, time, and quantum number must be broadcast-compatible") from exc
    phase = np.exp(-1.0j * energies_b * time_b / REDUCED_PLANCK_CONSTANT_J_S)
    return np.asarray(spatial_b * phase, dtype=np.complex128)


def expected_position_m(box_width_m: Real) -> float:
    width = _positive_scalar(box_width_m, name="box_width_m")
    return width / 2.0


def expected_position_squared_m2(
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number").astype(np.float64)
    width = _positive_scalar(box_width_m, name="box_width_m")
    return np.asarray(
        width**2 * (1.0 / 3.0 - 1.0 / (2.0 * np.pi**2 * np.square(n))),
        dtype=np.float64,
    )


def position_uncertainty_m(
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number").astype(np.float64)
    width = _positive_scalar(box_width_m, name="box_width_m")
    return np.asarray(
        width * np.sqrt(1.0 / 12.0 - 1.0 / (2.0 * np.pi**2 * np.square(n))),
        dtype=np.float64,
    )


def expected_momentum_kg_m_s(quantum_number: ArrayLike) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number")
    return np.zeros(n.shape, dtype=np.float64)


def expected_momentum_squared_kg2_m2_s2(
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number").astype(np.float64)
    width = _positive_scalar(box_width_m, name="box_width_m")
    return np.asarray(
        np.square(n * np.pi * REDUCED_PLANCK_CONSTANT_J_S / width),
        dtype=np.float64,
    )


def momentum_uncertainty_kg_m_s(
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number").astype(np.float64)
    width = _positive_scalar(box_width_m, name="box_width_m")
    return np.asarray(
        n * np.pi * REDUCED_PLANCK_CONSTANT_J_S / width,
        dtype=np.float64,
    )


def uncertainty_product_j_s(
    quantum_number: ArrayLike,
    box_width_m: Real,
) -> FloatArray:
    return np.asarray(
        position_uncertainty_m(quantum_number, box_width_m)
        * momentum_uncertainty_kg_m_s(quantum_number, box_width_m),
        dtype=np.float64,
    )


def uncertainty_product_over_hbar(quantum_number: ArrayLike) -> FloatArray:
    n = _positive_integer_array(quantum_number, name="quantum_number").astype(np.float64)
    return np.asarray(
        np.sqrt(np.square(n) * np.pi**2 / 12.0 - 0.5),
        dtype=np.float64,
    )


__all__ = [
    "energy_ev",
    "energy_j",
    "expected_momentum_kg_m_s",
    "expected_momentum_squared_kg2_m2_s2",
    "expected_position_m",
    "expected_position_squared_m2",
    "momentum_uncertainty_kg_m_s",
    "position_uncertainty_m",
    "probability_density_m_inv",
    "spatial_wavefunction_m_neg_half",
    "time_dependent_wavefunction_m_neg_half",
    "uncertainty_product_j_s",
    "uncertainty_product_over_hbar",
]
