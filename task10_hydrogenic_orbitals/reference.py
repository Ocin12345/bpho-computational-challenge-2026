"""Independent scalar reference formulas for Task 10."""

from __future__ import annotations

from math import acos, atan2, cos, exp, factorial, isfinite, lgamma, log, pi, sin, sqrt

from task10_hydrogenic_orbitals.configuration import HydrogenicState


def reference_associated_laguerre(
    order: int,
    alpha: int,
    x: float,
) -> float:
    """Evaluate the official finite factorial sum."""

    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise ValueError("order must be a non-negative integer")
    if isinstance(alpha, bool) or not isinstance(alpha, int) or alpha < 0:
        raise ValueError("alpha must be a non-negative integer")
    x = float(x)
    if not isfinite(x):
        raise ValueError("x must be a finite real scalar")

    total = 0.0
    upper_factorial = factorial(order + alpha)
    for k in range(order + 1):
        total += (
            upper_factorial
            * (-x) ** k
            / (
                factorial(alpha + k)
                * factorial(order - k)
                * factorial(k)
            )
        )
    return total


def _legendre_derivative_scalar(l: int, m: int, x: float) -> float:
    """Return the m-th derivative of P_l from its explicit power series."""

    total = 0.0
    for k in range(l // 2 + 1):
        power = l - 2 * k
        if power < m:
            continue
        coefficient = (
            (-1) ** k
            * factorial(2 * l - 2 * k)
            / (
                2**l
                * factorial(k)
                * factorial(l - k)
                * factorial(power)
            )
        )
        derivative_factor = factorial(power) / factorial(power - m)
        total += coefficient * derivative_factor * x ** (power - m)
    return total


def reference_associated_ferrers(l: int, m: int, x: float) -> float:
    """Evaluate the sign-free Ferrers function by differentiating P_l."""

    if isinstance(l, bool) or not isinstance(l, int) or l < 0:
        raise ValueError("l must be a non-negative integer")
    if isinstance(m, bool) or not isinstance(m, int) or not 0 <= m <= l:
        raise ValueError("m must satisfy 0 <= m <= l")
    x = float(x)
    if not isfinite(x) or not -1.0 <= x <= 1.0:
        raise ValueError("x must be finite and in [-1, 1]")
    return (max(0.0, 1.0 - x * x) ** (0.5 * m)) * (
        _legendre_derivative_scalar(l, m, x)
    )


def reference_real_spherical_harmonic(
    l: int,
    m: int,
    polar_angle_rad: float,
    azimuth_rad: float,
) -> float:
    """Independent normalized real harmonic."""

    if isinstance(l, bool) or not isinstance(l, int) or l < 0:
        raise ValueError("l must be a non-negative integer")
    if isinstance(m, bool) or not isinstance(m, int) or abs(m) > l:
        raise ValueError("m must satisfy -l <= m <= l")
    polar = float(polar_angle_rad)
    azimuth = float(azimuth_rad)
    if not isfinite(polar) or not 0.0 <= polar <= pi:
        raise ValueError("polar_angle_rad must be finite and in [0, pi]")
    if not isfinite(azimuth):
        raise ValueError("azimuth_rad must be finite")
    m_abs = abs(m)
    normalization = exp(
        0.5
        * (
            log(2 * l + 1)
            - log(4 * pi)
            + lgamma(l - m_abs + 1)
            - lgamma(l + m_abs + 1)
        )
    )
    ferrers = reference_associated_ferrers(l, m_abs, cos(polar))
    if m < 0:
        return sqrt(2.0) * normalization * ferrers * sin(m_abs * azimuth)
    if m == 0:
        return normalization * ferrers
    return sqrt(2.0) * normalization * ferrers * cos(m * azimuth)


def reference_scaled_radial_wavefunction(
    state: HydrogenicState,
    radius_over_a: float,
) -> float:
    """Independent direct-sum a^(3/2) R_nl."""

    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    radius = float(radius_over_a)
    if not isfinite(radius) or radius < 0.0:
        raise ValueError("radius_over_a must be finite and non-negative")
    order = state.n - state.l - 1
    alpha = 2 * state.l + 1
    rho = 2.0 * radius / state.n
    prefactor = sqrt(
        factorial(order) / (2.0 * state.n * factorial(state.n + state.l))
    ) * (2.0 / state.n) ** 1.5
    return (
        prefactor
        * exp(-0.5 * rho)
        * rho**state.l
        * reference_associated_laguerre(order, alpha, rho)
    )


def reference_scaled_wavefunction_cartesian(
    state: HydrogenicState,
    x_over_a: float,
    y_over_a: float,
    z_over_a: float,
) -> float:
    """Independent scalar Cartesian a^(3/2) psi."""

    x = float(x_over_a)
    y = float(y_over_a)
    z = float(z_over_a)
    if not all(isfinite(value) for value in (x, y, z)):
        raise ValueError("Cartesian coordinates must be finite")
    radius = sqrt(x * x + y * y + z * z)
    if radius == 0.0:
        polar = 0.0
        azimuth = 0.0
    else:
        polar = acos(max(-1.0, min(1.0, z / radius)))
        azimuth = atan2(y, x)
    return reference_scaled_radial_wavefunction(
        state, radius
    ) * reference_real_spherical_harmonic(
        state.l, state.m, polar, azimuth
    )


def analytic_1s_scaled_density(radius_over_a: float) -> float:
    radius = float(radius_over_a)
    if not isfinite(radius) or radius < 0.0:
        raise ValueError("radius_over_a must be finite and non-negative")
    return exp(-2.0 * radius) / pi


def analytic_2s_scaled_density(radius_over_a: float) -> float:
    radius = float(radius_over_a)
    if not isfinite(radius) or radius < 0.0:
        raise ValueError("radius_over_a must be finite and non-negative")
    return (2.0 - radius) ** 2 * exp(-radius) / (32.0 * pi)


def analytic_2pz_scaled_density(
    radius_over_a: float,
    polar_angle_rad: float,
) -> float:
    radius = float(radius_over_a)
    polar = float(polar_angle_rad)
    if (
        not isfinite(radius)
        or radius < 0.0
        or not isfinite(polar)
        or not 0.0 <= polar <= pi
    ):
        raise ValueError("invalid radius or polar angle")
    return (
        radius**2
        * exp(-radius)
        * cos(polar) ** 2
        / (32.0 * pi)
    )
