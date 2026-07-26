from __future__ import annotations

import unittest

import numpy as np

from task05_hydrogen_spectrum.constants import HC_EV_NM
from task05_hydrogen_spectrum.models import (
    bohr_energy_ev,
    bohr_energy_j,
    series_limit_energy_ev,
    series_limit_wavelength_m,
    transition_energy_ev,
    transition_energy_j,
    transition_frequency_hz,
    transition_wavelength_m,
)


class BohrModelTests(unittest.TestCase):
    def test_level_anchors_and_scalar_return_type(self) -> None:
        ground = bohr_energy_ev(1)
        self.assertEqual(ground.shape, ())
        self.assertEqual(ground.dtype, np.float64)
        self.assertAlmostEqual(float(ground), -13.6056931229905, places=12)
        self.assertAlmostEqual(float(bohr_energy_ev(2)), -3.40142328074763, places=12)
        self.assertLess(float(bohr_energy_j(1)), 0.0)

    def test_named_transition_anchors(self) -> None:
        cases = (
            (2, 1, 10.204269842242885, 121.5022734110182),
            (3, 2, 1.8896796004153491, 656.1122764194983),
            (4, 2, 2.5510674605607213, 486.0090936440728),
            (10, 9, 0.031914588807014785, 38848.75320904924),
        )
        for initial, final, expected_energy, expected_wavelength in cases:
            with self.subTest(initial=initial, final=final):
                self.assertAlmostEqual(
                    float(transition_energy_ev(initial, final)),
                    expected_energy,
                    places=12,
                )
                self.assertAlmostEqual(
                    float(transition_wavelength_m(initial, final) * 1.0e9),
                    expected_wavelength,
                    places=9,
                )

    def test_vectorization_broadcasting_and_dtypes(self) -> None:
        initial = np.array([[2], [3]], dtype=np.int64)
        final = np.array([1], dtype=np.int64)
        energy = transition_energy_ev(initial, final)
        self.assertEqual(energy.shape, (2, 1))
        self.assertEqual(energy.dtype, np.float64)
        self.assertTrue(np.all(energy > 0.0))

    def test_energy_frequency_and_wavelength_identities(self) -> None:
        initial = np.arange(2, 11, dtype=np.int64)
        final = np.ones(9, dtype=np.int64)
        energy = transition_energy_ev(initial, final)
        wavelength_nm = transition_wavelength_m(initial, final) * 1.0e9
        frequency = transition_frequency_hz(initial, final)
        np.testing.assert_allclose(energy * wavelength_nm, HC_EV_NM, rtol=5.0e-15)
        np.testing.assert_allclose(
            transition_energy_j(initial, final),
            energy * 1.602176634e-19,
            rtol=5.0e-15,
        )
        self.assertTrue(np.all(np.diff(frequency) > 0.0))

    def test_series_limits(self) -> None:
        finals = np.arange(1, 6, dtype=np.int64)
        energy = series_limit_energy_ev(finals)
        wavelength = series_limit_wavelength_m(finals) * 1.0e9
        np.testing.assert_allclose(
            energy,
            [13.6056931229905, 3.40142328074763, 1.51174368033228,
             0.850355820186907, 0.544227724919621],
            rtol=5.0e-14,
        )
        np.testing.assert_allclose(
            wavelength,
            [91.1267050583, 364.506820233, 820.140345524,
             1458.027280932, 2278.167626457],
            rtol=5.0e-12,
        )

    def test_models_reject_non_integer_or_invalid_quantum_numbers(self) -> None:
        invalid_levels = (True, 0, -1, 2.0, 2.5, 1 + 0j, [1, True])
        for value in invalid_levels:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                bohr_energy_ev(value)
        invalid_pairs = ((2, 2), (1, 2), (0, 1), (3.0, 2), (True, 1))
        for initial, final in invalid_pairs:
            with self.subTest(pair=(initial, final)), self.assertRaises((TypeError, ValueError)):
                transition_energy_ev(initial, final)

    def test_models_do_not_mutate_inputs(self) -> None:
        initial = np.array([2, 3, 4], dtype=np.int64)
        final = np.array([1, 1, 2], dtype=np.int64)
        initial_before = initial.copy()
        final_before = final.copy()
        transition_wavelength_m(initial, final)
        np.testing.assert_array_equal(initial, initial_before)
        np.testing.assert_array_equal(final, final_before)


if __name__ == "__main__":
    unittest.main()
