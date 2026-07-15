"""Architecture, transport, and collision physics for BPhO 2026 Task 2.

Steps 3 and 4 establish validated parameters, reproducible initialization, a
fixed time grid, free motion, scheduled direction resets, reflecting walls,
and result containers. Step 5 adds independently verified small-large contact
correction and restitution impulses. The complete run loop remains Step 6.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
IntegerArray = NDArray[np.int64]

REFERENCE_AVOGADRO_PER_MOL = 6.02e23
REFERENCE_SMALL_MASS_KG = 28.96e-3 / REFERENCE_AVOGADRO_PER_MOL
REFERENCE_LARGE_MASS_KG = 10.0 * REFERENCE_SMALL_MASS_KG
REFERENCE_BOLTZMANN_J_PER_K = 1.38e-23


def _validated_integer(value: int, name: str, *, minimum: int = 1) -> int:
    """Return an integer after rejecting booleans and low values."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _validated_real(
    value: float,
    name: str,
    *,
    minimum: float = 0.0,
    include_minimum: bool = False,
) -> float:
    """Return a finite real number within the requested lower bound."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    invalid = value < minimum if include_minimum else value <= minimum
    if invalid:
        relation = "at least" if include_minimum else "greater than"
        raise ValueError(f"{name} must be {relation} {minimum}")
    return value


def _validated_seed(seed: int | None) -> int | None:
    """Validate and normalize an optional reproducibility seed."""

    if seed is None:
        return None
    return _validated_integer(seed, "seed", minimum=0)


def _readonly_array(
    value: NDArray[np.generic],
    *,
    dtype: np.dtype[np.generic],
) -> NDArray[np.generic]:
    """Return an owned, read-only NumPy array."""

    array = np.array(value, dtype=dtype, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class BrownianParameters:
    """Validated physical and numerical inputs for the baseline model."""

    n_small: int = 1_000
    small_mass_kg: float = REFERENCE_SMALL_MASS_KG
    large_mass_kg: float = REFERENCE_LARGE_MASS_KG
    small_radius_nm: float = 0.16
    large_radius_nm: float = 1.60
    box_size_nm: float = 11.20
    gas_temperature_k: float = 373.0
    boltzmann_j_per_k: float = REFERENCE_BOLTZMANN_J_PER_K
    knudsen_parameter: float = 15.0
    restitution: float = 1.0
    max_time_ps: float = 200.0
    max_step_fraction: float = 0.10
    randomization_step_fraction: float = 0.01
    automatic_time_step_safety_factor: float = 0.20
    requested_time_step_ps: float | None = None
    max_collision_passes: int = 16
    seed: int | None = 2026

    def __post_init__(self) -> None:
        """Normalize values and enforce architecture-level constraints."""

        object.__setattr__(
            self,
            "n_small",
            _validated_integer(self.n_small, "n_small"),
        )
        object.__setattr__(
            self,
            "max_collision_passes",
            _validated_integer(
                self.max_collision_passes,
                "max_collision_passes",
            ),
        )
        for name in (
            "small_mass_kg",
            "large_mass_kg",
            "small_radius_nm",
            "large_radius_nm",
            "box_size_nm",
            "gas_temperature_k",
            "boltzmann_j_per_k",
            "knudsen_parameter",
            "max_time_ps",
        ):
            object.__setattr__(
                self,
                name,
                _validated_real(getattr(self, name), name),
            )

        restitution = _validated_real(
            self.restitution,
            "restitution",
            minimum=0.0,
            include_minimum=True,
        )
        if restitution > 1.0:
            raise ValueError("restitution must not exceed 1")
        object.__setattr__(self, "restitution", restitution)

        for name in (
            "max_step_fraction",
            "randomization_step_fraction",
            "automatic_time_step_safety_factor",
        ):
            value = _validated_real(getattr(self, name), name)
            if value > 1.0:
                raise ValueError(f"{name} must not exceed 1")
            object.__setattr__(self, name, value)

        object.__setattr__(self, "seed", _validated_seed(self.seed))

        minimum_box_size = 2.0 * (
            self.large_radius_nm + 2.0 * self.small_radius_nm
        )
        if self.box_size_nm <= minimum_box_size:
            raise ValueError(
                "box_size_nm is too small to place a small particle between "
                "the centred large particle and a wall"
            )

        if self.requested_time_step_ps is not None:
            requested = _validated_real(
                self.requested_time_step_ps,
                "requested_time_step_ps",
            )
            object.__setattr__(self, "requested_time_step_ps", requested)
            tolerance = 32.0 * np.finfo(np.float64).eps
            if requested > self.maximum_time_step_ps * (1.0 + tolerance):
                raise ValueError(
                    "requested_time_step_ps exceeds the specification's "
                    "initial stability limit"
                )

    @property
    def small_speed_m_per_s(self) -> float:
        """Three-dimensional RMS thermal speed supplied by the challenge."""

        return float(
            np.sqrt(
                3.0
                * self.boltzmann_j_per_k
                * self.gas_temperature_k
                / self.small_mass_kg
            )
        )

    @property
    def small_speed_nm_per_ps(self) -> float:
        """Reference molecular speed in simulation units."""

        return self.small_speed_m_per_s / 1_000.0

    @property
    def randomization_interval_ps(self) -> float:
        """Time between direction resets in the baseline stochastic bath."""

        return (
            self.knudsen_parameter
            * self.small_radius_nm
            / self.small_speed_nm_per_ps
        )

    @property
    def displacement_limited_time_step_ps(self) -> float:
        """Largest initial step allowed by the displacement criterion."""

        return (
            self.max_step_fraction
            * self.small_radius_nm
            / self.small_speed_nm_per_ps
        )

    @property
    def randomization_limited_time_step_ps(self) -> float:
        """Largest step allowed as a fraction of a reset interval."""

        return (
            self.randomization_step_fraction
            * self.randomization_interval_ps
        )

    @property
    def maximum_time_step_ps(self) -> float:
        """Initial upper bound satisfying both time-step criteria."""

        return min(
            self.displacement_limited_time_step_ps,
            self.randomization_limited_time_step_ps,
        )

    @property
    def collision_clearance_nm(self) -> float:
        """Floating-point clearance added by overlap correction."""

        return (
            64.0
            * np.finfo(np.float64).eps
            * max(
                self.small_radius_nm + self.large_radius_nm,
                self.box_size_nm,
                1.0,
            )
        )

    @property
    def automatic_time_step_upper_bound_ps(self) -> float:
        """Conservative default step below the nominal stability ceiling."""

        return (
            self.automatic_time_step_safety_factor
            * self.maximum_time_step_ps
        )


@dataclass(frozen=True)
class FixedTimeGrid:
    """Read-only fixed-step timeline reaching the requested end exactly."""

    step_size_ps: float
    n_steps: int
    times_ps: FloatArray

    def __post_init__(self) -> None:
        """Validate shape, spacing, and immutability of the timeline."""

        step_size = _validated_real(self.step_size_ps, "step_size_ps")
        n_steps = _validated_integer(self.n_steps, "n_steps")
        times = np.asarray(self.times_ps, dtype=np.float64)
        if times.shape != (n_steps + 1,):
            raise ValueError("times_ps must have shape (n_steps + 1,)")
        if not np.all(np.isfinite(times)):
            raise ValueError("times_ps must contain only finite values")
        if times[0] != 0.0:
            raise ValueError("times_ps must begin at zero")
        spacing_tolerance = (
            4.0
            * np.finfo(np.float64).eps
            * max(abs(float(times[-1])), 1.0)
        )
        if not np.allclose(
            np.diff(times),
            step_size,
            rtol=8.0 * np.finfo(np.float64).eps,
            atol=spacing_tolerance,
        ):
            raise ValueError("times_ps must be uniformly spaced")
        if not np.isclose(
            times[-1],
            n_steps * step_size,
            rtol=8.0 * np.finfo(np.float64).eps,
            atol=spacing_tolerance,
        ):
            raise ValueError("final time must equal n_steps * step_size_ps")

        object.__setattr__(self, "step_size_ps", step_size)
        object.__setattr__(self, "n_steps", n_steps)
        object.__setattr__(
            self,
            "times_ps",
            _readonly_array(times, dtype=np.dtype(np.float64)),
        )

    @property
    def final_time_ps(self) -> float:
        """Final represented simulation time."""

        return float(self.times_ps[-1])


def create_time_grid(parameters: BrownianParameters) -> FixedTimeGrid:
    """Build a fixed grid no larger than the allowed step.

    The candidate step is treated as an upper bound. Dividing max_time_ps by a
    ceiling number of steps makes the final time exact while only reducing the
    step size.
    """

    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")
    upper_bound = (
        parameters.automatic_time_step_upper_bound_ps
        if parameters.requested_time_step_ps is None
        else parameters.requested_time_step_ps
    )
    n_steps = int(np.ceil(parameters.max_time_ps / upper_bound))
    step_size = parameters.max_time_ps / n_steps
    times = np.linspace(
        0.0,
        parameters.max_time_ps,
        n_steps + 1,
        dtype=np.float64,
    )
    return FixedTimeGrid(
        step_size_ps=step_size,
        n_steps=n_steps,
        times_ps=times,
    )


def build_frame_steps(
    n_steps: int,
    *,
    max_frames: int = 240,
) -> IntegerArray:
    """Select monotonic physics steps for memory-aware display frames."""

    n_steps = _validated_integer(n_steps, "n_steps")
    max_frames = _validated_integer(max_frames, "max_frames", minimum=2)
    count = min(n_steps + 1, max_frames)
    steps = np.unique(
        np.rint(np.linspace(0, n_steps, count)).astype(np.int64)
    )
    steps.setflags(write=False)
    return steps


@dataclass
class SimulationState:
    """Mutable current state used by future in-place physics updates."""

    small_positions_nm: FloatArray
    small_velocities_nm_per_ps: FloatArray
    next_randomization_times_ps: FloatArray
    large_position_nm: FloatArray
    large_velocity_nm_per_ps: FloatArray
    time_ps: float = 0.0
    step_index: int = 0

    def __post_init__(self) -> None:
        """Own state arrays and validate architecture-level shapes."""

        positions = np.array(
            self.small_positions_nm,
            dtype=np.float64,
            copy=True,
        )
        velocities = np.array(
            self.small_velocities_nm_per_ps,
            dtype=np.float64,
            copy=True,
        )
        reset_times = np.array(
            self.next_randomization_times_ps,
            dtype=np.float64,
            copy=True,
        )
        large_position = np.array(
            self.large_position_nm,
            dtype=np.float64,
            copy=True,
        )
        large_velocity = np.array(
            self.large_velocity_nm_per_ps,
            dtype=np.float64,
            copy=True,
        )

        if positions.ndim != 2 or positions.shape[1] != 2:
            raise ValueError("small_positions_nm must have shape (N, 2)")
        if len(positions) < 1:
            raise ValueError("SimulationState must contain a small particle")
        if velocities.shape != positions.shape:
            raise ValueError(
                "small_velocities_nm_per_ps must match small_positions_nm"
            )
        if reset_times.shape != (len(positions),):
            raise ValueError(
                "next_randomization_times_ps must have shape (N,)"
            )
        if large_position.shape != (2,):
            raise ValueError("large_position_nm must have shape (2,)")
        if large_velocity.shape != (2,):
            raise ValueError("large_velocity_nm_per_ps must have shape (2,)")

        time_ps = _validated_real(
            self.time_ps,
            "time_ps",
            minimum=0.0,
            include_minimum=True,
        )
        step_index = _validated_integer(
            self.step_index,
            "step_index",
            minimum=0,
        )

        self.small_positions_nm = positions
        self.small_velocities_nm_per_ps = velocities
        self.next_randomization_times_ps = reset_times
        self.large_position_nm = large_position
        self.large_velocity_nm_per_ps = large_velocity
        self.time_ps = time_ps
        self.step_index = step_index

    @property
    def n_small(self) -> int:
        """Number of small particles in this state."""

        return len(self.small_positions_nm)

    @property
    def small_speeds_nm_per_ps(self) -> FloatArray:
        """Current speed of every small particle."""

        return np.linalg.norm(self.small_velocities_nm_per_ps, axis=1)

    def copy(self) -> SimulationState:
        """Return a deep copy suitable for independent mutation."""

        return SimulationState(
            small_positions_nm=self.small_positions_nm,
            small_velocities_nm_per_ps=self.small_velocities_nm_per_ps,
            next_randomization_times_ps=self.next_randomization_times_ps,
            large_position_nm=self.large_position_nm,
            large_velocity_nm_per_ps=self.large_velocity_nm_per_ps,
            time_ps=self.time_ps,
            step_index=self.step_index,
        )


@dataclass(frozen=True)
class InitializationValidationReport:
    """Deterministic validation summary for one initialized state."""

    passed: bool
    failures: tuple[str, ...]
    minimum_small_large_clearance_nm: float
    maximum_small_speed_error_nm_per_ps: float


@dataclass(frozen=True)
class WallReflectionReport:
    """Number of radius-aware wall impacts resolved in one operation."""

    small_particle_impacts: int
    large_particle_impacts: int

    @property
    def total_impacts(self) -> int:
        """Total impacts across both particle classes."""

        return self.small_particle_impacts + self.large_particle_impacts


@dataclass(frozen=True)
class TransportStepReport:
    """Verified summary of one reset-motion-wall transport step."""

    step_index: int
    start_time_ps: float
    end_time_ps: float
    time_step_ps: float
    direction_resets: int
    small_wall_impacts: int
    large_wall_impacts: int
    maximum_displacement_nm: float
    displacement_limit_nm: float
    maximum_small_speed_error_nm_per_ps: float

    @property
    def total_wall_impacts(self) -> int:
        """Total wall impacts resolved during this step."""

        return self.small_wall_impacts + self.large_wall_impacts


@dataclass(frozen=True)
class CollisionEventReport:
    """Numerical evidence for one detected small-large contact."""

    small_particle_index: int
    contact_normal: tuple[float, float]
    distance_before_nm: float
    penetration_before_nm: float
    distance_after_correction_nm: float
    residual_penetration_nm: float
    relative_normal_speed_before_nm_per_ps: float
    relative_normal_speed_after_nm_per_ps: float
    relative_tangential_speed_change_nm_per_ps: float
    impulse_applied: bool
    impulse_magnitude_kg_nm_per_ps: float
    normalized_momentum_error: float
    normalized_restitution_error: float
    kinetic_energy_change_j: float
    expected_kinetic_energy_change_j: float
    normalized_energy_identity_error: float


@dataclass(frozen=True)
class CollisionBatchReport:
    """Immutable collection and aggregate diagnostics for one collision pass."""

    events: tuple[CollisionEventReport, ...]

    @property
    def contacts_detected(self) -> int:
        """Number of touching or overlapping pairs processed."""

        return len(self.events)

    @property
    def impulses_applied(self) -> int:
        """Number of approaching contacts that received an impulse."""

        return sum(event.impulse_applied for event in self.events)

    @property
    def separating_contacts(self) -> int:
        """Number of contacts corrected without an impulse."""

        return self.contacts_detected - self.impulses_applied

    @property
    def maximum_residual_penetration_nm(self) -> float:
        """Greatest remaining penetration after positional correction."""

        return max(
            (event.residual_penetration_nm for event in self.events),
            default=0.0,
        )

    @property
    def maximum_normalized_momentum_error(self) -> float:
        """Worst normalized momentum residual among applied impulses."""

        return max(
            (
                event.normalized_momentum_error
                for event in self.events
                if event.impulse_applied
            ),
            default=0.0,
        )

    @property
    def maximum_normalized_restitution_error(self) -> float:
        """Worst normalized restitution residual among applied impulses."""

        return max(
            (
                event.normalized_restitution_error
                for event in self.events
                if event.impulse_applied
            ),
            default=0.0,
        )

    @property
    def maximum_normalized_energy_identity_error(self) -> float:
        """Worst normalized analytical-energy residual."""

        return max(
            (
                event.normalized_energy_identity_error
                for event in self.events
                if event.impulse_applied
            ),
            default=0.0,
        )

    @property
    def total_kinetic_energy_change_j(self) -> float:
        """Sum of measured kinetic-energy changes in this collision pass."""

        return sum(event.kinetic_energy_change_j for event in self.events)


@dataclass(frozen=True)
class SimulationStepReport:
    """Combined evidence from one complete transport-collision step."""

    transport: TransportStepReport
    collisions: CollisionBatchReport
    collision_passes: int
    post_collision_wall_impacts: WallReflectionReport
    remaining_contacts: int

    @property
    def total_small_wall_impacts(self) -> int:
        """Small-particle wall impacts before and after collision correction."""

        return (
            self.transport.small_wall_impacts
            + self.post_collision_wall_impacts.small_particle_impacts
        )

    @property
    def total_large_wall_impacts(self) -> int:
        """Large-particle wall impacts before and after collision correction."""

        return (
            self.transport.large_wall_impacts
            + self.post_collision_wall_impacts.large_particle_impacts
        )


@dataclass(frozen=True)
class SimulationDiagnostics:
    """Read-only step histories and aggregate numerical validation evidence."""

    direction_resets_per_step: IntegerArray
    small_wall_impacts_per_step: IntegerArray
    large_wall_impacts_per_step: IntegerArray
    contacts_per_step: IntegerArray
    impulses_per_step: IntegerArray
    collision_passes_per_step: IntegerArray
    maximum_displacement_nm: float
    maximum_residual_penetration_nm: float
    maximum_normalized_momentum_error: float
    maximum_normalized_restitution_error: float
    maximum_normalized_energy_identity_error: float
    total_collision_energy_change_j: float

    def __post_init__(self) -> None:
        """Validate count histories, scalar evidence, and immutable ownership."""

        names = (
            "direction_resets_per_step",
            "small_wall_impacts_per_step",
            "large_wall_impacts_per_step",
            "contacts_per_step",
            "impulses_per_step",
            "collision_passes_per_step",
        )
        arrays: list[IntegerArray] = []
        expected_shape: tuple[int, ...] | None = None
        for name in names:
            raw = np.asarray(getattr(self, name))
            if raw.ndim != 1:
                raise ValueError(f"{name} must be one-dimensional")
            if not np.issubdtype(raw.dtype, np.integer):
                raise TypeError(f"{name} must contain integers")
            array = np.asarray(raw, dtype=np.int64)
            if np.any(array < 0):
                raise ValueError(f"{name} must be non-negative")
            if expected_shape is None:
                expected_shape = array.shape
            elif array.shape != expected_shape:
                raise ValueError("all diagnostic histories must have one shape")
            arrays.append(array)

        for name, array in zip(names, arrays):
            object.__setattr__(
                self,
                name,
                _readonly_array(array, dtype=np.dtype(np.int64)),
            )

        nonnegative_names = (
            "maximum_displacement_nm",
            "maximum_residual_penetration_nm",
            "maximum_normalized_momentum_error",
            "maximum_normalized_restitution_error",
            "maximum_normalized_energy_identity_error",
        )
        for name in nonnegative_names:
            value = _validated_real(
                getattr(self, name),
                name,
                minimum=0.0,
                include_minimum=True,
            )
            object.__setattr__(self, name, value)
        energy_change = _validated_real(
            self.total_collision_energy_change_j,
            "total_collision_energy_change_j",
            minimum=-np.inf,
            include_minimum=True,
        )
        object.__setattr__(
            self,
            "total_collision_energy_change_j",
            energy_change,
        )

    @classmethod
    def zeros(cls, n_steps: int) -> SimulationDiagnostics:
        """Create a valid empty diagnostic record for a known run length."""

        n_steps = _validated_integer(n_steps, "n_steps")
        zero_counts = np.zeros(n_steps, dtype=np.int64)
        return cls(
            direction_resets_per_step=zero_counts,
            small_wall_impacts_per_step=zero_counts,
            large_wall_impacts_per_step=zero_counts,
            contacts_per_step=zero_counts,
            impulses_per_step=zero_counts,
            collision_passes_per_step=zero_counts,
            maximum_displacement_nm=0.0,
            maximum_residual_penetration_nm=0.0,
            maximum_normalized_momentum_error=0.0,
            maximum_normalized_restitution_error=0.0,
            maximum_normalized_energy_identity_error=0.0,
            total_collision_energy_change_j=0.0,
        )

    @property
    def n_steps(self) -> int:
        """Number of represented physics steps."""

        return len(self.contacts_per_step)

    @property
    def total_direction_resets(self) -> int:
        """Total direction resets in the run."""

        return int(np.sum(self.direction_resets_per_step))

    @property
    def total_small_wall_impacts(self) -> int:
        """Total small-particle wall impacts in the run."""

        return int(np.sum(self.small_wall_impacts_per_step))

    @property
    def total_large_wall_impacts(self) -> int:
        """Total large-particle wall impacts in the run."""

        return int(np.sum(self.large_wall_impacts_per_step))

    @property
    def total_contacts(self) -> int:
        """Total small-large contacts processed."""

        return int(np.sum(self.contacts_per_step))

    @property
    def total_impulses(self) -> int:
        """Total approaching contacts receiving impulses."""

        return int(np.sum(self.impulses_per_step))


def validate_initial_state(
    state: SimulationState,
    parameters: BrownianParameters,
) -> InitializationValidationReport:
    """Validate exact initial geometry, velocity, phase, and time contracts."""

    if not isinstance(state, SimulationState):
        raise TypeError("state must be SimulationState")
    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")

    failures: list[str] = []
    if state.n_small != parameters.n_small:
        failures.append(
            f"state contains {state.n_small} small particles, "
            f"expected {parameters.n_small}"
        )

    arrays = (
        state.small_positions_nm,
        state.small_velocities_nm_per_ps,
        state.next_randomization_times_ps,
        state.large_position_nm,
        state.large_velocity_nm_per_ps,
    )
    if not all(np.all(np.isfinite(array)) for array in arrays):
        failures.append(
            "all initialized coordinates, velocities, and times must be finite"
        )

    scale = max(parameters.box_size_nm, 1.0)
    tolerance = 64.0 * np.finfo(np.float64).eps * scale
    centre = np.full(2, parameters.box_size_nm / 2.0, dtype=np.float64)

    if state.step_index != 0 or state.time_ps != 0.0:
        failures.append("initialized state must be at step 0 and time 0")
    if not np.allclose(
        state.large_position_nm,
        centre,
        rtol=0.0,
        atol=tolerance,
    ):
        failures.append("large particle must begin at the box centre")
    if not np.array_equal(
        state.large_velocity_nm_per_ps,
        np.zeros(2, dtype=np.float64),
    ):
        failures.append("large particle must begin exactly at rest")

    positions = state.small_positions_nm
    low = parameters.small_radius_nm - tolerance
    high = parameters.box_size_nm - parameters.small_radius_nm + tolerance
    if np.any(positions < low) or np.any(positions > high):
        failures.append(
            "small-particle centres must lie inside radius-aware walls"
        )

    separations = np.linalg.norm(
        positions - state.large_position_nm,
        axis=1,
    )
    clearance = separations - (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    minimum_clearance = float(np.min(clearance))
    if minimum_clearance <= -tolerance:
        failures.append("small particles must not overlap the large particle")

    speed_errors = np.abs(
        state.small_speeds_nm_per_ps
        - parameters.small_speed_nm_per_ps
    )
    maximum_speed_error = float(np.max(speed_errors))
    speed_tolerance = (
        64.0
        * np.finfo(np.float64).eps
        * max(parameters.small_speed_nm_per_ps, 1.0)
    )
    if maximum_speed_error > speed_tolerance:
        failures.append(
            "all initial small particles must have the reference speed"
        )

    reset_times = state.next_randomization_times_ps
    if np.any(reset_times < 0.0) or np.any(
        reset_times >= parameters.randomization_interval_ps
    ):
        failures.append(
            "initial reset times must lie in [0, randomization_interval_ps)"
        )

    return InitializationValidationReport(
        passed=not failures,
        failures=tuple(failures),
        minimum_small_large_clearance_nm=minimum_clearance,
        maximum_small_speed_error_nm_per_ps=maximum_speed_error,
    )


def _sample_small_positions(
    parameters: BrownianParameters,
    rng: np.random.Generator,
) -> FloatArray:
    """Sample independent positions outside the centred large particle."""

    positions = np.empty((parameters.n_small, 2), dtype=np.float64)
    centre = np.full(2, parameters.box_size_nm / 2.0, dtype=np.float64)
    minimum_separation = (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    filled = 0
    sampled = 0
    maximum_samples = max(10_000, 1_000 * parameters.n_small)

    while filled < parameters.n_small:
        batch_size = max(64, 2 * (parameters.n_small - filled))
        candidates = rng.uniform(
            parameters.small_radius_nm,
            parameters.box_size_nm - parameters.small_radius_nm,
            size=(batch_size, 2),
        )
        separations = np.linalg.norm(candidates - centre, axis=1)
        valid = candidates[separations > minimum_separation]
        take = min(len(valid), parameters.n_small - filled)
        positions[filled : filled + take] = valid[:take]
        filled += take
        sampled += batch_size
        if sampled > maximum_samples and filled < parameters.n_small:
            raise RuntimeError(
                "could not initialize small particles outside the large particle"
            )

    return positions


@dataclass
class SimulationContext:
    """Parameters, grid, mutable state, and future reset random stream."""

    parameters: BrownianParameters
    time_grid: FixedTimeGrid
    frame_steps: IntegerArray
    state: SimulationState
    reset_rng: np.random.Generator
    initialization_report: InitializationValidationReport

    def __post_init__(self) -> None:
        """Validate context contracts without advancing any physics."""

        if not isinstance(self.parameters, BrownianParameters):
            raise TypeError("parameters must be BrownianParameters")
        if not isinstance(self.time_grid, FixedTimeGrid):
            raise TypeError("time_grid must be FixedTimeGrid")
        if not isinstance(self.state, SimulationState):
            raise TypeError("state must be SimulationState")
        if not isinstance(self.reset_rng, np.random.Generator):
            raise TypeError("reset_rng must be a numpy.random.Generator")
        if not isinstance(
            self.initialization_report,
            InitializationValidationReport,
        ):
            raise TypeError(
                "initialization_report must be InitializationValidationReport"
            )
        if self.state.n_small != self.parameters.n_small:
            raise ValueError(
                "state particle count must match parameters.n_small"
            )
        if not self.initialization_report.passed:
            raise ValueError("initialization_report must record a valid state")
        time_tolerance = (
            8.0
            * np.finfo(np.float64).eps
            * max(self.parameters.max_time_ps, 1.0)
        )
        if not np.isclose(
            self.time_grid.final_time_ps,
            self.parameters.max_time_ps,
            rtol=8.0 * np.finfo(np.float64).eps,
            atol=time_tolerance,
        ):
            raise ValueError(
                "time_grid final time must match parameters.max_time_ps"
            )

        frame_steps = np.asarray(self.frame_steps, dtype=np.int64)
        if frame_steps.ndim != 1 or len(frame_steps) < 2:
            raise ValueError("frame_steps must be a one-dimensional schedule")
        if frame_steps[0] != 0 or frame_steps[-1] != self.time_grid.n_steps:
            raise ValueError(
                "frame_steps must include step 0 and the final step"
            )
        if np.any(np.diff(frame_steps) <= 0):
            raise ValueError("frame_steps must be strictly increasing")
        self.frame_steps = _readonly_array(
            frame_steps,
            dtype=np.dtype(np.int64),
        )


def initialize_simulation(
    parameters: BrownianParameters | None = None,
    *,
    max_frames: int = 240,
) -> SimulationContext:
    """Create a valid, reproducible context without advancing the model."""

    if parameters is None:
        parameters = BrownianParameters()
    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")

    seed_sequence = np.random.SeedSequence(parameters.seed)
    (
        position_sequence,
        initial_direction_sequence,
        phase_sequence,
        reset_sequence,
    ) = seed_sequence.spawn(4)
    position_rng = np.random.default_rng(position_sequence)
    initial_direction_rng = np.random.default_rng(initial_direction_sequence)
    phase_rng = np.random.default_rng(phase_sequence)
    reset_rng = np.random.default_rng(reset_sequence)

    small_positions = _sample_small_positions(parameters, position_rng)
    angles = initial_direction_rng.uniform(
        0.0,
        2.0 * np.pi,
        size=parameters.n_small,
    )
    small_velocities = parameters.small_speed_nm_per_ps * np.column_stack(
        (np.cos(angles), np.sin(angles))
    )
    next_reset_times = phase_rng.uniform(
        0.0,
        parameters.randomization_interval_ps,
        size=parameters.n_small,
    )
    centre = np.full(2, parameters.box_size_nm / 2.0, dtype=np.float64)
    state = SimulationState(
        small_positions_nm=small_positions,
        small_velocities_nm_per_ps=small_velocities,
        next_randomization_times_ps=next_reset_times,
        large_position_nm=centre,
        large_velocity_nm_per_ps=np.zeros(2, dtype=np.float64),
    )
    report = validate_initial_state(state, parameters)
    if not report.passed:
        details = "; ".join(report.failures)
        raise RuntimeError(f"initialized state failed validation: {details}")

    time_grid = create_time_grid(parameters)
    return SimulationContext(
        parameters=parameters,
        time_grid=time_grid,
        frame_steps=build_frame_steps(
            time_grid.n_steps,
            max_frames=max_frames,
        ),
        state=state,
        reset_rng=reset_rng,
        initialization_report=report,
    )


def _validate_runtime_state(
    state: SimulationState,
    parameters: BrownianParameters,
) -> None:
    """Reject a malformed runtime state before an in-place update."""

    if not isinstance(state, SimulationState):
        raise TypeError("state must be SimulationState")
    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")
    if state.n_small != parameters.n_small:
        raise ValueError("state particle count must match parameters.n_small")

    arrays = (
        state.small_positions_nm,
        state.small_velocities_nm_per_ps,
        state.next_randomization_times_ps,
        state.large_position_nm,
        state.large_velocity_nm_per_ps,
    )
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise ValueError("runtime coordinates, velocities, and times must be finite")
    if not np.isfinite(state.time_ps):
        raise ValueError("state.time_ps must be finite")
    if (
        isinstance(state.step_index, (bool, np.bool_))
        or not isinstance(state.step_index, (int, np.integer))
        or state.step_index < 0
    ):
        raise ValueError("state.step_index must be a non-negative integer")

    tolerance = (
        64.0
        * np.finfo(np.float64).eps
        * max(parameters.box_size_nm, 1.0)
    )
    small_low = parameters.small_radius_nm - tolerance
    small_high = (
        parameters.box_size_nm - parameters.small_radius_nm + tolerance
    )
    if np.any(state.small_positions_nm < small_low) or np.any(
        state.small_positions_nm > small_high
    ):
        raise ValueError("small-particle centres begin outside their wall limits")

    large_low = parameters.large_radius_nm - tolerance
    large_high = (
        parameters.box_size_nm - parameters.large_radius_nm + tolerance
    )
    if np.any(state.large_position_nm < large_low) or np.any(
        state.large_position_nm > large_high
    ):
        raise ValueError("large-particle centre begins outside its wall limits")


def _expired_direction_mask(
    state: SimulationState,
    parameters: BrownianParameters,
) -> NDArray[np.bool_]:
    """Return resets due at the state's current time and reject stale timers."""

    expired = state.next_randomization_times_ps <= state.time_ps
    if np.any(
        state.next_randomization_times_ps[expired]
        + parameters.randomization_interval_ps
        <= state.time_ps
    ):
        raise RuntimeError(
            "a direction-reset timer is more than one interval overdue"
        )
    return expired


