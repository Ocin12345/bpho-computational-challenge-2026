"""Discrete position and momentum moments for finite-difference box states."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from task07_particle_in_box.analysis import NumericalSolution
from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION, Task07Configuration
from task07_particle_in_box.constants import REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.models import (
    energy_j,
    momentum_uncertainty_kg_m_s,
    position_uncertainty_m,
    uncertainty_product_over_hbar,
)


@dataclass(frozen=True)
class NumericalMomentumObservables:
    """Moments obtained only from one numerical grid and its eigenvectors."""

    normalizations: np.ndarray
    expected_x_m: np.ndarray
    expected_x_squared_m2: np.ndarray
    p_mean_kg_m_s: np.ndarray
    p_squared_kg2_m2_s2: np.ndarray
    delta_x_m: np.ndarray
    delta_p_kg_m_s: np.ndarray
    uncertainty_products_j_s: np.ndarray
    uncertainty_products_over_hbar: np.ndarray
    heisenberg_ratios: np.ndarray

    def __post_init__(self) -> None:
        state_count = np.asarray(self.normalizations).size
        complex_fields = ("p_mean_kg_m_s",)
        float_fields = (
            "normalizations",
            "expected_x_m",
            "expected_x_squared_m2",
            "p_squared_kg2_m2_s2",
            "delta_x_m",
            "delta_p_kg_m_s",
            "uncertainty_products_j_s",
            "uncertainty_products_over_hbar",
            "heisenberg_ratios",
        )
        for name in float_fields:
            array = np.array(getattr(self, name), dtype=np.float64, copy=True)
            if array.shape != (state_count,) or not np.all(np.isfinite(array)):
                raise ValueError(f"{name} must be a finite state vector")
            array.setflags(write=False)
            object.__setattr__(self, name, array)
        for name in complex_fields:
            array = np.array(getattr(self, name), dtype=np.complex128, copy=True)
            if array.shape != (state_count,) or not np.all(np.isfinite(array)):
                raise ValueError(f"{name} must be a finite state vector")
            array.setflags(write=False)
            object.__setattr__(self, name, array)


@dataclass(frozen=True)
class NumericalMomentumStudy:
    """Five-grid moment and uncertainty evidence with analytical comparisons."""

    grid_sizes: np.ndarray
    grid_spacings_m: np.ndarray
    quantum_numbers: np.ndarray
    normalizations: np.ndarray
    expected_x_m: np.ndarray
    expected_x_squared_m2: np.ndarray
    p_mean_kg_m_s: np.ndarray
    p_squared_kg2_m2_s2: np.ndarray
    delta_x_m: np.ndarray
    delta_p_kg_m_s: np.ndarray
    uncertainty_products_j_s: np.ndarray
    uncertainty_products_over_hbar: np.ndarray
    heisenberg_ratios: np.ndarray
    analytical_delta_x_m: np.ndarray
    analytical_delta_p_kg_m_s: np.ndarray
    analytical_uncertainty_products_j_s: np.ndarray
    analytical_uncertainty_products_over_hbar: np.ndarray
    relative_delta_x_errors: np.ndarray
    relative_p_squared_errors: np.ndarray
    relative_delta_p_errors: np.ndarray
    relative_uncertainty_errors: np.ndarray
    relative_energy_errors: np.ndarray
    eigenvector_overlaps: np.ndarray
    p_mean_scale_ratios: np.ndarray
    delta_p_convergence_orders: np.ndarray
    p_squared_convergence_orders: np.ndarray
    uncertainty_product_convergence_orders: np.ndarray

    def __post_init__(self) -> None:
        grid_count = np.asarray(self.grid_sizes).size
        state_count = np.asarray(self.quantum_numbers).size
        for name in ("grid_sizes", "quantum_numbers"):
            array = np.array(getattr(self, name), dtype=np.int64, copy=True)
            array.setflags(write=False)
            object.__setattr__(self, name, array)
        matrix_fields = (
            "normalizations",
            "expected_x_m",
            "expected_x_squared_m2",
            "p_squared_kg2_m2_s2",
            "delta_x_m",
            "delta_p_kg_m_s",
            "uncertainty_products_j_s",
            "uncertainty_products_over_hbar",
            "heisenberg_ratios",
            "relative_delta_x_errors",
            "relative_p_squared_errors",
            "relative_delta_p_errors",
            "relative_uncertainty_errors",
            "relative_energy_errors",
            "eigenvector_overlaps",
            "p_mean_scale_ratios",
        )
        reference_fields = (
            "analytical_delta_x_m",
            "analytical_delta_p_kg_m_s",
            "analytical_uncertainty_products_j_s",
            "analytical_uncertainty_products_over_hbar",
        )
        order_fields = (
            "delta_p_convergence_orders",
            "p_squared_convergence_orders",
            "uncertainty_product_convergence_orders",
        )
        for name in matrix_fields + reference_fields + order_fields + ("grid_spacings_m",):
            array = np.array(getattr(self, name), dtype=np.float64, copy=True)
            if not np.all(np.isfinite(array)):
                raise ValueError(f"{name} must be finite")
            array.setflags(write=False)
            object.__setattr__(self, name, array)
        p_mean = np.array(self.p_mean_kg_m_s, dtype=np.complex128, copy=True)
        if not np.all(np.isfinite(p_mean)):
            raise ValueError("p_mean_kg_m_s must be finite")
        p_mean.setflags(write=False)
        object.__setattr__(self, "p_mean_kg_m_s", p_mean)
        for name in matrix_fields + ("p_mean_kg_m_s",):
            if getattr(self, name).shape != (grid_count, state_count):
                raise ValueError(f"{name} has an invalid shape")
        for name in reference_fields + order_fields:
            if getattr(self, name).shape != (state_count,):
                raise ValueError(f"{name} has an invalid shape")
        if self.grid_spacings_m.shape != (grid_count,):
            raise ValueError("grid_spacings_m has an invalid shape")


def _discrete_norms(psi: np.ndarray, spacing: float) -> np.ndarray:
    """Return Dirichlet-grid norms, including zero-valued walls implicitly."""

    return np.real(np.sum(np.conj(psi) * psi, axis=0) * spacing)


def numerical_momentum_observables(
    solution: NumericalSolution,
    particle_mass_kg: float,
) -> NumericalMomentumObservables:
    """Apply central-difference x, p and p-squared operators to eigenvectors.

    The input vectors occupy the interior grid. Zero ghost values impose the
    two Dirichlet walls. The second-derivative stencil is exactly the stencil
    used by the numerical Hamiltonian; no analytical moment is called here.
    """

    if not isinstance(solution, NumericalSolution):
        raise TypeError("solution must be a NumericalSolution")
    if not np.isfinite(particle_mass_kg) or particle_mass_kg <= 0.0:
        raise ValueError("particle_mass_kg must be finite and positive")
    spacing = solution.spacing_m
    positions = solution.positions_m[:, None]
    raw = np.asarray(solution.wavefunctions_m_neg_half, dtype=np.complex128)
    normalizations = _discrete_norms(raw, spacing)
    if np.any(normalizations <= 0.0) or not np.all(np.isfinite(normalizations)):
        raise ValueError("finite-difference eigenvectors must have positive norms")
    psi = raw / np.sqrt(normalizations)[None, :]

    left = np.vstack((np.zeros((1, psi.shape[1]), dtype=np.complex128), psi[:-1]))
    right = np.vstack((psi[1:], np.zeros((1, psi.shape[1]), dtype=np.complex128)))
    first_derivative = (right - left) / (2.0 * spacing)
    second_derivative = (right - 2.0 * psi + left) / spacing**2
    p_applied = -1.0j * REDUCED_PLANCK_CONSTANT_J_S * first_derivative
    p_squared_applied = -(REDUCED_PLANCK_CONSTANT_J_S**2) * second_derivative

    expected_x = np.sum(np.conj(psi) * positions * psi, axis=0) * spacing
    expected_x_squared = (
        np.sum(np.conj(psi) * positions**2 * psi, axis=0) * spacing
    )
    p_mean = np.sum(np.conj(psi) * p_applied, axis=0) * spacing
    p_squared_complex = np.sum(np.conj(psi) * p_squared_applied, axis=0) * spacing

    momentum_scale = np.sqrt(np.max(np.abs(p_squared_complex.real)))
    momentum_squared_scale = np.max(np.abs(p_squared_complex.real))
    if np.max(np.abs(p_mean.imag)) > 5.0e-12 * momentum_scale:
        raise ValueError("momentum expectation has a non-negligible imaginary part")
    if np.max(np.abs(p_squared_complex.imag)) > 5.0e-12 * momentum_squared_scale:
        raise ValueError("momentum-squared expectation is not Hermitian")
    if np.max(np.abs(expected_x.imag)) > 5.0e-14 * np.max(positions):
        raise ValueError("position expectation is not real")
    if np.max(np.abs(expected_x_squared.imag)) > 5.0e-14 * np.max(positions) ** 2:
        raise ValueError("position-squared expectation is not real")

    expected_x = expected_x.real
    expected_x_squared = expected_x_squared.real
    p_squared = p_squared_complex.real
    position_variance = expected_x_squared - expected_x**2
    momentum_variance = p_squared - np.abs(p_mean) ** 2
    position_tolerance = 5.0e-14 * np.max(expected_x_squared)
    momentum_tolerance = 5.0e-14 * np.max(p_squared)
    if np.min(position_variance) < -position_tolerance:
        raise ValueError("numerical position variance is negative")
    if np.min(momentum_variance) < -momentum_tolerance:
        raise ValueError("numerical momentum variance is negative")
    delta_x = np.sqrt(np.clip(position_variance, 0.0, None))
    delta_p = np.sqrt(np.clip(momentum_variance, 0.0, None))
    products = delta_x * delta_p
    return NumericalMomentumObservables(
        normalizations=normalizations,
        expected_x_m=expected_x,
        expected_x_squared_m2=expected_x_squared,
        p_mean_kg_m_s=p_mean,
        p_squared_kg2_m2_s2=p_squared,
        delta_x_m=delta_x,
        delta_p_kg_m_s=delta_p,
        uncertainty_products_j_s=products,
        uncertainty_products_over_hbar=products / REDUCED_PLANCK_CONSTANT_J_S,
        heisenberg_ratios=2.0 * products / REDUCED_PLANCK_CONSTANT_J_S,
    )


def _fit_orders(spacings: np.ndarray, errors: np.ndarray) -> np.ndarray:
    return np.asarray(
        [
            np.polyfit(np.log(spacings), np.log(errors[:, index]), 1)[0]
            for index in range(errors.shape[1])
        ],
        dtype=np.float64,
    )


def build_numerical_momentum_study(
    configuration: Task07Configuration = DEFAULT_CONFIGURATION,
    solutions: tuple[NumericalSolution, ...] | None = None,
) -> NumericalMomentumStudy:
    """Compute canonical moment evidence on every configured numerical grid."""

    if not isinstance(configuration, Task07Configuration):
        raise TypeError("configuration must be a Task07Configuration")
    from task07_particle_in_box.analysis import solve_numerical_box

    if solutions is None:
        solutions = tuple(
            solve_numerical_box(
                grid_size,
                configuration.numerical_state_count,
                configuration.particle_mass_kg,
                configuration.box_width_m,
            )
            for grid_size in configuration.numerical_grid_sizes
        )
    else:
        solutions = tuple(solutions)
        if tuple(solution.interior_point_count for solution in solutions) != tuple(
            configuration.numerical_grid_sizes
        ):
            raise ValueError("solutions do not match the configured numerical grids")
    observables = tuple(
        numerical_momentum_observables(solution, configuration.particle_mass_kg)
        for solution in solutions
    )
    stack = lambda name: np.vstack([getattr(item, name) for item in observables])
    n = np.arange(1, configuration.numerical_state_count + 1, dtype=np.int64)
    analytic_dx = position_uncertainty_m(n, configuration.box_width_m)
    analytic_dp = momentum_uncertainty_kg_m_s(n, configuration.box_width_m)
    analytic_product_over_hbar = uncertainty_product_over_hbar(n)
    analytic_product = analytic_product_over_hbar * REDUCED_PLANCK_CONSTANT_J_S
    numerical_dx = stack("delta_x_m")
    numerical_dp = stack("delta_p_kg_m_s")
    numerical_p2 = stack("p_squared_kg2_m2_s2")
    numerical_products = stack("uncertainty_products_j_s")
    numerical_products_over_hbar = stack("uncertainty_products_over_hbar")
    relative = lambda observed, expected: np.abs((observed - expected) / expected)
    dx_errors = relative(numerical_dx, analytic_dx[None, :])
    dp_errors = relative(numerical_dp, analytic_dp[None, :])
    p2_errors = relative(numerical_p2, np.square(analytic_dp)[None, :])
    product_errors = relative(
        numerical_products_over_hbar, analytic_product_over_hbar[None, :]
    )
    analytical_energies = energy_j(
        n, configuration.particle_mass_kg, configuration.box_width_m
    )
    energy_errors = np.vstack(
        [relative(solution.energies_j, analytical_energies) for solution in solutions]
    )
    spacings = np.asarray([solution.spacing_m for solution in solutions], dtype=np.float64)
    p_mean = stack("p_mean_kg_m_s")
    return NumericalMomentumStudy(
        grid_sizes=np.asarray(configuration.numerical_grid_sizes, dtype=np.int64),
        grid_spacings_m=spacings,
        quantum_numbers=n,
        normalizations=stack("normalizations"),
        expected_x_m=stack("expected_x_m"),
        expected_x_squared_m2=stack("expected_x_squared_m2"),
        p_mean_kg_m_s=p_mean,
        p_squared_kg2_m2_s2=numerical_p2,
        delta_x_m=numerical_dx,
        delta_p_kg_m_s=numerical_dp,
        uncertainty_products_j_s=numerical_products,
        uncertainty_products_over_hbar=numerical_products_over_hbar,
        heisenberg_ratios=stack("heisenberg_ratios"),
        analytical_delta_x_m=analytic_dx,
        analytical_delta_p_kg_m_s=analytic_dp,
        analytical_uncertainty_products_j_s=analytic_product,
        analytical_uncertainty_products_over_hbar=analytic_product_over_hbar,
        relative_delta_x_errors=dx_errors,
        relative_p_squared_errors=p2_errors,
        relative_delta_p_errors=dp_errors,
        relative_uncertainty_errors=product_errors,
        relative_energy_errors=energy_errors,
        eigenvector_overlaps=np.vstack([solution.overlaps for solution in solutions]),
        p_mean_scale_ratios=np.abs(p_mean) / analytic_dp[None, :],
        delta_p_convergence_orders=_fit_orders(spacings, dp_errors),
        p_squared_convergence_orders=_fit_orders(spacings, p2_errors),
        uncertainty_product_convergence_orders=_fit_orders(spacings, product_errors),
    )


__all__ = [
    "NumericalMomentumObservables",
    "NumericalMomentumStudy",
    "build_numerical_momentum_study",
    "numerical_momentum_observables",
]
