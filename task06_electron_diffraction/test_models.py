from __future__ import annotations

import unittest

import numpy as np

from task06_electron_diffraction.models import (
    bragg_angle_rad,
    bragg_ratio,
    caliper_diameter_m,
    electron_momentum_kg_m_s,
    electron_wavelength_m,
    maximum_bragg_order,
    maximum_screen_order,
    photo_ring_radius_m,
    scattering_angle_rad,
    screen_visible,
)


class ModelTests(unittest.TestCase):
    def test_scalar_wavelength_contract_and_anchors(self) -> None:
        at_one = electron_wavelength_m(1000.0)
        at_five = electron_wavelength_m(5000.0)
        self.assertEqual(at_one.shape, ())
        self.assertEqual(at_one.dtype, np.float64)
        self.assertAlmostEqual(float(at_one) * 1e12, 38.782994319927006, places=11)
        self.assertAlmostEqual(float(at_five) * 1e12, 17.344282334069003, places=11)

    def test_momentum_and_wavelength_are_vectorized(self) -> None:
        voltage = np.asarray([[1000.0], [5000.0]])
        momentum = electron_momentum_kg_m_s(voltage)
        wavelength = electron_wavelength_m(voltage)
        self.assertEqual(momentum.shape, (2, 1))
        self.assertEqual(wavelength.shape, (2, 1))
        self.assertTrue(np.all(momentum > 0.0))
        self.assertTrue(np.all(np.diff(wavelength[:, 0]) < 0.0))

    def test_bragg_angles_and_geometries_use_exact_equations(self) -> None:
        voltage = np.asarray([1000.0, 5000.0])
        spacing = 0.123e-9
        ratio = bragg_ratio(voltage, spacing, 1)
        theta = bragg_angle_rad(voltage, spacing, 1)
        phi = scattering_angle_rad(voltage, spacing, 1)
        photo = photo_ring_radius_m(voltage, spacing, 1, 0.065)
        caliper = caliper_diameter_m(voltage, spacing, 1, 0.065)
        np.testing.assert_allclose(np.sin(theta), ratio, rtol=5e-15)
        np.testing.assert_allclose(phi, 2.0 * theta, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(photo, 0.065 * np.sin(2.0 * phi), rtol=5e-15)
        np.testing.assert_allclose(caliper, 0.13 * np.sin(phi), rtol=5e-15)
        self.assertFalse(np.allclose(photo, caliper, rtol=1e-4))
        self.assertAlmostEqual(float(photo[0]) * 1e3, 38.465414872, places=9)

    def test_maximum_order_anchors(self) -> None:
        voltage = np.asarray([[1000.0], [5000.0]])
        spacing = np.asarray([[0.123e-9, 0.213e-9]])
        np.testing.assert_array_equal(
            maximum_bragg_order(voltage, spacing),
            np.asarray([[6, 10], [14, 24]], dtype=np.int64),
        )
        np.testing.assert_array_equal(
            maximum_screen_order(voltage, spacing),
            np.asarray([[4, 7], [10, 17]], dtype=np.int64),
        )

    def test_visibility_distinguishes_back_scattering(self) -> None:
        self.assertTrue(bool(screen_visible(1000.0, 0.123e-9, 4)))
        self.assertFalse(bool(screen_visible(1000.0, 0.123e-9, 5)))
        self.assertLess(float(photo_ring_radius_m(1000.0, 0.123e-9, 6, 0.065)), 0.0)

    def test_broadcasting_contract(self) -> None:
        ratio = bragg_ratio(
            np.asarray([[1000.0], [2000.0]]),
            np.asarray([[0.123e-9, 0.213e-9]]),
            1,
        )
        self.assertEqual(ratio.shape, (2, 2))

    def test_invalid_inputs_fail_explicitly(self) -> None:
        invalid_voltage = (True, 999.0, 5001.0, 0.0, np.nan, 1.0 + 1.0j, "1000")
        for value in invalid_voltage:
            with self.subTest(voltage=value), self.assertRaises((TypeError, ValueError)):
                electron_wavelength_m(value)
        invalid_order = (True, 0, -1, 1.0, 1.0 + 0.0j)
        for value in invalid_order:
            with self.subTest(order=value), self.assertRaises((TypeError, ValueError)):
                bragg_ratio(1000.0, 0.123e-9, value)
        with self.assertRaises(ValueError):
            bragg_angle_rad(1000.0, 0.123e-9, 7)
        with self.assertRaises(ValueError):
            bragg_ratio([1000.0, 2000.0], [0.123e-9, 0.213e-9, 0.3e-9], 1)
        with self.assertRaises(ValueError):
            photo_ring_radius_m([1000.0, 2000.0], 0.123e-9, 1, [0.06, 0.07, 0.08])


if __name__ == "__main__":
    unittest.main()
