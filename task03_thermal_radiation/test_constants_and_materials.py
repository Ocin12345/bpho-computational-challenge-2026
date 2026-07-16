"""Tests for authoritative Task 3 constants and official material data.

Stage 4 protects the physical constants. Official Einstein-material tests will
be added to this module in Stage 6.
"""

from __future__ import annotations

import unittest

from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
    STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
    WIEN_DISPLACEMENT_CONSTANT_M_K,
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


if __name__ == "__main__":
    unittest.main()
