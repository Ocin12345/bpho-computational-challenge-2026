from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO

import numpy as np

from task05_hydrogen_spectrum.analysis import build_task05_study
from task05_hydrogen_spectrum.validate_task05 import main
from task05_hydrogen_spectrum.validation import validate_task05


class Task05ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.study = build_task05_study()

    def test_complete_study_passes_all_thirty_checks(self) -> None:
        report = validate_task05(self.study)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 30)
        self.assertEqual(report.failed_checks, ())

    def test_validation_is_deterministic(self) -> None:
        self.assertEqual(validate_task05(self.study), validate_task05(self.study))

    def test_energy_corruption_fails(self) -> None:
        values = np.array(self.study.photon_energy_ev, copy=True)
        values[0] += 0.1
        corrupted = replace(self.study, photon_energy_ev=values)
        report = validate_task05(corrupted)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("transition_energy_difference", failed)
        self.assertIn("energy_wavelength_identity", failed)

    def test_wavelength_corruption_fails(self) -> None:
        values = np.array(self.study.wavelength_nm, copy=True)
        values[10] += 1.0
        corrupted = replace(self.study, wavelength_nm=values)
        failed = {check.name for check in validate_task05(corrupted).failed_checks}
        self.assertIn("energy_wavelength_identity", failed)
        self.assertIn("rydberg_wavelength_reference", failed)

    def test_series_label_corruption_fails(self) -> None:
        labels = list(self.study.series_names)
        labels[0] = "Balmer"
        corrupted = replace(self.study, series_names=tuple(labels))
        failed = {check.name for check in validate_task05(corrupted).failed_checks}
        self.assertIn("series_and_line_labels", failed)

    def test_spectral_label_corruption_fails(self) -> None:
        regions = list(self.study.spectral_regions)
        regions[0] = "infrared"
        corrupted = replace(self.study, spectral_regions=tuple(regions))
        failed = {check.name for check in validate_task05(corrupted).failed_checks}
        self.assertIn("spectral_classification", failed)

    def test_validation_rejects_wrong_inputs(self) -> None:
        with self.assertRaises(TypeError):
            validate_task05(None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            main(["unexpected"])

    def test_cli_returns_success(self) -> None:
        with redirect_stdout(StringIO()):
            self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
