"""Pure vectorized equations for ideal Bohr levels and emissions."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task05_hydrogen_spectrum.constants import (
    ELECTRONVOLT_J,
    HC_EV_M,
    PLANCK_CONSTANT_J_S,
    RYDBERG_ENERGY_EV,
    RYDBERG_ENERGY_J,
)


IntegerArray = NDArray[np.int64]
FloatArray = NDArray[np.float64]


def _positive_integer_array(value: ArrayLike, *, name: str) -> IntegerArray:
    """Return a positive int64 array without numerical coercion."""

    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain integers, not booleans")
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.integer):
        raise TypeError(f"{name} must contain integers")
    try:
        array = np.asarray(value, dtype=np.int64)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} values must fit in int64") from exc
    if np.any(array < 1):
        raise ValueError(f"{name} must be positive")
    return array


def _transition_arrays(
    initial_n: ArrayLike,
    final_n: ArrayLike,
) -> tuple[IntegerArray, IntegerArray]:
    initial = _positive_integer_array(initial_n, name="initial_n")
    final = _positive_integer_array(final_n, name="final_n")
    try:
        initial_b, final_b = np.broadcast_arrays(initial, final)
    except ValueError as exc:
        raise ValueError("initial_n and final_n must be broadcast-compatible") from exc
    initial_b = np.asarray(initial_b, dtype=np.int64)
    final_b = np.asarray(final_b, dtype=np.int64)
    if np.any(initial_b <= final_b):
        raise ValueError("emission requires initial_n > final_n")
    return initial_b, final_b


def bohr_energy_ev(n: ArrayLike) -> FloatArray:
    """Return negative ideal Bohr level energy in electronvolts."""

    levels = _positive_integer_array(n, name="n").astype(np.float64)
    return np.asarray(-RYDBERG_ENERGY_EV / np.square(levels), dtype=np.float64)


def bohr_energy_j(n: ArrayLike) -> FloatArray:
    """Return negative ideal Bohr level energy in joules."""

    levels = _positive_integer_array(n, name="n").astype(np.float64)
    return np.asarray(-RYDBERG_ENERGY_J / np.square(levels), dtype=np.float64)


def transition_energy_ev(
    initial_n: ArrayLike,
    final_n: ArrayLike,
) -> FloatArray:
    """Return positive emitted-photon energy in electronvolts."""

    initial, final = _transition_arrays(initial_n, final_n)
    initial_f = initial.astype(np.float64)
    final_f = final.astype(np.float64)
    difference = 1.0 / np.square(final_f) - 1.0 / np.square(initial_f)
    return np.asarray(RYDBERG_ENERGY_EV * difference, dtype=np.float64)


def transition_energy_j(
    initial_n: ArrayLike,
    final_n: ArrayLike,
) -> FloatArray:
    """Return positive emitted-photon energy in joules."""

    return np.asarray(
        transition_energy_ev(initial_n, final_n) * ELECTRONVOLT_J,
        dtype=np.float64,
    )


def transition_frequency_hz(
    initial_n: ArrayLike,
    final_n: ArrayLike,
) -> FloatArray:
    """Return emitted-photon frequency in hertz."""

    return np.asarray(
        transition_energy_j(initial_n, final_n) / PLANCK_CONSTANT_J_S,
        dtype=np.float64,
    )


def transition_wavelength_m(
    initial_n: ArrayLike,
    final_n: ArrayLike,
) -> FloatArray:
    """Return emitted-photon vacuum wavelength in metres."""

    return np.asarray(
        HC_EV_M / transition_energy_ev(initial_n, final_n),
        dtype=np.float64,
    )


def series_limit_energy_ev(final_n: ArrayLike) -> FloatArray:
    """Return the analytical photon-energy limit for a final level."""

    final = _positive_integer_array(final_n, name="final_n").astype(np.float64)
    return np.asarray(RYDBERG_ENERGY_EV / np.square(final), dtype=np.float64)


def series_limit_wavelength_m(final_n: ArrayLike) -> FloatArray:
    """Return the analytical shortest wavelength for a series."""

    return np.asarray(
        HC_EV_M / series_limit_energy_ev(final_n),
        dtype=np.float64,
    )


__all__ = [
    "bohr_energy_ev",
    "bohr_energy_j",
    "series_limit_energy_ev",
    "series_limit_wavelength_m",
    "transition_energy_ev",
    "transition_energy_j",
    "transition_frequency_hz",
    "transition_wavelength_m",
]
