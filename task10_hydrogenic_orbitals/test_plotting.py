"""Quality and reproducibility tests for Task 10 publication figures."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.generate_task10 import REPOSITORY_ROOT
from task10_hydrogenic_orbitals.plotting import (
    FIGURE_FONT_FAMILY,
    _glass_stack_data,
    _outer_density_isosurface,
    _rgba_density,
    build_coloured_glass_figure,
    build_radial_structure_figure,
    build_rendering_comparison_figure,
    build_required_gallery_figure,
    build_summary_figure,
    density_maximum_projection,
    generate_publication_figures,
    verify_data_gate,
    write_figure_manifest,
)


class PlottingTests(unittest.TestCase):
    def test_projection_is_finite_normalized_and_immutable(self) -> None:
        result = density_maximum_projection(
            HydrogenicState(3, 2, 0),
            resolution=51,
            depth_samples=31,
        )
        self.assertEqual(result.relative_density.shape, (51, 51))
        self.assertTrue(np.all(np.isfinite(result.relative_density)))
        self.assertGreaterEqual(float(np.min(result.relative_density)), 0.0)
        self.assertAlmostEqual(float(np.max(result.relative_density)), 1.0)
        self.assertFalse(result.relative_density.flags.writeable)
        with self.assertRaises(ValueError):
            result.relative_density[0, 0] = 0.0

    def test_invalid_render_parameters_are_rejected(self) -> None:
        state = HydrogenicState(2, 1, 0)
        for resolution in (39, 40, 52):
            with self.assertRaises(ValueError):
                density_maximum_projection(state, resolution=resolution)
        for samples in (29, 30, 40):
            with self.assertRaises(ValueError):
                density_maximum_projection(state, depth_samples=samples)
        with self.assertRaises(TypeError):
            density_maximum_projection(object())  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            _rgba_density(np.ones((3, 3)), threshold=1.0)
        with self.assertRaises(ValueError):
            _rgba_density(np.ones(3), threshold=0.15)
        with self.assertRaises(ValueError):
            _glass_stack_data(state, resolution=30)
        with self.assertRaises(ValueError):
            _glass_stack_data(state, slice_count=4)
        with self.assertRaises(ValueError):
            _outer_density_isosurface(HydrogenicState(2, 1, 1))

    def test_data_gate_detects_corrupt_state_digest(self) -> None:
        source = REPOSITORY_ROOT / "data/task10"
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            shutil.copy2(source / "manifest.json", directory / "manifest.json")
            shutil.copy2(
                source / "validation_report.json",
                directory / "validation_report.json",
            )
            report_path = directory / "validation_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["state_digest"] = "0" * 64
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "current scientific state"):
                verify_data_gate(directory)

    def test_figure_level_text_stays_inside_canvas(self) -> None:
        builders = (
            build_required_gallery_figure,
            build_radial_structure_figure,
            build_coloured_glass_figure,
            build_rendering_comparison_figure,
            build_summary_figure,
        )
        for builder in builders:
            figure = builder()
            try:
                figure.canvas.draw()
                renderer = figure.canvas.get_renderer()
                width, height = figure.canvas.get_width_height()
                for artist in figure.texts:
                    bounds = artist.get_window_extent(renderer=renderer)
                    self.assertGreaterEqual(bounds.x0, -1.0, artist.get_text())
                    self.assertGreaterEqual(bounds.y0, -1.0, artist.get_text())
                    self.assertLessEqual(bounds.x1, width + 1.0, artist.get_text())
                    self.assertLessEqual(bounds.y1, height + 1.0, artist.get_text())
            finally:
                import matplotlib.pyplot as plt

                plt.close(figure)

    def test_complete_figure_package_is_reproducible_and_high_resolution(self) -> None:
        data_directory = REPOSITORY_ROOT / "data/task10"
        verify_data_gate(data_directory)
        expected_dimensions = {
            "required_orbital_gallery.png": (3840, 2400),
            "radial_and_nodal_structure.png": (2400, 1500),
            "coloured_glass_density.png": (3000, 1875),
            "rendering_comparison.png": (3000, 1800),
            "task10_summary.png": (3840, 2160),
        }
        with tempfile.TemporaryDirectory() as first_name, tempfile.TemporaryDirectory() as second_name:
            first_directory = Path(first_name)
            second_directory = Path(second_name)
            first_outputs = generate_publication_figures(first_directory)
            second_outputs = generate_publication_figures(second_directory)
            first_manifest = write_figure_manifest(
                first_directory, data_directory, first_outputs
            )
            second_manifest = write_figure_manifest(
                second_directory, data_directory, second_outputs
            )

            self.assertEqual(len(first_outputs), 13)
            for first_path in first_outputs:
                second_path = second_directory / first_path.name
                self.assertEqual(
                    hashlib.sha256(first_path.read_bytes()).digest(),
                    hashlib.sha256(second_path.read_bytes()).digest(),
                    first_path.name,
                )
                if first_path.suffix == ".png":
                    with Image.open(first_path) as image:
                        self.assertEqual(image.size, expected_dimensions[first_path.name])
                        dpi = image.info["dpi"]
                        self.assertAlmostEqual(float(dpi[0]), 300.0, places=2)
                        self.assertAlmostEqual(float(dpi[1]), 300.0, places=2)
                elif first_path.suffix == ".svg":
                    text = first_path.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("<?xml"))
                    self.assertIn("<svg", text[:500])
                    self.assertIn(FIGURE_FONT_FAMILY, text)
                    self.assertNotIn("DejaVu Sans", text)
                elif first_path.suffix == ".pdf":
                    content = first_path.read_bytes()
                    self.assertTrue(content.startswith(b"%PDF-"))
                    self.assertIn(b"TimesNewRoman", content)
                    self.assertIn(b"/FontFile2", content)
                else:
                    self.fail(f"unexpected figure format: {first_path.name}")

            self.assertEqual(first_manifest.read_bytes(), second_manifest.read_bytes())
            payload = json.loads(first_manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["science_gate"]["checks_passed"], 22)
            self.assertEqual(payload["science_gate"]["checks_total"], 22)
            self.assertEqual(len(payload["figures"]), 13)
            self.assertEqual(payload["renderer"]["font_family"], FIGURE_FONT_FAMILY)


if __name__ == "__main__":
    unittest.main()
