"""Tests for the Task 9 final artifact acceptance gate."""

from __future__ import annotations

import unittest

from task09_compton_scattering.final_validation import validate_task09_final


class FinalAcceptanceValidationTests(unittest.TestCase):
    def test_complete_final_artifact_package_passes(self) -> None:
        report = validate_task09_final()

        self.assertTrue(
            report.passed,
            msg="; ".join(
                f"{check.name}: {check.detail}" for check in report.failed_checks
            ),
        )
        self.assertEqual(len(report.checks), 8)


if __name__ == "__main__":
    unittest.main()
