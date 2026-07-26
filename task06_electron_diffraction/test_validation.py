from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace

import numpy as np

from task06_electron_diffraction.analysis import build_task06_study
from task06_electron_diffraction.validation import (
    Task06ValidationReport,
    ValidationCheck,
    task06_study_digest,
    validate_task06,
)


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task06_study()
        cls.report = validate_task06(cls.study)

    def test_complete_report_passes_with_unique_checks(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertEqual(len(self.report.checks), 39)
        self.assertEqual(len({check.name for check in self.report.checks}), 39)
        self.assertEqual(self.report.study_digest, task06_study_digest(self.study))

    def test_validation_records_are_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            self.report.study_digest = "0" * 64  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            self.report.checks[0].passed = False  # type: ignore[misc]

    def test_corrupted_scientific_fields_fail_validation(self) -> None:
        corruptions = []

        wavelengths = self.study.wavelengths_m.copy()
        wavelengths[0] *= 1.01
        corruptions.append(("wavelength", replace(self.study, wavelengths_m=wavelengths)))

        maximum = self.study.maximum_bragg_orders.copy()
        maximum[0, 0] += 1
        corruptions.append(("maximum order", replace(self.study, maximum_bragg_orders=maximum)))

        ratios = self.study.bragg_ratios_q.copy()
        ratios[0] *= 0.99
        corruptions.append(("Bragg ratio", replace(self.study, bragg_ratios_q=ratios)))

        phi = self.study.phi_rad.copy()
        phi[0] *= 1.01
        corruptions.append(("angle", replace(self.study, phi_rad=phi)))

        radii = self.study.photo_radii_m.copy()
        radii[0] += 1e-4
        corruptions.append(("radius", replace(self.study, photo_radii_m=radii)))

        flags = self.study.screen_visible_flags.copy()
        flags[0] = not flags[0]
        statuses = list(self.study.order_statuses)
        statuses[0] = "back_scattering" if statuses[0] == "forward_screen" else "forward_screen"
        corruptions.append(
            (
                "visibility",
                replace(
                    self.study,
                    screen_visible_flags=flags,
                    order_statuses=tuple(statuses),
                ),
            )
        )

        labels = ("incorrect label", self.study.spacing_labels[1])
        corruptions.append(("spacing label", replace(self.study, spacing_labels=labels)))

        bad_fit = replace(
            self.study.first_order_fits[0],
            constrained_gradient_v_inv_sqrt=(
                self.study.first_order_fits[0].constrained_gradient_v_inv_sqrt * 1.01
            ),
        )
        corruptions.append(
            (
                "fit",
                replace(
                    self.study,
                    first_order_fits=(bad_fit, self.study.first_order_fits[1]),
                ),
            )
        )

        for label, corrupted in corruptions:
            with self.subTest(corruption=label):
                result = validate_task06(corrupted)
                self.assertFalse(result.passed)
                self.assertTrue(result.failed_checks)

    def test_invalid_report_and_check_records_fail(self) -> None:
        with self.assertRaises(ValueError):
            ValidationCheck("", True, 0.0, 0.0, "unit", "comparison", 0.0, "text")
        with self.assertRaises(ValueError):
            Task06ValidationReport("wrong", "0" * 64, self.report.checks)
        with self.assertRaises(ValueError):
            Task06ValidationReport(self.report.schema_version, "bad", self.report.checks)
        with self.assertRaises(TypeError):
            validate_task06(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
