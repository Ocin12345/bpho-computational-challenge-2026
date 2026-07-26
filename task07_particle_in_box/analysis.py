"""Immutable analytical study and independent finite-difference eigensolver."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eigh_tridiagonal

from task07_particle_in_box.configuration import (
    DEFAULT_CONFIGURATION,
    Task07Configuration,
)
from task07_particle_in_box.constants import ELECTRONVOLT_J, REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.models import (
    energy_j,
    expected_momentum_kg_m_s,
    expected_momentum_squared_kg2_m2_s2,
    expected_position_m,
    expected_position_squared_m2,
    momentum_uncertainty_kg_m_s,
    position_uncertainty_m,
    probability_density_m_inv,
    spatial_wavefunction_m_neg_half,
    uncertainty_product_j_s,
    uncertainty_product_over_hbar,
)


FloatArray = NDArray[np.float64]
IntegerArray = NDArray[np.int64]


def _readonly_float_array(value: object, *, name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    array.setflags(write=False)
    return array


def _readonly_integer_array(value: object, *, name: str) -> IntegerArray:
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.integer):
        raise TypeError(f"{name} must contain integers")
    array = np.array(value, dtype=np.int64, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class NumericalSolution:
    """One normalized finite-difference solution on an interior grid."""

    interior_point_count: int
    positions_m: FloatArray
    energies_j: FloatArray
    wavefunctions_m_neg_half: FloatArray
    overlaps: FloatArray

    def __post_init__(self) -> None:
        if isinstance(self.interior_point_count, bool) or not isinstance(
            self.interior_point_count, int
        ):
            raise TypeError("interior_point_count must be an integer")
        if self.interior_point_count < 3:
            raise ValueError("interior_point_count must be at least three")
        for field_name in (
            "positions_m",
            "energies_j",
            "wavefunctions_m_neg_half",
            "overlaps",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )
        state_count = self.energies_j.size
        if self.positions_m.shape != (self.interior_point_count,):
            raise ValueError("positions_m has an invalid shape")
        if self.wavefunctions_m_neg_half.shape != (
            self.interior_point_count,
            state_count,
        ):
            raise ValueError("wavefunctions_m_neg_half has an invalid shape")
        if self.overlaps.shape != (state_count,):
            raise ValueError("overlaps has an invalid shape")
        if np.any(self.energies_j <= 0.0):
            raise ValueError("numerical energies must be positive")
        if np.any((self.overlaps < 0.0) | (self.overlaps > 1.0 + 1e-12)):
            raise ValueError("overlaps must lie between zero and one")

    @property
    def spacing_m(self) -> float:
        if self.positions_m.size < 2:
            raise ValueError("at least two positions are required")
        return float(self.positions_m[1] - self.positions_m[0])


def solve_numerical_box(
    interior_point_count: int,
    state_count: int,
    particle_mass_kg: float,
    box_width_m: float,
) -> NumericalSolution:
    """Solve the Dirichlet box Hamiltonian without analytical eigenvalues."""

    for value, name, minimum in (
        (interior_point_count, "interior_point_count", 3),
        (state_count, "state_count", 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < minimum:
            raise ValueError(f"{name} must be at least {minimum}")
    if state_count >= interior_point_count:
        raise ValueError("state_count must be smaller than the interior grid")
    mass = float(particle_mass_kg)
    width = float(box_width_m)
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("particle_mass_kg must be finite and positive")
    if not np.isfinite(width) or width <= 0.0:
        raise ValueError("box_width_m must be finite and positive")

    spacing = width / (interior_point_count + 1)
    kinetic_scale = REDUCED_PLANCK_CONSTANT_J_S**2 / (2.0 * mass * spacing**2)
    diagonal = np.full(interior_point_count, 2.0 * kinetic_scale, dtype=np.float64)
    off_diagonal = np.full(interior_point_count - 1, -kinetic_scale, dtype=np.float64)
    energies, eigenvectors = eigh_tridiagonal(
        diagonal,
        off_diagonal,
        select="i",
        select_range=(0, state_count - 1),
        check_finite=True,
    )
    positions = spacing * np.arange(1, interior_point_count + 1, dtype=np.float64)
    wavefunctions = np.asarray(eigenvectors / np.sqrt(spacing), dtype=np.float64)
    quantum_numbers = np.arange(1, state_count + 1, dtype=np.int64)
    analytical = spatial_wavefunction_m_neg_half(
        positions[:, None],
        quantum_numbers[None, :],
        width,
    )
    signed_overlaps = np.sum(wavefunctions * analytical, axis=0) * spacing
    signs = np.where(signed_overlaps < 0.0, -1.0, 1.0)
    wavefunctions *= signs[None, :]
    overlaps = np.abs(np.sum(wavefunctions * analytical, axis=0) * spacing)
    return NumericalSolution(
        interior_point_count=interior_point_count,
        positions_m=positions,
        energies_j=energies,
        wavefunctions_m_neg_half=wavefunctions,
        overlaps=overlaps,
    )


@dataclass(frozen=True)
class Task07StudyResult:
    """Complete immutable analytical and numerical Task 7 evidence."""

    schema_version: str
    quantum_numbers: IntegerArray
    energies_j: FloatArray
    energies_ev: FloatArray
    energy_ratios: FloatArray
    positions_m: FloatArray
    density_quantum_numbers: IntegerArray
    wavefunctions_m_neg_half: FloatArray
    probability_densities_m_inv: FloatArray
    expected_positions_m: FloatArray
    expected_positions_squared_m2: FloatArray
    position_uncertainties_m: FloatArray
    expected_momenta_kg_m_s: FloatArray
    expected_momenta_squared_kg2_m2_s2: FloatArray
    momentum_uncertainties_kg_m_s: FloatArray
    uncertainty_products_j_s: FloatArray
    uncertainty_products_over_hbar: FloatArray
    numerical_grid_sizes: IntegerArray
    numerical_grid_spacings_m: FloatArray
    numerical_energies_j: FloatArray
    numerical_relative_errors: FloatArray
    numerical_convergence_orders: FloatArray
    numerical_positions_m: FloatArray
    numerical_wavefunctions_m_neg_half: FloatArray
    numerical_overlaps: FloatArray

    def __post_init__(self) -> None:
        if self.schema_version != "task07-study-v1":
            raise ValueError("invalid Task 7 study schema")
        for field_name in (
            "quantum_numbers",
            "density_quantum_numbers",
            "numerical_grid_sizes",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_integer_array(getattr(self, field_name), name=field_name),
            )
        for field_name in (
            "energies_j",
            "energies_ev",
            "energy_ratios",
            "positions_m",
            "wavefunctions_m_neg_half",
            "probability_densities_m_inv",
            "expected_positions_m",
            "expected_positions_squared_m2",
            "position_uncertainties_m",
            "expected_momenta_kg_m_s",
            "expected_momenta_squared_kg2_m2_s2",
            "momentum_uncertainties_kg_m_s",
            "uncertainty_products_j_s",
            "uncertainty_products_over_hbar",
            "numerical_grid_spacings_m",
            "numerical_energies_j",
            "numerical_relative_errors",
            "numerical_convergence_orders",
            "numerical_positions_m",
            "numerical_wavefunctions_m_neg_half",
            "numerical_overlaps",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )
        state_count = self.quantum_numbers.size
        density_count = self.density_quantum_numbers.size
        point_count = self.positions_m.size
        numerical_grid_count = self.numerical_grid_sizes.size
        numerical_state_count = self.numerical_energies_j.shape[1]
        if self.energies_j.shape != (state_count,) or self.energies_ev.shape != (state_count,):
            raise ValueError("energy arrays have invalid shapes")
        if self.energy_ratios.shape != (state_count,):
            raise ValueError("energy_ratios has an invalid shape")
        if self.wavefunctions_m_neg_half.shape != (point_count, density_count):
            raise ValueError("wavefunction matrix has an invalid shape")
        if self.probability_densities_m_inv.shape != (point_count, density_count):
            raise ValueError("probability-density matrix has an invalid shape")
        for field_name in (
            "expected_positions_m",
            "expected_positions_squared_m2",
            "position_uncertainties_m",
            "expected_momenta_kg_m_s",
            "expected_momenta_squared_kg2_m2_s2",
            "momentum_uncertainties_kg_m_s",
            "uncertainty_products_j_s",
            "uncertainty_products_over_hbar",
        ):
            if getattr(self, field_name).shape != (state_count,):
                raise ValueError(f"{field_name} has an invalid shape")
        if self.numerical_grid_spacings_m.shape != (numerical_grid_count,):
            raise ValueError("numerical_grid_spacings_m has an invalid shape")
        if self.numerical_energies_j.shape != (
            numerical_grid_count,
            numerical_state_count,
        ):
            raise ValueError("numerical_energies_j has an invalid shape")
        if self.numerical_relative_errors.shape != self.numerical_energies_j.shape:
            raise ValueError("numerical_relative_errors has an invalid shape")
        if self.numerical_convergence_orders.shape != (numerical_state_count,):
            raise ValueError("numerical_convergence_orders has an invalid shape")
        if self.numerical_wavefunctions_m_neg_half.shape != (
            self.numerical_positions_m.size,
            numerical_state_count,
        ):
            raise ValueError("numerical wavefunction matrix has an invalid shape")
        if self.numerical_overlaps.shape != (numerical_state_count,):
            raise ValueError("numerical_overlaps has an invalid shape")

    @property
    def ground_energy_ev(self) -> float:
        return float(self.energies_ev[0])

    @property
    def ground_uncertainty_over_hbar(self) -> float:
        return float(self.uncertainty_products_over_hbar[0])


def build_task07_study(
    configuration: Task07Configuration = DEFAULT_CONFIGURATION,
) -> Task07StudyResult:
    """Build the complete analytical study and numerical convergence evidence."""

    if not isinstance(configuration, Task07Configuration):
        raise TypeError("configuration must be a Task07Configuration")
    n = np.asarray(configuration.quantum_numbers, dtype=np.int64)
    energies = energy_j(n, configuration.particle_mass_kg, configuration.box_width_m)
    positions = np.linspace(
        0.0,
        configuration.box_width_m,
        configuration.position_point_count,
        dtype=np.float64,
    )
    density_n = np.asarray(configuration.density_quantum_numbers, dtype=np.int64)
    wavefunctions = spatial_wavefunction_m_neg_half(
        positions[:, None],
        density_n[None, :],
        configuration.box_width_m,
    )
    densities = probability_density_m_inv(
        positions[:, None],
        density_n[None, :],
        configuration.box_width_m,
    )

    numerical_solutions = tuple(
        solve_numerical_box(
            grid_size,
            configuration.numerical_state_count,
            configuration.particle_mass_kg,
            configuration.box_width_m,
        )
        for grid_size in configuration.numerical_grid_sizes
    )
    analytical_numerical_energies = energies[: configuration.numerical_state_count]
    numerical_energies = np.vstack(
        [solution.energies_j for solution in numerical_solutions]
    )
    numerical_errors = np.abs(
        (numerical_energies - analytical_numerical_energies[None, :])
        / analytical_numerical_energies[None, :]
    )
    grid_spacings = np.asarray(
        [
            configuration.box_width_m / (grid_size + 1)
            for grid_size in configuration.numerical_grid_sizes
        ],
        dtype=np.float64,
    )
    convergence_orders = np.asarray(
        [
            np.polyfit(np.log(grid_spacings), np.log(numerical_errors[:, index]), 1)[0]
            for index in range(configuration.numerical_state_count)
        ],
        dtype=np.float64,
    )
    finest = numerical_solutions[-1]
    expected_x = np.full(n.shape, expected_position_m(configuration.box_width_m))
    return Task07StudyResult(
        schema_version="task07-study-v1",
        quantum_numbers=n,
        energies_j=energies,
        energies_ev=energies / ELECTRONVOLT_J,
        energy_ratios=energies / energies[0],
        positions_m=positions,
        density_quantum_numbers=density_n,
        wavefunctions_m_neg_half=wavefunctions,
        probability_densities_m_inv=densities,
        expected_positions_m=expected_x,
        expected_positions_squared_m2=expected_position_squared_m2(
            n, configuration.box_width_m
        ),
        position_uncertainties_m=position_uncertainty_m(n, configuration.box_width_m),
        expected_momenta_kg_m_s=expected_momentum_kg_m_s(n),
        expected_momenta_squared_kg2_m2_s2=(
            expected_momentum_squared_kg2_m2_s2(n, configuration.box_width_m)
        ),
        momentum_uncertainties_kg_m_s=momentum_uncertainty_kg_m_s(
            n, configuration.box_width_m
        ),
        uncertainty_products_j_s=uncertainty_product_j_s(
            n, configuration.box_width_m
        ),
        uncertainty_products_over_hbar=uncertainty_product_over_hbar(n),
        numerical_grid_sizes=np.asarray(configuration.numerical_grid_sizes, dtype=np.int64),
        numerical_grid_spacings_m=grid_spacings,
        numerical_energies_j=numerical_energies,
        numerical_relative_errors=numerical_errors,
        numerical_convergence_orders=convergence_orders,
        numerical_positions_m=finest.positions_m,
        numerical_wavefunctions_m_neg_half=finest.wavefunctions_m_neg_half,
        numerical_overlaps=finest.overlaps,
    )


__all__ = [
    "NumericalSolution",
    "Task07StudyResult",
    "build_task07_study",
    "solve_numerical_box",
]
