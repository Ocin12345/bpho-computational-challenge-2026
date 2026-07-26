"""Tests for the normalized Task 10 production model."""

from __future__ import annotations

import math
import unittest

import numpy as np

from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.models import (
    associated_ferrers,
    associated_laguerre,
    cartesian_to_spherical,
    density_m_neg_three,
    effective_bohr_radius_m,
    normalize_density_for_display,
    orbital_energy_ev,
    orbital_summary,
    real_spherical_harmonic,
    scaled_density_cartesian,
    scaled_radial_probability,
    scaled_radial_wavefunction,
    scaled_wavefunction_cartesian,
)
from task10_hydrogenic_orbitals.reference import (
    analytic_1s_scaled_density,
    analytic_2pz_scaled_density,
    analytic_2s_scaled_density,
)


class HydrogenicModelTests(unittest.TestCase):
    def test_official_hydrogen_anchors(self) -> None:
        ground = HydrogenicState(1, 0, 0)
        state_3d = HydrogenicState(3, 2, 0)
        summary = orbital_summary(ground)
        self.assertAlmostEqual(summary.reduced_mass_ratio, 0.9994517208658746, 15)
        self.assertAlmostEqual(summary.effective_bohr_radius_angstrom, 0.5294675065300278, 15)
        self.assertAlmostEqual(summary.energy_ev, -13.598233405345852, 13)
        self.assertAlmostEqual(orbital_energy_ev(state_3d), -1.5109148228162058, 13)
        self.assertEqual(summary.radial_nodes, 0)
        self.assertEqual(summary.angular_nodes, 0)
        self.assertEqual(summary.degeneracy, 1)
        self.assertEqual(summary.parity, 1)

    def test_energy_and_length_scaling_are_exactly_structured(self) -> None:
        states = (
            HydrogenicState(1, 0, 0, 1, 1),
            HydrogenicState(2, 1, 0, 2, 4),
            HydrogenicState(3, 2, 1, 6, 12),
            HydrogenicState(5, 4, -4, 20, 40),
        )
        invariant_energy = []
        invariant_length = []
        for state in states:
            summary = orbital_summary(state)
            invariant_energy.append(
                summary.energy_ev
                * state.n**2
                / state.atomic_number**2
                / summary.reduced_mass_ratio
            )
            invariant_length.append(
                summary.effective_bohr_radius_m
                * state.atomic_number
                * summary.reduced_mass_ratio
            )
        np.testing.assert_allclose(
            invariant_energy,
            [-0.5 * CONSTANTS.hartree_energy_ev] * len(states),
            rtol=5e-15,
            atol=0.0,
        )
        np.testing.assert_allclose(
            invariant_length,
            [CONSTANTS.bohr_radius_m] * len(states),
            rtol=5e-15,
            atol=0.0,
        )

    def test_associated_laguerre_known_polynomials(self) -> None:
        x = np.array([0.0, 0.5, 2.0, 7.0])
        np.testing.assert_allclose(associated_laguerre(0, 3, x), 1.0)
        np.testing.assert_allclose(associated_laguerre(1, 3, x), 4.0 - x)
        np.testing.assert_allclose(
            associated_laguerre(2, 1, x),
            0.5 * (x**2 - 6.0 * x + 6.0),
            rtol=1e-15,
            atol=1e-15,
        )

    def test_sign_free_ferrers_low_orders(self) -> None:
        x = np.linspace(-1.0, 1.0, 9)
        np.testing.assert_allclose(associated_ferrers(0, 0, x), 1.0)
        np.testing.assert_allclose(associated_ferrers(1, 0, x), x)
        np.testing.assert_allclose(
            associated_ferrers(1, 1, x),
            np.sqrt(np.maximum(0.0, 1.0 - x**2)),
            atol=2e-15,
        )
        np.testing.assert_allclose(
            associated_ferrers(2, 0, x),
            0.5 * (3.0 * x**2 - 1.0),
            atol=2e-15,
        )

    def test_real_p_orbital_orientation(self) -> None:
        expected = math.sqrt(3.0 / (4.0 * math.pi))
        self.assertAlmostEqual(
            real_spherical_harmonic(1, 1, math.pi / 2.0, 0.0),
            expected,
            15,
        )
        self.assertAlmostEqual(
            real_spherical_harmonic(1, -1, math.pi / 2.0, math.pi / 2.0),
            expected,
            15,
        )
        self.assertAlmostEqual(
            real_spherical_harmonic(1, 0, 0.0, 1.7),
            expected,
            15,
        )
        self.assertAlmostEqual(
            real_spherical_harmonic(0, 0, 0.7, -2.1),
            1.0 / math.sqrt(4.0 * math.pi),
            15,
        )

    def test_low_state_radial_closed_forms(self) -> None:
        radius = np.linspace(0.0, 12.0, 101)
        state_1s = HydrogenicState(1, 0, 0)
        state_2s = HydrogenicState(2, 0, 0)
        state_2p = HydrogenicState(2, 1, 0)
        np.testing.assert_allclose(
            scaled_radial_wavefunction(state_1s, radius),
            2.0 * np.exp(-radius),
            rtol=2e-15,
            atol=2e-15,
        )
        np.testing.assert_allclose(
            scaled_radial_wavefunction(state_2s, radius),
            (2.0 - radius) * np.exp(-radius / 2.0) / (2.0 * math.sqrt(2.0)),
            rtol=3e-15,
            atol=3e-15,
        )
        np.testing.assert_allclose(
            scaled_radial_wavefunction(state_2p, radius),
            radius * np.exp(-radius / 2.0) / (2.0 * math.sqrt(6.0)),
            rtol=3e-15,
            atol=3e-15,
        )
        self.assertAlmostEqual(scaled_radial_wavefunction(state_2s, 2.0), 0.0, 15)

    def test_analytic_density_anchors(self) -> None:
        state_1s = HydrogenicState(1, 0, 0)
        state_2s = HydrogenicState(2, 0, 0)
        state_2pz = HydrogenicState(2, 1, 0)
        for radius in (0.0, 0.3, 2.0, 5.7):
            self.assertAlmostEqual(
                scaled_density_cartesian(state_1s, radius, 0.0, 0.0),
                analytic_1s_scaled_density(radius),
                14,
            )
            self.assertAlmostEqual(
                scaled_density_cartesian(state_2s, radius, 0.0, 0.0),
                analytic_2s_scaled_density(radius),
                14,
            )
            self.assertAlmostEqual(
                scaled_density_cartesian(state_2pz, 0.0, 0.0, radius),
                analytic_2pz_scaled_density(radius, 0.0),
                14,
            )

    def test_cartesian_origin_axes_and_broadcasting(self) -> None:
        radius, polar, azimuth = cartesian_to_spherical(
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([0.0, 0.0, 0.0]),
        )
        np.testing.assert_allclose(radius, [0.0, 1.0, 1.0])
        np.testing.assert_allclose(polar, [0.0, math.pi / 2, math.pi / 2])
        np.testing.assert_allclose(azimuth, [0.0, 0.0, math.pi / 2])

        state_1s = HydrogenicState(1, 0, 0)
        state_2px = HydrogenicState(2, 1, 1)
        self.assertAlmostEqual(
            scaled_density_cartesian(state_1s, 0.0, 0.0, 0.0),
            1.0 / math.pi,
            15,
        )
        self.assertEqual(
            scaled_wavefunction_cartesian(state_2px, 0.0, 0.0, 0.0),
            0.0,
        )
        self.assertGreater(
            abs(scaled_wavefunction_cartesian(state_2px, 1.0, 0.0, 0.0)),
            0.0,
        )
        self.assertAlmostEqual(
            scaled_wavefunction_cartesian(state_2px, 0.0, 1.0, 0.0),
            0.0,
            15,
        )

    def test_physical_density_has_expected_scaling(self) -> None:
        state = HydrogenicState(1, 0, 0)
        radius = effective_bohr_radius_m(state)
        physical = density_m_neg_three(state, [0.0, radius], 0.0, 0.0)
        scaled = scaled_density_cartesian(state, [0.0, 1.0], 0.0, 0.0)
        np.testing.assert_allclose(physical * radius**3, scaled, rtol=2e-15)

    def test_outputs_are_immutable_and_display_normalization_is_separate(self) -> None:
        state = HydrogenicState(3, 2, 1)
        radius = np.linspace(0.0, 20.0, 51)
        outputs = (
            associated_laguerre(2, 3, radius),
            associated_ferrers(3, 2, np.linspace(-1.0, 1.0, 51)),
            scaled_radial_wavefunction(state, radius),
            scaled_radial_probability(state, radius),
            scaled_density_cartesian(state, radius, 0.2, -0.1),
        )
        for output in outputs:
            self.assertIsInstance(output, np.ndarray)
            self.assertFalse(output.flags.writeable)
            with self.assertRaises(ValueError):
                output[0] = 99.0

        density = np.array([0.0, 2.0, 1.0])
        relative = normalize_density_for_display(density)
        np.testing.assert_allclose(relative, [0.0, 1.0, 0.5])
        np.testing.assert_allclose(density, [0.0, 2.0, 1.0])
        self.assertFalse(relative.flags.writeable)

    def test_invalid_inputs_are_rejected(self) -> None:
        state = HydrogenicState(1, 0, 0)
        invalid_calls = (
            lambda: associated_laguerre(-1, 0, 1.0),
            lambda: associated_laguerre(1, -1, 1.0),
            lambda: associated_laguerre(1, 0, float("nan")),
            lambda: associated_ferrers(1, 2, 0.0),
            lambda: associated_ferrers(1, 0, 1.1),
            lambda: real_spherical_harmonic(1, 2, 0.2, 0.3),
            lambda: real_spherical_harmonic(1, 0, -0.1, 0.3),
            lambda: scaled_radial_wavefunction(state, -1.0),
            lambda: cartesian_to_spherical([1.0, 2.0], [1.0, 2.0, 3.0], 0.0),
            lambda: normalize_density_for_display([0.0, 0.0]),
            lambda: normalize_density_for_display([0.0, -1.0]),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
