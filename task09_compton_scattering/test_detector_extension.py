"""Tests for Compton material transport and detector broadening."""

from __future__ import annotations

import unittest

import numpy as np

from task09_compton_scattering.detector_extension import (
    DetectorResponseConfiguration,
    detector_fwhm_kev,
    simulate_detector_response,
)


class ComptonDetectorExtensionTests(unittest.TestCase):
    def test_zero_effect_limit_matches_core_event_by_event(self) -> None:
        result = simulate_detector_response(
            DetectorResponseConfiguration(
                event_count=3000,
                binding_energy_kev=0.0,
                doppler_sigma_fraction=0.0,
                multiple_scatter_probability=0.0,
                detector_noise_fwhm_kev=0.0,
                detector_stochastic_fwhm_sqrt_kev=0.0,
                detector_constant_fwhm_fraction=0.0,
                seed=1,
            )
        )
        np.testing.assert_array_equal(
            result.measured_energy_kev, result.ideal_single_scatter_energy_kev
        )
        self.assertEqual(result.multiple_scatter_fraction, 0.0)

    def test_multiple_scattering_lowers_mean_exit_energy(self) -> None:
        single = simulate_detector_response(
            DetectorResponseConfiguration(
                event_count=6000,
                multiple_scatter_probability=0.0,
                detector_noise_fwhm_kev=0.0,
                detector_stochastic_fwhm_sqrt_kev=0.0,
                detector_constant_fwhm_fraction=0.0,
                seed=12,
            )
        )
        multiple = simulate_detector_response(
            DetectorResponseConfiguration(
                event_count=6000,
                multiple_scatter_probability=1.0,
                detector_noise_fwhm_kev=0.0,
                detector_stochastic_fwhm_sqrt_kev=0.0,
                detector_constant_fwhm_fraction=0.0,
                seed=12,
            )
        )
        self.assertLess(multiple.measured_mean_energy_kev, single.measured_mean_energy_kev)
        self.assertEqual(multiple.multiple_scatter_fraction, 1.0)

    def test_detector_resolution_grows_with_energy(self) -> None:
        config = DetectorResponseConfiguration(event_count=100)
        widths = detector_fwhm_kev(np.asarray([10.0, 100.0, 1000.0]), config)
        self.assertTrue(np.all(np.diff(widths) > 0.0))

    def test_sampled_angles_and_energies_stay_physical(self) -> None:
        result = simulate_detector_response(
            DetectorResponseConfiguration(event_count=4000, seed=44)
        )
        self.assertTrue(np.all((result.first_scatter_angle_deg >= 0.0) & (result.first_scatter_angle_deg <= 180.0)))
        self.assertTrue(np.all(result.material_exit_energy_kev > 0.0))
        self.assertTrue(np.all(result.measured_energy_kev >= 0.0))
        self.assertGreater(result.multiple_scatter_fraction, 0.15)
        self.assertLess(result.multiple_scatter_fraction, 0.21)

    def test_seed_reproducibility(self) -> None:
        config = DetectorResponseConfiguration(event_count=1200, seed=88)
        first = simulate_detector_response(config)
        second = simulate_detector_response(config)
        np.testing.assert_array_equal(first.measured_energy_kev, second.measured_energy_kev)
        np.testing.assert_array_equal(first.first_scatter_angle_deg, second.first_scatter_angle_deg)


if __name__ == "__main__":
    unittest.main()
