"""Core simulation for BPhO Computational Challenge 2026, Task 1.

The model takes ``n_steps`` independent steps of fixed length ``step_size``.
Each direction is sampled uniformly from the interval [0, 2*pi).

This module deliberately contains no plotting. It provides the numerical
models and deterministic validation used by the separate presentation scripts.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


@dataclass
class RandomWalkResult:
    """Complete numerical result for one two-dimensional random walk."""

    n_steps: int
    step_size: float
    seed: int | None
    angles: FloatArray
    displacements: FloatArray
    positions: FloatArray

    @property
    def x(self) -> FloatArray:
        """Horizontal coordinate at the origin and after every step."""

        return self.positions[:, 0]

    @property
    def y(self) -> FloatArray:
        """Vertical coordinate at the origin and after every step."""

        return self.positions[:, 1]

    @property
    def step_lengths(self) -> FloatArray:
        """Numerically calculated length of every displacement vector."""

        return np.hypot(self.displacements[:, 0], self.displacements[:, 1])

    @property
    def final_position(self) -> tuple[float, float]:
        """Coordinates reached after the final step."""

        return float(self.positions[-1, 0]), float(self.positions[-1, 1])

    @property
    def final_distance(self) -> float:
        """Straight-line distance from the origin after the final step."""

        return float(np.hypot(*self.positions[-1]))


@dataclass
class RandomWalkEnsembleResult:
    """Complete numerical result for several independent random walks."""

    n_walks: int
    n_steps: int
    step_size: float
    seed: int | None
    angles: FloatArray
    displacements: FloatArray
    positions: FloatArray

    @property
    def step_lengths(self) -> FloatArray:
        """Numerically calculated length of every step in every walk."""

        return np.linalg.norm(self.displacements, axis=2)

    @property
    def final_positions(self) -> FloatArray:
        """Final x and y coordinates for every walk."""

        return self.positions[:, -1, :]

    @property
    def final_distances(self) -> FloatArray:
        """Final distance from the origin for every walk."""

        return np.linalg.norm(self.final_positions, axis=1)


@dataclass(frozen=True)
class ValidationReport:
    """Outcome of deterministic consistency checks on one simulated walk."""

    passed: bool
    failures: tuple[str, ...]
    max_step_length_error: float


def _validated_parameters(
    n_steps: int,
    step_size: float,
    seed: int | None,
) -> tuple[int, float, int | None]:
    """Validate and normalise public simulation parameters."""

    if isinstance(n_steps, (bool, np.bool_)) or not isinstance(
        n_steps, (int, np.integer)
    ):
        raise TypeError("n_steps must be an integer")
    if n_steps <= 0:
        raise ValueError("n_steps must be greater than zero")

    if isinstance(step_size, (bool, np.bool_)) or not isinstance(
        step_size, (int, float, np.integer, np.floating)
    ):
        raise TypeError("step_size must be a real number")
    step_size = float(step_size)
    if not np.isfinite(step_size) or step_size <= 0.0:
        raise ValueError("step_size must be finite and greater than zero")

    if seed is not None:
        if isinstance(seed, (bool, np.bool_)) or not isinstance(
            seed, (int, np.integer)
        ):
            raise TypeError("seed must be a non-negative integer or None")
        if seed < 0:
            raise ValueError("seed must be non-negative")
        seed = int(seed)

    return int(n_steps), step_size, seed


def simulate_random_walk(
    n_steps: int,
    step_size: float,
    *,
    seed: int | None = None,
) -> RandomWalkResult:
    """Simulate one isotropic two-dimensional random walk.

    Parameters
    ----------
    n_steps:
        Number of independent steps. Must be a positive integer.
    step_size:
        Fixed length of every step. Must be positive and finite.
    seed:
        Optional non-negative seed for reproducible random numbers. With
        ``None``, NumPy obtains fresh entropy from the operating system.

    Returns
    -------
    RandomWalkResult
        Angles, displacement vectors, and all positions. The positions array
        has shape ``(n_steps + 1, 2)`` because it includes the origin.
    """

    n_steps, step_size, seed = _validated_parameters(n_steps, step_size, seed)
    rng = np.random.default_rng(seed)

    angles = rng.uniform(0.0, 2.0 * np.pi, size=n_steps)
    displacements = step_size * np.column_stack(
        (np.cos(angles), np.sin(angles))
    )

    positions = np.empty((n_steps + 1, 2), dtype=np.float64)
    positions[0] = (0.0, 0.0)
    positions[1:] = np.cumsum(displacements, axis=0)

    return RandomWalkResult(
        n_steps=n_steps,
        step_size=step_size,
        seed=seed,
        angles=angles,
        displacements=displacements,
        positions=positions,
    )


def simulate_random_walk_ensemble(
    n_walks: int,
    n_steps: int,
    step_size: float,
    *,
    seed: int | None = None,
) -> RandomWalkEnsembleResult:
    """Simulate several independent isotropic two-dimensional random walks.

    Parameters
    ----------
    n_walks:
        Number of independent trajectories. Must be a positive integer.
    n_steps:
        Number of fixed-length steps in each trajectory.
    step_size:
        Fixed length of every step in every trajectory.
    seed:
        Optional non-negative master seed for reproducibility.

    Returns
    -------
    RandomWalkEnsembleResult
        Angles, displacements, and positions for all walks. The positions array
        has shape ``(n_walks, n_steps + 1, 2)`` and includes every origin.
    """

    if isinstance(n_walks, (bool, np.bool_)) or not isinstance(
        n_walks, (int, np.integer)
    ):
        raise TypeError("n_walks must be an integer")
    if n_walks <= 0:
        raise ValueError("n_walks must be greater than zero")

    n_steps, step_size, seed = _validated_parameters(n_steps, step_size, seed)
    n_walks = int(n_walks)
    rng = np.random.default_rng(seed)

    angles = rng.uniform(0.0, 2.0 * np.pi, size=(n_walks, n_steps))
    displacements = step_size * np.stack(
        (np.cos(angles), np.sin(angles)),
        axis=2,
    )

    positions = np.empty((n_walks, n_steps + 1, 2), dtype=np.float64)
    positions[:, 0, :] = (0.0, 0.0)
    positions[:, 1:, :] = np.cumsum(displacements, axis=1)

    return RandomWalkEnsembleResult(
        n_walks=n_walks,
        n_steps=n_steps,
        step_size=step_size,
        seed=seed,
        angles=angles,
        displacements=displacements,
        positions=positions,
    )


def validate_walk(result: RandomWalkResult) -> ValidationReport:
    """Check exact structural and numerical requirements for one walk.

    These checks are deterministic. Statistical predictions such as mean
    squared displacement require an ensemble of walks and belong to Step 6.
    """

    failures: list[str] = []
    expected_position_shape = (result.n_steps + 1, 2)
    expected_step_shape = (result.n_steps, 2)

    if result.positions.shape != expected_position_shape:
        failures.append(
            "positions must have shape "
            f"{expected_position_shape}, not {result.positions.shape}"
        )
    if result.displacements.shape != expected_step_shape:
        failures.append(
            "displacements must have shape "
            f"{expected_step_shape}, not {result.displacements.shape}"
        )
    if result.angles.shape != (result.n_steps,):
        failures.append(
            f"angles must have shape {(result.n_steps,)}, not {result.angles.shape}"
        )

    arrays = (result.angles, result.displacements, result.positions)
    if not all(np.all(np.isfinite(array)) for array in arrays):
        failures.append("angles, displacements, and positions must all be finite")

    if result.positions.shape == expected_position_shape:
        tolerance = 32.0 * np.finfo(np.float64).eps * max(1.0, result.step_size)
        if not np.allclose(result.positions[0], 0.0, rtol=0.0, atol=tolerance):
            failures.append("the first stored position must be the origin")

        reconstructed_steps = np.diff(result.positions, axis=0)
        if result.displacements.shape == expected_step_shape and not np.allclose(
            reconstructed_steps,
            result.displacements,
            rtol=2.0e-15,
            atol=tolerance,
        ):
            failures.append("positions are not the cumulative sum of displacements")

    if result.angles.shape == (result.n_steps,) and not np.all(
        (result.angles >= 0.0) & (result.angles < 2.0 * np.pi)
    ):
        failures.append("every angle must lie in the interval [0, 2*pi)")

    if result.displacements.shape == expected_step_shape:
        step_lengths = result.step_lengths
        max_step_length_error = float(
            np.max(np.abs(step_lengths - result.step_size), initial=0.0)
        )
        if not np.allclose(
            step_lengths,
            result.step_size,
            rtol=2.0e-15,
            atol=32.0
            * np.finfo(np.float64).eps
            * max(1.0, result.step_size),
        ):
            failures.append("not every displacement has the requested step size")
    else:
        max_step_length_error = float("nan")

    return ValidationReport(
        passed=not failures,
        failures=tuple(failures),
        max_step_length_error=max_step_length_error,
    )


def validate_ensemble(result: RandomWalkEnsembleResult) -> ValidationReport:
    """Check deterministic structural and numerical requirements for an ensemble."""

    failures: list[str] = []
    expected_position_shape = (result.n_walks, result.n_steps + 1, 2)
    expected_step_shape = (result.n_walks, result.n_steps, 2)
    expected_angle_shape = (result.n_walks, result.n_steps)

    if result.positions.shape != expected_position_shape:
        failures.append(
            "positions must have shape "
            f"{expected_position_shape}, not {result.positions.shape}"
        )
    if result.displacements.shape != expected_step_shape:
        failures.append(
            "displacements must have shape "
            f"{expected_step_shape}, not {result.displacements.shape}"
        )
    if result.angles.shape != expected_angle_shape:
        failures.append(
            f"angles must have shape {expected_angle_shape}, not {result.angles.shape}"
        )

    arrays = (result.angles, result.displacements, result.positions)
    if not all(np.all(np.isfinite(array)) for array in arrays):
        failures.append("angles, displacements, and positions must all be finite")

    tolerance = 32.0 * np.finfo(np.float64).eps * max(1.0, result.step_size)
    if result.positions.shape == expected_position_shape:
        if not np.allclose(
            result.positions[:, 0, :],
            0.0,
            rtol=0.0,
            atol=tolerance,
        ):
            failures.append("every walk must begin at the origin")

        reconstructed_steps = np.diff(result.positions, axis=1)
        if result.displacements.shape == expected_step_shape and not np.allclose(
            reconstructed_steps,
            result.displacements,
            rtol=2.0e-15,
            atol=tolerance,
        ):
            failures.append("positions are not cumulative displacement sums")

    if result.angles.shape == expected_angle_shape and not np.all(
        (result.angles >= 0.0) & (result.angles < 2.0 * np.pi)
    ):
        failures.append("every angle must lie in the interval [0, 2*pi)")

    if result.displacements.shape == expected_step_shape:
        step_lengths = result.step_lengths
        max_step_length_error = float(
            np.max(np.abs(step_lengths - result.step_size), initial=0.0)
        )
        if not np.allclose(
            step_lengths,
            result.step_size,
            rtol=2.0e-15,
            atol=tolerance,
        ):
            failures.append("not every displacement has the requested step size")
    else:
        max_step_length_error = float("nan")

    return ValidationReport(
        passed=not failures,
        failures=tuple(failures),
        max_step_length_error=max_step_length_error,
    )


def _positive_integer(value: str) -> int:
    """Parse a positive integer for the command-line interface."""

    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    """Parse a positive finite float for the command-line interface."""

    parsed = float(value)
    if not np.isfinite(parsed) or parsed <= 0.0:
        raise argparse.ArgumentTypeError("must be finite and greater than zero")
    return parsed


def _non_negative_integer(value: str) -> int:
    """Parse a non-negative integer for the command-line interface."""

    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser without executing the simulation."""

    parser = argparse.ArgumentParser(
        description="Simulate and validate one 2D fixed-step random walk."
    )
    parser.add_argument(
        "-n",
        "--steps",
        type=_positive_integer,
        default=1_000,
        help="number of steps (default: 1000)",
    )
    parser.add_argument(
        "-s",
        "--step-size",
        type=_positive_float,
        default=1.0,
        help="fixed length of every step (default: 1.0)",
    )
    parser.add_argument(
        "--seed",
        type=_non_negative_integer,
        default=None,
        help="optional non-negative random seed",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the simulation from the command line and report its validation."""

    args = build_argument_parser().parse_args(argv)
    result = simulate_random_walk(args.steps, args.step_size, seed=args.seed)
    report = validate_walk(result)
    final_x, final_y = result.final_position

    print("Two-dimensional random walk")
    print(f"  steps: {result.n_steps}")
    print(f"  step size: {result.step_size:g}")
    print(f"  seed: {result.seed if result.seed is not None else 'random'}")
    print(f"  stored positions: {len(result.positions)}")
    print(f"  final position: ({final_x:.8g}, {final_y:.8g})")
    print(f"  final distance: {result.final_distance:.8g}")
    print(f"  maximum step-length error: {report.max_step_length_error:.3e}")
    print(f"  validation: {'PASS' if report.passed else 'FAIL'}")

    if not report.passed:
        for failure in report.failures:
            print(f"    - {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
