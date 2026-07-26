from __future__ import annotations

import unittest

from task07_particle_in_box.configuration import Task07Configuration
from task07_particle_in_box.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    REDUCED_PLANCK_CONSTANT_J_S,
)


class ConstantsAndConfigurationTests(unittest.TestCase):
    def test_frozen_constants(self) -> None:
        self.assertEqual(PLANCK_CONSTANT_J_S, 6.62607015e-34)
        self.assertEqual(ELEMENTARY_CHARGE_C, 1.602176634e-19)
        self.assertEqual(ELECTRON_MASS_KG, 9.1093837139e-31)
        self.assertAlmostEqual(
            REDUCED_PLANCK_CONSTANT_J_S * 2.0 * 3.141592653589793,
            PLANCK_CONSTANT_J_S,
            places=45,
        )

    def test_default_configuration_contract(self) -> None:
        configuration = Task07Configuration()
        self.assertEqual(configuration.quantum_numbers, tuple(range(1, 11)))
        self.assertEqual(configuration.density_quantum_numbers, (1, 2, 3, 4))
        self.assertEqual(configuration.numerical_grid_sizes[-1], 1600)
        self.assertEqual(configuration.position_point_count, 2001)
        self.assertAlmostEqual(configuration.box_width_nm, 1.0)

    def test_rejects_invalid_configuration_values(self) -> None:
        with self.assertRaises(ValueError):
            Task07Configuration(box_width_m=0.0)
        with self.assertRaises(TypeError):
            Task07Configuration(maximum_quantum_number=True)
        with self.assertRaises(ValueError):
            Task07Configuration(position_point_count=2000)
        with self.assertRaises(ValueError):
            Task07Configuration(density_quantum_numbers=(1, 1, 2))
        with self.assertRaises(ValueError):
            Task07Configuration(numerical_grid_sizes=(100, 80, 200))
        with self.assertRaises(ValueError):
            Task07Configuration(maximum_quantum_number=4, numerical_state_count=5)


if __name__ == "__main__":
    unittest.main()
