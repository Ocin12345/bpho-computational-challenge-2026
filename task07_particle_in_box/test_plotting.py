from __future__ import annotations

import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from PIL import Image

from task07_particle_in_box.analysis import build_task07_study
from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION
from task07_particle_in_box.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
    generate_task07_figures,
)
from task07_particle_in_box.validation import validate_task07


class PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task07_study()
        cls.report = validate_task07(cls.study)

    def test_all_figure_pairs_have_expected_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = generate_task07_figures(self.study, self.report, Path(temporary))
            self.assertEqual(tuple(path.name for path in paths), FIGURE_FILENAMES)
            for path in paths:
                self.assertGreater(path.stat().st_size, 1000)
                if path.suffix == ".png":
                    with Image.open(path) as image:
                        expected = (
                            (
                                DEFAULT_CONFIGURATION.summary_width_px,
                                DEFAULT_CONFIGURATION.summary_height_px,
                            )
                            if path.name == "task07_summary.png"
                            else (
                                DEFAULT_CONFIGURATION.figure_width_px,
                                DEFAULT_CONFIGURATION.figure_height_px,
                            )
                        )
                        self.assertEqual(image.size, expected)
                        self.assertEqual(image.format, "PNG")
                else:
                    self.assertTrue(ET.parse(path).getroot().tag.endswith("svg"))
                    svg_text = path.read_text(encoding="utf-8")
                    font_families = set(
                        re.findall(r"font:[^;]+?'([^']+)'", svg_text)
                    )
                    self.assertEqual(font_families, {FIGURE_FONT_FAMILY})

    def test_plotting_rejects_report_for_another_study(self) -> None:
        energies = self.study.energies_ev.copy()
        energies[0] *= 1.001
        corrupted = replace(self.study, energies_ev=energies)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                generate_task07_figures(corrupted, self.report, Path(temporary))

    def test_plotting_rejects_failed_report(self) -> None:
        products = self.study.uncertainty_products_over_hbar.copy()
        products[0] = 0.49
        corrupted = replace(self.study, uncertainty_products_over_hbar=products)
        failed_report = validate_task07(corrupted)
        self.assertFalse(failed_report.passed)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                generate_task07_figures(corrupted, failed_report, Path(temporary))


if __name__ == "__main__":
    unittest.main()
