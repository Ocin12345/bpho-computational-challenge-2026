"""Maxwellian many-particle hard-disc extension for BPhO Task 2.

``small_particle_extension`` already resolves every gas--gas and gas--tracer
contact.  This module completes the molecular-gas interpretation by replacing
the baseline's monoenergetic directions with the two-dimensional
Maxwell--Boltzmann velocity distribution and by reporting kinetic-temperature,
Rayleigh-speed and energy-conservation diagnostics.

The simulation is still a deliberately small two-dimensional gas.  It is not a
hydrodynamic model of water or a quantitatively scaled pollen grain.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    SimulationState,
)
from task02_brownian_motion.small_particle_extension import (
    advance_hard_disc_step,
    initialize_hard_disc_state,
)


FloatArray = NDArray[np.float64]
METRES_PER_SECOND_TO_NANOMETRES_PER_PICOSECOND = 1.0e-3


@dataclass(frozen=True)
class MaxwellBathDiagnostics:
    """Initial/final thermodynamic and collision diagnostics."""

    target_temperature_k: float
    initial_temperature_k: float
    final_temperature_k: float
    initial_mean_speed_nm_per_ps: float
    final_mean_speed_nm_per_ps: float
    rayleigh_expected_mean_speed_nm_per_ps: float
    relative_kinetic_energy_drift: float
    gas_gas_contacts: int
    gas_gas_impulses: int
    gas_tracer_contacts: int
    tracer_displacement_nm: float
    direction_resets: int = 0


def maxwell_component_scale_nm_per_ps(
    parameters: BrownianParameters,
    temperature_k: float | None = None,
) -> float:
    """Return sqrt(kT/m), the Gaussian scale of each 2D velocity component."""

    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")
    temperature = (
        parameters.gas_temperature_k
        if temperature_k is None
        else float(temperature_k)
    )
    if not np.isfinite(temperature) or temperature <= 0.0:
        raise ValueError("temperature_k must be finite and positive")
    scale_m_s = np.sqrt(
        parameters.boltzmann_j_per_k * temperature / parameters.small_mass_kg
    )
    return float(scale_m_s * METRES_PER_SECOND_TO_NANOMETRES_PER_PICOSECOND)


def kinetic_temperature_k(
    velocities_nm_per_ps: FloatArray,
    *,
    particle_mass_kg: float,
    boltzmann_j_per_k: float,
) -> float:
    """Infer the 2D kinetic temperature after subtracting centre-of-mass flow."""

    velocities = np.asarray(velocities_nm_per_ps, dtype=np.float64)
    if velocities.ndim != 2 or velocities.shape[1] != 2 or len(velocities) < 2:
        raise ValueError("velocities must have shape (N, 2) with N at least two")
    if np.any(~np.isfinite(velocities)):
        raise ValueError("velocities must be finite")
    mass = float(particle_mass_kg)
    boltzmann = float(boltzmann_j_per_k)
    if mass <= 0.0 or boltzmann <= 0.0:
        raise ValueError("mass and Boltzmann constant must be positive")
    thermal = velocities - np.mean(velocities, axis=0)
    mean_square_m_s = float(np.mean(np.sum(thermal**2, axis=1))) * 1.0e6
    return mass * mean_square_m_s / (2.0 * boltzmann)


def initialize_maxwellian_hard_disc_state(
    parameters: BrownianParameters,
    *,
    temperature_k: float | None = None,
    seed: int | None = None,
) -> SimulationState:
    """Create a non-overlapping bath with Maxwellian components and zero drift."""

    state = initialize_hard_disc_state(parameters, seed=seed)
    actual_seed = parameters.seed if seed is None else seed
    rng = np.random.default_rng(actual_seed)
    scale = maxwell_component_scale_nm_per_ps(parameters, temperature_k)
    velocities = rng.normal(0.0, scale, size=(parameters.n_small, 2))
    velocities -= np.mean(velocities, axis=0)
    # A finite sample does not have exactly the requested kinetic temperature.
    # Rescaling makes controlled comparisons share the same total gas energy.
    current_temperature = kinetic_temperature_k(
        velocities,
        particle_mass_kg=parameters.small_mass_kg,
        boltzmann_j_per_k=parameters.boltzmann_j_per_k,
    )
    target = parameters.gas_temperature_k if temperature_k is None else float(temperature_k)
    velocities *= np.sqrt(target / current_temperature)
    state.small_velocities_nm_per_ps[:] = velocities
    state.large_velocity_nm_per_ps[:] = 0.0
    return state


def _kinetic_energy(state: SimulationState, parameters: BrownianParameters) -> float:
    conversion_squared = 1.0e6  # (nm/ps)^2 -> (m/s)^2
    gas = 0.5 * parameters.small_mass_kg * conversion_squared * float(
        np.sum(state.small_velocities_nm_per_ps**2)
    )
    tracer = 0.5 * parameters.large_mass_kg * conversion_squared * float(
        np.dot(state.large_velocity_nm_per_ps, state.large_velocity_nm_per_ps)
    )
    return gas + tracer


def run_maxwellian_hard_disc_simulation(
    parameters: BrownianParameters,
    *,
    temperature_k: float | None = None,
) -> MaxwellBathDiagnostics:
    """Run the complete gas--gas--tracer model and return compact evidence."""

    state = initialize_maxwellian_hard_disc_state(
        parameters, temperature_k=temperature_k
    )
    target = parameters.gas_temperature_k if temperature_k is None else float(temperature_k)
    initial_temperature = kinetic_temperature_k(
        state.small_velocities_nm_per_ps,
        particle_mass_kg=parameters.small_mass_kg,
        boltzmann_j_per_k=parameters.boltzmann_j_per_k,
    )
    initial_speeds = np.linalg.norm(state.small_velocities_nm_per_ps, axis=1)
    initial_energy = _kinetic_energy(state, parameters)
    initial_tracer_position = state.large_position_nm.copy()

    maximum_speed = max(float(np.max(initial_speeds)), 1.0e-15)
    displacement_step = (
        parameters.max_step_fraction * parameters.small_radius_nm / maximum_speed
    )
    upper_step = min(parameters.maximum_time_step_ps, displacement_step)
    step_count = max(1, int(np.ceil(parameters.max_time_ps / upper_step)))
    time_step = parameters.max_time_ps / step_count
    gas_contacts = 0
    gas_impulses = 0
    tracer_contacts = 0
    for _ in range(step_count):
        batch, tracer_count = advance_hard_disc_step(
            state, parameters, time_step_ps=time_step
        )
        gas_contacts += batch.contacts_detected
        gas_impulses += batch.impulses_applied
        tracer_contacts += tracer_count

    final_energy = _kinetic_energy(state, parameters)
    final_speeds = np.linalg.norm(state.small_velocities_nm_per_ps, axis=1)
    final_temperature = kinetic_temperature_k(
        state.small_velocities_nm_per_ps,
        particle_mass_kg=parameters.small_mass_kg,
        boltzmann_j_per_k=parameters.boltzmann_j_per_k,
    )
    scale = maxwell_component_scale_nm_per_ps(parameters, target)
    return MaxwellBathDiagnostics(
        target_temperature_k=target,
        initial_temperature_k=initial_temperature,
        final_temperature_k=final_temperature,
        initial_mean_speed_nm_per_ps=float(np.mean(initial_speeds)),
        final_mean_speed_nm_per_ps=float(np.mean(final_speeds)),
        rayleigh_expected_mean_speed_nm_per_ps=float(scale * np.sqrt(np.pi / 2.0)),
        relative_kinetic_energy_drift=(final_energy - initial_energy) / initial_energy,
        gas_gas_contacts=gas_contacts,
        gas_gas_impulses=gas_impulses,
        gas_tracer_contacts=tracer_contacts,
        tracer_displacement_nm=float(
            np.linalg.norm(state.large_position_nm - initial_tracer_position)
        ),
    )


__all__ = [
    "METRES_PER_SECOND_TO_NANOMETRES_PER_PICOSECOND",
    "MaxwellBathDiagnostics",
    "initialize_maxwellian_hard_disc_state",
    "kinetic_temperature_k",
    "maxwell_component_scale_nm_per_ps",
    "run_maxwellian_hard_disc_simulation",
]
