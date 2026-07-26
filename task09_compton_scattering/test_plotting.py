"""Tests for deterministic publication-quality Task 9 figures."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from PIL import Image

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.configuration import DEFAULT_CONFIGURATION
from task09_compton_scattering.cross_section import build_klein_nishina_study
from task09_compton_scattering.cross_section_validation import (
    validate_cross_section_study,
)
from task09_compton_scattering.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
    generate_task09_figures,
)
from task09_compton_scattering.validation import validate_task09


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task09_study()
        cls.report = validate_task09(cls.study)
        cls.cross_section_study = build_klein_nishina_study(
            cls.study.incident_energy_kev,
            cls.study.theta_deg,
        )
        cls.cross_section_report = validate_cross_section_study(
            cls.cross_section_study
        )

    def test_all_png_and_svg_outputs_are_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "figures"
            first = generate_task09_figures(
                self.study,
                self.report,
                self.cross_section_study,
                self.cross_section_report,
                output,
            )
            self.assertEqual(tuple(path.name for path in first), FIGURE_FILENAMES)
            first_hashes = {path.name: _digest(path) for path in first}
            second = generate_task09_figures(
                self.study,
                self.report,
                self.cross_section_study,
                self.cross_section_report,
                output,
            )
            self.assertEqual(first_hashes, {path.name: _digest(path) for path in second})

    def test_raster_dimensions_resolution_and_vector_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = generate_task09_figures(
                self.study,
                self.report,
                self.cross_section_study,
                self.cross_section_report,
                Path(temporary),
            )
            for path in paths:
                if path.suffix == ".png":
                    with Image.open(path) as image:
                        expected = (
                            (
                                DEFAULT_CONFIGURATION.summary_width_px,
                                DEFAULT_CONFIGURATION.summary_height_px,
                            )
                            if path.name == "task09_summary.png"
                            else (
                                DEFAULT_CONFIGURATION.figure_width_px,
                                DEFAULT_CONFIGURATION.figure_height_px,
                            )
                        )
                        self.assertEqual(image.format, "PNG")
                        self.assertEqual(image.size, expected)
                        self.assertTrue(
                            all(
                                abs(value - DEFAULT_CONFIGURATION.figure_dpi) < 0.1
                                for value in image.info["dpi"]
                            )
                        )
                elif path.suffix == ".svg":
                    self.assertTrue(ET.parse(path).getroot().tag.endswith("svg"))
                    svg = path.read_text(encoding="utf-8")
                    self.assertIn(FIGURE_FONT_FAMILY, svg)
                    self.assertNotIn("DejaVu Sans", svg)
                else:
                    pdf_bytes = path.read_bytes()
                    self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
                    self.assertIn(b"TimesNewRoman", pdf_bytes)
                    self.assertIn(b"/FontFile2", pdf_bytes)

    def test_mismatched_or_failed_reports_are_rejected(self) -> None:
        altered_values = self.study.fractional_wavelength_shift.copy()
        altered_values[0, 1] += 1.0e-6
        altered_study = replace(
            self.study,
            fractional_wavelength_shift=altered_values,
        )
        failed_core_check = replace(self.report.checks[0], passed=False)
        failed_core_report = replace(
            self.report,
            checks=(failed_core_check, *self.report.checks[1:]),
        )
        failed_extension_check = replace(
            self.cross_section_report.checks[0], passed=False
        )
        failed_extension_report = replace(
            self.cross_section_report,
            checks=(
                failed_extension_check,
                *self.cross_section_report.checks[1:],
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with self.assertRaises(ValueError):
                generate_task09_figures(
                    altered_study,
                    self.report,
                    self.cross_section_study,
                    self.cross_section_report,
                    output,
                )
            with self.assertRaises(RuntimeError):
                generate_task09_figures(
                    self.study,
                    failed_core_report,
                    self.cross_section_study,
                    self.cross_section_report,
                    output,
                )
            with self.assertRaises(RuntimeError):
                generate_task09_figures(
                    self.study,
                    self.report,
                    self.cross_section_study,
                    failed_extension_report,
                    output,
                )

    def test_wrong_input_types_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(TypeError):
                generate_task09_figures(
                    object(),  # type: ignore[arg-type]
                    self.report,
                    self.cross_section_study,
                    self.cross_section_report,
                    Path(temporary),
                )


if __name__ == "__main__":
    unittest.main()
