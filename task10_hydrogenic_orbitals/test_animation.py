"""Tests for the deterministic Task 10 view-rotation animation."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

from task10_hydrogenic_orbitals.animation import (
    ANIMATION_TITLE,
    build_task10_animation_scene,
    write_task10_animation,
)
from task10_hydrogenic_orbitals.validation import validate_task10


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = validate_task10()

    def test_scene_uses_immutable_seamless_camera_schedule(self) -> None:
        scene = build_task10_animation_scene(
            self.report,
            frame_count=8,
            width_px=640,
            height_px=360,
            dpi=80,
            resolution=31,
            slice_count=7,
        )
        try:
            self.assertEqual(
                scene.camera_azimuth_deg.tolist(),
                [-54.0, -9.0, 36.0, 81.0, 126.0, 171.0, 216.0, 261.0],
            )
            self.assertFalse(scene.camera_azimuth_deg.flags.writeable)
            self.assertFalse(scene.camera_elevation_deg.flags.writeable)
            self.assertEqual(len(scene.update(0)), 2)
            self.assertEqual(len(scene.update(7)), 2)
            with self.assertRaises(IndexError):
                scene.update(8)
        finally:
            plt.close(scene.figure)

    def test_small_webp_is_complete_reproducible_and_tagged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first, poster, evidence = write_task10_animation(
                self.report,
                directory / "first.webp",
                poster_path=directory / "poster.png",
                frame_count=8,
                frames_per_second=10,
                width_px=640,
                height_px=360,
                dpi=80,
                quality=82,
                resolution=31,
                slice_count=7,
            )
            second, _, second_evidence = write_task10_animation(
                self.report,
                directory / "second.webp",
                frame_count=8,
                frames_per_second=10,
                width_px=640,
                height_px=360,
                dpi=80,
                quality=82,
                resolution=31,
                slice_count=7,
            )
            self.assertEqual(_digest(first), _digest(second))
            self.assertEqual(evidence, second_evidence)
            self.assertIsNotNone(poster)
            assert poster is not None
            with Image.open(poster) as image:
                self.assertEqual(image.size, (640, 360))
                self.assertEqual(image.format, "PNG")
            with Image.open(first) as image:
                self.assertEqual(image.format, "WEBP")
                self.assertEqual(image.size, (640, 360))
                self.assertEqual(image.n_frames, 8)
                self.assertEqual(image.info.get("loop"), 0)
                self.assertIn(ANIMATION_TITLE.encode(), image.info.get("xmp", b""))
            self.assertEqual(evidence["duration_ms"], 800)
            self.assertTrue(evidence["continuous_loop"])

    def test_invalid_parameters_and_failed_report_are_rejected(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check, *self.report.checks[1:]),
        )
        with self.assertRaises(RuntimeError):
            build_task10_animation_scene(failed_report)
        with self.assertRaises(ValueError):
            build_task10_animation_scene(
                self.report,
                width_px=800,
                height_px=600,
            )
        with self.assertRaises(ValueError):
            build_task10_animation_scene(self.report, resolution=32)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                write_task10_animation(
                    self.report,
                    Path(temporary) / "animation.gif",
                )
            with self.assertRaises(ValueError):
                write_task10_animation(
                    self.report,
                    Path(temporary) / "animation.webp",
                    frames_per_second=18,
                )


if __name__ == "__main__":
    unittest.main()