def _apply_direction_resets(
    state: SimulationState,
    parameters: BrownianParameters,
    rng: np.random.Generator,
    expired: NDArray[np.bool_],
) -> int:
    """Apply one reset to each selected particle and advance its timer."""

    count = int(np.count_nonzero(expired))
    if count == 0:
        return 0
    angles = rng.uniform(0.0, 2.0 * np.pi, size=count)
    state.small_velocities_nm_per_ps[expired] = (
        parameters.small_speed_nm_per_ps
        * np.column_stack((np.cos(angles), np.sin(angles)))
    )
    state.next_randomization_times_ps[expired] += (
        parameters.randomization_interval_ps
    )
    return count


def randomize_expired_directions(
    state: SimulationState,
    parameters: BrownianParameters,
    rng: np.random.Generator,
) -> int:
    """Reset all directions due at the current state time.

    Each affected particle receives a uniform independent angle, its prescribed
    thermal speed is restored, and its deadline advances by exactly one
    randomization interval.
    """

    _validate_runtime_state(state, parameters)
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    expired = _expired_direction_mask(state, parameters)
    return _apply_direction_resets(state, parameters, rng, expired)


def advance_free_motion(
    state: SimulationState,
    time_step_ps: float,
) -> float:
    """Advance all positions in place at constant velocity.

    Time and step counters are intentionally unchanged here; the ordered
    transport-step function commits those values only after wall resolution.
    The returned value is the greatest distance moved by any particle.
    """

    if not isinstance(state, SimulationState):
        raise TypeError("state must be SimulationState")
    time_step = _validated_real(time_step_ps, "time_step_ps")
    velocity_arrays = (
        state.small_velocities_nm_per_ps,
        state.large_velocity_nm_per_ps,
    )
    if not all(np.all(np.isfinite(array)) for array in velocity_arrays):
        raise ValueError("velocities must be finite before free motion")

    maximum_speed = max(
        float(np.max(state.small_speeds_nm_per_ps)),
        float(np.linalg.norm(state.large_velocity_nm_per_ps)),
    )
    state.small_positions_nm += (
        state.small_velocities_nm_per_ps * time_step
    )
    state.large_position_nm += state.large_velocity_nm_per_ps * time_step
    return maximum_speed * time_step


