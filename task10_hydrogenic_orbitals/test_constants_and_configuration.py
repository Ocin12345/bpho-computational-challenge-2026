"""Tests for Task 10 constants and immutable configuration."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from task10_hydrogenic_orbitals.configuration import (
    DEFAULT_CONFIGURATION,
    HydrogenicConfiguration,
    HydrogenicState,
    official_gallery_states,
)
from task10_hydrogenic_orbitals.constants import CONSTANTS


class ConstantsAndConfigurationTests(unittest.TestCase):
    def test_codata_2022_constants_are_frozen(self) -> None:
        self.assertEqual(CONSTANTS.electron_mass_kg, 9.109_383_713_9e-31)
        self.assertEqual(CONSTANTS.atomic_mass_constant_kg, 1.660_539_068_92e-27)
        self.assertEqual(CONSTANTS.bohr_radius_m, 5.291_772_105_44e-11)
        self.assertEqual(CONSTANTS.hartree_energy_ev, 27.211_386_245_981)
        self.assertEqual(CONSTANTS.elementary_charge_c, 1.602_176_634e-19)
        with self.assertRaises(FrozenInstanceError):
            CONSTANTS.bohr_radius_m = 1.0  # type: ignore[misc]

    def test_state_properties_and_immutability(self) -> None:
        state = HydrogenicState(5, 4, -3, atomic_number=6, mass_number=12)
        self.assertEqual(state.family, "G")
        self.assertEqual(state.label, "5g (m=-3)")
        self.assertEqual(state.radial_node_count, 0)
        self.assertEqual(state.angular_node_count, 4)
        with self.assertRaises(FrozenInstanceError):
            state.m = 0  # type: ignore[misc]

    def test_invalid_quantum_and_nuclear_numbers_are_rejected(self) -> None:
        invalid_arguments = (
            (0, 0, 0, 1, 1),
            (9, 0, 0, 1, 1),
            (2, 2, 0, 1, 1),
            (2, 1, 2, 1, 1),
            (2, 1, 0, 0, 1),
            (2, 1, 0, 21, 42),
            (2, 1, 0, 6, 5),
            (2, 1, 0, 6, 19),
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    HydrogenicState(
                        arguments[0],
                        arguments[1],
                        arguments[2],
                        atomic_number=arguments[3],
                        mass_number=arguments[4],
                    )
        for arguments in ((True, 0, 0), (2, 1.0, 0), (2, 1, False)):
            with self.subTest(arguments=arguments):
                with self.assertRaises(TypeError):
                    HydrogenicState(*arguments)  # type: ignore[arg-type]

    def test_default_configuration_and_invalid_domains(self) -> None:
        self.assertEqual(DEFAULT_CONFIGURATION.maximum_n, 8)
        self.assertEqual(DEFAULT_CONFIGURATION.display_threshold, 0.15)
        self.assertEqual(DEFAULT_CONFIGURATION.probability_containment, 0.9995)
        self.assertEqual(DEFAULT_CONFIGURATION.slice_resolution, 161)
        self.assertEqual(DEFAULT_CONFIGURATION.slice_count, 17)
        self.assertEqual(
            (DEFAULT_CONFIGURATION.animation_width_px, DEFAULT_CONFIGURATION.animation_height_px),
            (3840, 2160),
        )
        self.assertEqual(DEFAULT_CONFIGURATION.animation_frame_count, 80)
        self.assertEqual(DEFAULT_CONFIGURATION.animation_frames_per_second, 20)
        self.assertEqual(DEFAULT_CONFIGURATION.animation_quality, 93)
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.slice_count = 9  # type: ignore[misc]

        invalid = (
            {"maximum_n": 0},
            {"maximum_n": 9},
            {"maximum_atomic_number": 0},
            {"display_threshold": -0.1},
            {"display_threshold": 1.0},
            {"probability_containment": 0.98},
            {"probability_containment": 1.0},
            {"radial_profile_points": 500},
            {"slice_resolution": 80},
            {"slice_count": 6},
            {"animation_width_px": 800, "animation_height_px": 600},
            {"animation_dpi": 71},
            {"animation_frames_per_second": 0},
            {"animation_frame_count": 7},
            {"animation_quality": 101},
            {"animation_size_budget_bytes": 1000},
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    HydrogenicConfiguration(**values)

    def test_official_gallery_is_complete_and_ordered(self) -> None:
        states = official_gallery_states()
        self.assertEqual(len(states), 25)
        self.assertEqual(states[0], HydrogenicState(1, 0, 0))
        self.assertEqual(states[-1], HydrogenicState(5, 4, 4))
        self.assertEqual(
            {(state.n, state.l, state.m) for state in states},
            {
                (l + 1, l, m)
                for l in range(5)
                for m in range(-l, l + 1)
            },
        )
        carbon = official_gallery_states(atomic_number=6, mass_number=12)
        self.assertTrue(
            all(
                state.atomic_number == 6 and state.mass_number == 12
                for state in carbon
            )
        )


if __name__ == "__main__":
    unittest.main()
