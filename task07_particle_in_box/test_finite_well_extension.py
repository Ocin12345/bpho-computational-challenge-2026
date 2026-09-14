"""Tests for finite wells, tunnelling and packet revival."""

from __future__ import annotations

import unittest

import numpy as np

from task07_particle_in_box.constants import ELECTRON_MASS_KG, REDUCED_PLANCK_CONSTANT_J_S
from task07_particle_in_box.finite_well_extension import (
    finite_square_well_states,
    finite_well_wavefunction_m_neg_half,
    gaussian_wavepacket_evolution,
    rectangular_barrier_transmission,
)


class FiniteWellExtensionTests(unittest.TestCase):
    def test_bound_states_are_ordered_below_the_barrier(self) -> None:
        states = finite_square_well_states(1.0e-9, 20.0)
        self.assertGreaterEqual(len(states), 7)
        energies = np.asarray([state.energy_above_bottom_ev for state in states])
        self.assertTrue(np.all(np.diff(energies) > 0.0))
        self.assertTrue(np.all(energies < 20.0))
        self.assertTrue(all(state.binding_energy_ev < 0.0 for state in states))
        self.assertEqual(tuple(state.parity for state in states[:4]), ("even", "odd", "even", "odd"))

    def test_finite_well_wavefunction_is_normalized_and_continuous(self) -> None:
        state = finite_square_well_states(1.0e-9, 20.0)[0]
        x = np.linspace(-3.0e-9, 3.0e-9, 100001)
        psi = finite_well_wavefunction_m_neg_half(x, state, 1.0e-9)
        self.assertAlmostEqual(float(np.trapezoid(psi**2, x)), 1.0, places=7)
        epsilon = 1.0e-16
        boundary = finite_well_wavefunction_m_neg_half(
            np.asarray([0.5e-9 - epsilon, 0.5e-9 + epsilon]), state, 1.0e-9
        )
        relative_jump = abs(float(boundary[1] - boundary[0])) / max(
            abs(float(boundary[0])), abs(float(boundary[1]))
        )
        # The two samples are separated by 2e-16 m, so the remaining change is
        # the physical derivative across that finite interval, not a jump.
        self.assertLess(relative_jump, 1.0e-5)

    def test_tunnelling_falls_exponentially_with_width(self) -> None:
        narrow = float(rectangular_barrier_transmission(5.0, 10.0, 0.2e-9))
        wide = float(rectangular_barrier_transmission(5.0, 10.0, 0.8e-9))
        self.assertGreater(narrow, wide)
        self.assertGreater(narrow, 0.0)
        self.assertLess(wide, 1.0)

    def test_barrier_transmission_is_bounded_above_and_below_height(self) -> None:
        values = rectangular_barrier_transmission(
            np.asarray([2.0, 10.0, 20.0]), 10.0, 0.4e-9
        )
        self.assertTrue(np.all((values >= 0.0) & (values <= 1.0)))

    def test_packet_norm_and_full_revival(self) -> None:
        width = 1.0e-9
        revival = 4.0 * ELECTRON_MASS_KG * width**2 / (
            np.pi * REDUCED_PLANCK_CONSTANT_J_S
        )
        x = np.linspace(0.0, width, 2001)
        result = gaussian_wavepacket_evolution(
            x,
            np.asarray([0.0, 0.17 * revival, revival]),
            box_width_m=width,
            centre_m=0.32e-9,
            spatial_sigma_m=0.06e-9,
            mean_wavenumber_per_m=35.0e9,
            maximum_state=180,
        )
        np.testing.assert_allclose(result.norm, np.ones(3), atol=2.0e-10)
        overlap = abs(
            np.trapezoid(
                np.conjugate(result.wavefunction_m_neg_half[0])
                * result.wavefunction_m_neg_half[-1],
                x,
            )
        )
        self.assertGreater(float(overlap), 1.0 - 2.0e-10)
        self.assertAlmostEqual(result.revival_time_s, revival, places=20)


if __name__ == "__main__":
    unittest.main()
