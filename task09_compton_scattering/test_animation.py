"""Tests for the deterministic Task 9 angle-sweep animation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.animation import (
    build_task09_animation_scene,
    write_task09_animation,
)
from task09_compton_scattering.validation import validate_task09


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task09_study()
        cls.report = validate_task09(cls.study)

    def test_scene_uses_inclusive_immutable_grid_schedule(self) -> None:
        scene = build_task09_animation_scene(
            self.study,
            self.report,
            frame_count=9,
            width_px=640,
            height_px=360,
            dpi=80,
        )
        try:
            self.assertEqual(scene.frame_indices.tolist(), [0, 90, 180, 270, 360, 450, 540, 630, 720])
            self.assertFalse(scene.frame_indices.flags.writeable)
            self.assertEqual(len(scene.update(0)), 12)
            self.assertEqual(len(scene.update(8)), 12)
            with self.assertRaises(IndexError):
                scene.update(9)
            scene.animation._draw_was_started = True
        finally:
            plt.close(scene.figure)

    def test_small_gif_is_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = write_task09_animation(
                self.study,
                self.report,
                Path(temporary) / "first.gif",
                frame_count=9,
                frames_per_second=6,
                width_px=640,
                height_px=360,
                dpi=80,
            )
            second = write_task09_animation(
                self.study,
                self.report,
                Path(temporary) / "second.gif",
                frame_count=9,
                frames_per_second=6,
                width_px=640,
                height_px=360,
                dpi=80,
            )
            self.assertEqual(_digest(first), _digest(second))
            with Image.open(first) as image:
                self.assertEqual(image.format, "GIF")
                self.assertEqual(image.size, (640, 360))
                self.assertEqual(image.n_frames, 9)
                self.assertEqual(image.info.get("loop"), 0)

    def test_invalid_parameters_and_failed_report_are_rejected(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check, *self.report.checks[1:]),
        )
        with self.assertRaises(RuntimeError):
            build_task09_animation_scene(self.study, failed_report)
        with self.assertRaises(ValueError):
            build_task09_animation_scene(
                self.study,
                self.report,
                energy_kev=75.0,
            )
        with self.assertRaises(ValueError):
            build_task09_animation_scene(
                self.study,
                self.report,
                width_px=800,
                height_px=600,
            )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                write_task09_animation(
                    self.study,
                    self.report,
                    Path(temporary) / "animation.png",
                )


if __name__ == "__main__":
    unittest.main()
