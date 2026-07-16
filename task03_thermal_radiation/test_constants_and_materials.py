"""Tests for authoritative Task 3 constants and official material data."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

import numpy as np

from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    EINSTEIN_DEBYE_FACTOR,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
    STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
    WIEN_DISPLACEMENT_CONSTANT_M_K,
)
from task03_thermal_radiation.materials import (
    EinsteinMaterial,
    OFFICIAL_MATERIALS,
)


class PhysicalConstantTests(unittest.TestCase):
    """Protect the exact SI values and independently documented identities."""

    def test_defining_constants_have_exact_selected_values(self) -> None:
        self.assertEqual(PLANCK_CONSTANT_J_S, 6.62607015e-34)
        self.assertEqual(SPEED_OF_LIGHT_M_S, 299_792_458.0)
        self.assertEqual(BOLTZMANN_CONSTANT_J_K, 1.380649e-23)

    def test_derived_stefan_boltzmann_constant_matches_specification(self) -> None:
        self.assertAlmostEqual(
            STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
            5.670374419184e-8,
            delta=5.0e-21,
        )

    def test_wien_constant_matches_independent_reference(self) -> None:
        self.assertAlmostEqual(
            WIEN_DISPLACEMENT_CONSTANT_M_K,
            2.897771955185e-3,
            delta=5.0e-16,
        )

    def test_einstein_debye_factor_matches_specification(self) -> None:
        self.assertAlmostEqual(
            EINSTEIN_DEBYE_FACTOR,
            0.805995977008235,
            delta=5.0e-16,
        )


class OfficialMaterialTests(unittest.TestCase):
    """Protect every source field transcribed from the official slide."""

    def test_official_rows_match_source_order_and_values(self) -> None:
        observed = tuple(
            (
                material.name,
                material.symbol,
                material.debye_temperature_k,
                material.official_frequency_1e13_hz,
            )
            for material in OFFICIAL_MATERIALS
        )
        expected = (
            ("Gold", "Au", 170.0, 0.2855),
            ("Copper", "Cu", 343.5, 0.5769),
            ("Titanium", "Ti", 420.0, 0.7054),
            ("Aluminium", "Al", 428.0, 0.7188),
            ("Iron", "Fe", 470.0, 0.7893),
            ("Silicon", "Si", 645.0, 1.0832),
            ("Carbon", "C", 2230.0, 3.7451),
        )

        self.assertIsInstance(OFFICIAL_MATERIALS, tuple)
        self.assertEqual(observed, expected)

    def test_official_names_and_symbols_are_unique(self) -> None:
        names = [material.name for material in OFFICIAL_MATERIALS]
        symbols = [material.symbol for material in OFFICIAL_MATERIALS]

        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_material_record_is_frozen(self) -> None:
        material = OFFICIAL_MATERIALS[0]

        with self.assertRaises(FrozenInstanceError):
            material.debye_temperature_k = 200.0

    def test_labels_must_be_non_empty_text(self) -> None:
        invalid_rows = (
            ("", "Au"),
            ("   ", "Au"),
            ("Gold", ""),
            (3, "Au"),
            ("Gold", None),
        )
        for name, symbol in invalid_rows:
            with self.subTest(name=name, symbol=symbol):
                with self.assertRaises((TypeError, ValueError)):
                    EinsteinMaterial(name, symbol, 170.0, 0.2855)

    def test_source_numbers_must_be_positive_finite_reals(self) -> None:
        invalid_values = (0.0, -1.0, np.nan, np.inf, True, "170")
        for value in invalid_values:
            with self.subTest(debye_temperature_k=value):
                with self.assertRaises((TypeError, ValueError)):
                    EinsteinMaterial("Gold", "Au", value, 0.2855)
            with self.subTest(official_frequency_1e13_hz=value):
                with self.assertRaises((TypeError, ValueError)):
                    EinsteinMaterial("Gold", "Au", 170.0, value)


if __name__ == "__main__":
    unittest.main()
