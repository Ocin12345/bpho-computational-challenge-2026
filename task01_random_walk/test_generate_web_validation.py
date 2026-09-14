"""Tests for the Task 1 browser-validation dataset."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from task01_random_walk.generate_web_validation import (
    build_validation_payload,
    save_validation_payload,
)


class WebValidationDataTests(unittest.TestCase):
    """Verify deterministic evidence generation and serialization."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = {
            "angle_samples": 2_400,
            "angle_bins": 12,
            "radial_walks": 1_000,
            "radial_steps": 100,
            "radial_bins": 16,
            "batch_size": 200,
            "seed": 17,
        }
        cls.payload = build_validation_payload(**cls.parameters)

    def test_histogram_counts_preserve_all_samples(self) -> None:
        angular = self.payload["angular"]
        radial = self.payload["radial"]
        self.assertEqual(
            sum(item["count"] for item in angular["bins"]),
            angular["sample_count"],
        )
        self.assertEqual(
            sum(item["count"] for item in radial["bins"]),
            radial["n_walks"],
        )

    def test_theoretical_predictions_are_present_and_consistent(self) -> None:
        msd = self.payload["msd"]
        radial = self.payload["radial"]
        self.assertAlmostEqual(msd["theoretical_coefficient"], 1.0)
        self.assertGreater(radial["radius_95"], radial["radius_50"])
        self.assertAlmostEqual(radial["observed_fraction_50"], 0.5, delta=0.06)
        self.assertAlmostEqual(radial["observed_fraction_95"], 0.95, delta=0.03)

    def test_generation_is_reproducible(self) -> None:
        repeated = build_validation_payload(**self.parameters)
        self.assertEqual(self.payload, repeated)

    def test_saved_payload_round_trips_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "validation.json"
            saved_path = save_validation_payload(self.payload, output_path)
            self.assertEqual(
                json.loads(saved_path.read_text(encoding="utf-8")),
                self.payload,
            )


if __name__ == "__main__":
    unittest.main()