def _reflect_array_at_square_walls(
    positions_nm: FloatArray,
    velocities_nm_per_ps: FloatArray,
    *,
    radius_nm: float,
    box_size_nm: float,
) -> int:
    """Resolve any number of one-dimensional wall crossings per coordinate."""

    if positions_nm.ndim != 2 or positions_nm.shape[1] != 2:
        raise ValueError("positions_nm must have shape (N, 2)")
    if velocities_nm_per_ps.shape != positions_nm.shape:
        raise ValueError("velocities_nm_per_ps must match positions_nm")
    if not np.all(np.isfinite(positions_nm)) or not np.all(
        np.isfinite(velocities_nm_per_ps)
    ):
        raise ValueError("wall inputs must be finite")

    low = radius_nm
    high = box_size_nm - radius_nm
    width = high - low
    total_impacts = 0

    for axis in range(2):
        unfolded = positions_nm[:, axis] - low
        velocity = velocities_nm_per_ps[:, axis]
        moving_positive = velocity > 0.0
        moving_negative = velocity < 0.0

        impossible = (
            ((unfolded < 0.0) & ~moving_negative)
            | ((unfolded > width) & ~moving_positive)
        )
        if np.any(impossible):
            raise ValueError(
                "an out-of-bounds coordinate is inconsistent with its velocity"
            )

        impacts = np.zeros(len(unfolded), dtype=np.int64)
        right_crossing = moving_positive & (unfolded >= width)
        impacts[right_crossing] = np.floor(
            unfolded[right_crossing] / width
        ).astype(np.int64)
        left_crossing = moving_negative & (unfolded <= 0.0)
        impacts[left_crossing] = (
            np.floor(-unfolded[left_crossing] / width).astype(np.int64)
            + 1
        )

        phase = np.mod(unfolded, 2.0 * width)
        folded = np.where(phase <= width, phase, 2.0 * width - phase)
        positions_nm[:, axis] = np.clip(low + folded, low, high)
        odd_impacts = impacts % 2 == 1
        velocities_nm_per_ps[odd_impacts, axis] *= -1.0
        total_impacts += int(np.sum(impacts))

    return total_impacts


