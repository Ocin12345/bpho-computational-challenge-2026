"""Tests for fine structure, selection rules, intensities and linewidths."""

from __future__ import annotations

import unittest

from task05_hydrogen_spectrum.precision_spectroscopy_extension import (
    LAMB_2S_2P_FREQUENCY_HZ,
    corrected_level_energy_ev,
    dirac_binding_energy_ev,
    e1_transition_allowed,
    pedagogical_lamb_shift_ev,
    radial_dipole_matrix_element_m,
    transition_profile,
)


class PrecisionHydrogenExtensionTests(unittest.TestCase):
    def test_dirac_ground_state_is_close_to_reduced_mass_bohr_value(self) -> None:
        energy = dirac_binding_energy_ev(1, 0, 0.5)
        self.assertGreater(energy, -13.61)
        self.assertLess(energy, -13.59)

    def test_fine_structure_splits_2p_j_levels(self) -> None:
        p_half = dirac_binding_energy_ev(2, 1, 0.5)
        p_three_half = dirac_binding_energy_ev(2, 1, 1.5)
        self.assertLess(p_half, p_three_half)
        self.assertGreater(p_three_half - p_half, 1.0e-5)
        self.assertLess(p_three_half - p_half, 1.0e-4)

    def test_lamb_anchor_and_n_cubed_scaling(self) -> None:
        shift_2s = pedagogical_lamb_shift_ev(2, 0, 0.5)
        shift_4s = pedagogical_lamb_shift_ev(4, 0, 0.5)
        frequency = shift_2s * 1.602176634e-19 / 6.62607015e-34
        self.assertAlmostEqual(frequency, LAMB_2S_2P_FREQUENCY_HZ, places=3)
        self.assertAlmostEqual(shift_2s / shift_4s, 8.0, places=12)
        self.assertEqual(pedagogical_lamb_shift_ev(2, 1, 0.5), 0.0)

    def test_e1_selection_rules(self) -> None:
        self.assertTrue(e1_transition_allowed((2, 1, 1.5), (1, 0, 0.5)))
        self.assertTrue(e1_transition_allowed((3, 0, 0.5), (2, 1, 1.5)))
        self.assertFalse(e1_transition_allowed((2, 0, 0.5), (1, 0, 0.5)))
        self.assertFalse(e1_transition_allowed((3, 2, 2.5), (1, 0, 0.5)))

    def test_lyman_alpha_rate_matches_known_atomic_scale(self) -> None:
        line = transition_profile((2, 1, 1.5), (1, 0, 0.5), gas_temperature_k=0.0)
        self.assertGreater(line.einstein_a_per_s, 6.0e8)
        self.assertLess(line.einstein_a_per_s, 6.6e8)
        self.assertGreater(line.wavelength_nm, 121.4)
        self.assertLess(line.wavelength_nm, 121.7)
        self.assertEqual(line.doppler_fwhm_hz, 0.0)

    def test_radial_integral_and_thermal_width_are_physical(self) -> None:
        radial = radial_dipole_matrix_element_m(2, 1, 1, 0)
        self.assertGreater(radial, 1.0e-11)
        cold = transition_profile((3, 1, 1.5), (2, 0, 0.5), gas_temperature_k=100.0)
        hot = transition_profile((3, 1, 1.5), (2, 0, 0.5), gas_temperature_k=400.0)
        self.assertAlmostEqual(hot.doppler_fwhm_hz / cold.doppler_fwhm_hz, 2.0, places=12)
        self.assertGreater(hot.voigt_fwhm_hz, hot.natural_fwhm_hz)

    def test_corrected_energy_lifts_2s_above_2p_half(self) -> None:
        self.assertGreater(
            corrected_level_energy_ev(2, 0, 0.5),
            corrected_level_energy_ev(2, 1, 0.5),
        )


if __name__ == "__main__":
    unittest.main()
