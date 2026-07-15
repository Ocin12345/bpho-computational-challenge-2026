"""Architecture and initialization for BPhO 2026 Task 2.

This module deliberately stops before motion, wall reflection, randomization,
or particle-collision updates. Step 3 establishes validated parameters,
reproducible initial state, a fixed time grid, and result containers so later
physics code has stable and testable contracts.
"""

from __future__ import annotations

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
    requested_time_step_ps: float | None = None
    seed: int | None = 2026

    def __post_init__(self) -> None:
        """Normalize values and enforce architecture-level constraints."""

        object.__setattr__(
            self,
            "n_small",
            _validated_integer(self.n_small, "n_small"),
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

        for name in ("max_step_fraction", "randomization_step_fraction"):
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
        parameters.maximum_time_step_ps
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

    def __post_init__(self) -> None:
        """Validate result dimensions, values, and frame alignment."""

        if not isinstance(self.parameters, BrownianParameters):
            raise TypeError("parameters must be BrownianParameters")
        if not isinstance(self.time_grid, FixedTimeGrid):
            raise TypeError("time_grid must be FixedTimeGrid")
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
