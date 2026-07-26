"""Pure vectorized equations for the Task 6 electron-diffraction model."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task06_electron_diffraction.configuration import DEFAULT_CONFIGURATION
from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    INV_SQRT_TWO,
    PLANCK_CONSTANT_J_S,
)


FloatArray = NDArray[np.float64]
IntegerArray = NDArray[np.int64]
BooleanArray = NDArray[np.bool_]


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


def _voltage_array(value: ArrayLike) -> FloatArray:
    voltage = _real_array(value, name="voltage_v", positive=True)
    if np.any(voltage < DEFAULT_CONFIGURATION.voltage_min_v) or np.any(
        voltage > DEFAULT_CONFIGURATION.voltage_max_v
    ):
        raise ValueError("voltage_v must be within 1000 to 5000 V inclusive")
    return voltage


def _positive_integer_array(value: ArrayLike, *, name: str) -> IntegerArray:
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


def electron_momentum_kg_m_s(voltage_v: ArrayLike) -> FloatArray:
    """Return non-relativistic electron momentum after acceleration."""

    voltage = _voltage_array(voltage_v)
    return np.asarray(
        np.sqrt(2.0 * ELECTRON_MASS_KG * ELEMENTARY_CHARGE_C * voltage),
        dtype=np.float64,
    )


def electron_wavelength_m(voltage_v: ArrayLike) -> FloatArray:
    """Return the official non-relativistic de Broglie wavelength."""

    return np.asarray(
        PLANCK_CONSTANT_J_S / electron_momentum_kg_m_s(voltage_v),
        dtype=np.float64,
    )


def _diffraction_arrays(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> tuple[FloatArray, FloatArray, IntegerArray]:
    voltage = _voltage_array(voltage_v)
    spacing = _real_array(spacing_m, name="spacing_m", positive=True)
    order = _positive_integer_array(order_n, name="order_n")
    try:
        voltage_b, spacing_b, order_b = np.broadcast_arrays(voltage, spacing, order)
    except ValueError as exc:
        raise ValueError(
            "voltage_v, spacing_m, and order_n must be broadcast-compatible"
        ) from exc
    return (
        np.asarray(voltage_b, dtype=np.float64),
        np.asarray(spacing_b, dtype=np.float64),
        np.asarray(order_b, dtype=np.int64),
    )


def bragg_ratio(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> FloatArray:
    """Return q = n lambda / (2d) without imposing the Bragg domain."""

    voltage, spacing, order = _diffraction_arrays(voltage_v, spacing_m, order_n)
    wavelength = electron_wavelength_m(voltage)
    return np.asarray(order.astype(np.float64) * wavelength / (2.0 * spacing), dtype=np.float64)


def _allowed_bragg_ratio(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> FloatArray:
    ratio = bragg_ratio(voltage_v, spacing_m, order_n)
    if np.any(ratio > 1.0):
        raise ValueError("requested diffraction order is outside the Bragg domain")
    return ratio


def bragg_angle_rad(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> FloatArray:
    """Return the Bragg angle theta in radians for allowed orders."""

    return np.asarray(np.arcsin(_allowed_bragg_ratio(voltage_v, spacing_m, order_n)), dtype=np.float64)


def scattering_angle_rad(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> FloatArray:
    """Return the total scattering angle phi = 2 theta in radians."""

    return np.asarray(2.0 * bragg_angle_rad(voltage_v, spacing_m, order_n), dtype=np.float64)


def _radius_array(value: ArrayLike) -> FloatArray:
    return _real_array(value, name="tube_radius_m", positive=True)


def photo_ring_radius_m(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
    tube_radius_m: ArrayLike,
) -> FloatArray:
    """Return signed photographic projection x = r sin(2 phi)."""

    phi = scattering_angle_rad(voltage_v, spacing_m, order_n)
    radius = _radius_array(tube_radius_m)
    try:
        phi_b, radius_b = np.broadcast_arrays(phi, radius)
    except ValueError as exc:
        raise ValueError("tube_radius_m must broadcast with diffraction inputs") from exc
    return np.asarray(radius_b * np.sin(2.0 * phi_b), dtype=np.float64)


def caliper_diameter_m(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
    tube_radius_m: ArrayLike,
) -> FloatArray:
    """Return full caliper chord y = 2r sin(phi)."""

    phi = scattering_angle_rad(voltage_v, spacing_m, order_n)
    radius = _radius_array(tube_radius_m)
    try:
        phi_b, radius_b = np.broadcast_arrays(phi, radius)
    except ValueError as exc:
        raise ValueError("tube_radius_m must broadcast with diffraction inputs") from exc
    return np.asarray(2.0 * radius_b * np.sin(phi_b), dtype=np.float64)


def _maximum_order_base(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    *,
    multiplier: float,
) -> IntegerArray:
    voltage = _voltage_array(voltage_v)
    spacing = _real_array(spacing_m, name="spacing_m", positive=True)
    try:
        voltage_b, spacing_b = np.broadcast_arrays(voltage, spacing)
    except ValueError as exc:
        raise ValueError("voltage_v and spacing_m must be broadcast-compatible") from exc
    raw = multiplier * spacing_b / electron_wavelength_m(voltage_b)
    return np.asarray(np.floor(raw), dtype=np.int64)


def maximum_bragg_order(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
) -> IntegerArray:
    """Return floor(2d/lambda), the official maximum Bragg order."""

    return _maximum_order_base(voltage_v, spacing_m, multiplier=2.0)


def maximum_screen_order(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
) -> IntegerArray:
    """Return floor(sqrt(2)d/lambda), the maximum forward-screen order."""

    return _maximum_order_base(voltage_v, spacing_m, multiplier=np.sqrt(2.0))


def screen_visible(
    voltage_v: ArrayLike,
    spacing_m: ArrayLike,
    order_n: ArrayLike,
) -> BooleanArray:
    """Return whether an allowed order lands on the forward hemisphere."""

    return np.asarray(
        _allowed_bragg_ratio(voltage_v, spacing_m, order_n) <= INV_SQRT_TWO,
        dtype=np.bool_,
    )


__all__ = [
    "bragg_angle_rad",
    "bragg_ratio",
    "caliper_diameter_m",
    "electron_momentum_kg_m_s",
    "electron_wavelength_m",
    "maximum_bragg_order",
    "maximum_screen_order",
    "photo_ring_radius_m",
    "scattering_angle_rad",
    "screen_visible",
]
