"""Explicit small-particle hard-disc extension for BPhO Task 2.

The competition baseline uses stochastic direction resets and deliberately
omits small-small contacts.  This extension provides the alternative bath:
directions are never reset and equal-mass gas particles exchange momentum in
elastic hard-disc collisions.  The two mechanisms are intentionally separate
so molecular scattering is not counted twice.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    SimulationState,
    advance_free_motion,
    reflect_square_walls,
    resolve_small_large_collisions,
)


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class SmallSmallCollisionBatch:
    """Conservation and contact diagnostics from one collision pass."""

    contacts_detected: int
    impulses_applied: int
    maximum_residual_penetration_nm: float
    maximum_normalized_momentum_error: float
    maximum_normalized_energy_error: float


@dataclass(frozen=True)
class HardDiscSimulationResult:
    """Compact output from the explicit hard-disc heat bath."""

    parameters: BrownianParameters
    times_ps: FloatArray
    tracer_positions_nm: FloatArray
    small_position_frames_nm: FloatArray
    total_small_small_contacts: int
    total_small_small_impulses: int
    total_small_large_contacts: int
    maximum_residual_penetration_nm: float
    maximum_normalized_momentum_error: float
    maximum_normalized_energy_error: float
    relative_kinetic_energy_drift: float
    direction_resets: int = 0


def _validate_pair_arrays(
    positions_nm: FloatArray, velocities_nm_per_ps: FloatArray
) -> tuple[FloatArray, FloatArray]:
    positions = np.asarray(positions_nm, dtype=np.float64)
    velocities = np.asarray(velocities_nm_per_ps, dtype=np.float64)
    if positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError("positions_nm must have shape (N, 2)")
    if velocities.shape != positions.shape:
        raise ValueError("velocities_nm_per_ps must match positions_nm")
    if len(positions) < 2:
        raise ValueError("at least two particles are required")
    if not np.all(np.isfinite(positions)) or not np.all(np.isfinite(velocities)):
        raise ValueError("positions and velocities must be finite")
    return positions, velocities


def resolve_small_small_collisions(
    positions_nm: FloatArray,
    velocities_nm_per_ps: FloatArray,
    *,
    radius_nm: float,
    mass_kg: float,
    restitution: float = 1.0,
    clearance_nm: float | None = None,
) -> SmallSmallCollisionBatch:
    """Resolve one deterministic pass of equal-mass hard-disc contacts.

    Positions and velocities are updated in place.  For each contacting pair,
    overlap is divided equally and only the relative normal velocity changes.
    The elastic case therefore conserves pair momentum and kinetic energy to
    floating-point precision.
    """

    positions, velocities = _validate_pair_arrays(
        positions_nm, velocities_nm_per_ps
    )
    radius = float(radius_nm)
    mass = float(mass_kg)
    coefficient = float(restitution)
    if not np.isfinite(radius) or radius <= 0.0:
        raise ValueError("radius_nm must be finite and positive")
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("mass_kg must be finite and positive")
    if not np.isfinite(coefficient) or not 0.0 <= coefficient <= 1.0:
        raise ValueError("restitution must lie between zero and one")
    clearance = (
        64.0 * np.finfo(np.float64).eps * max(radius, 1.0)
        if clearance_nm is None
        else float(clearance_nm)
    )
    if not np.isfinite(clearance) or clearance < 0.0:
        raise ValueError("clearance_nm must be finite and non-negative")

    contact_distance = 2.0 * radius
    row, column = np.triu_indices(len(positions), k=1)
    separation = positions[column] - positions[row]
    squared_distance = np.einsum("ij,ij->i", separation, separation)
    candidates = np.flatnonzero(squared_distance <= contact_distance**2)

    contacts = 0
    impulses = 0
    maximum_penetration = 0.0
    maximum_momentum_error = 0.0
    maximum_energy_error = 0.0
    tiny = np.finfo(np.float64).tiny

    for raw_candidate in candidates:
        candidate = int(raw_candidate)
        first = int(row[candidate])
        second = int(column[candidate])
        delta = positions[second] - positions[first]
        distance = float(np.linalg.norm(delta))
        if distance > contact_distance:
            continue
        if distance == 0.0:
            raise RuntimeError("coincident small-particle centres are undefined")

        contacts += 1
        normal = delta / distance
        penetration = max(contact_distance - distance, 0.0)
        correction = 0.5 * (penetration + clearance)
        positions[first] -= correction * normal
        positions[second] += correction * normal
        residual = max(
            contact_distance
            - float(np.linalg.norm(positions[second] - positions[first])),
            0.0,
        )
        maximum_penetration = max(maximum_penetration, residual)

        first_before = velocities[first].copy()
        second_before = velocities[second].copy()
        relative_normal_speed = float(
            np.dot(second_before - first_before, normal)
        )
        if relative_normal_speed >= 0.0:
            continue

        impulses += 1
        momentum_before = mass * (first_before + second_before)
        energy_before = 0.5 * mass * (
            float(np.dot(first_before, first_before))
            + float(np.dot(second_before, second_before))
        )
        impulse = -0.5 * mass * (1.0 + coefficient) * relative_normal_speed
        velocities[first] = first_before - impulse / mass * normal
        velocities[second] = second_before + impulse / mass * normal
        momentum_after = mass * (velocities[first] + velocities[second])
        energy_after = 0.5 * mass * (
            float(np.dot(velocities[first], velocities[first]))
            + float(np.dot(velocities[second], velocities[second]))
        )
        expected_energy_change = (
            -0.25 * mass * (1.0 - coefficient**2) * relative_normal_speed**2
        )
        momentum_scale = max(
            float(np.linalg.norm(momentum_before)),
            mass
            * (
                float(np.linalg.norm(first_before))
                + float(np.linalg.norm(second_before))
            ),
            abs(impulse),
            tiny,
        )
        energy_scale = max(abs(energy_before), abs(expected_energy_change), tiny)
        maximum_momentum_error = max(
            maximum_momentum_error,
            float(np.linalg.norm(momentum_after - momentum_before))
            / momentum_scale,
        )
        maximum_energy_error = max(
            maximum_energy_error,
            abs((energy_after - energy_before) - expected_energy_change)
            / energy_scale,
        )

    return SmallSmallCollisionBatch(
        contacts_detected=contacts,
        impulses_applied=impulses,
        maximum_residual_penetration_nm=maximum_penetration,
        maximum_normalized_momentum_error=maximum_momentum_error,
        maximum_normalized_energy_error=maximum_energy_error,
    )


def initialize_hard_disc_state(
    parameters: BrownianParameters, *, seed: int | None = None
) -> SimulationState:
    """Create a reproducible non-overlapping gas and centred tracer."""

    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")
    rng = np.random.default_rng(parameters.seed if seed is None else seed)
    radius = parameters.small_radius_nm
    tracer_radius = parameters.large_radius_nm
    centre = np.full(2, parameters.box_size_nm / 2.0, dtype=np.float64)
    positions = np.empty((parameters.n_small, 2), dtype=np.float64)

    for index in range(parameters.n_small):
        for _ in range(50_000):
            candidate = rng.uniform(
                radius,
                parameters.box_size_nm - radius,
                size=2,
            )
            if np.linalg.norm(candidate - centre) <= radius + tracer_radius:
                continue
            if index and np.any(
                np.linalg.norm(positions[:index] - candidate, axis=1)
                <= 2.0 * radius
            ):
                continue
            positions[index] = candidate
            break
        else:
            raise RuntimeError(
                "could not place a non-overlapping hard-disc bath; reduce density"
            )

    angles = rng.uniform(0.0, 2.0 * np.pi, size=parameters.n_small)
    velocities = parameters.small_speed_nm_per_ps * np.column_stack(
        (np.cos(angles), np.sin(angles))
    )
    return SimulationState(
        small_positions_nm=positions,
        small_velocities_nm_per_ps=velocities,
        next_randomization_times_ps=np.full(
            parameters.n_small,
            parameters.max_time_ps + parameters.randomization_interval_ps + 1.0,
        ),
        large_position_nm=centre,
        large_velocity_nm_per_ps=np.zeros(2, dtype=np.float64),
    )


def _total_kinetic_energy(state: SimulationState, parameters: BrownianParameters) -> float:
    small = 0.5 * parameters.small_mass_kg * float(
        np.sum(state.small_velocities_nm_per_ps**2)
    )
    large = 0.5 * parameters.large_mass_kg * float(
        np.dot(state.large_velocity_nm_per_ps, state.large_velocity_nm_per_ps)
    )
    return small + large


def _count_small_large_contacts(
    state: SimulationState, parameters: BrownianParameters
) -> int:
    distance = np.linalg.norm(
        state.small_positions_nm - state.large_position_nm, axis=1
    )
    contact_distance = parameters.small_radius_nm + parameters.large_radius_nm
    tolerance = 1.0e-11 * max(contact_distance, 1.0)
    return int(np.count_nonzero(distance < contact_distance - tolerance))


def _count_small_small_contacts(state: SimulationState, radius_nm: float) -> int:
    positions = state.small_positions_nm
    row, column = np.triu_indices(len(positions), k=1)
    distances = np.linalg.norm(positions[column] - positions[row], axis=1)
    contact_distance = 2.0 * radius_nm
    tolerance = 1.0e-11 * max(contact_distance, 1.0)
    return int(np.count_nonzero(distances < contact_distance - tolerance))


def advance_hard_disc_step(
    state: SimulationState,
    parameters: BrownianParameters,
    *,
    time_step_ps: float,
) -> tuple[SmallSmallCollisionBatch, int]:
    """Advance one no-reset step with gas-gas and gas-tracer contacts."""

    advance_free_motion(state, time_step_ps)
    reflect_square_walls(state, parameters)
    contacts = 0
    impulses = 0
    max_penetration = 0.0
    max_momentum_error = 0.0
    max_energy_error = 0.0
    tracer_contacts = 0

    for _ in range(parameters.max_collision_passes):
        tracer_count = _count_small_large_contacts(state, parameters)
        pair_count = _count_small_small_contacts(
            state, parameters.small_radius_nm
        )
        if tracer_count == 0 and pair_count == 0:
            break
        if tracer_count:
            tracer_batch = resolve_small_large_collisions(state, parameters)
            tracer_contacts += tracer_batch.contacts_detected
        pair_batch = resolve_small_small_collisions(
            state.small_positions_nm,
            state.small_velocities_nm_per_ps,
            radius_nm=parameters.small_radius_nm,
            mass_kg=parameters.small_mass_kg,
            restitution=parameters.restitution,
            clearance_nm=1.0e-9 * parameters.small_radius_nm,
        )
        contacts += pair_batch.contacts_detected
        impulses += pair_batch.impulses_applied
        max_penetration = max(
            max_penetration, pair_batch.maximum_residual_penetration_nm
        )
        max_momentum_error = max(
            max_momentum_error, pair_batch.maximum_normalized_momentum_error
        )
        max_energy_error = max(
            max_energy_error, pair_batch.maximum_normalized_energy_error
        )
        reflect_square_walls(state, parameters)
    else:
        raise RuntimeError("hard-disc contacts did not converge")

    state.step_index += 1
    state.time_ps += float(time_step_ps)
    return (
        SmallSmallCollisionBatch(
            contacts_detected=contacts,
            impulses_applied=impulses,
            maximum_residual_penetration_nm=max_penetration,
            maximum_normalized_momentum_error=max_momentum_error,
            maximum_normalized_energy_error=max_energy_error,
        ),
        tracer_contacts,
    )


def run_hard_disc_simulation(
    parameters: BrownianParameters,
    *,
    max_frames: int = 160,
) -> HardDiscSimulationResult:
    """Run the explicit bath and return compact deterministic evidence."""

    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")
    if max_frames < 2:
        raise ValueError("max_frames must be at least two")
    time_step = parameters.maximum_time_step_ps
    n_steps = int(np.ceil(parameters.max_time_ps / time_step))
    time_step = parameters.max_time_ps / n_steps
    frame_steps = np.unique(
        np.rint(np.linspace(0, n_steps, min(max_frames, n_steps + 1))).astype(int)
    )
    frame_lookup = {int(step): index for index, step in enumerate(frame_steps)}
    state = initialize_hard_disc_state(parameters)
    times = frame_steps.astype(np.float64) * time_step
    tracer = np.empty((len(frame_steps), 2), dtype=np.float64)
    frames = np.empty(
        (len(frame_steps), parameters.n_small, 2), dtype=np.float64
    )
    tracer[0] = state.large_position_nm
    frames[0] = state.small_positions_nm
    initial_energy = _total_kinetic_energy(state, parameters)
    total_contacts = 0
    total_impulses = 0
    total_tracer_contacts = 0
    max_penetration = 0.0
    max_momentum_error = 0.0
    max_energy_error = 0.0

    for step in range(1, n_steps + 1):
        batch, tracer_contacts = advance_hard_disc_step(
            state, parameters, time_step_ps=time_step
        )
        total_contacts += batch.contacts_detected
        total_impulses += batch.impulses_applied
        total_tracer_contacts += tracer_contacts
        max_penetration = max(
            max_penetration, batch.maximum_residual_penetration_nm
        )
        max_momentum_error = max(
            max_momentum_error, batch.maximum_normalized_momentum_error
        )
        max_energy_error = max(
            max_energy_error, batch.maximum_normalized_energy_error
        )
        if step in frame_lookup:
            frame = frame_lookup[step]
            tracer[frame] = state.large_position_nm
            frames[frame] = state.small_positions_nm

    final_energy = _total_kinetic_energy(state, parameters)
    energy_drift = (final_energy - initial_energy) / initial_energy
    for array in (times, tracer, frames):
        array.setflags(write=False)
    return HardDiscSimulationResult(
        parameters=parameters,
        times_ps=times,
        tracer_positions_nm=tracer,
        small_position_frames_nm=frames,
        total_small_small_contacts=total_contacts,
        total_small_small_impulses=total_impulses,
        total_small_large_contacts=total_tracer_contacts,
        maximum_residual_penetration_nm=max_penetration,
        maximum_normalized_momentum_error=max_momentum_error,
        maximum_normalized_energy_error=max_energy_error,
        relative_kinetic_energy_drift=energy_drift,
    )
