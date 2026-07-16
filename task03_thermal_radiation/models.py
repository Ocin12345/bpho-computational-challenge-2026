"""Vectorized physical models for Task 3.

The Planck-spectrum and Einstein-solid APIs are deterministic, vectorized, and
side-effect free. Plotting, validation targets, and file output live elsewhere.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    EINSTEIN_DEBYE_FACTOR,
    METRES_PER_NANOMETRE,
    MOLAR_GAS_CONSTANT_J_MOL_K,
    PLANCK_EXPONENT_CONSTANT_M_K,
    PLANCK_RADIANCE_PREFACTOR,
    PLANCK_CONSTANT_J_S,
)


FloatArray = NDArray[np.float64]

_EXPONENT_BRANCH_POINT = 50.0
_EINSTEIN_SERIES_BOUNDARY = 1.0e-3
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


def einstein_temperature_from_debye(
    debye_temperature_k: ArrayLike,
) -> FloatArray:
    """Convert positive Debye temperatures to Einstein temperatures in K."""

    debye_temperature = _positive_float_array(
        debye_temperature_k,
        name="debye_temperature_k",
    )
    einstein_temperature = EINSTEIN_DEBYE_FACTOR * debye_temperature
    if (
        not np.all(np.isfinite(einstein_temperature))
        or np.any(einstein_temperature <= 0.0)
    ):
        raise FloatingPointError(
            "Einstein temperature is not representable for the supplied input"
        )
    return np.asarray(einstein_temperature, dtype=np.float64)


def einstein_frequency_from_temperature(
    einstein_temperature_k: ArrayLike,
) -> FloatArray:
    """Return Einstein oscillator frequency in Hz from temperature in K."""

    einstein_temperature = _positive_float_array(
        einstein_temperature_k,
        name="einstein_temperature_k",
    )
    with np.errstate(over="ignore", under="ignore"):
        frequency = (
            BOLTZMANN_CONSTANT_J_K
            * einstein_temperature
            / PLANCK_CONSTANT_J_S
        )
    if not np.all(np.isfinite(frequency)) or np.any(frequency <= 0.0):
        raise FloatingPointError(
            "Einstein frequency is not representable for the supplied input"
        )
    return np.asarray(frequency, dtype=np.float64)


def _broadcast_einstein_inputs(
    temperature_k: ArrayLike,
    einstein_temperature_k: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    """Validate and broadcast heat-capacity inputs without mutation."""

    temperature = _finite_float_array(temperature_k, name="temperature_k")
    if np.any(temperature < 0.0):
        raise ValueError("temperature_k must be non-negative")
    einstein_temperature = _positive_float_array(
        einstein_temperature_k,
        name="einstein_temperature_k",
    )

    try:
        temperature, einstein_temperature = np.broadcast_arrays(
            temperature,
            einstein_temperature,
        )
    except ValueError as exc:
        raise ValueError(
            "temperature_k and einstein_temperature_k must be "
            "broadcast-compatible"
        ) from exc

    return (
        np.asarray(temperature, dtype=np.float64),
        np.asarray(einstein_temperature, dtype=np.float64),
    )


def einstein_molar_heat_capacity(
    temperature_k: ArrayLike,
    einstein_temperature_k: ArrayLike,
) -> FloatArray:
    """Return Einstein constant-volume molar heat capacity in J mol^-1 K^-1.

    ``temperature_k`` may include zero, where the continuous limiting value is
    assigned exactly. Positive temperatures use ``x = T_E / T``. For
    ``x < 1e-3`` a high-temperature series prevents cancellation; all other
    finite ratios use a logarithmic version of the stable negative-exponential
    expression. Infinite ratios caused by a representable very small
    temperature correctly give zero heat capacity.
    """

    temperature, einstein_temperature = _broadcast_einstein_inputs(
        temperature_k,
        einstein_temperature_k,
    )
    shape = temperature.shape
    temperature_flat = np.ravel(temperature)
    einstein_temperature_flat = np.ravel(einstein_temperature)

    ratio = np.full(temperature_flat.shape, np.inf, dtype=np.float64)
    positive_temperature = temperature_flat > 0.0
    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        np.divide(
            einstein_temperature_flat,
            temperature_flat,
            out=ratio,
            where=positive_temperature,
        )

    normalized_capacity = np.zeros(ratio.shape, dtype=np.float64)
    finite_ratio = positive_temperature & np.isfinite(ratio)
    series = finite_ratio & (ratio < _EINSTEIN_SERIES_BOUNDARY)
    regular = finite_ratio & ~series

    ratio_series = ratio[series]
    ratio_series_squared = ratio_series * ratio_series
    normalized_capacity[series] = (
        1.0
        - ratio_series_squared / 12.0
        + ratio_series_squared * ratio_series_squared / 240.0
    )

    ratio_regular = ratio[regular]
    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        denominator = -np.expm1(-ratio_regular)
        log_normalized_capacity = (
            2.0 * np.log(ratio_regular)
            - ratio_regular
            - 2.0 * np.log(denominator)
        )
        normalized_capacity[regular] = np.exp(log_normalized_capacity)

    heat_capacity = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K * normalized_capacity
    upper_bound = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K
    if (
        not np.all(np.isfinite(heat_capacity))
        or np.any(heat_capacity < 0.0)
        or np.any(heat_capacity > upper_bound)
    ):
        raise FloatingPointError(
            "Einstein heat capacity calculation left its physical bounds"
        )

    return np.asarray(heat_capacity.reshape(shape), dtype=np.float64)


__all__ = [
    "einstein_frequency_from_temperature",
    "einstein_molar_heat_capacity",
    "einstein_temperature_from_debye",
    "planck_spectral_exitance",
    "planck_spectral_radiance",
    "spectral_density_per_nanometre",
]
