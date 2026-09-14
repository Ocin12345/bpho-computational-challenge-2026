"""Tests for the Task 2 extension evidence exporter."""

from __future__ import annotations

import unittest

from task02_brownian_motion.generate_extension_evidence import generate_payload


class ExtensionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = generate_payload(seed=2026)

    def test_payload_is_accepted_and_modes_are_mutually_exclusive(self) -> None:
        self.assertTrue(self.payload["accepted"])
        baseline = self.payload["modes"]["random_reset"]
        hard_disc = self.payload["modes"]["hard_disc"]
        self.assertGreater(baseline["direction_resets"], 0)
        self.assertEqual(baseline["small_small_impulses"], 0)
        self.assertEqual(hard_disc["direction_resets"], 0)
        self.assertGreater(hard_disc["small_small_impulses"], 0)

    def test_paths_and_conservation_evidence_are_complete(self) -> None:
        for mode in self.payload["modes"].values():
            lengths = {len(values) for values in mode["path"].values()}
            self.assertEqual(len(lengths), 1)
            self.assertGreater(next(iter(lengths)), 20)
        controlled = self.payload["controlled_collisions"]
        self.assertEqual(controlled["impulses_applied"], controlled["sample_count"])
        self.assertLess(controlled["maximum_normalized_momentum_error"], 1.0e-12)
        self.assertLess(controlled["maximum_normalized_energy_error"], 1.0e-12)


if __name__ == "__main__":
    unittest.main()
