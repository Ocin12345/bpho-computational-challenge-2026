"""Independent scalar reference calculations for Task 4.

This module deliberately uses only the Python standard library and decimal
text representations of the exact SI constants.  It must remain independent
of the NumPy implementation in :mod:`task04_photoelectric_effect.models`.
"""

from __future__ import annotations

import math
from decimal import Decimal, localcontext
from numbers import Real


_PLANCK_CONSTANT_J_S = Decimal("6.62607015e-34")
_ELEMENTARY_CHARGE_C = Decimal("1.602176634e-19")
_SPEED_OF_LIGHT_M_S = Decimal("299792458")
_NANOMETRES_PER_METRE = Decimal("1e9")
_REFERENCE_PRECISION = 50


def _decimal_scalar(
    value: Real,
    *,
    name: str,
    positive: bool = False,
    non_negative: bool = False,
) -> Decimal:
    """Validate one real scalar and convert it through decimal text."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if positive and normalized <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    if non_negative and normalized < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return Decimal(str(normalized))


def _finite_float(value: Decimal, *, name: str) -> float:
    """Convert a Decimal result to one finite binary float."""

    result = float(value)
    if not math.isfinite(result):
        raise FloatingPointError(f"{name} is not representable as a float")
    return result


def reference_common_gradient_v_s() -> float:
    """Return the independently calculated common gradient ``h/e``."""

    with localcontext() as context:
        context.prec = _REFERENCE_PRECISION
        value = _PLANCK_CONSTANT_J_S / _ELEMENTARY_CHARGE_C
    return _finite_float(value, name="reference common gradient")


def reference_cutoff_frequency_hz(work_function_ev: Real) -> float:
    """Return the independent threshold frequency ``e W / h``."""

    work_function = _decimal_scalar(
        work_function_ev,
        name="work_function_ev",
        positive=True,
    )
    with localcontext() as context:
        context.prec = _REFERENCE_PRECISION
        value = work_function * _ELEMENTARY_CHARGE_C / _PLANCK_CONSTANT_J_S
    return _finite_float(value, name="reference cutoff frequency")


def reference_cutoff_wavelength_nm(work_function_ev: Real) -> float:
    """Return the independent maximum emitting wavelength in nanometres."""

    work_function = _decimal_scalar(
        work_function_ev,
        name="work_function_ev",
        positive=True,
    )
    with localcontext() as context:
        context.prec = _REFERENCE_PRECISION
        value = (
            _PLANCK_CONSTANT_J_S
            * _SPEED_OF_LIGHT_M_S
            * _NANOMETRES_PER_METRE
            / (_ELEMENTARY_CHARGE_C * work_function)
        )
    return _finite_float(value, name="reference cutoff wavelength")


def reference_voltage_at_frequency_v(
    frequency_hz: Real,
    work_function_ev: Real,
) -> float:
    """Return signed stopping voltage at one frequency independently."""

    frequency = _decimal_scalar(
        frequency_hz,
        name="frequency_hz",
        non_negative=True,
    )
    work_function = _decimal_scalar(
        work_function_ev,
        name="work_function_ev",
        positive=True,
    )
    with localcontext() as context:
        context.prec = _REFERENCE_PRECISION
        value = (
            _PLANCK_CONSTANT_J_S * frequency / _ELEMENTARY_CHARGE_C
            - work_function
        )
    return _finite_float(value, name="reference frequency voltage")


def reference_voltage_at_wavelength_v(
    wavelength_nm: Real,
    work_function_ev: Real,
) -> float:
    """Return signed stopping voltage at one vacuum wavelength independently."""

    wavelength = _decimal_scalar(
        wavelength_nm,
        name="wavelength_nm",
        positive=True,
    )
    work_function = _decimal_scalar(
        work_function_ev,
        name="work_function_ev",
        positive=True,
    )
    with localcontext() as context:
        context.prec = _REFERENCE_PRECISION
        value = (
            _PLANCK_CONSTANT_J_S
            * _SPEED_OF_LIGHT_M_S
            * _NANOMETRES_PER_METRE
            / (_ELEMENTARY_CHARGE_C * wavelength)
            - work_function
        )
    return _finite_float(value, name="reference wavelength voltage")


__all__ = [
    "reference_common_gradient_v_s",
    "reference_cutoff_frequency_hz",
    "reference_cutoff_wavelength_nm",
    "reference_voltage_at_frequency_v",
    "reference_voltage_at_wavelength_v",
]
