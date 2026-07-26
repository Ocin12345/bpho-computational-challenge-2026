from __future__ import annotations

import math
import unittest

from task08_quantum_cryptography.reference import (
    REFERENCE_CASES,
    reference_classical_mismatch,
    reference_quantum_mismatch,
)


class ReferenceTests(unittest.TestCase):
    def test_exact_cases_match_double_angle_references(self) -> None:
        self.assertEqual(len(REFERENCE_CASES), 5)
        for case in REFERENCE_CASES:
            self.assertAlmostEqual(
                reference_classical_mismatch(case.theta_deg, case.phi_deg),
                float(case.classical_mismatch),
                places=15,
            )
            self.assertAlmostEqual(
                reference_quantum_mismatch(case.theta_deg, case.phi_deg),
                float(case.quantum_mismatch),
                places=15,
            )

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            reference_classical_mismatch(True, 0.0)
        with self.assertRaises(ValueError):
            reference_quantum_mismatch(math.inf, 0.0)


if __name__ == "__main__":
    unittest.main()
