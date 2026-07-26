"""Independent Gauss–Legendre references for Klein–Nishina totals."""

from __future__ import annotations

import math
from numbers import Integral, Real

import numpy as np

from task09_compton_scattering.constants import (
    CLASSICAL_ELECTRON_RADIUS_M,
    ELECTRON_REST_ENERGY_KEV,
)


def _positive_scalar(value: Real, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return normalized


def reference_total_cross_section_m2(
    incident_energy_kev: Real,
    quadrature_order: Integral = 256,
) -> float:
    """Integrate d-sigma/d-Omega over mu=cos(theta) independently."""

    energy = _positive_scalar(incident_energy_kev, name="incident_energy_kev")
    if isinstance(quadrature_order, bool) or not isinstance(quadrature_order, Integral):
        raise TypeError("quadrature_order must be an integer")
    order = int(quadrature_order)
    if order < 32:
        raise ValueError("quadrature_order must be at least 32")
    mu, weights = np.polynomial.legendre.leggauss(order)
    alpha = energy / ELECTRON_REST_ENERGY_KEV
    ratio = 1.0 / (1.0 + alpha * (1.0 - mu))
    sine_squared = 1.0 - np.square(mu)
    differential = (
        0.5
        * CLASSICAL_ELECTRON_RADIUS_M**2
        * np.square(ratio)
        * (ratio + 1.0 / ratio - sine_squared)
    )
    return float(2.0 * math.pi * np.dot(weights, differential))


__all__ = ["reference_total_cross_section_m2"]
