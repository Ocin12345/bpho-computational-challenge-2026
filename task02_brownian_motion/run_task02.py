"""Command-line runner for the integrated BPhO Task 2 simulation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    run_simulation,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the Task 2 command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the collision-driven Brownian-motion baseline and print "
            "its numerical validation summary."
        )
    )
    parser.add_argument(
        "--particles",
        type=int,
        default=1_000,
        help="number of small particles (default: 1000)",
    )
    parser.add_argument(
        "--time-ps",
        type=float,
        default=200.0,
        help="simulation duration in picoseconds (default: 200)",
    )
    parser.add_argument(
        "--restitution",
        type=float,
        default=1.0,
        help="small-large coefficient of restitution (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="reproducibility seed (default: 2026)",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=240,
        help="maximum stored animation frames (default: 240)",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run one simulation and print concise, reproducible evidence."""

    options = build_parser().parse_args(arguments)
    parameters = BrownianParameters(
        n_small=options.particles,
        max_time_ps=options.time_ps,
        restitution=options.restitution,
        seed=options.seed,
    )
    result = run_simulation(parameters, max_frames=options.frames)
    diagnostics = result.diagnostics

    print("Task 2 Brownian-motion simulation complete")
    print(f"seed: {parameters.seed}")
    print(f"small particles: {parameters.n_small:,}")
    print(
        f"physics grid: {result.time_grid.n_steps:,} steps x "
        f"{result.time_grid.step_size_ps:.9f} ps"
    )
    print(f"final time: {result.time_grid.final_time_ps:.6f} ps")
    print(f"contacts: {diagnostics.total_contacts:,}")
    print(f"collision impulses: {diagnostics.total_impulses:,}")
    print(f"direction resets: {diagnostics.total_direction_resets:,}")
    print(
        "wall impacts (small, large): "
        f"{diagnostics.total_small_wall_impacts:,}, "
        f"{diagnostics.total_large_wall_impacts:,}"
    )
    print(
        f"final tracer displacement: "
        f"{result.final_displacement_nm:.9f} nm"
    )
    print(
        f"maximum one-step displacement: "
        f"{diagnostics.maximum_displacement_nm:.9f} nm"
    )
    print(
        "maximum normalized errors (momentum, restitution, energy): "
        f"{diagnostics.maximum_normalized_momentum_error:.3e}, "
        f"{diagnostics.maximum_normalized_restitution_error:.3e}, "
        f"{diagnostics.maximum_normalized_energy_identity_error:.3e}"
    )
    print(
        "maximum residual penetration: "
        f"{diagnostics.maximum_residual_penetration_nm:.3e} nm"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
