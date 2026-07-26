"""Tests for the deterministic publication-quality Task 8 figures."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from PIL import Image

from task08_quantum_cryptography.analysis import build_task08_study
from task08_quantum_cryptography.configuration import DEFAULT_CONFIGURATION
from task08_quantum_cryptography.generate_task08_figure_manifest import (
    generate_task08_figure_manifest,
)
from task08_quantum_cryptography.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
    generate_task08_figures,
)
from task08_quantum_cryptography.statistical_validation import (
    validate_task08_statistics,
)
from task08_quantum_cryptography.validation import validate_task08


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task08_study()
        cls.report = validate_task08(cls.study)
        cls.statistics_report = validate_task08_statistics()

    def test_all_png_svg_and_pdf_outputs_are_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "figures"
            first = generate_task08_figures(
                self.study,
                self.report,
                self.statistics_report,
                output,
            )
            self.assertEqual(tuple(path.name for path in first), FIGURE_FILENAMES)
            first_hashes = {path.name: _digest(path) for path in first}
            second = generate_task08_figures(
                self.study,
                self.report,
                self.statistics_report,
                output,
            )
            self.assertEqual(
                first_hashes,
                {path.name: _digest(path) for path in second},
            )

    def test_figure_manifest_hashes_every_representation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "figures"
            generate_task08_figures(
                self.study,
                self.report,
                self.statistics_report,
                output,
            )
            manifest_path = generate_task08_figure_manifest(output)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["figure_font_family"], FIGURE_FONT_FAMILY)
            self.assertEqual(payload["schema_version"], "task08-figure-manifest-v2")
            self.assertEqual(len(payload["files"]), 12)
            for item in payload["files"]:
                self.assertEqual(_digest(output / item["filename"]), item["sha256"])

    def test_raster_dimensions_resolution_and_vector_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = generate_task08_figures(
                self.study,
                self.report,
                self.statistics_report,
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
                            if path.name == "task08_summary.png"
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
                    font_families = set(
                        re.findall(
                            r"font:[^;]+?'([^']+)'",
                            path.read_text(encoding="utf-8"),
                        )
                    )
                    self.assertEqual(font_families, {FIGURE_FONT_FAMILY})
                else:
                    pdf_bytes = path.read_bytes()
                    self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
                    self.assertIn(b"TimesNewRoman", pdf_bytes)
                    self.assertIn(b"/FontFile2", pdf_bytes)

    def test_mismatched_or_failed_scientific_report_is_rejected(self) -> None:
        altered_sweep = self.study.sweep_classical_mismatch.copy()
        altered_sweep[0] += 1.0e-6
        altered_study = replace(
            self.study,
            sweep_classical_mismatch=altered_sweep,
        )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                generate_task08_figures(
                    altered_study,
                    self.report,
                    self.statistics_report,
                    Path(temporary),
                )

            failed_check = replace(self.report.checks[0], passed=False)
            failed_report = replace(
                self.report,
                checks=(failed_check, *self.report.checks[1:]),
            )
            with self.assertRaises(RuntimeError):
                generate_task08_figures(
                    self.study,
                    failed_report,
                    self.statistics_report,
                    Path(temporary),
                )

    def test_failed_statistics_and_wrong_input_types_are_rejected(self) -> None:
        failed_check = replace(self.statistics_report.checks[0], passed=False)
        failed_report = replace(
            self.statistics_report,
            checks=(failed_check, *self.statistics_report.checks[1:]),
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with self.assertRaises(RuntimeError):
                generate_task08_figures(
                    self.study,
                    self.report,
                    failed_report,
                    output,
                )
            with self.assertRaises(TypeError):
                generate_task08_figures(
                    object(),  # type: ignore[arg-type]
                    self.report,
                    self.statistics_report,
                    output,
                )


if __name__ == "__main__":
    unittest.main()
