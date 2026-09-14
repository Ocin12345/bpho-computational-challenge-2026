"""Coherent two-state superposition for the optional Task 7 extension."""

from __future__ import annotations

import math
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task07_particle_in_box.constants import REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.models import energy_ev, energy_j


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def _real_array(value: ArrayLike, *, name: str) -> FloatArray:
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
    return array


def _positive_scalar(value: Real, *, name: str) -> float:
    array = _real_array(value, name=name)
    if array.ndim != 0:
        raise TypeError(f"{name} must be a scalar")
    normalized = float(array)
    if normalized <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return normalized


def dimensionless_wavefunction(
    position_over_width: ArrayLike,
    relative_phase_rad: ArrayLike,
) -> ComplexArray:
    """Return ``sqrt(a) Psi`` for an equal ``n=1`` and ``n=2`` superposition.

    The common global phase is omitted. The remaining relative phase is
    ``(E_2-E_1)t/hbar``.
    """

    position = _real_array(position_over_width, name="position_over_width")
    phase = _real_array(relative_phase_rad, name="relative_phase_rad")
    try:
        position_b, phase_b = np.broadcast_arrays(position, phase)
    except ValueError as exc:
        raise ValueError("position and phase must be broadcast-compatible") from exc
    values = np.zeros(position_b.shape, dtype=np.complex128)
    inside = (position_b >= 0.0) & (position_b <= 1.0)
    u = position_b[inside]
    theta = phase_b[inside]
    values[inside] = np.sin(np.pi * u) + np.exp(-1.0j * theta) * np.sin(
        2.0 * np.pi * u
    )
    return values


def dimensionless_probability_density(
    position_over_width: ArrayLike,
    relative_phase_rad: ArrayLike,
) -> FloatArray:
    """Return the normalized dimensionless density ``a |Psi|^2``."""

    return np.asarray(
        np.abs(
            dimensionless_wavefunction(position_over_width, relative_phase_rad)
        )
        ** 2,
        dtype=np.float64,
    )


def expected_position_over_width(relative_phase_rad: ArrayLike) -> FloatArray:
    """Return ``<x>/a`` for the coherent equal-weight state."""

    phase = _real_array(relative_phase_rad, name="relative_phase_rad")
    return np.asarray(
        0.5 - 16.0 * np.cos(phase) / (9.0 * np.pi**2),
        dtype=np.float64,
    )


def left_half_probability(relative_phase_rad: ArrayLike) -> FloatArray:
    """Return the probability of finding the particle in ``0 <= x <= a/2``."""

    phase = _real_array(relative_phase_rad, name="relative_phase_rad")
    return np.asarray(
        0.5 + 4.0 * np.cos(phase) / (3.0 * np.pi),
        dtype=np.float64,
    )


def beat_period_s(particle_mass_kg: Real, box_width_m: Real) -> float:
    """Return ``T = 2 pi hbar / (E_2-E_1)`` for the two-state density cycle."""

    mass = _positive_scalar(particle_mass_kg, name="particle_mass_kg")
    width = _positive_scalar(box_width_m, name="box_width_m")
    energies = energy_j(np.asarray([1, 2], dtype=np.int64), mass, width)
    return float(
        2.0
        * np.pi
        * REDUCED_PLANCK_CONSTANT_J_S
        / (float(energies[1]) - float(energies[0]))
    )


def mean_energy_ev(particle_mass_kg: Real, box_width_m: Real) -> float:
    """Return the time-independent equal-weight energy expectation."""

    mass = _positive_scalar(particle_mass_kg, name="particle_mass_kg")
    width = _positive_scalar(box_width_m, name="box_width_m")
    energies = energy_ev(np.asarray([1, 2], dtype=np.int64), mass, width)
    return float((energies[0] + energies[1]) / 2.0)


def energy_uncertainty_ev(particle_mass_kg: Real, box_width_m: Real) -> float:
    """Return the constant energy standard deviation for equal weights."""

    mass = _positive_scalar(particle_mass_kg, name="particle_mass_kg")
    width = _positive_scalar(box_width_m, name="box_width_m")
    energies = energy_ev(np.asarray([1, 2], dtype=np.int64), mass, width)
    return float((energies[1] - energies[0]) / 2.0)


__all__ = [
    "beat_period_s",
    "dimensionless_probability_density",
    "dimensionless_wavefunction",
    "energy_uncertainty_ev",
    "expected_position_over_width",
    "left_half_probability",
    "mean_energy_ev",
]