def reflect_square_walls(
    state: SimulationState,
    parameters: BrownianParameters,
) -> WallReflectionReport:
    """Apply elastic, radius-aware reflections to small and large particles."""

    if not isinstance(state, SimulationState):
        raise TypeError("state must be SimulationState")
    if not isinstance(parameters, BrownianParameters):
        raise TypeError("parameters must be BrownianParameters")

    small_impacts = _reflect_array_at_square_walls(
        state.small_positions_nm,
        state.small_velocities_nm_per_ps,
        radius_nm=parameters.small_radius_nm,
        box_size_nm=parameters.box_size_nm,
    )
    large_impacts = _reflect_array_at_square_walls(
        state.large_position_nm.reshape(1, 2),
        state.large_velocity_nm_per_ps.reshape(1, 2),
        radius_nm=parameters.large_radius_nm,
        box_size_nm=parameters.box_size_nm,
    )
    return WallReflectionReport(
        small_particle_impacts=small_impacts,
        large_particle_impacts=large_impacts,
    )


def advance_transport_step(
    context: SimulationContext,
) -> TransportStepReport:
    """Execute one ordered reset-motion-wall step and commit exact grid time."""

    if not isinstance(context, SimulationContext):
        raise TypeError("context must be SimulationContext")
    state = context.state
    parameters = context.parameters
    _validate_runtime_state(state, parameters)

    if state.step_index >= context.time_grid.n_steps:
        raise RuntimeError("the simulation is already at its final time")
    expected_start = context.time_grid.times_ps[state.step_index]
    time_tolerance = (
        8.0
        * np.finfo(np.float64).eps
        * max(parameters.max_time_ps, 1.0)
    )
    if not np.isclose(
        state.time_ps,
        expected_start,
        rtol=8.0 * np.finfo(np.float64).eps,
        atol=time_tolerance,
    ):
        raise RuntimeError("state time and step index do not match the time grid")

    expired = _expired_direction_mask(state, parameters)
    effective_small_speeds = state.small_speeds_nm_per_ps.copy()
    effective_small_speeds[expired] = parameters.small_speed_nm_per_ps
    maximum_speed = max(
        float(np.max(effective_small_speeds)),
        float(np.linalg.norm(state.large_velocity_nm_per_ps)),
    )
    maximum_displacement = maximum_speed * context.time_grid.step_size_ps
    displacement_limit = (
        parameters.max_step_fraction * parameters.small_radius_nm
    )
    displacement_tolerance = (
        64.0
        * np.finfo(np.float64).eps
        * max(displacement_limit, 1.0)
    )
    if maximum_displacement > displacement_limit + displacement_tolerance:
        raise RuntimeError(
            "time-step displacement limit exceeded; repeat with a smaller step"
        )

    start_time = float(expected_start)
    reset_count = _apply_direction_resets(
        state,
        parameters,
        context.reset_rng,
        expired,
    )
    measured_displacement = advance_free_motion(
        state,
        context.time_grid.step_size_ps,
    )
    wall_report = reflect_square_walls(state, parameters)

    state.step_index += 1
    state.time_ps = float(context.time_grid.times_ps[state.step_index])
    _validate_runtime_state(state, parameters)

    small_speed_error = float(
        np.max(
            np.abs(
                state.small_speeds_nm_per_ps
                - parameters.small_speed_nm_per_ps
            )
        )
    )
    return TransportStepReport(
        step_index=state.step_index,
        start_time_ps=start_time,
        end_time_ps=state.time_ps,
        time_step_ps=context.time_grid.step_size_ps,
        direction_resets=reset_count,
        small_wall_impacts=wall_report.small_particle_impacts,
        large_wall_impacts=wall_report.large_particle_impacts,
        maximum_displacement_nm=measured_displacement,
        displacement_limit_nm=displacement_limit,
        maximum_small_speed_error_nm_per_ps=small_speed_error,
    )


