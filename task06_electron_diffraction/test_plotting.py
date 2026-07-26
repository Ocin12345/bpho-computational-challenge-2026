from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from PIL import Image

from task06_electron_diffraction.analysis import build_task06_study
from task06_electron_diffraction.configuration import DEFAULT_CONFIGURATION
from task06_electron_diffraction.plotting import (
    FIGURE_FILENAMES,
    generate_task06_figures,
)
from task06_electron_diffraction.validation import validate_task06


class PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task06_study()
        cls.report = validate_task06(cls.study)

    def test_all_figure_pairs_have_expected_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = generate_task06_figures(
                self.study,
                self.report,
                Path(temporary),
            )
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
                            if path.name == "task06_summary.png"
                            else (
                                DEFAULT_CONFIGURATION.figure_width_px,
                                DEFAULT_CONFIGURATION.figure_height_px,
                            )
                        )
                        self.assertEqual(image.size, expected)
                        self.assertEqual(image.format, "PNG")
                else:
                    self.assertTrue(ET.parse(path).getroot().tag.endswith("svg"))

    def test_plotting_rejects_a_report_for_another_study(self) -> None:
        wavelengths = self.study.wavelengths_m.copy()
        wavelengths[0] *= 1.01
        corrupted = replace(self.study, wavelengths_m=wavelengths)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                generate_task06_figures(
                    corrupted,
                    self.report,
                    Path(temporary),
                )

    def test_plotting_rejects_failed_report(self) -> None:
        wavelengths = self.study.wavelengths_m.copy()
        wavelengths[0] *= 1.01
        corrupted = replace(self.study, wavelengths_m=wavelengths)
        failed_report = validate_task06(corrupted)
        self.assertFalse(failed_report.passed)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                generate_task06_figures(
                    corrupted,
                    failed_report,
                    Path(temporary),
                )


if __name__ == "__main__":
    unittest.main()
