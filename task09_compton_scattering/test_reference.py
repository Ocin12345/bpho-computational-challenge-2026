"""Cross-check production kinematics against independent scalar references."""

from __future__ import annotations

import unittest

import numpy as np

from task09_compton_scattering.models import compton_kinematics
from task09_compton_scattering.reference import reference_kinematics


class IndependentReferenceTests(unittest.TestCase):
    def test_complete_reference_sample_matches_production(self) -> None:
        energies = (50.0, 100.0, 200.0, 500.0, 1_000.0)
        angles = (0.0, 0.25, 1.0, 30.0, 60.0, 90.0, 120.0, 150.0, 179.75, 180.0)
        for energy in energies:
            for theta in angles:
                with self.subTest(energy=energy, theta=theta):
                    production = compton_kinematics(energy, theta)
                    reference = reference_kinematics(energy, theta)
                    for field_name in (
                        "fractional_wavelength_shift",
                        "scattered_energy_kev",
                        "electron_kinetic_energy_kev",
                        "electron_gamma",
                        "electron_beta",
                        "electron_pc_kev",
                        "electron_recoil_angle_deg",
                    ):
                        self.assertAlmostEqual(
                            float(getattr(production, field_name)),
                            float(getattr(reference, field_name)),
                            delta=2.0e-11 * max(1.0, abs(float(getattr(reference, field_name)))),
                        )
                    self.assertEqual(
                        bool(production.electron_recoil_direction_defined),
                        reference.electron_recoil_direction_defined,
                    )

    def test_reference_mass_shell_and_energy_conservation(self) -> None:
        rest_energy = 510.9989506917531
        for energy in (50.0, 200.0, 1_000.0):
            for theta in np.linspace(0.0, 180.0, 37):
                state = reference_kinematics(energy, float(theta))
                total_electron_energy = rest_energy + state.electron_kinetic_energy_kev
                self.assertAlmostEqual(
                    energy,
                    state.scattered_energy_kev + state.electron_kinetic_energy_kev,
                    delta=4.0e-13,
                )
                self.assertAlmostEqual(
                    total_electron_energy**2 - state.electron_pc_kev**2,
                    rest_energy**2,
                    delta=2.0e-9,
                )

    def test_reference_rejects_invalid_scalars(self) -> None:
        with self.assertRaises(TypeError):
            reference_kinematics(True, 30.0)
        with self.assertRaises(ValueError):
            reference_kinematics(float("nan"), 30.0)
        with self.assertRaises(ValueError):
            reference_kinematics(100.0, -1.0)
        with self.assertRaises(ValueError):
            reference_kinematics(100.0, 181.0)


if __name__ == "__main__":
    unittest.main()
