"""Tests for the presentation-quality Task 1 single-walk figure."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

from task01_random_walk.plot_single_walk import (  # noqa: E402
    create_single_walk_figure,
    save_single_walk_figure,
)
from task01_random_walk.random_walk import simulate_random_walk  # noqa: E402


class SingleWalkFigureTests(unittest.TestCase):
    """Check the plot's data content, geometry, and saved formats."""

    def test_figure_contains_one_coloured_segment_per_step(self) -> None:
        result = simulate_random_walk(120, 1.0, seed=4)
        figure = create_single_walk_figure(result)
        self.addCleanup(plt.close, figure)

        axis = figure.axes[0]
        paths = [
            artist
            for artist in axis.collections
            if isinstance(artist, LineCollection)
        ]

        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0].get_segments()), result.n_steps)

    def test_figure_uses_equal_axes_and_clear_labels(self) -> None:
        result = simulate_random_walk(100, 0.5, seed=5)
        figure = create_single_walk_figure(result)
        self.addCleanup(plt.close, figure)

        axis = figure.axes[0]
        self.assertEqual(axis.get_aspect(), 1.0)
        self.assertIn("x position", axis.get_xlabel())
        self.assertIn("y position", axis.get_ylabel())
        self.assertIn("isotropic random walk", axis.get_title(loc="left"))

    def test_png_and_svg_outputs_are_created(self) -> None:
        result = simulate_random_walk(80, 1.0, seed=6)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_stem = Path(temporary_directory) / "single_walk"
            png_path, svg_path = save_single_walk_figure(
                result,
                output_stem,
                dpi=100,
            )

            self.assertTrue(png_path.is_file())
            self.assertTrue(svg_path.is_file())
            self.assertGreater(png_path.stat().st_size, 10_000)
            self.assertGreater(svg_path.stat().st_size, 10_000)
            self.assertEqual(png_path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8")[:1_000])

    def test_invalid_dpi_is_rejected(self) -> None:
        result = simulate_random_walk(10, 1.0, seed=7)

        with self.assertRaises(ValueError):
            save_single_walk_figure(result, dpi=0)


if __name__ == "__main__":
    unittest.main()
