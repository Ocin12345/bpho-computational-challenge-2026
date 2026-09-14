"""Debye heat-capacity extension for BPhO Computational Challenge Task 3.

The accepted baseline uses Einstein's single oscillator frequency.  The Debye
extension replaces it with a continuum of acoustic modes and therefore
recovers the experimentally important cubic low-temperature law.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from numpy.polynomial.legendre import leggauss
from numpy.typing import ArrayLike, NDArray

from task03_thermal_radiation.constants import MOLAR_GAS_CONSTANT_J_MOL_K


FloatArray = NDArray[np.float64]
DEBYE_INTEGRAL_INFINITY = 4.0 * math.pi**4 / 15.0
LOW_TEMPERATURE_COEFFICIENT = (
    12.0 * math.pi**4 * MOLAR_GAS_CONSTANT_J_MOL_K / 5.0
)


def _finite_array(value: ArrayLike, *, name: str) -> FloatArray:
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_):
        raise TypeError(f"{name} must not contain booleans")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must not contain complex values")
    result = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite values")
    return result


@lru_cache(maxsize=8)
def _quadrature(order: int) -> tuple[FloatArray, FloatArray]:
    if isinstance(order, bool) or not isinstance(order, int):
        raise TypeError("quadrature_order must be an integer")
    if order < 32 or order > 1024:
        raise ValueError("quadrature_order must be between 32 and 1024")
    nodes, weights = leggauss(order)
    return np.asarray(nodes, dtype=np.float64), np.asarray(weights, dtype=np.float64)


def _debye_integrand(x: FloatArray) -> FloatArray:
    result = np.empty_like(x)
    small = x < 1.0e-4
    x_small = x[small]
    result[small] = x_small**2 - x_small**4 / 12.0 + x_small**6 / 240.0
    regular = ~small
    x_regular = x[regular]
    negative_exponential = np.exp(-x_regular)
    denominator = -np.expm1(-x_regular)
    result[regular] = (
        x_regular**4 * negative_exponential / denominator**2
    )
    return result


def debye_integral(
    upper_limit: ArrayLike,
    *,
    quadrature_order: int = 160,
) -> FloatArray:
    """Return integral_0^y x^4 exp(x)/(exp(x)-1)^2 dx.

    Gauss--Legendre quadrature is used up to ``y=60``. Above that point the
    missing tail is below double-precision relevance for this application and
    the exact infinite-limit integral is returned.
    """

    upper = _finite_array(upper_limit, name="upper_limit")
    if np.any(upper < 0.0):
        raise ValueError("upper_limit must be non-negative")
    nodes, weights = _quadrature(quadrature_order)
    result = np.zeros_like(upper)
    flat_upper = upper.reshape(-1)
    flat_result = result.reshape(-1)
    for index, value in enumerate(flat_upper):
        if value == 0.0:
            continue
        if value >= 60.0:
            flat_result[index] = DEBYE_INTEGRAL_INFINITY
            continue
        transformed = 0.5 * value * (nodes + 1.0)
        flat_result[index] = 0.5 * value * float(
            np.dot(weights, _debye_integrand(transformed))
        )
    return np.asarray(result, dtype=np.float64)


def debye_molar_heat_capacity(
    temperature_k: ArrayLike,
    debye_temperature_k: ArrayLike,
    *,
    quadrature_order: int = 160,
) -> FloatArray:
    """Return Debye constant-volume molar heat capacity in J mol^-1 K^-1."""

    temperature = _finite_array(temperature_k, name="temperature_k")
    debye_temperature = _finite_array(
        debye_temperature_k,
        name="debye_temperature_k",
    )
    if np.any(temperature < 0.0):
        raise ValueError("temperature_k must be non-negative")
    if np.any(debye_temperature <= 0.0):
        raise ValueError("debye_temperature_k must be strictly positive")
    try:
        temperature, debye_temperature = np.broadcast_arrays(
            temperature,
            debye_temperature,
        )
    except ValueError as exc:
        raise ValueError(
            "temperature_k and debye_temperature_k must be broadcast-compatible"
        ) from exc

    ratio = np.full(temperature.shape, np.inf, dtype=np.float64)
    positive = temperature > 0.0
    np.divide(debye_temperature, temperature, out=ratio, where=positive)
    normalized = np.zeros(temperature.shape, dtype=np.float64)

    high_temperature = positive & (ratio < 1.0e-3)
    y_high = ratio[high_temperature]
    normalized[high_temperature] = (
        1.0 - y_high**2 / 20.0 + y_high**4 / 560.0
    )

    regular = positive & ~high_temperature
    y_regular = ratio[regular]
    if y_regular.size:
        normalized[regular] = (
            3.0
            * debye_integral(
                y_regular,
                quadrature_order=quadrature_order,
            )
            / y_regular**3
        )

    heat_capacity = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K * normalized
    upper_bound = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K
    tolerance = 32.0 * np.finfo(np.float64).eps * upper_bound
    if (
        not np.all(np.isfinite(heat_capacity))
        or np.any(heat_capacity < -tolerance)
        or np.any(heat_capacity > upper_bound + tolerance)
    ):
        raise FloatingPointError("Debye heat capacity left its physical bounds")
    return np.asarray(np.clip(heat_capacity, 0.0, upper_bound), dtype=np.float64)


def debye_low_temperature_heat_capacity(
    temperature_k: ArrayLike,
    debye_temperature_k: ArrayLike,
) -> FloatArray:
    """Return the Debye T^3 low-temperature asymptote."""

    temperature = _finite_array(temperature_k, name="temperature_k")
    debye_temperature = _finite_array(
        debye_temperature_k,
        name="debye_temperature_k",
    )
    if np.any(temperature < 0.0):
        raise ValueError("temperature_k must be non-negative")
    if np.any(debye_temperature <= 0.0):
        raise ValueError("debye_temperature_k must be strictly positive")
    try:
        temperature, debye_temperature = np.broadcast_arrays(
            temperature,
            debye_temperature,
        )
    except ValueError as exc:
        raise ValueError(
            "temperature_k and debye_temperature_k must be broadcast-compatible"
        ) from exc
    return np.asarray(
        LOW_TEMPERATURE_COEFFICIENT
        * (temperature / debye_temperature) ** 3,
        dtype=np.float64,
    )


__all__ = [
    "DEBYE_INTEGRAL_INFINITY",
    "LOW_TEMPERATURE_COEFFICIENT",
    "debye_integral",
    "debye_low_temperature_heat_capacity",
    "debye_molar_heat_capacity",
]
