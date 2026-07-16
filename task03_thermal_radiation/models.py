"""Vectorized physical models for Task 3.

Stage 4 implements only the Planck-spectrum API. Einstein-model functions will
be added in their dedicated implementation stage. This module has no plotting
or file-system side effects.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task03_thermal_radiation.constants import (
    METRES_PER_NANOMETRE,
    PLANCK_EXPONENT_CONSTANT_M_K,
    PLANCK_RADIANCE_PREFACTOR,
)


FloatArray = NDArray[np.float64]

_EXPONENT_BRANCH_POINT = 50.0
_LOG_MAX_FLOAT64 = float(np.log(np.finfo(np.float64).max))


def _finite_float_array(value: ArrayLike, *, name: str) -> FloatArray:
    """Return ``value`` as a finite float64 array.

    Boolean, complex, textual, and non-numeric object arrays are rejected
    rather than silently interpreted as physical measurements.
    """

    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real numbers, not complex values")

    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _positive_float_array(value: ArrayLike, *, name: str) -> FloatArray:
    """Return a finite float64 array whose entries are strictly positive."""

    array = _finite_float_array(value, name=name)
    if np.any(array <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    return array


def _broadcast_planck_inputs(
    wavelength_m: ArrayLike,
    temperature_k: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    """Validate and broadcast wavelength and temperature without mutation."""

    wavelength = _positive_float_array(wavelength_m, name="wavelength_m")
    temperature = _positive_float_array(temperature_k, name="temperature_k")

    try:
        wavelength, temperature = np.broadcast_arrays(wavelength, temperature)
    except ValueError as exc:
        raise ValueError(
            "wavelength_m and temperature_k must be broadcast-compatible"
        ) from exc

    return (
        np.asarray(wavelength, dtype=np.float64),
        np.asarray(temperature, dtype=np.float64),
    )


def planck_spectral_radiance(
    wavelength_m: ArrayLike,
    temperature_k: ArrayLike,
) -> FloatArray:
    """Return wavelength spectral radiance in W m^-3 sr^-1.

    Parameters
    ----------
    wavelength_m:
        Positive finite vacuum wavelength in metres.
    temperature_k:
        Positive finite absolute temperature in kelvin.

    Returns
    -------
    numpy.ndarray
        Float64 values with the broadcast shape of the two inputs. Scalar
        inputs produce a zero-dimensional array.

    Notes
    -----
    The mathematical model is

    ``B = (2 h c^2 / wavelength^5) / expm1(h c / wavelength k_B T)``.

    The occupation factor uses the two branches frozen in the mathematical
    specification. Radiance is assembled in logarithmic form to prevent a
    numerically indeterminate ``infinity * 0`` at very short wavelengths.
    """

    wavelength, temperature = _broadcast_planck_inputs(
        wavelength_m,
        temperature_k,
    )
    shape = wavelength.shape
    wavelength_flat = np.ravel(wavelength)
    temperature_flat = np.ravel(temperature)

    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        exponent = PLANCK_EXPONENT_CONSTANT_M_K / (
            wavelength_flat * temperature_flat
        )

    log_occupation = np.full(exponent.shape, -np.inf, dtype=np.float64)
    finite_exponent = np.isfinite(exponent)
    moderate = finite_exponent & (exponent <= _EXPONENT_BRANCH_POINT)
    large = finite_exponent & ~moderate

    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        log_occupation[moderate] = -np.log(np.expm1(exponent[moderate]))
        negative_exponential = np.exp(-exponent[large])
        log_occupation[large] = (
            -exponent[large] - np.log1p(-negative_exponential)
        )
        log_prefactor = (
            math.log(PLANCK_RADIANCE_PREFACTOR)
            - 5.0 * np.log(wavelength_flat)
        )

    log_radiance = log_prefactor + log_occupation
    if np.any(np.isnan(log_radiance)):
        raise FloatingPointError(
            "Planck radiance is not representable for the supplied inputs"
        )
    if np.any(log_radiance > _LOG_MAX_FLOAT64):
        raise FloatingPointError(
            "Planck radiance exceeds the float64 representable range"
        )

    with np.errstate(under="ignore"):
        radiance = np.exp(log_radiance)

    if not np.all(np.isfinite(radiance)) or np.any(radiance < 0.0):
        raise FloatingPointError("Planck radiance calculation was not finite")

    return np.asarray(radiance.reshape(shape), dtype=np.float64)


def planck_spectral_exitance(
    wavelength_m: ArrayLike,
    temperature_k: ArrayLike,
) -> FloatArray:
    """Return hemispherical spectral exitance in W m^-3.

    An ideal black body is Lambertian, so its spectral exitance is exactly
    ``pi`` times its spectral radiance.
    """

    radiance = planck_spectral_radiance(wavelength_m, temperature_k)
    exitance = math.pi * radiance
    if not np.all(np.isfinite(exitance)):
        raise FloatingPointError("Planck exitance exceeds float64 range")
    return np.asarray(exitance, dtype=np.float64)


def spectral_density_per_nanometre(
    density_per_metre: ArrayLike,
) -> FloatArray:
    """Convert a non-negative spectral density from per metre to per nm."""

    density = _finite_float_array(
        density_per_metre,
        name="density_per_metre",
    )
    if np.any(density < 0.0):
        raise ValueError("density_per_metre must be non-negative")
    converted = METRES_PER_NANOMETRE * density
    return np.asarray(converted, dtype=np.float64)


__all__ = [
    "planck_spectral_exitance",
    "planck_spectral_radiance",
    "spectral_density_per_nanometre",
]
