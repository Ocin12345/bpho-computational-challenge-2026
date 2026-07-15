"""Command-line generator for all Task 2 figures and animation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from task02_brownian_motion.visualization import create_all_visuals


def build_parser() -> argparse.ArgumentParser:
    """Create the visual-generation command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Create Task 2 PNG/SVG figures and the reference GIF from "
            "committed statistical evidence."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="repository root (default: current directory)",
    )
    parser.add_argument(
        "--animation-frames",
        type=int,
        default=180,
        help="stored animation frames (default: 180)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG resolution (default: 300)",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Generate and list every Step 9 output."""

    options = build_parser().parse_args(arguments)
    outputs = create_all_visuals(
        options.repository_root,
        max_animation_frames=options.animation_frames,
        dpi=options.dpi,
    )
    print("Task 2 visual generation complete")
    for path in outputs:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
