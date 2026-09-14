"""Checks for the accepted Task 1 dimensional browser evidence."""

from __future__ import annotations

import unittest

from task01_random_walk.generate_dimensional_validation import generate_payload


class DimensionalValidationPayloadTests(unittest.TestCase):
    def test_payload_contains_all_dimensions_and_invariants(self) -> None:
        payload = generate_payload(
            n_walks=6_000,
            max_steps=400,
            step_size=1.0,
            seed=2026,
        )
        self.assertTrue(payload["accepted"])
        self.assertEqual(
            [entry["dimension"] for entry in payload["dimensions"]],
            [1, 2, 3],
        )
        self.assertEqual(
            payload["invariants"]["rms_displacement"],
            "r_RMS = s sqrt(N)",
        )

    def test_distribution_and_scaling_arrays_are_complete(self) -> None:
        payload = generate_payload(
            n_walks=2_500,
            max_steps=320,
            step_size=0.75,
            seed=17,
        )
        for entry in payload["dimensions"]:
            self.assertEqual(len(entry["distribution"]["density"]), 36)
            self.assertEqual(len(entry["distribution"]["theory_density"]), 36)
            self.assertGreaterEqual(len(entry["scaling"]), 6)
            self.assertEqual(entry["scaling"][-1]["n_steps"], 320)


if __name__ == "__main__":
    unittest.main()
