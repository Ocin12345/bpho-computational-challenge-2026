"""Deterministic state inventories, radial nodes and display extents."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import factorial

import numpy as np

from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.models import (
    scaled_radial_probability,
    scaled_radial_wavefunction,
)


@dataclass(frozen=True)
class RadialProfile:
    """One immutable radial profile through a declared containment radius."""

    state: HydrogenicState
    containment_target: float
    extent_over_a: float
    radius_over_a: np.ndarray
    radius_over_n_squared_a: np.ndarray
    scaled_radial_wavefunction: np.ndarray
    scaled_radial_probability: np.ndarray
    cumulative_probability: np.ndarray


def _readonly(values: object) -> np.ndarray:
    result = np.array(values, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def supported_states() -> tuple[HydrogenicState, ...]:
    """Return all 204 validated real basis states through n=8."""

    return tuple(
        HydrogenicState(n, l, m)
        for n in range(1, 9)
        for l in range(n)
        for m in range(-l, l + 1)
    )


def distinct_radial_states() -> tuple[HydrogenicState, ...]:
    """Return one m=0 representative for each of the 36 n,l radial functions."""

    return tuple(
        HydrogenicState(n, l, 0)
        for n in range(1, 9)
        for l in range(n)
    )


def official_family_representatives() -> tuple[HydrogenicState, ...]:
    """Return 1s, 2p_z, 3d_z2, 4f_m0 and 5g_m0."""

    return tuple(HydrogenicState(l + 1, l, 0) for l in range(5))


def associated_laguerre_coefficients(order: int, alpha: int) -> np.ndarray:
    """Return ascending-power coefficients from the official factorial sum."""

    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise ValueError("order must be a non-negative integer")
    if isinstance(alpha, bool) or not isinstance(alpha, int) or alpha < 0:
        raise ValueError("alpha must be a non-negative integer")
    numerator = factorial(order + alpha)
    coefficients = [
        numerator
        * (-1) ** k
        / (
            factorial(alpha + k)
            * factorial(order - k)
            * factorial(k)
        )
        for k in range(order + 1)
    ]
    return _readonly(coefficients)


def radial_node_positions_over_a(state: HydrogenicState) -> np.ndarray:
    """Return positive radial nodes r/a from independent polynomial roots."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    order = state.radial_node_count
    if order == 0:
        return _readonly([])
    coefficients = associated_laguerre_coefficients(
        order, 2 * state.l + 1
    )
    roots = np.polynomial.polynomial.polyroots(coefficients)
    positive = sorted(
        float(root.real)
        for root in roots
        if abs(root.imag) <= 1e-10 and root.real > 0.0
    )
    if len(positive) != order:
        raise ArithmeticError(
            f"expected {order} positive nodes, found {len(positive)}"
        )
    return _readonly(0.5 * state.n * np.asarray(positive))


@lru_cache(maxsize=1)
def _cdf_quadrature() -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = np.polynomial.legendre.leggauss(160)
    return _readonly(nodes), _readonly(weights)


def radial_probability_cdf(
    state: HydrogenicState,
    radius_over_a: float,
) -> float:
    """Integrate the dimensionless radial probability from zero to r/a."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    radius = float(radius_over_a)
    if not np.isfinite(radius) or radius < 0.0:
        raise ValueError("radius_over_a must be finite and non-negative")
    if radius == 0.0:
        return 0.0
    nodes, weights = _cdf_quadrature()
    sample_radius = 0.5 * radius * (nodes + 1.0)
    probability = np.asarray(scaled_radial_probability(state, sample_radius))
    value = float(np.sum(weights * probability) * 0.5 * radius)
    return min(1.0, max(0.0, value))


def radial_containment_radius_over_a(
    state: HydrogenicState,
    probability: float = 0.9995,
) -> float:
    """Find the smallest radius containing the requested radial probability."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    probability = float(probability)
    if not np.isfinite(probability) or not 0.99 <= probability < 1.0:
        raise ValueError("probability must be finite and in [0.99, 1)")

    lower = 0.0
    upper = max(8.0, 2.0 * state.n**2)
    while radial_probability_cdf(state, upper) < probability:
        upper *= 1.5
        if upper > 40.0 * state.n**2:
            raise ArithmeticError("failed to bracket radial containment radius")

    for _ in range(60):
        midpoint = 0.5 * (lower + upper)
        if radial_probability_cdf(state, midpoint) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return 0.5 * (lower + upper)


def build_radial_profile(
    state: HydrogenicState,
    *,
    points: int = 1201,
    containment: float = 0.9995,
) -> RadialProfile:
    """Build a deterministic immutable radial profile."""

    if not isinstance(points, int) or isinstance(points, bool):
        raise TypeError("points must be an integer")
    if points < 501 or points % 2 == 0:
        raise ValueError("points must be odd and at least 501")
    extent = radial_containment_radius_over_a(state, containment)
    radius = np.linspace(0.0, extent, points)
    wavefunction = np.asarray(scaled_radial_wavefunction(state, radius))
    probability = np.asarray(scaled_radial_probability(state, radius))
    cumulative = np.zeros_like(radius)
    cumulative[1:] = np.cumsum(
        0.5
        * (probability[1:] + probability[:-1])
        * np.diff(radius)
    )
    return RadialProfile(
        state=state,
        containment_target=float(containment),
        extent_over_a=float(extent),
        radius_over_a=_readonly(radius),
        radius_over_n_squared_a=_readonly(radius / state.n**2),
        scaled_radial_wavefunction=_readonly(wavefunction),
        scaled_radial_probability=_readonly(probability),
        cumulative_probability=_readonly(cumulative),
    )
