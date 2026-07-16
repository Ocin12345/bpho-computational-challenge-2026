"""Vectorized photoelectric-effect equations for Task 4.

The functions in this module are deterministic and side-effect free. Source
materials, independent validation targets, plotting, and file output live in
separate modules.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task04_photoelectric_effect.constants import (
    ELEMENTARY_CHARGE_C,
    HC_OVER_CHARGE_V_M,
    PLANCK_CONSTANT_J_S,
    PLANCK_OVER_CHARGE_V_S,
)


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def _finite_float_array(value: ArrayLike, *, name: str) -> FloatArray:
    """Return ``value`` as a finite real float64 array."""

    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain real numbers, not booleans")

    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
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


def _non_negative_float_array(value: ArrayLike, *, name: str) -> FloatArray:
    """Return a finite float64 array whose entries are non-negative."""

    array = _finite_float_array(value, name=name)
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    return array


def _broadcast_inputs(
    independent_variable: FloatArray,
    work_function_ev: FloatArray,
    *,
    independent_name: str,
) -> tuple[FloatArray, FloatArray]:
    """Broadcast one independent variable against work function."""

    try:
        independent, work_function = np.broadcast_arrays(
            independent_variable,
            work_function_ev,
        )
    except ValueError as exc:
        raise ValueError(
            f"{independent_name} and work_function_ev must be "
            "broadcast-compatible"
        ) from exc
    return (
        np.asarray(independent, dtype=np.float64),
        np.asarray(work_function, dtype=np.float64),
    )


def _finite_result(value: FloatArray, *, name: str) -> FloatArray:
    """Require one calculated float64 result to remain representable."""

    result = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError(f"{name} is not representable as float64")
    return result


def cutoff_frequency_hz(work_function_ev: ArrayLike) -> FloatArray:
    """Return the threshold frequency ``e W_eV / h`` in hertz."""

    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    with np.errstate(over="ignore", under="ignore"):
        result = work_function * ELEMENTARY_CHARGE_C / PLANCK_CONSTANT_J_S
    result = _finite_result(result, name="cutoff frequency")
    if np.any(result <= 0.0):
        raise FloatingPointError("cutoff frequency underflowed to zero")
    return result


def cutoff_wavelength_m(work_function_ev: ArrayLike) -> FloatArray:
    """Return the longest photoemitting vacuum wavelength in metres."""

    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        result = HC_OVER_CHARGE_V_M / work_function
    result = _finite_result(result, name="cutoff wavelength")
    if np.any(result <= 0.0):
        raise FloatingPointError("cutoff wavelength underflowed to zero")
    return result


def linear_stopping_voltage_from_frequency(
    frequency_hz: ArrayLike,
    work_function_ev: ArrayLike,
) -> FloatArray:
    """Return signed ``(h/e) f - W_eV`` in volts."""

    frequency = _non_negative_float_array(frequency_hz, name="frequency_hz")
    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    frequency, work_function = _broadcast_inputs(
        frequency,
        work_function,
        independent_name="frequency_hz",
    )
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = PLANCK_OVER_CHARGE_V_S * frequency - work_function
    return _finite_result(result, name="frequency stopping voltage")


def linear_stopping_voltage_from_wavelength(
    wavelength_m: ArrayLike,
    work_function_ev: ArrayLike,
) -> FloatArray:
    """Return signed ``hc/(e wavelength) - W_eV`` in volts."""

    wavelength = _positive_float_array(wavelength_m, name="wavelength_m")
    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    wavelength, work_function = _broadcast_inputs(
        wavelength,
        work_function,
        independent_name="wavelength_m",
    )
    with np.errstate(over="ignore", under="ignore", divide="ignore"):
        result = HC_OVER_CHARGE_V_M / wavelength - work_function
    return _finite_result(result, name="wavelength stopping voltage")


def emission_possible_from_frequency(
    frequency_hz: ArrayLike,
    work_function_ev: ArrayLike,
) -> BoolArray:
    """Return ``True`` exactly where frequency reaches the cut-off."""

    frequency = _non_negative_float_array(frequency_hz, name="frequency_hz")
    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    frequency, work_function = _broadcast_inputs(
        frequency,
        work_function,
        independent_name="frequency_hz",
    )
    return np.asarray(
        frequency >= cutoff_frequency_hz(work_function),
        dtype=np.bool_,
    )


def emission_possible_from_wavelength(
    wavelength_m: ArrayLike,
    work_function_ev: ArrayLike,
) -> BoolArray:
    """Return ``True`` exactly where wavelength is at most the cut-off."""

    wavelength = _positive_float_array(wavelength_m, name="wavelength_m")
    work_function = _positive_float_array(
        work_function_ev,
        name="work_function_ev",
    )
    wavelength, work_function = _broadcast_inputs(
        wavelength,
        work_function,
        independent_name="wavelength_m",
    )
    return np.asarray(
        wavelength <= cutoff_wavelength_m(work_function),
        dtype=np.bool_,
    )


def physical_stopping_voltage_from_frequency(
    frequency_hz: ArrayLike,
    work_function_ev: ArrayLike,
) -> FloatArray:
    """Return non-negative voltage in-domain and ``NaN`` below threshold."""

    linear_voltage = linear_stopping_voltage_from_frequency(
        frequency_hz,
        work_function_ev,
    )
    mask = emission_possible_from_frequency(frequency_hz, work_function_ev)
    return np.asarray(
        np.where(mask, np.maximum(linear_voltage, 0.0), np.nan),
        dtype=np.float64,
    )


def physical_stopping_voltage_from_wavelength(
    wavelength_m: ArrayLike,
    work_function_ev: ArrayLike,
) -> FloatArray:
    """Return non-negative voltage in-domain and ``NaN`` above cut-off."""

    linear_voltage = linear_stopping_voltage_from_wavelength(
        wavelength_m,
        work_function_ev,
    )
    mask = emission_possible_from_wavelength(wavelength_m, work_function_ev)
    return np.asarray(
        np.where(mask, np.maximum(linear_voltage, 0.0), np.nan),
        dtype=np.float64,
    )


__all__ = [
    "cutoff_frequency_hz",
    "cutoff_wavelength_m",
    "emission_possible_from_frequency",
    "emission_possible_from_wavelength",
    "linear_stopping_voltage_from_frequency",
    "linear_stopping_voltage_from_wavelength",
    "physical_stopping_voltage_from_frequency",
    "physical_stopping_voltage_from_wavelength",
]
