"""Finite wells, tunnelling and wave-packet dynamics for BPhO Task 7.

The official infinite-well stationary states remain the reference model.  This
extension relaxes two idealisations: finite walls admit evanescent tails and
barrier transmission, while a Gaussian packet expanded in the exact infinite-
well basis exhibits interference, spreading and quantum revival.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq

from task07_particle_in_box.constants import (
    ELECTRONVOLT_J,
    ELECTRON_MASS_KG,
    REDUCED_PLANCK_CONSTANT_J_S,
)
from task07_particle_in_box.models import energy_j, spatial_wavefunction_m_neg_half


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class FiniteWellState:
    """One bound state of a centred finite square well."""

    index: int
    parity: str
    z: float
    energy_above_bottom_ev: float
    binding_energy_ev: float
    wavenumber_per_m: float
    decay_constant_per_m: float


@dataclass(frozen=True)
class WavePacketEvolution:
    """Basis-expanded wave packet on a supplied position/time grid."""

    position_m: FloatArray
    time_s: FloatArray
    wavefunction_m_neg_half: ComplexArray
    probability_density_m_inv: FloatArray
    norm: FloatArray
    expected_position_m: FloatArray
    basis_coefficients: ComplexArray
    revival_time_s: float


def finite_square_well_states(
    width_m: float,
    barrier_height_ev: float,
    *,
    particle_mass_kg: float = ELECTRON_MASS_KG,
) -> tuple[FiniteWellState, ...]:
    """Solve the even/odd transcendental equations for every bound state."""

    width = float(width_m)
    height_ev = float(barrier_height_ev)
    mass = float(particle_mass_kg)
    if not np.isfinite(width) or width <= 0.0:
        raise ValueError("width_m must be finite and positive")
    if not np.isfinite(height_ev) or height_ev <= 0.0:
        raise ValueError("barrier_height_ev must be finite and positive")
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("particle_mass_kg must be finite and positive")
    half_width = width / 2.0
    height_j = height_ev * ELECTRONVOLT_J
    z0 = half_width * np.sqrt(2.0 * mass * height_j) / REDUCED_PLANCK_CONSTANT_J_S
    epsilon = 1.0e-10
    roots: list[tuple[float, str]] = []

    def root_in_interval(left: float, right: float, parity: str) -> None:
        lower = max(left + epsilon, epsilon)
        upper = min(right - epsilon, z0 - epsilon)
        if upper <= lower:
            return

        def equation(z: float) -> float:
            outside = np.sqrt(max(z0**2 - z**2, 0.0))
            if parity == "even":
                return z * np.tan(z) - outside
            return -z / np.tan(z) - outside

        lower_value, upper_value = equation(lower), equation(upper)
        if lower_value == 0.0:
            root = lower
        elif upper_value == 0.0:
            root = upper
        elif lower_value * upper_value > 0.0:
            return
        else:
            root = brentq(equation, lower, upper, xtol=1.0e-14, rtol=1.0e-14)
        roots.append((float(root), parity))

    maximum_interval = int(np.ceil(z0 / np.pi)) + 1
    for interval in range(maximum_interval):
        root_in_interval(interval * np.pi, interval * np.pi + np.pi / 2.0, "even")
        root_in_interval(
            interval * np.pi + np.pi / 2.0,
            (interval + 1) * np.pi,
            "odd",
        )
    roots.sort(key=lambda item: item[0])
    states: list[FiniteWellState] = []
    for index, (z, parity) in enumerate(roots, start=1):
        energy_joule = REDUCED_PLANCK_CONSTANT_J_S**2 * z**2 / (
            2.0 * mass * half_width**2
        )
        k = z / half_width
        kappa = np.sqrt(2.0 * mass * (height_j - energy_joule)) / REDUCED_PLANCK_CONSTANT_J_S
        states.append(
            FiniteWellState(
                index=index,
                parity=parity,
                z=z,
                energy_above_bottom_ev=float(energy_joule / ELECTRONVOLT_J),
                binding_energy_ev=float(energy_joule / ELECTRONVOLT_J - height_ev),
                wavenumber_per_m=float(k),
                decay_constant_per_m=float(kappa),
            )
        )
    return tuple(states)


def finite_well_wavefunction_m_neg_half(
    position_m: ArrayLike,
    state: FiniteWellState,
    width_m: float,
) -> FloatArray:
    """Return an analytically normalized finite-well bound eigenfunction."""

    if not isinstance(state, FiniteWellState):
        raise TypeError("state must be a FiniteWellState")
    position = np.asarray(position_m, dtype=np.float64)
    if np.any(~np.isfinite(position)):
        raise ValueError("position_m must be finite")
    width = float(width_m)
    if not np.isfinite(width) or width <= 0.0:
        raise ValueError("width_m must be positive")
    a = width / 2.0
    k, kappa = state.wavenumber_per_m, state.decay_constant_per_m
    inside = np.abs(position) <= a
    values = np.empty(position.shape, dtype=np.float64)
    if state.parity == "even":
        inside_integral = a + np.sin(2.0 * k * a) / (2.0 * k)
        outside_integral = np.cos(k * a) ** 2 / kappa
        normalization = 1.0 / np.sqrt(inside_integral + outside_integral)
        values[inside] = normalization * np.cos(k * position[inside])
        values[~inside] = (
            normalization
            * np.cos(k * a)
            * np.exp(-kappa * (np.abs(position[~inside]) - a))
        )
    elif state.parity == "odd":
        inside_integral = a - np.sin(2.0 * k * a) / (2.0 * k)
        outside_integral = np.sin(k * a) ** 2 / kappa
        normalization = 1.0 / np.sqrt(inside_integral + outside_integral)
        values[inside] = normalization * np.sin(k * position[inside])
        values[~inside] = (
            normalization
            * np.sign(position[~inside])
            * np.sin(k * a)
            * np.exp(-kappa * (np.abs(position[~inside]) - a))
        )
    else:
        raise ValueError("state parity must be even or odd")
    return values


def rectangular_barrier_transmission(
    energy_ev: ArrayLike,
    barrier_height_ev: float,
    barrier_width_m: float,
    *,
    particle_mass_kg: float = ELECTRON_MASS_KG,
) -> FloatArray:
    """Return exact 1D rectangular-barrier transmission for E > 0."""

    energy = np.asarray(energy_ev, dtype=np.float64)
    height = float(barrier_height_ev)
    width = float(barrier_width_m)
    mass = float(particle_mass_kg)
    if np.any(~np.isfinite(energy)) or np.any(energy <= 0.0):
        raise ValueError("energy_ev must be finite and positive")
    if height <= 0.0 or width <= 0.0 or mass <= 0.0:
        raise ValueError("height, width and mass must be positive")
    result = np.empty(energy.shape, dtype=np.float64)
    below = energy < height
    above = energy > height
    equal = ~(below | above)
    if np.any(below):
        e_j = energy[below] * ELECTRONVOLT_J
        difference_j = (height - energy[below]) * ELECTRONVOLT_J
        kappa = np.sqrt(2.0 * mass * difference_j) / REDUCED_PLANCK_CONSTANT_J_S
        argument = np.minimum(kappa * width, 350.0)
        denominator = 1.0 + (
            height**2
            * np.sinh(argument) ** 2
            / (4.0 * energy[below] * (height - energy[below]))
        )
        result[below] = 1.0 / denominator
    if np.any(above):
        q = np.sqrt(
            2.0 * mass * (energy[above] - height) * ELECTRONVOLT_J
        ) / REDUCED_PLANCK_CONSTANT_J_S
        denominator = 1.0 + (
            height**2
            * np.sin(q * width) ** 2
            / (4.0 * energy[above] * (energy[above] - height))
        )
        result[above] = 1.0 / denominator
    if np.any(equal):
        factor = mass * height * ELECTRONVOLT_J * width**2 / (
            2.0 * REDUCED_PLANCK_CONSTANT_J_S**2
        )
        result[equal] = 1.0 / (1.0 + factor)
    return np.asarray(np.clip(result, 0.0, 1.0), dtype=np.float64)


def gaussian_wavepacket_evolution(
    position_m: ArrayLike,
    time_s: ArrayLike,
    *,
    box_width_m: float,
    centre_m: float,
    spatial_sigma_m: float,
    mean_wavenumber_per_m: float,
    maximum_state: int = 160,
    particle_mass_kg: float = ELECTRON_MASS_KG,
) -> WavePacketEvolution:
    """Expand a truncated Gaussian packet in exact infinite-well eigenstates."""

    position = np.asarray(position_m, dtype=np.float64)
    times = np.asarray(time_s, dtype=np.float64)
    width, centre, sigma, wave_number, mass = (
        float(box_width_m),
        float(centre_m),
        float(spatial_sigma_m),
        float(mean_wavenumber_per_m),
        float(particle_mass_kg),
    )
    if position.ndim != 1 or position.size < 101 or np.any(~np.isfinite(position)):
        raise ValueError("position_m must be a finite 1D grid with at least 101 points")
    if times.ndim != 1 or times.size < 1 or np.any(~np.isfinite(times)):
        raise ValueError("time_s must be a non-empty finite 1D grid")
    if np.any(np.diff(position) <= 0.0) or position[0] < 0.0 or position[-1] > width:
        raise ValueError("position grid must increase within [0, box_width_m]")
    if width <= 0.0 or sigma <= 0.0 or mass <= 0.0:
        raise ValueError("width, sigma and mass must be positive")
    if not 0.0 < centre < width:
        raise ValueError("centre_m must lie inside the box")
    if isinstance(maximum_state, bool) or int(maximum_state) < 2:
        raise ValueError("maximum_state must be an integer of at least two")
    levels = np.arange(1, int(maximum_state) + 1, dtype=np.int64)
    initial = np.exp(
        -((position - centre) ** 2) / (4.0 * sigma**2)
        + 1.0j * wave_number * position
    )
    initial /= np.sqrt(np.trapezoid(np.abs(initial) ** 2, position))
    basis = spatial_wavefunction_m_neg_half(
        position[None, :], levels[:, None], width
    )
    coefficients = np.trapezoid(basis * initial[None, :], position, axis=1)
    coefficients /= np.sqrt(np.sum(np.abs(coefficients) ** 2))
    energies = energy_j(levels, mass, width)
    phases = np.exp(
        -1.0j
        * times[:, None]
        * energies[None, :]
        / REDUCED_PLANCK_CONSTANT_J_S
    )
    wavefunction = np.einsum(
        "tn,n,nx->tx", phases, coefficients, basis, optimize=True
    )
    density = np.asarray(np.abs(wavefunction) ** 2, dtype=np.float64)
    norm = np.asarray(np.trapezoid(density, position, axis=1), dtype=np.float64)
    expected_position = np.asarray(
        np.trapezoid(density * position[None, :], position, axis=1), dtype=np.float64
    )
    revival = 4.0 * mass * width**2 / (
        np.pi * REDUCED_PLANCK_CONSTANT_J_S
    )
    for array in (position, times, wavefunction, density, norm, expected_position, coefficients):
        array.setflags(write=False)
    return WavePacketEvolution(
        position_m=position,
        time_s=times,
        wavefunction_m_neg_half=wavefunction,
        probability_density_m_inv=density,
        norm=norm,
        expected_position_m=expected_position,
        basis_coefficients=coefficients,
        revival_time_s=float(revival),
    )


__all__ = [
    "FiniteWellState",
    "WavePacketEvolution",
    "finite_square_well_states",
    "finite_well_wavefunction_m_neg_half",
    "gaussian_wavepacket_evolution",
    "rectangular_barrier_transmission",
]
