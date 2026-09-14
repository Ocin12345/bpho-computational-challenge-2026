"""Checks for the accepted Task 3 Debye browser evidence."""

from __future__ import annotations

import unittest

from task03_thermal_radiation.generate_debye_validation import generate_payload


class DebyeValidationPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = generate_payload()

    def test_payload_is_accepted_and_complete(self) -> None:
        self.assertTrue(self.payload["accepted"])
        self.assertEqual(self.payload["schema_version"], 1)
        self.assertEqual(len(self.payload["materials"]), 7)
        self.assertEqual(len(self.payload["curve"]), 251)
        self.assertEqual(len(self.payload["diagnostics"]), 6)

    def test_curve_has_physical_limits_and_ordering(self) -> None:
        curve = self.payload["curve"]
        self.assertEqual(curve[0]["debye_over_3r"], 0.0)
        self.assertEqual(curve[0]["einstein_over_3r"], 0.0)
        for point in curve[1:]:
            self.assertGreater(point["debye_over_3r"], point["einstein_over_3r"])
            self.assertLessEqual(point["debye_over_3r"], 1.0)

    def test_independent_checks_clear_declared_tolerances(self) -> None:
        checks = self.payload["checks"]
        self.assertTrue(checks["zero_temperature_limit"])
        self.assertTrue(checks["debye_bounded_and_monotonic"])
        self.assertTrue(checks["debye_exceeds_einstein_on_displayed_domain"])
        self.assertLess(checks["low_temperature_cubic_relative_error"], 1e-10)
        self.assertLess(checks["high_temperature_series_relative_error"], 1e-12)
        self.assertLess(checks["quadrature_convergence_over_3r"], 1e-11)


if __name__ == "__main__":
    unittest.main()
