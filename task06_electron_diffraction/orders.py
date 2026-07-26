"""Deterministic enumeration helpers for Task 6 diffraction orders."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


IntegerArray = NDArray[np.int64]


def enumerate_order_indices(
    maximum_orders: ArrayLike,
) -> tuple[IntegerArray, IntegerArray, IntegerArray]:
    """Return voltage, spacing, and order arrays in frozen row order."""

    raw = np.asarray(maximum_orders)
    if not np.issubdtype(raw.dtype, np.integer):
        raise TypeError("maximum_orders must contain integers")
    maximum = np.asarray(maximum_orders, dtype=np.int64)
    if maximum.ndim != 2:
        raise ValueError("maximum_orders must be a two-dimensional array")
    if np.any(maximum < 1):
        raise ValueError("every maximum order must be positive")

    voltage_indices: list[int] = []
    spacing_indices: list[int] = []
    orders: list[int] = []
    for voltage_index in range(maximum.shape[0]):
        for spacing_index in range(maximum.shape[1]):
            maximum_order = int(maximum[voltage_index, spacing_index])
            voltage_indices.extend([voltage_index] * maximum_order)
            spacing_indices.extend([spacing_index] * maximum_order)
            orders.extend(range(1, maximum_order + 1))

    return (
        np.asarray(voltage_indices, dtype=np.int64),
        np.asarray(spacing_indices, dtype=np.int64),
        np.asarray(orders, dtype=np.int64),
    )


def order_status_labels(screen_visible_flags: ArrayLike) -> tuple[str, ...]:
    """Return controlled immutable labels for visibility flags."""

    flags = np.asarray(screen_visible_flags)
    if flags.dtype != np.bool_:
        raise TypeError("screen_visible_flags must be boolean")
    return tuple(
        "forward_screen" if bool(flag) else "back_scattering"
        for flag in flags.flat
    )


__all__ = ["enumerate_order_indices", "order_status_labels"]
