"""Numerically independent scalar reference calculations for Task 6."""

from __future__ import annotations

import math
from decimal import Decimal, localcontext
from numbers import Integral, Real

from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG_STRING,
    ELEMENTARY_CHARGE_C_STRING,
    PLANCK_CONSTANT_J_S_STRING,
)


REFERENCE_PRECISION = 60


def _decimal_real(value: Real | Decimal, *, name: str, positive: bool = True) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise TypeError(f"{name} must be a real number")
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    if positive and decimal_value <= 0:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _positive_integer(value: Integral, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 1:
        raise ValueError(f"{name} must be positive")
    return normalized


def reference_momentum_kg_m_s(voltage_v: Real | Decimal) -> float:
    """Return a 60-digit Decimal momentum reference as a float."""

    voltage = _decimal_real(voltage_v, name="voltage_v")
    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        return float((Decimal(2) * mass * charge * voltage).sqrt())


def reference_wavelength_m(voltage_v: Real | Decimal) -> float:
    """Return a 60-digit Decimal de Broglie wavelength reference."""

    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        planck = Decimal(PLANCK_CONSTANT_J_S_STRING)
        voltage = _decimal_real(voltage_v, name="voltage_v")
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        momentum = (Decimal(2) * mass * charge * voltage).sqrt()
        return float(planck / momentum)


def reference_bragg_ratio(
    voltage_v: Real | Decimal,
    spacing_m: Real | Decimal,
    order_n: Integral,
) -> float:
    """Return q through an independent Decimal path."""

    spacing = _decimal_real(spacing_m, name="spacing_m")
    order = _positive_integer(order_n, name="order_n")
    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        voltage = _decimal_real(voltage_v, name="voltage_v")
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        planck = Decimal(PLANCK_CONSTANT_J_S_STRING)
        exact_wavelength = planck / (Decimal(2) * mass * charge * voltage).sqrt()
        return float(Decimal(order) * exact_wavelength / (Decimal(2) * spacing))


def reference_maximum_bragg_order(
    voltage_v: Real | Decimal,
    spacing_m: Real | Decimal,
) -> int:
    """Return floor(2d/lambda) through Decimal arithmetic."""

    spacing = _decimal_real(spacing_m, name="spacing_m")
    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        voltage = _decimal_real(voltage_v, name="voltage_v")
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        planck = Decimal(PLANCK_CONSTANT_J_S_STRING)
        wavelength = planck / (Decimal(2) * mass * charge * voltage).sqrt()
        return int((Decimal(2) * spacing / wavelength).to_integral_value(rounding="ROUND_FLOOR"))


def reference_maximum_screen_order(
    voltage_v: Real | Decimal,
    spacing_m: Real | Decimal,
) -> int:
    """Return floor(sqrt(2)d/lambda) through Decimal arithmetic."""

    spacing = _decimal_real(spacing_m, name="spacing_m")
    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        voltage = _decimal_real(voltage_v, name="voltage_v")
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        planck = Decimal(PLANCK_CONSTANT_J_S_STRING)
        wavelength = planck / (Decimal(2) * mass * charge * voltage).sqrt()
        raw = Decimal(2).sqrt() * spacing / wavelength
        return int(raw.to_integral_value(rounding="ROUND_FLOOR"))


def reference_fit_gradient_v_inv_sqrt(
    spacing_m: Real | Decimal,
    order_n: Integral = 1,
) -> float:
    """Return the official line gradient through Decimal arithmetic."""

    spacing = _decimal_real(spacing_m, name="spacing_m")
    order = _positive_integer(order_n, name="order_n")
    with localcontext() as context:
        context.prec = REFERENCE_PRECISION
        mass = Decimal(ELECTRON_MASS_KG_STRING)
        charge = Decimal(ELEMENTARY_CHARGE_C_STRING)
        planck = Decimal(PLANCK_CONSTANT_J_S_STRING)
        numerator = Decimal(2) * spacing * (Decimal(2) * mass * charge).sqrt()
        return float(numerator / (Decimal(order) * planck))


def reference_first_order_anchor(
    voltage_v: Real | Decimal,
    spacing_m: Real | Decimal,
    tube_radius_m: Real | Decimal,
) -> tuple[float, float, float]:
    """Return wavelength, phi, and photographic radius through a scalar path."""

    radius = float(_decimal_real(tube_radius_m, name="tube_radius_m"))
    wavelength = reference_wavelength_m(voltage_v)
    ratio = reference_bragg_ratio(voltage_v, spacing_m, 1)
    if ratio > 1.0:
        raise ValueError("first order is outside the Bragg domain")
    phi = 2.0 * math.asin(ratio)
    photo_radius = radius * math.sin(2.0 * phi)
    return wavelength, phi, photo_radius


__all__ = [
    "REFERENCE_PRECISION",
    "reference_bragg_ratio",
    "reference_first_order_anchor",
    "reference_fit_gradient_v_inv_sqrt",
    "reference_maximum_bragg_order",
    "reference_maximum_screen_order",
    "reference_momentum_kg_m_s",
    "reference_wavelength_m",
]
