"""Independent analytical reference relationships for Task 3.

This module deliberately does not import ``models.py``. Its values provide
external targets against which the numerical calculations are checked.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task03_thermal_radiation.constants import (
    MOLAR_GAS_CONSTANT_J_MOL_K,
    STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
    WIEN_DISPLACEMENT_CONSTANT_M_K,
)


FloatArray = NDArray[np.float64]


def _positive_temperature_array(temperature_k: ArrayLike) -> FloatArray:
    """Return positive finite temperatures as float64 without model imports."""

    raw = np.asarray(temperature_k)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError("temperature_k must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_):
        raise TypeError("temperature_k must not contain booleans")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError("temperature_k must not contain complex values")

    temperature = np.asarray(temperature_k, dtype=np.float64)
    if not np.all(np.isfinite(temperature)):
        raise ValueError("temperature_k must contain only finite values")
    if np.any(temperature <= 0.0):
        raise ValueError("temperature_k must be strictly positive")
    return temperature


def wien_peak_wavelength(temperature_k: ArrayLike) -> FloatArray:
    """Return the wavelength-form Wien peak in metres."""

    temperature = _positive_temperature_array(temperature_k)
    result = WIEN_DISPLACEMENT_CONSTANT_M_K / temperature
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("Wien peak is outside float64 range")
    return np.asarray(result, dtype=np.float64)


def stefan_boltzmann_exitance(temperature_k: ArrayLike) -> FloatArray:
    """Return total black-body exitance ``sigma T^4`` in W m^-2."""

    temperature = _positive_temperature_array(temperature_k)
    with np.errstate(over="ignore"):
        result = STEFAN_BOLTZMANN_CONSTANT_W_M2_K4 * temperature**4
    if not np.all(np.isfinite(result)):
        raise FloatingPointError(
            "Stefan--Boltzmann exitance is outside float64 range"
        )
    return np.asarray(result, dtype=np.float64)


def dulong_petit_limit() -> float:
    """Return the Einstein model's high-temperature molar limit ``3R``."""

    return 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K


def einstein_anchor_ratio() -> float:
    """Return ``C_V/(3R)`` at the independent reference point ``T = T_E``."""

    return math.exp(1.0) / math.expm1(1.0) ** 2


__all__ = [
    "dulong_petit_limit",
    "einstein_anchor_ratio",
    "stefan_boltzmann_exitance",
    "wien_peak_wavelength",
]
