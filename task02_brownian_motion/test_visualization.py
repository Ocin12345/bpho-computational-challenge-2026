"""Tests for Task 2 static figures and animation output."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from task02_brownian_motion.brownian_motion import (  # noqa: E402
    BrownianParameters,
    run_simulation,
)
from task02_brownian_motion.visualization import (  # noqa: E402
    _save_figure,
    create_all_visuals,
    create_baseline_statistics_figure,
    create_numerical_validation_figure,
    create_parameter_experiments_figure,
    create_reference_animation,
    create_reference_scene,
)


TASK_DIRECTORY = Path(__file__).resolve().parent


class StaticFigureTests(unittest.TestCase):
    """Verify that committed evidence produces complete, savable figures."""

    def test_committed_evidence_builds_all_statistical_figures(self) -> None:
        cases = (
            (
                create_baseline_statistics_figure,
                TASK_DIRECTORY / "analysis",
                2,
            ),
            (
                create_parameter_experiments_figure,
                TASK_DIRECTORY / "analysis",
                4,
            ),
            (
                create_numerical_validation_figure,
                TASK_DIRECTORY / "validation",
                3,
            ),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            for index, (factory, source, expected_axes) in enumerate(cases):
                with self.subTest(factory=factory.__name__):
                    figure = factory(source)
                    self.assertEqual(len(figure.axes), expected_axes)
                    png_path, svg_path = _save_figure(
                        figure,
                        output_directory / f"figure_{index}",
                        dpi=80,
                    )
                    plt.close(figure)
                    self.assertGreater(png_path.stat().st_size, 1_000)
                    self.assertGreater(svg_path.stat().st_size, 1_000)
                    self.assertFalse(
                        any(
                            line.endswith((" ", "\t"))
                            for line in svg_path.read_text(
                                encoding="utf-8"
                            ).splitlines()
                        )
                    )


class ReferenceVisualTests(unittest.TestCase):
    """Verify the particle scene and GIF on a compact real simulation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_simulation(
            BrownianParameters(
                n_small=20,
                max_time_ps=0.1,
                seed=2026,
            ),
            max_frames=6,
        )

    def test_reference_scene_contains_particles_trail_and_tracer(self) -> None:
        figure = create_reference_scene(self.result)

        self.assertEqual(len(figure.axes), 1)
        self.assertGreaterEqual(len(figure.axes[0].collections), 2)
        self.assertEqual(len(figure.axes[0].patches), 1)
        plt.close(figure)

    def test_reference_animation_writes_every_recorded_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "compact.gif"
            create_reference_animation(
                self.result,
                output_path,
                frames_per_second=5,
                dpi=60,
            )

            self.assertGreater(output_path.stat().st_size, 1_000)
            from PIL import Image

            with Image.open(output_path) as animation:
                self.assertEqual(
                    animation.n_frames,
                    self.result.n_recorded_frames,
                )

    def test_animation_rejects_non_positive_frame_rate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ValueError):
                create_reference_animation(
                    self.result,
                    Path(temporary_directory) / "invalid.gif",
                    frames_per_second=0,
                )

    def test_visual_generators_reject_invalid_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            with self.assertRaises(ValueError):
                create_reference_animation(
                    self.result,
                    output_directory / "invalid.gif",
                    dpi=0,
                )
            with self.assertRaises(ValueError):
                create_all_visuals(
                    output_directory,
                    max_animation_frames=1,
                )
            with self.assertRaises(ValueError):
                create_all_visuals(output_directory, dpi=0)


if __name__ == "__main__":
    unittest.main()
