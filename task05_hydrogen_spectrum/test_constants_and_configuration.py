from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from task05_hydrogen_spectrum.configuration import (
    DEFAULT_CONFIGURATION,
    Task05Configuration,
)
from task05_hydrogen_spectrum.constants import (
    ELEMENTARY_CHARGE_C,
    HC_EV_NM,
    PLANCK_CONSTANT_J_S,
    RYDBERG_CONSTANT_PER_M,
    RYDBERG_ENERGY_EV,
    RYDBERG_WAVELENGTH_NM,
    SPEED_OF_LIGHT_M_S,
)
from task05_hydrogen_spectrum.transitions import (
    HIGHER_SERIES_DISPLAY_GROUP,
    display_group_for_final,
    enumerate_transition_pairs,
    line_name_for_transition,
    series_name_for_final,
    spectral_region_for_wavelength_nm,
)


class ConstantAndConfigurationTests(unittest.TestCase):
    def test_frozen_source_constants_and_derived_values(self) -> None:
        self.assertEqual(PLANCK_CONSTANT_J_S, float("6.62607015e-34"))
        self.assertEqual(SPEED_OF_LIGHT_M_S, float("299792458"))
        self.assertEqual(ELEMENTARY_CHARGE_C, float("1.602176634e-19"))
        self.assertEqual(RYDBERG_CONSTANT_PER_M, float("10973731.568157"))
        self.assertAlmostEqual(HC_EV_NM, 1239.8419843320026, places=12)
        self.assertAlmostEqual(RYDBERG_ENERGY_EV, 13.6056931229905, places=12)
        self.assertAlmostEqual(RYDBERG_WAVELENGTH_NM, 91.1267050583, places=9)

    def test_default_configuration_is_frozen_and_complete(self) -> None:
        self.assertEqual(DEFAULT_CONFIGURATION.maximum_level, 10)
        self.assertEqual(DEFAULT_CONFIGURATION.expected_transition_count, 45)
        self.assertEqual(DEFAULT_CONFIGURATION.highlighted_series_final_max, 5)
        self.assertEqual(DEFAULT_CONFIGURATION.visible_min_nm, 380.0)
        self.assertEqual(DEFAULT_CONFIGURATION.visible_max_nm, 750.0)
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.maximum_level = 11  # type: ignore[misc]

    def test_configuration_rejects_invalid_values(self) -> None:
        invalid = (
            {"maximum_level": True},
            {"maximum_level": 1},
            {"highlighted_series_final_max": 10},
            {"visible_min_nm": 0.0},
            {"visible_min_nm": 800.0, "visible_max_nm": 700.0},
            {"level_energy_tolerance_ev": -1.0},
            {"evidence_size_budget_bytes": 0},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                Task05Configuration(**kwargs)

    def test_transition_pair_enumeration_is_complete_and_ordered(self) -> None:
        pairs = enumerate_transition_pairs(10)
        self.assertEqual(len(pairs), 45)
        self.assertEqual(pairs[:3], ((2, 1), (3, 1), (4, 1)))
        self.assertEqual(pairs[-3:], ((9, 8), (10, 8), (10, 9)))
        self.assertEqual(len(set(pairs)), 45)

    def test_series_and_line_labels_are_declared(self) -> None:
        self.assertEqual(series_name_for_final(1), "Lyman")
        self.assertEqual(series_name_for_final(6), "Humphreys")
        self.assertEqual(series_name_for_final(7), "n_f=7 series")
        self.assertEqual(display_group_for_final(5), "Pfund")
        self.assertEqual(display_group_for_final(6), HIGHER_SERIES_DISPLAY_GROUP)
        self.assertEqual(line_name_for_transition(3, 2), "H-alpha")
        self.assertEqual(line_name_for_transition(3, 1), "Lyman-beta")
        self.assertIsNone(line_name_for_transition(7, 2))

    def test_spectral_region_boundaries_are_inclusive(self) -> None:
        classify = lambda value: spectral_region_for_wavelength_nm(
            value,
            visible_min_nm=380.0,
            visible_max_nm=750.0,
        )
        self.assertEqual(classify(379.999), "ultraviolet")
        self.assertEqual(classify(380.0), "visible")
        self.assertEqual(classify(750.0), "visible")
        self.assertEqual(classify(750.001), "infrared")

    def test_transition_helpers_reject_invalid_inputs(self) -> None:
        with self.assertRaises(TypeError):
            enumerate_transition_pairs(True)
        with self.assertRaises(ValueError):
            enumerate_transition_pairs(1)
        with self.assertRaises(ValueError):
            line_name_for_transition(2, 2)
        with self.assertRaises(ValueError):
            spectral_region_for_wavelength_nm(
                0.0,
                visible_min_nm=380.0,
                visible_max_nm=750.0,
            )


if __name__ == "__main__":
    unittest.main()
