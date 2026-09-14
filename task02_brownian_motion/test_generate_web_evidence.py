"""Tests for the Task 2 website evidence exporter."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from task02_brownian_motion.generate_web_evidence import (
    build_payload,
    write_javascript_payload,
    write_payload,
)


class WebEvidenceTests(unittest.TestCase):
    def test_payload_preserves_reference_results(self) -> None:
        payload = build_payload()

        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["reference_parameters"]["n_small"], 1_000)
        self.assertEqual(payload["ensemble"]["run_count"], 64)
        self.assertEqual(len(payload["ensemble"]["endpoints"]), 64)
        self.assertEqual(payload["ensemble"]["source_series_points"], 2_001)
        self.assertLessEqual(len(payload["ensemble"]["series"]), 242)
        self.assertAlmostEqual(
            payload["ensemble"]["msd_fit_r_squared"],
            0.9832392581647977,
        )
        self.assertGreater(
            payload["validation"]["minimum_observed_order"],
            1.0,
        )
        self.assertEqual(
            payload["validation"]["maximum_residual_penetration_nm"],
            0.0,
        )

    def test_writer_creates_round_trippable_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "task-02-evidence.json"
            write_payload(output)
            recovered = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(recovered["schema_version"], 1)
        self.assertEqual(recovered["ensemble"]["run_count"], 64)
        self.assertIn("validation_report", recovered["provenance"])

    def test_javascript_writer_creates_local_file_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "task-02-evidence.js"
            write_javascript_payload(output)
            source = output.read_text(encoding="utf-8")

        prefix = "window.TASK02_EVIDENCE = "
        self.assertTrue(source.startswith(prefix))
        recovered = json.loads(source.removeprefix(prefix).removesuffix(";\n"))
        self.assertTrue(recovered["passed"])
        self.assertEqual(recovered["ensemble"]["run_count"], 64)


if __name__ == "__main__":
    unittest.main()
