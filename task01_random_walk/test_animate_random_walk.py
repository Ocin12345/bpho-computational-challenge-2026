"""Tests for the Task 1 presentation animation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

from task01_random_walk.animate_random_walk import (  # noqa: E402
    build_frame_schedule,
    create_random_walk_animation,
    save_random_walk_animation,
)
from task01_random_walk.random_walk import simulate_random_walk  # noqa: E402


class RandomWalkAnimationTests(unittest.TestCase):
    """Verify schedule, geometry, rendering, and GIF output."""

    def test_frame_schedule_includes_start_finish_and_holds(self) -> None:
        schedule = build_frame_schedule(
            1_000,
            max_moving_frames=100,
            start_hold_frames=3,
            end_hold_frames=5,
        )

        self.assertEqual(schedule[0], 0)
        self.assertEqual(schedule[-1], 1_000)
        self.assertGreaterEqual((schedule == 0).sum(), 4)
        self.assertGreaterEqual((schedule == 1_000).sum(), 6)
        self.assertTrue((schedule[1:] >= schedule[:-1]).all())

    def test_final_frame_contains_the_complete_path(self) -> None:
        result = simulate_random_walk(60, 1.0, seed=4)
        scene = create_random_walk_animation(
            result,
            max_moving_frames=20,
            start_hold_frames=0,
            end_hold_frames=0,
            fps=10,
        )
        self.addCleanup(plt.close, scene.figure)
        scene.render_step(result.n_steps)

        axis = scene.figure.axes[0]
        paths = [
            artist
            for artist in axis.collections
            if isinstance(artist, LineCollection)
        ]
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0].get_segments()), result.n_steps)
        self.assertEqual(axis.get_aspect(), 1.0)

    def test_endpoint_markers_are_not_covered_by_current_marker(self) -> None:
        result = simulate_random_walk(60, 1.0, seed=4)
        scene = create_random_walk_animation(
            result,
            max_moving_frames=20,
            start_hold_frames=0,
            end_hold_frames=0,
            fps=10,
        )
        self.addCleanup(plt.close, scene.figure)
        axis = scene.figure.axes[0]
        current_marker = next(
            line for line in axis.lines if line.get_label() == "Current position"
        )
        final_marker = next(
            line for line in axis.lines if line.get_label() == "Finish"
        )

        scene.render_step(0)
        self.assertEqual(len(current_marker.get_xdata()), 0)
        self.assertEqual(len(final_marker.get_xdata()), 0)

        scene.render_step(result.n_steps // 2)
        self.assertEqual(len(current_marker.get_xdata()), 1)
        self.assertEqual(len(final_marker.get_xdata()), 0)

        scene.render_step(result.n_steps)
        self.assertEqual(len(current_marker.get_xdata()), 0)
        self.assertEqual(len(final_marker.get_xdata()), 1)

    def test_small_gif_is_created(self) -> None:
        result = simulate_random_walk(20, 1.0, seed=5)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "animation.gif"
            saved_path, frame_count = save_random_walk_animation(
                result,
                output_path,
                max_moving_frames=8,
                start_hold_frames=1,
                end_hold_frames=2,
                fps=8,
                dpi=55,
            )

            self.assertTrue(saved_path.is_file())
            self.assertGreater(saved_path.stat().st_size, 5_000)
            self.assertIn(saved_path.read_bytes()[:6], (b"GIF87a", b"GIF89a"))
            self.assertGreater(frame_count, 8)

    def test_invalid_animation_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_frame_schedule(0)
        with self.assertRaises(ValueError):
            build_frame_schedule(10, max_moving_frames=1)


if __name__ == "__main__":
    unittest.main()
