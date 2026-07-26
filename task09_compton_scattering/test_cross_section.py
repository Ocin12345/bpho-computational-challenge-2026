"""Tests for the separately labelled Klein–Nishina extension."""

from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from task09_compton_scattering.configuration import DEFAULT_CONFIGURATION
from task09_compton_scattering.constants import (
    CLASSICAL_ELECTRON_RADIUS_M,
    THOMSON_CROSS_SECTION_M2,
)
from task09_compton_scattering.cross_section import (
    build_klein_nishina_study,
    klein_nishina_differential_cross_section_m2_sr,
    klein_nishina_total_cross_section_m2,
)
from task09_compton_scattering.cross_section_reference import (
    reference_total_cross_section_m2,
)
from task09_compton_scattering.cross_section_validation import (
    cross_section_study_digest,
    validate_cross_section_study,
)
from task09_compton_scattering.models import angle_samples


class KleinNishinaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        energies = np.asarray(DEFAULT_CONFIGURATION.incident_energies_kev)[:, None]
        theta = angle_samples()[None, :]
        cls.study = build_klein_nishina_study(energies, theta)

    def test_forward_value_and_total_anchors(self) -> None:
        np.testing.assert_allclose(
            self.study.differential_cross_section_m2_sr[:, 0],
            CLASSICAL_ELECTRON_RADIUS_M**2,
            rtol=2.0e-15,
            atol=0.0,
        )
        expected = np.asarray(
            [0.561506943706434, 0.492748487639704, 0.406482469509729, 0.289166317232033, 0.211207882544261]
        )
        np.testing.assert_allclose(
            self.study.total_cross_section_barn[:, 0],
            expected,
            rtol=5.0e-13,
            atol=0.0,
        )

    def test_closed_form_matches_independent_quadrature(self) -> None:
        energies = np.asarray(DEFAULT_CONFIGURATION.incident_energies_kev)
        analytical = klein_nishina_total_cross_section_m2(energies)
        numerical = np.asarray(
            [reference_total_cross_section_m2(float(energy)) for energy in energies]
        )
        np.testing.assert_allclose(analytical, numerical, rtol=3.0e-13, atol=0.0)

    def test_low_energy_limit_and_bounds(self) -> None:
        low_energy = reference_total_cross_section_m2(1.0e-6)
        self.assertAlmostEqual(low_energy / THOMSON_CROSS_SECTION_M2, 1.0, delta=1.0e-8)
        self.assertTrue(np.all(self.study.differential_cross_section_m2_sr >= 0.0))
        self.assertTrue(np.all(self.study.total_cross_section_m2 > 0.0))
        self.assertTrue(np.all(self.study.total_cross_section_m2 < THOMSON_CROSS_SECTION_M2))

    def test_extension_arrays_are_read_only(self) -> None:
        for value in vars(self.study).values():
            self.assertFalse(value.flags.writeable)
        with self.assertRaises(ValueError):
            self.study.theta_pdf_rad_inv[0, 0] = 1.0

    def test_complete_extension_validation_passes(self) -> None:
        report = validate_cross_section_study(self.study)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 30)
        self.assertEqual(len({check.name for check in report.checks}), 30)
        self.assertEqual(report.study_digest, cross_section_study_digest(self.study))

    def test_corrupted_differential_cross_section_is_detected(self) -> None:
        values = self.study.differential_cross_section_m2_sr.copy()
        values[2, 360] *= 1.05
        corrupted = replace(self.study, differential_cross_section_m2_sr=values)
        report = validate_cross_section_study(corrupted)
        self.assertFalse(report.passed)
        failed = {check.name for check in report.failed_checks}
        self.assertIn("relative_differential_identity", failed)
        self.assertIn("theta_density_identity", failed)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            klein_nishina_differential_cross_section_m2_sr(True, 30.0)
        with self.assertRaises(ValueError):
            klein_nishina_differential_cross_section_m2_sr(100.0, 181.0)
        with self.assertRaises(ValueError):
            klein_nishina_total_cross_section_m2(0.0)
        with self.assertRaises(TypeError):
            reference_total_cross_section_m2(100.0, True)


if __name__ == "__main__":
    unittest.main()