def _kinetic_energy_model_units(
    small_velocity_nm_per_ps: FloatArray,
    large_velocity_nm_per_ps: FloatArray,
    parameters: BrownianParameters,
) -> float:
    """Pair kinetic energy in kg nm² ps⁻² before conversion to joules."""

    return 0.5 * (
        parameters.small_mass_kg
        * float(np.dot(small_velocity_nm_per_ps, small_velocity_nm_per_ps))
        + parameters.large_mass_kg
        * float(np.dot(large_velocity_nm_per_ps, large_velocity_nm_per_ps))
    )


def resolve_small_large_collisions(
    state: SimulationState,
    parameters: BrownianParameters,
) -> CollisionBatchReport:
    """Resolve one deterministic pass of small-large contacts.

    Candidate small particles are processed in ascending index order. Position
    and velocity changes are prepared on copies and committed only after the
    entire pass succeeds, so a coincident-centre error cannot leave a partially
    updated state. Small-small contacts are deliberately ignored.
    """

    _validate_runtime_state(state, parameters)
    contact_distance = (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    displacements = state.large_position_nm - state.small_positions_nm
    distances = np.linalg.norm(displacements, axis=1)
    candidates = np.flatnonzero(distances <= contact_distance)
    if len(candidates) == 0:
        return CollisionBatchReport(events=())
    if np.any(distances[candidates] == 0.0):
        raise RuntimeError(
            "cannot resolve a collision with exactly coincident centres"
        )

    small_positions = state.small_positions_nm.copy()
    small_velocities = state.small_velocities_nm_per_ps.copy()
    large_position = state.large_position_nm.copy()
    large_velocity = state.large_velocity_nm_per_ps.copy()
    reports: list[CollisionEventReport] = []

    small_mass = parameters.small_mass_kg
    large_mass = parameters.large_mass_kg
    total_mass = small_mass + large_mass
    reduced_mass = small_mass * large_mass / total_mass
    clearance = parameters.collision_clearance_nm
    tiny = np.finfo(np.float64).tiny

    for raw_index in candidates:
        index = int(raw_index)
        displacement = large_position - small_positions[index]
        distance = float(np.linalg.norm(displacement))
        if distance > contact_distance:
            continue
        if distance == 0.0:
            raise RuntimeError(
                "cannot resolve a collision with exactly coincident centres"
            )
        normal = displacement / distance
        tangent = np.array([-normal[1], normal[0]], dtype=np.float64)
        penetration = max(contact_distance - distance, 0.0)

        correction = penetration + clearance
        small_positions[index] -= (
            large_mass / total_mass * correction * normal
        )
        large_position += small_mass / total_mass * correction * normal
        corrected_distance = float(
            np.linalg.norm(large_position - small_positions[index])
        )
        residual_penetration = max(
            contact_distance - corrected_distance,
            0.0,
        )

        small_before = small_velocities[index].copy()
        large_before = large_velocity.copy()
        relative_before = large_before - small_before
        normal_speed_before = float(np.dot(relative_before, normal))
        tangent_speed_before = float(np.dot(relative_before, tangent))
        momentum_before = (
            small_mass * small_before + large_mass * large_before
        )
        energy_before = _kinetic_energy_model_units(
            small_before,
            large_before,
            parameters,
        )

        impulse_applied = normal_speed_before < 0.0
        impulse_magnitude = 0.0
        expected_energy_change_model = 0.0
        if impulse_applied:
            impulse_magnitude = (
                -(1.0 + parameters.restitution)
                * normal_speed_before
                / (1.0 / small_mass + 1.0 / large_mass)
            )
            small_velocities[index] = (
                small_before
                - impulse_magnitude / small_mass * normal
            )
            large_velocity = (
                large_before
                + impulse_magnitude / large_mass * normal
            )
            expected_energy_change_model = (
                -0.5
                * reduced_mass
                * (1.0 - parameters.restitution**2)
                * normal_speed_before**2
            )

        small_after = small_velocities[index]
        large_after = large_velocity
        relative_after = large_after - small_after
        normal_speed_after = float(np.dot(relative_after, normal))
        tangent_speed_after = float(np.dot(relative_after, tangent))
        momentum_after = (
            small_mass * small_after + large_mass * large_after
        )
        energy_after = _kinetic_energy_model_units(
            small_after,
            large_after,
            parameters,
        )
        energy_change_model = energy_after - energy_before

        momentum_scale = max(
            float(np.linalg.norm(momentum_before)),
            small_mass * float(np.linalg.norm(small_before))
            + large_mass * float(np.linalg.norm(large_before)),
            abs(impulse_magnitude),
            tiny,
        )
        normalized_momentum_error = (
            float(np.linalg.norm(momentum_after - momentum_before))
            / momentum_scale
        )
        restitution_scale = max(
            abs(normal_speed_before),
            float(np.linalg.norm(relative_before)),
            tiny,
        )
        normalized_restitution_error = (
            abs(
                normal_speed_after
                + parameters.restitution * normal_speed_before
            )
            / restitution_scale
            if impulse_applied
            else 0.0
        )
        energy_scale = max(
            abs(energy_before),
            abs(expected_energy_change_model),
            tiny,
        )
        normalized_energy_error = (
            abs(energy_change_model - expected_energy_change_model)
            / energy_scale
            if impulse_applied
            else 0.0
        )

        reports.append(
            CollisionEventReport(
                small_particle_index=index,
                contact_normal=(float(normal[0]), float(normal[1])),
                distance_before_nm=distance,
                penetration_before_nm=penetration,
                distance_after_correction_nm=corrected_distance,
                residual_penetration_nm=residual_penetration,
                relative_normal_speed_before_nm_per_ps=normal_speed_before,
                relative_normal_speed_after_nm_per_ps=normal_speed_after,
                relative_tangential_speed_change_nm_per_ps=(
                    tangent_speed_after - tangent_speed_before
                ),
                impulse_applied=impulse_applied,
                impulse_magnitude_kg_nm_per_ps=impulse_magnitude,
                normalized_momentum_error=normalized_momentum_error,
                normalized_restitution_error=(
                    normalized_restitution_error
                ),
                kinetic_energy_change_j=energy_change_model * 1.0e6,
                expected_kinetic_energy_change_j=(
                    expected_energy_change_model * 1.0e6
                ),
                normalized_energy_identity_error=normalized_energy_error,
            )
        )

    if reports:
        state.small_positions_nm[:] = small_positions
        state.small_velocities_nm_per_ps[:] = small_velocities
        state.large_position_nm[:] = large_position
        state.large_velocity_nm_per_ps[:] = large_velocity
    return CollisionBatchReport(events=tuple(reports))


def _count_small_large_contacts(
    state: SimulationState,
    parameters: BrownianParameters,
) -> int:
    """Count current small-large contacts without changing state."""

    contact_distance = (
        parameters.small_radius_nm + parameters.large_radius_nm
    )
    distances = np.linalg.norm(
        state.small_positions_nm - state.large_position_nm,
        axis=1,
    )
    return int(np.count_nonzero(distances <= contact_distance))


def _restore_state(
    target: SimulationState,
    snapshot: SimulationState,
) -> None:
    """Restore a state object in place after a failed complete step."""

    target.small_positions_nm[:] = snapshot.small_positions_nm
    target.small_velocities_nm_per_ps[:] = (
        snapshot.small_velocities_nm_per_ps
    )
    target.next_randomization_times_ps[:] = (
        snapshot.next_randomization_times_ps
    )
    target.large_position_nm[:] = snapshot.large_position_nm
    target.large_velocity_nm_per_ps[:] = snapshot.large_velocity_nm_per_ps
    target.time_ps = snapshot.time_ps
    target.step_index = snapshot.step_index


def advance_simulation_step(
    context: SimulationContext,
) -> SimulationStepReport:
    """Advance one complete, transactional transport-collision step."""

    if not isinstance(context, SimulationContext):
        raise TypeError("context must be SimulationContext")
    state_snapshot = context.state.copy()
    random_snapshot = copy.deepcopy(context.reset_rng.bit_generator.state)

    try:
        transport = advance_transport_step(context)
        all_events: list[CollisionEventReport] = []
        collision_passes = 0
        small_post_wall_impacts = 0
        large_post_wall_impacts = 0
        remaining_contacts = _count_small_large_contacts(
            context.state,
            context.parameters,
        )

        while remaining_contacts > 0:
            if collision_passes >= context.parameters.max_collision_passes:
                raise RuntimeError(
                    "small-large contacts did not converge within "
                    "max_collision_passes"
                )
            collision_pass = resolve_small_large_collisions(
                context.state,
                context.parameters,
            )
            if collision_pass.contacts_detected == 0:
                raise RuntimeError(
                    "contact counter and collision pass disagree"
                )
            collision_passes += 1
            all_events.extend(collision_pass.events)

            if (
                collision_pass.maximum_normalized_momentum_error
                > 1.0e-12
            ):
                raise RuntimeError(
                    "collision momentum error exceeded 1e-12"
                )
            if (
                collision_pass.maximum_normalized_restitution_error
                > 1.0e-12
            ):
                raise RuntimeError(
                    "collision restitution error exceeded 1e-12"
                )
            if (
                collision_pass.maximum_normalized_energy_identity_error
                > 1.0e-12
            ):
                raise RuntimeError(
                    "collision energy identity error exceeded 1e-12"
                )
            penetration_limit = (
                1.0e-9
                * (
                    context.parameters.small_radius_nm
                    + context.parameters.large_radius_nm
                )
            )
            if (
                collision_pass.maximum_residual_penetration_nm
                > penetration_limit
            ):
                raise RuntimeError(
                    "collision penetration exceeded the declared tolerance"
                )

            wall_report = reflect_square_walls(
                context.state,
                context.parameters,
            )
            small_post_wall_impacts += wall_report.small_particle_impacts
            large_post_wall_impacts += wall_report.large_particle_impacts
            remaining_contacts = _count_small_large_contacts(
                context.state,
                context.parameters,
            )

        _validate_runtime_state(context.state, context.parameters)
        return SimulationStepReport(
            transport=transport,
            collisions=CollisionBatchReport(events=tuple(all_events)),
            collision_passes=collision_passes,
            post_collision_wall_impacts=WallReflectionReport(
                small_particle_impacts=small_post_wall_impacts,
                large_particle_impacts=large_post_wall_impacts,
            ),
            remaining_contacts=remaining_contacts,
        )
    except Exception:
        _restore_state(context.state, state_snapshot)
        context.reset_rng.bit_generator.state = random_snapshot
        raise


def run_simulation(
    parameters: BrownianParameters | None = None,
    *,
    max_frames: int = 240,
) -> BrownianSimulationResult:
    """Run the complete baseline model and return immutable recorded evidence."""

    context = initialize_simulation(parameters, max_frames=max_frames)
    n_steps = context.time_grid.n_steps
    n_frames = len(context.frame_steps)

    large_positions = np.empty((n_steps + 1, 2), dtype=np.float64)
    large_velocities = np.empty((n_steps + 1, 2), dtype=np.float64)
    small_frames = np.empty(
        (n_frames, context.parameters.n_small, 2),
        dtype=np.float64,
    )
    large_positions[0] = context.state.large_position_nm
    large_velocities[0] = context.state.large_velocity_nm_per_ps
    small_frames[0] = context.state.small_positions_nm
    next_frame = 1

    direction_resets = np.zeros(n_steps, dtype=np.int64)
    small_wall_impacts = np.zeros(n_steps, dtype=np.int64)
    large_wall_impacts = np.zeros(n_steps, dtype=np.int64)
    contacts = np.zeros(n_steps, dtype=np.int64)
    impulses = np.zeros(n_steps, dtype=np.int64)
    collision_passes = np.zeros(n_steps, dtype=np.int64)
    maximum_displacement = 0.0
    maximum_penetration = 0.0
    maximum_momentum_error = 0.0
    maximum_restitution_error = 0.0
    maximum_energy_error = 0.0
    total_collision_energy_change = 0.0

    for array_index in range(n_steps):
        report = advance_simulation_step(context)
        state_index = context.state.step_index
        large_positions[state_index] = context.state.large_position_nm
        large_velocities[state_index] = (
            context.state.large_velocity_nm_per_ps
        )

        direction_resets[array_index] = report.transport.direction_resets
        small_wall_impacts[array_index] = report.total_small_wall_impacts
        large_wall_impacts[array_index] = report.total_large_wall_impacts
        contacts[array_index] = report.collisions.contacts_detected
        impulses[array_index] = report.collisions.impulses_applied
        collision_passes[array_index] = report.collision_passes
        maximum_displacement = max(
            maximum_displacement,
            report.transport.maximum_displacement_nm,
        )
        maximum_penetration = max(
            maximum_penetration,
            report.collisions.maximum_residual_penetration_nm,
        )
        maximum_momentum_error = max(
            maximum_momentum_error,
            report.collisions.maximum_normalized_momentum_error,
        )
        maximum_restitution_error = max(
            maximum_restitution_error,
            report.collisions.maximum_normalized_restitution_error,
        )
        maximum_energy_error = max(
            maximum_energy_error,
            report.collisions.maximum_normalized_energy_identity_error,
        )
        total_collision_energy_change += (
            report.collisions.total_kinetic_energy_change_j
        )

        if (
            next_frame < n_frames
            and state_index == context.frame_steps[next_frame]
        ):
            small_frames[next_frame] = context.state.small_positions_nm
            next_frame += 1

    if next_frame != n_frames:
        raise RuntimeError("not every requested animation frame was recorded")

    diagnostics = SimulationDiagnostics(
        direction_resets_per_step=direction_resets,
        small_wall_impacts_per_step=small_wall_impacts,
        large_wall_impacts_per_step=large_wall_impacts,
        contacts_per_step=contacts,
        impulses_per_step=impulses,
        collision_passes_per_step=collision_passes,
        maximum_displacement_nm=maximum_displacement,
        maximum_residual_penetration_nm=maximum_penetration,
        maximum_normalized_momentum_error=maximum_momentum_error,
        maximum_normalized_restitution_error=maximum_restitution_error,
        maximum_normalized_energy_identity_error=maximum_energy_error,
        total_collision_energy_change_j=total_collision_energy_change,
    )
    return BrownianSimulationResult(
        parameters=context.parameters,
        time_grid=context.time_grid,
        large_positions_nm=large_positions,
        large_velocities_nm_per_ps=large_velocities,
        frame_steps=context.frame_steps,
        small_position_frames_nm=small_frames,
        diagnostics=diagnostics,
    )


@dataclass(frozen=True)
class BrownianSimulationResult:
    """Immutable, memory-aware output contract for the future engine.

    Large-particle state is retained at every physics step for statistical
    analysis. Small-particle positions are retained only at selected display
    frames, avoiding an unnecessary full time-particle-coordinate history.
    """

    parameters: BrownianParameters
    time_grid: FixedTimeGrid
    large_positions_nm: FloatArray
    large_velocities_nm_per_ps: FloatArray
    frame_steps: IntegerArray
    small_position_frames_nm: FloatArray
    diagnostics: SimulationDiagnostics

    def __post_init__(self) -> None:
        """Validate result dimensions, values, and frame alignment."""

        if not isinstance(self.parameters, BrownianParameters):
            raise TypeError("parameters must be BrownianParameters")
        if not isinstance(self.time_grid, FixedTimeGrid):
            raise TypeError("time_grid must be FixedTimeGrid")
        if not isinstance(self.diagnostics, SimulationDiagnostics):
            raise TypeError("diagnostics must be SimulationDiagnostics")
        if self.diagnostics.n_steps != self.time_grid.n_steps:
            raise ValueError(
                "diagnostic history length must match time_grid.n_steps"
            )
        time_tolerance = (
            8.0
            * np.finfo(np.float64).eps
            * max(self.parameters.max_time_ps, 1.0)
        )
        if not np.isclose(
            self.time_grid.final_time_ps,
            self.parameters.max_time_ps,
            rtol=8.0 * np.finfo(np.float64).eps,
            atol=time_tolerance,
        ):
            raise ValueError(
                "time_grid final time must match parameters.max_time_ps"
            )
        expected_large_shape = (self.time_grid.n_steps + 1, 2)
        large_positions = np.asarray(
            self.large_positions_nm,
            dtype=np.float64,
        )
        large_velocities = np.asarray(
            self.large_velocities_nm_per_ps,
            dtype=np.float64,
        )
        if large_positions.shape != expected_large_shape:
            raise ValueError(
                f"large_positions_nm must have shape {expected_large_shape}"
            )
        if large_velocities.shape != expected_large_shape:
            raise ValueError(
                "large_velocities_nm_per_ps must match large_positions_nm"
            )

        frame_steps = np.asarray(self.frame_steps, dtype=np.int64)
        if frame_steps.ndim != 1 or len(frame_steps) < 2:
            raise ValueError("frame_steps must be one-dimensional")
        if frame_steps[0] != 0 or frame_steps[-1] != self.time_grid.n_steps:
            raise ValueError(
                "frame_steps must contain the first and final step"
            )
        if np.any(np.diff(frame_steps) <= 0):
            raise ValueError("frame_steps must be strictly increasing")

        small_frames = np.asarray(
            self.small_position_frames_nm,
            dtype=np.float64,
        )
        expected_small_shape = (
            len(frame_steps),
            self.parameters.n_small,
            2,
        )
        if small_frames.shape != expected_small_shape:
            raise ValueError(
                "small_position_frames_nm must have shape "
                f"{expected_small_shape}"
            )
        if not all(
            np.all(np.isfinite(array))
            for array in (large_positions, large_velocities, small_frames)
        ):
            raise ValueError("all result arrays must contain finite values")

        object.__setattr__(
            self,
            "large_positions_nm",
            _readonly_array(large_positions, dtype=np.dtype(np.float64)),
        )
        object.__setattr__(
            self,
            "large_velocities_nm_per_ps",
            _readonly_array(large_velocities, dtype=np.dtype(np.float64)),
        )
        object.__setattr__(
            self,
            "frame_steps",
            _readonly_array(frame_steps, dtype=np.dtype(np.int64)),
        )
        object.__setattr__(
            self,
            "small_position_frames_nm",
            _readonly_array(small_frames, dtype=np.dtype(np.float64)),
        )

    @property
    def final_position_nm(self) -> tuple[float, float]:
        """Final large-particle coordinates."""

        return tuple(float(value) for value in self.large_positions_nm[-1])

    @property
    def final_displacement_nm(self) -> float:
        """Distance between initial and final large-particle positions."""

        displacement = self.large_positions_nm[-1] - self.large_positions_nm[0]
        return float(np.linalg.norm(displacement))

    @property
    def n_recorded_frames(self) -> int:
        """Number of stored small-particle animation frames."""

        return len(self.frame_steps)
