"""Independent numerical validation for the Task 2 simulation engine."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    BrownianSimulationResult,
    advance_simulation_step,
    create_time_grid,
    initialize_simulation,
    run_simulation,
)


@dataclass(frozen=True)
class ControlledConvergenceRow:
    """Error from one controlled-collision time-step resolution."""

    n_steps: int
    time_step_ps: float
    rms_endpoint_error_nm: float
    maximum_endpoint_error_nm: float
    observed_order_from_previous: float | None


@dataclass(frozen=True)
class ReferenceRefinementRow:
    """Summary of one complete reference time-step refinement."""

    refinement_factor: int
    n_steps: int
    time_step_ps: float
    final_displacement_x_nm: float
    final_displacement_y_nm: float
    final_displacement_nm: float
    rms_path_difference_from_previous_nm: float | None
    maximum_path_difference_from_previous_nm: float | None
    total_contacts: int
    total_impulses: int
    total_direction_resets: int
    maximum_collision_passes: int
    maximum_displacement_nm: float
    maximum_residual_penetration_nm: float
    maximum_normalized_momentum_error: float
    maximum_normalized_restitution_error: float
    maximum_normalized_energy_identity_error: float


@dataclass(frozen=True)
class ValidationCheck:
    """One named validation claim with measured evidence."""

    name: str
    passed: bool
    measured: str
    threshold: str
    explanation: str


@dataclass(frozen=True)
class Task2ValidationReport:
    """Serializable Step 7 validation evidence."""

    model: str
    seed: int | None
    checks: tuple[ValidationCheck, ...]
    controlled_convergence: tuple[ControlledConvergenceRow, ...]
    reference_refinement: tuple[ReferenceRefinementRow, ...]
    interpretation: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Whether every declared validation check passed."""

        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible report."""

        return {
            "model": self.model,
            "seed": self.seed,
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
            "controlled_convergence": [
                asdict(row) for row in self.controlled_convergence
            ],
            "reference_refinement": [
                asdict(row) for row in self.reference_refinement
            ],
            "interpretation": list(self.interpretation),
        }


def _run_controlled_collision(
    *,
    n_steps: int,
    collision_time_ps: float,
) -> float:
    """Return endpoint error for one analytical head-on collision."""

    final_time = 2.0
    time_step = final_time / n_steps
    parameters = BrownianParameters(
        n_small=1,
        small_mass_kg=1.0,
        large_mass_kg=3.0,
        small_radius_nm=0.5,
        large_radius_nm=1.0,
        box_size_nm=20.0,
        max_time_ps=final_time,
        max_step_fraction=1.0,
        requested_time_step_ps=time_step,
        seed=1,
    )
    context = initialize_simulation(parameters, max_frames=2)
    large_start_x = 10.0
    contact_distance = (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    small_start_x = (
        large_start_x - contact_distance - collision_time_ps
    )
    context.state.small_positions_nm[0] = [small_start_x, 10.0]
    context.state.small_velocities_nm_per_ps[0] = [1.0, 0.0]
    context.state.next_randomization_times_ps[0] = final_time + 1.0
    context.state.large_position_nm[:] = [large_start_x, 10.0]
    context.state.large_velocity_nm_per_ps[:] = [0.0, 0.0]

    while context.state.step_index < context.time_grid.n_steps:
        advance_simulation_step(context)

    time_after_collision = final_time - collision_time_ps
    exact_small_x = (
        large_start_x
        - contact_distance
        - 0.5 * time_after_collision
    )
    exact_large_x = large_start_x + 0.5 * time_after_collision
    error_vector = np.array(
        [
            context.state.small_positions_nm[0, 0] - exact_small_x,
            context.state.large_position_nm[0] - exact_large_x,
        ]
    )
    return float(np.linalg.norm(error_vector))


def controlled_collision_convergence(
    *,
    step_counts: Sequence[int] = (16, 32, 64, 128),
    phase_count: int = 61,
) -> tuple[ControlledConvergenceRow, ...]:
    """Measure convergence over collision times spanning grid phases."""

    if len(step_counts) < 3:
        raise ValueError("step_counts must contain at least three resolutions")
    if phase_count < 5:
        raise ValueError("phase_count must be at least 5")
    collision_times = np.linspace(0.603, 1.397, phase_count)
    rows: list[ControlledConvergenceRow] = []
    previous_rms: float | None = None
    previous_time_step: float | None = None

    for raw_n_steps in step_counts:
        if (
            isinstance(raw_n_steps, (bool, np.bool_))
            or not isinstance(raw_n_steps, (int, np.integer))
        ):
            raise ValueError("step_counts must contain positive integers")
        n_steps = int(raw_n_steps)
        if n_steps < 1:
            raise ValueError("step_counts must contain positive integers")
        errors = np.array(
            [
                _run_controlled_collision(
                    n_steps=n_steps,
                    collision_time_ps=float(collision_time),
                )
                for collision_time in collision_times
            ],
            dtype=np.float64,
        )
        rms_error = float(np.sqrt(np.mean(errors**2)))
        observed_order = (
            None
            if previous_rms is None
            else float(
                np.log(previous_rms / rms_error)
                / np.log(previous_time_step / (2.0 / n_steps))
            )
        )
        rows.append(
            ControlledConvergenceRow(
                n_steps=n_steps,
                time_step_ps=2.0 / n_steps,
                rms_endpoint_error_nm=rms_error,
                maximum_endpoint_error_nm=float(np.max(errors)),
                observed_order_from_previous=observed_order,
            )
        )
        previous_rms = rms_error
        previous_time_step = 2.0 / n_steps

    return tuple(rows)


def _geometry_is_valid(result: BrownianSimulationResult) -> bool:
    """Check all recorded geometry, finiteness, walls, and pair clearance."""

    parameters = result.parameters
    arrays = (
        result.large_positions_nm,
        result.large_velocities_nm_per_ps,
        result.small_position_frames_nm,
    )
    if not all(np.all(np.isfinite(array)) for array in arrays):
        return False

    large_low = parameters.large_radius_nm
    large_high = parameters.box_size_nm - parameters.large_radius_nm
    if np.any(result.large_positions_nm < large_low) or np.any(
        result.large_positions_nm > large_high
    ):
        return False

    small_low = parameters.small_radius_nm
    small_high = parameters.box_size_nm - parameters.small_radius_nm
    if np.any(result.small_position_frames_nm < small_low) or np.any(
        result.small_position_frames_nm > small_high
    ):
        return False

    contact_distance = (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    for frame_index, step_index in enumerate(result.frame_steps):
        distances = np.linalg.norm(
            result.small_position_frames_nm[frame_index]
            - result.large_positions_nm[step_index],
            axis=1,
        )
        if np.any(distances <= contact_distance):
            return False
    return True


def reference_time_step_refinement(
    parameters: BrownianParameters | None = None,
    *,
    refinement_factors: Sequence[int] = (1, 2, 4),
    max_frames: int = 20,
) -> tuple[
    tuple[ReferenceRefinementRow, ...],
    tuple[BrownianSimulationResult, ...],
]:
    """Run one reference configuration at aligned fixed-step refinements."""

    if parameters is None:
        parameters = BrownianParameters()
    if any(
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, (int, np.integer))
        for value in refinement_factors
    ):
        raise ValueError("refinement_factors must contain integers")
    factors = tuple(int(value) for value in refinement_factors)
    if len(factors) < 2 or factors[0] != 1:
        raise ValueError("refinement_factors must begin with 1")
    if any(value < 1 for value in factors):
        raise ValueError("refinement_factors must be positive")
    if any(
        current % previous != 0
        for previous, current in zip(factors, factors[1:])
    ):
        raise ValueError(
            "each refinement factor must be a multiple of the previous one"
        )

    base_step = create_time_grid(parameters).step_size_ps
    results: list[BrownianSimulationResult] = []
    rows: list[ReferenceRefinementRow] = []
    previous: BrownianSimulationResult | None = None

    for factor in factors:
        refined_parameters = (
            parameters
            if factor == 1
            else replace(
                parameters,
                requested_time_step_ps=base_step / factor,
            )
        )
        result = run_simulation(
            refined_parameters,
            max_frames=max_frames,
        )
        path_rms: float | None = None
        path_maximum: float | None = None
        if previous is not None:
            ratio = result.time_grid.n_steps // previous.time_grid.n_steps
            if (
                ratio * previous.time_grid.n_steps
                != result.time_grid.n_steps
            ):
                raise RuntimeError("refined time grids are not aligned")
            differences = np.linalg.norm(
                previous.large_positions_nm
                - result.large_positions_nm[::ratio],
                axis=1,
            )
            path_rms = float(np.sqrt(np.mean(differences**2)))
            path_maximum = float(np.max(differences))

        displacement = (
            result.large_positions_nm[-1] - result.large_positions_nm[0]
        )
        diagnostics = result.diagnostics
        rows.append(
            ReferenceRefinementRow(
                refinement_factor=factor,
                n_steps=result.time_grid.n_steps,
                time_step_ps=result.time_grid.step_size_ps,
                final_displacement_x_nm=float(displacement[0]),
                final_displacement_y_nm=float(displacement[1]),
                final_displacement_nm=result.final_displacement_nm,
                rms_path_difference_from_previous_nm=path_rms,
                maximum_path_difference_from_previous_nm=path_maximum,
                total_contacts=diagnostics.total_contacts,
                total_impulses=diagnostics.total_impulses,
                total_direction_resets=diagnostics.total_direction_resets,
                maximum_collision_passes=int(
                    np.max(diagnostics.collision_passes_per_step)
                ),
                maximum_displacement_nm=(
                    diagnostics.maximum_displacement_nm
                ),
                maximum_residual_penetration_nm=(
                    diagnostics.maximum_residual_penetration_nm
                ),
                maximum_normalized_momentum_error=(
                    diagnostics.maximum_normalized_momentum_error
                ),
                maximum_normalized_restitution_error=(
                    diagnostics.maximum_normalized_restitution_error
                ),
                maximum_normalized_energy_identity_error=(
                    diagnostics.maximum_normalized_energy_identity_error
                ),
            )
        )
        results.append(result)
        previous = result

    return tuple(rows), tuple(results)


def _reproducibility_passes() -> bool:
    """Compare every recorded output from two compact equal-seed runs."""

    parameters = BrownianParameters(
        n_small=100,
        max_time_ps=5.0,
        seed=7,
    )
    first = run_simulation(parameters, max_frames=12)
    second = run_simulation(parameters, max_frames=12)
    return all(
        np.array_equal(left, right)
        for left, right in (
            (first.large_positions_nm, second.large_positions_nm),
            (first.large_velocities_nm_per_ps, second.large_velocities_nm_per_ps),
            (first.small_position_frames_nm, second.small_position_frames_nm),
            (
                first.diagnostics.contacts_per_step,
                second.diagnostics.contacts_per_step,
            ),
            (
                first.diagnostics.impulses_per_step,
                second.diagnostics.impulses_per_step,
            ),
            (
                first.diagnostics.direction_resets_per_step,
                second.diagnostics.direction_resets_per_step,
            ),
        )
    )


def run_validation_suite(
    parameters: BrownianParameters | None = None,
    *,
    controlled_step_counts: Sequence[int] = (16, 32, 64, 128),
    controlled_phase_count: int = 61,
    refinement_factors: Sequence[int] = (1, 2, 4),
    max_frames: int = 20,
) -> Task2ValidationReport:
    """Run the complete deterministic and time-step validation suite."""

    if parameters is None:
        parameters = BrownianParameters()
    controlled = controlled_collision_convergence(
        step_counts=controlled_step_counts,
        phase_count=controlled_phase_count,
    )
    refinement, results = reference_time_step_refinement(
        parameters,
        refinement_factors=refinement_factors,
        max_frames=max_frames,
    )

    controlled_errors = [
        row.rms_endpoint_error_nm for row in controlled
    ]
    observed_orders = [
        row.observed_order_from_previous
        for row in controlled
        if row.observed_order_from_previous is not None
    ]
    impulse_counts = np.array(
        [row.total_impulses for row in refinement],
        dtype=np.float64,
    )
    impulse_relative_span = float(
        (np.max(impulse_counts) - np.min(impulse_counts))
        / np.mean(impulse_counts)
    )
    physical_displacement_limit = (
        parameters.max_step_fraction * parameters.small_radius_nm
    )
    baseline_displacement_fraction = (
        refinement[0].maximum_displacement_nm
        / physical_displacement_limit
    )
    worst_collision_identity_error = max(
        max(
            row.maximum_normalized_momentum_error,
            row.maximum_normalized_restitution_error,
            row.maximum_normalized_energy_identity_error,
        )
        for row in refinement
    )
    worst_residual_penetration = max(
        row.maximum_residual_penetration_nm for row in refinement
    )

    checks = (
        ValidationCheck(
            name="controlled_error_decreases",
            passed=all(
                later < earlier
                for earlier, later in zip(
                    controlled_errors,
                    controlled_errors[1:],
                )
            ),
            measured=" -> ".join(
                f"{value:.6e} nm" for value in controlled_errors
            ),
            threshold="strict decrease at every halving",
            explanation=(
                "RMS endpoint error is averaged over collision phases so "
                "grid-alignment accidents do not dominate."
            ),
        ),
        ValidationCheck(
            name="controlled_first_order_convergence",
            passed=min(observed_orders) >= 0.9,
            measured=(
                f"minimum observed order {min(observed_orders):.6f}"
            ),
            threshold="order >= 0.9",
            explanation=(
                "A finite-step overlap correction is expected to converge "
                "approximately at first order."
            ),
        ),
        ValidationCheck(
            name="all_recorded_geometry_valid",
            passed=all(_geometry_is_valid(result) for result in results),
            measured=f"{len(results)} refined runs checked",
            threshold="finite, inside walls, and no recorded overlap",
            explanation=(
                "Every stored frame and every tracer history point is checked."
            ),
        ),
        ValidationCheck(
            name="runtime_displacement_limit",
            passed=all(
                row.maximum_displacement_nm
                <= physical_displacement_limit
                for row in refinement
            ),
            measured=(
                f"baseline uses {baseline_displacement_fraction:.3%} "
                "of limit"
            ),
            threshold=(
                f"maximum displacement <= "
                f"{physical_displacement_limit:.9f} nm"
            ),
            explanation=(
                "The automatic baseline retains margin and refinements reduce "
                "the distance further."
            ),
        ),
        ValidationCheck(
            name="collision_identity_tolerances",
            passed=all(
                max(
                    row.maximum_normalized_momentum_error,
                    row.maximum_normalized_restitution_error,
                    row.maximum_normalized_energy_identity_error,
                )
                < 1.0e-12
                for row in refinement
            ),
            measured=(
                f"worst normalized error "
                f"{worst_collision_identity_error:.6e}"
            ),
            threshold="< 1e-12",
            explanation=(
                "Momentum, restitution, and analytical energy identities are "
                "checked on every applied impulse."
            ),
        ),
        ValidationCheck(
            name="penetration_tolerance",
            passed=all(
                row.maximum_residual_penetration_nm
                <= 1.0e-9
                * (
                    parameters.small_radius_nm
                    + parameters.large_radius_nm
                )
                for row in refinement
            ),
            measured=(
                f"worst residual "
                f"{worst_residual_penetration:.6e} nm"
            ),
            threshold=(
                "<= 1e-9 times the small-large contact distance"
            ),
            explanation="No unresolved overlap remains after a complete step.",
        ),
        ValidationCheck(
            name="collision_pass_convergence",
            passed=all(
                row.maximum_collision_passes
                <= parameters.max_collision_passes
                for row in refinement
            ),
            measured=(
                f"maximum "
                f"{max(row.maximum_collision_passes for row in refinement)} "
                "passes"
            ),
            threshold=(
                f"<= {parameters.max_collision_passes} passes"
            ),
            explanation=(
                "Post-correction walls and simultaneous contacts converge "
                "within the configured ceiling."
            ),
        ),
        ValidationCheck(
            name="refined_impulse_count_stability",
            passed=impulse_relative_span < 0.02,
            measured=(
                f"counts {[int(value) for value in impulse_counts]}; "
                f"relative span {impulse_relative_span:.3%}"
            ),
            threshold="relative span < 2%",
            explanation=(
                "Individual chaotic paths diverge, so the physically relevant "
                "event count is compared instead of pointwise trajectories."
            ),
        ),
        ValidationCheck(
            name="equal_seed_reproducibility",
            passed=_reproducibility_passes(),
            measured="all compact-run arrays compared exactly",
            threshold="bit-for-bit equality",
            explanation=(
                "Positions, velocities, frames, contacts, impulses, and reset "
                "histories must all reproduce."
            ),
        ),
    )

    return Task2ValidationReport(
        model="BPhO 2026 Task 2 Brownian motion",
        seed=parameters.seed,
        checks=checks,
        controlled_convergence=controlled,
        reference_refinement=refinement,
        interpretation=(
            (
                "The controlled collision study demonstrates first-order "
                "finite-step convergence after averaging over collision phase."
            ),
            (
                "Pointwise Brownian trajectories separate under refinement "
                "because collision ordering and random-bath timing make the "
                "many-particle dynamics chaotic."
            ),
            (
                "Applied-impulse counts remain stable across the baseline, "
                "half-step, and quarter-step reference runs; Step 8 will test "
                "ensemble statistics rather than demand identical paths."
            ),
        ),
    )


def write_validation_report(
    report: Task2ValidationReport,
    output_directory: Path | str,
) -> tuple[Path, Path, Path]:
    """Write JSON plus controlled and reference CSV evidence."""

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "reference_validation.json"
    controlled_path = directory / "controlled_collision_convergence.csv"
    refinement_path = directory / "reference_time_step_refinement.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(report.to_dict(), handle, indent=2)
        handle.write("\n")

    controlled_rows = [
        asdict(row) for row in report.controlled_convergence
    ]
    with controlled_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(controlled_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(controlled_rows)

    refinement_rows = [
        asdict(row) for row in report.reference_refinement
    ]
    with refinement_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(refinement_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(refinement_rows)

    return json_path, controlled_path, refinement_path
