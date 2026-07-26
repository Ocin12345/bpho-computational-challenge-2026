"""Tests for vectorised Task 9 production kinematics."""

from __future__ import annotations

import unittest

import numpy as np

from task09_compton_scattering.configuration import DEFAULT_CONFIGURATION
from task09_compton_scattering.constants import SPEED_OF_LIGHT_M_S
from task09_compton_scattering.models import (
    angle_samples,
    compton_kinematics,
    degrees_to_radians,
    energy_angle_study,
    radians_to_degrees,
)


class ComptonModelTests(unittest.TestCase):
    def test_angle_conversions_are_reciprocal(self) -> None:
        angles = np.asarray([0.0, 30.0, 90.0, 180.0])
        np.testing.assert_allclose(
            radians_to_degrees(degrees_to_radians(angles)),
            angles,
            rtol=0.0,
            atol=2.0e-14,
        )

    def test_forward_endpoint_preserves_undefined_direction(self) -> None:
        state = compton_kinematics(200.0, 0.0)
        self.assertEqual(float(state.fractional_wavelength_shift), 0.0)
        self.assertEqual(float(state.scattered_energy_kev), 200.0)
        self.assertEqual(float(state.electron_kinetic_energy_kev), 0.0)
        self.assertEqual(float(state.electron_beta), 0.0)
        self.assertEqual(float(state.electron_pc_kev), 0.0)
        self.assertEqual(float(state.electron_recoil_angle_deg), 90.0)
        self.assertFalse(bool(state.electron_recoil_direction_defined))

    def test_backscatter_anchors_for_all_official_energies(self) -> None:
        energies = np.asarray(DEFAULT_CONFIGURATION.incident_energies_kev)
        state = compton_kinematics(energies, 180.0)
        expected_shift = np.asarray(
            [0.195695118091, 0.391390236182, 0.782780472364, 1.956951180910, 3.913902361820]
        )
        expected_beta = np.asarray(
            [0.176848642672, 0.318793384428, 0.521337140407, 0.794736221542, 0.920465867749]
        )
        np.testing.assert_allclose(
            state.fractional_wavelength_shift,
            expected_shift,
            rtol=2.0e-12,
            atol=2.0e-13,
        )
        np.testing.assert_allclose(
            state.electron_beta,
            expected_beta,
            rtol=3.0e-12,
            atol=2.0e-13,
        )
        np.testing.assert_array_equal(state.electron_recoil_angle_deg, 0.0)
        np.testing.assert_array_equal(state.electron_recoil_direction_defined, True)

    def test_right_angle_recoil_angle_anchors(self) -> None:
        energies = np.asarray(DEFAULT_CONFIGURATION.incident_energies_kev)
        state = compton_kinematics(energies, 90.0)
        expected = np.asarray(
            [42.329552359076, 39.906872163848, 35.705015209771, 26.813843232391, 18.684825897744]
        )
        np.testing.assert_allclose(
            state.electron_recoil_angle_deg,
            expected,
            rtol=2.0e-13,
            atol=2.0e-12,
        )

    def test_wavelength_and_energy_forms_are_consistent(self) -> None:
        state = compton_kinematics(
            np.asarray([50.0, 500.0, 1_000.0])[:, None],
            np.asarray([0.0, 37.0, 90.0, 143.0, 180.0])[None, :],
        )
        np.testing.assert_allclose(
            state.scattered_wavelength_m,
            state.incident_wavelength_m + state.wavelength_shift_m,
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_allclose(
            state.fractional_wavelength_shift,
            state.wavelength_shift_m / state.incident_wavelength_m,
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_allclose(
            state.electron_kinetic_energy_kev + state.scattered_energy_kev,
            state.incident_energy_kev,
            rtol=3.0e-15,
            atol=3.0e-13,
        )

    def test_official_study_shape_monotonicity_and_bounds(self) -> None:
        study = energy_angle_study()
        self.assertEqual(study.theta_deg.shape, (5, 721))
        self.assertEqual(float(study.theta_deg[0, 360]), 90.0)
        self.assertTrue(np.all(np.diff(study.fractional_wavelength_shift, axis=1) >= 0.0))
        self.assertTrue(np.all(np.diff(study.electron_beta, axis=1) >= -2.0e-15))
        self.assertTrue(np.all(np.diff(study.electron_recoil_angle_deg, axis=1) <= 2.0e-13))
        self.assertTrue(np.all(study.electron_beta >= 0.0))
        self.assertTrue(np.all(study.electron_beta < 1.0))
        self.assertTrue(np.all(study.electron_speed_m_s < SPEED_OF_LIGHT_M_S))
        self.assertTrue(np.all(study.scattered_energy_kev > 0.0))

    def test_outputs_are_read_only(self) -> None:
        state = compton_kinematics(200.0, np.asarray([0.0, 90.0, 180.0]))
        for value in vars(state).values():
            self.assertFalse(value.flags.writeable)
        with self.assertRaises(ValueError):
            state.electron_beta[0] = 1.0

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            compton_kinematics(True, 30.0)
        with self.assertRaises(TypeError):
            compton_kinematics(100.0, False)
        with self.assertRaises(ValueError):
            compton_kinematics(0.0, 30.0)
        with self.assertRaises(ValueError):
            compton_kinematics(100.0, -1.0)
        with self.assertRaises(ValueError):
            compton_kinematics(100.0, 181.0)
        with self.assertRaises(ValueError):
            compton_kinematics(np.ones(2), np.ones(3))
        with self.assertRaises(TypeError):
            angle_samples(True)
        with self.assertRaises(ValueError):
            angle_samples(100)
        with self.assertRaises(ValueError):
            energy_angle_study([100.0, 50.0])


if __name__ == "__main__":
    unittest.main()
