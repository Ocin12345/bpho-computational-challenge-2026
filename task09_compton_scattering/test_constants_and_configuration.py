"""Tests for frozen Task 9 constants and configuration."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from task09_compton_scattering.configuration import Task09Configuration
from task09_compton_scattering.constants import (
    ELECTRON_COMPTON_WAVELENGTH_M,
    ELECTRON_MASS_KG,
    ELECTRON_REST_ENERGY_KEV,
    ELEMENTARY_CHARGE_C,
    OFFICIAL_INCIDENT_ENERGIES_KEV,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
    THOMSON_CROSS_SECTION_M2,
)


class ConstantsAndConfigurationTests(unittest.TestCase):
    def test_frozen_si_and_codata_constants(self) -> None:
        self.assertEqual(SPEED_OF_LIGHT_M_S, 299_792_458.0)
        self.assertEqual(PLANCK_CONSTANT_J_S, 6.626_070_15e-34)
        self.assertEqual(ELEMENTARY_CHARGE_C, 1.602_176_634e-19)
        self.assertEqual(ELECTRON_MASS_KG, 9.109_383_7139e-31)
        self.assertAlmostEqual(ELECTRON_REST_ENERGY_KEV, 510.9989506917531, places=12)
        self.assertAlmostEqual(
            ELECTRON_COMPTON_WAVELENGTH_M,
            2.426310235380317e-12,
            places=26,
        )
        self.assertAlmostEqual(THOMSON_CROSS_SECTION_M2, 6.652458705237673e-29, places=42)

    def test_default_configuration_matches_official_study(self) -> None:
        configuration = Task09Configuration()
        self.assertEqual(
            configuration.incident_energies_kev,
            OFFICIAL_INCIDENT_ENERGIES_KEV,
        )
        self.assertEqual(configuration.angle_minimum_deg, 0.0)
        self.assertEqual(configuration.angle_maximum_deg, 180.0)
        self.assertEqual(configuration.angle_point_count, 721)
        self.assertEqual(configuration.angle_spacing_deg, 0.25)
        self.assertEqual(configuration.browser_angle_spacing_deg, 0.5)
        self.assertEqual(
            (configuration.animation_width_px, configuration.animation_height_px),
            (1600, 900),
        )
        self.assertEqual(configuration.animation_frame_count, 73)
        self.assertEqual(configuration.cross_section_quadrature_order, 256)

    def test_configuration_is_immutable(self) -> None:
        configuration = Task09Configuration()
        with self.assertRaises(FrozenInstanceError):
            configuration.angle_point_count = 3

    def test_invalid_energy_configurations_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Task09Configuration(incident_energies_kev=(50.0, True))
        with self.assertRaises(ValueError):
            Task09Configuration(incident_energies_kev=())
        with self.assertRaises(ValueError):
            Task09Configuration(incident_energies_kev=(100.0, 50.0))
        with self.assertRaises(ValueError):
            Task09Configuration(maximum_interactive_energy_kev=500.0)
        with self.assertRaises(ValueError):
            Task09Configuration(default_incident_energy_kev=10_000.0)

    def test_invalid_angle_and_grid_configurations_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task09Configuration(angle_minimum_deg=-1.0)
        with self.assertRaises(ValueError):
            Task09Configuration(angle_maximum_deg=179.0)
        with self.assertRaises(TypeError):
            Task09Configuration(angle_point_count=True)
        with self.assertRaises(ValueError):
            Task09Configuration(angle_point_count=720)
        with self.assertRaises(ValueError):
            Task09Configuration(browser_angle_point_count=1)
        with self.assertRaises(ValueError):
            Task09Configuration(cross_section_quadrature_order=31)
        with self.assertRaises(ValueError):
            Task09Configuration(cross_section_quadrature_order=255)


if __name__ == "__main__":
    unittest.main()
