"""Tests for the Task 10 offline-app acceptance contract."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from task10_hydrogenic_orbitals.validate_task10_app import APP_DIRECTORY, validate_app


class AppValidationTests(unittest.TestCase):
    def test_complete_app_contract_passes(self) -> None:
        report = validate_app()
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 23)
        self.assertEqual(len({check.name for check in report.checks}), 23)

    def test_remote_dependency_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app_copy = Path(temporary_directory) / "app"
            shutil.copytree(APP_DIRECTORY, app_copy)
            index_path = app_copy / "index.html"
            html = index_path.read_text(encoding="utf-8")
            index_path.write_text(
                html.replace(
                    "</head>",
                    '<script src="https://example.invalid/runtime.js"></script></head>',
                ),
                encoding="utf-8",
            )
            report = validate_app(app_copy)
            self.assertFalse(report.passed)
            self.assertIn("offline_html", {check.name for check in report.failed_checks})

    def test_missing_canvas_accessibility_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app_copy = Path(temporary_directory) / "app"
            shutil.copytree(APP_DIRECTORY, app_copy)
            index_path = app_copy / "index.html"
            html = index_path.read_text(encoding="utf-8")
            index_path.write_text(
                html.replace(
                    'aria-label="Relative density on the x-y plane at z equals zero"',
                    "",
                ).replace(
                    "The x-y probability-density slice requires Canvas support.",
                    "",
                ),
                encoding="utf-8",
            )
            report = validate_app(app_copy)
            self.assertFalse(report.passed)
            failed = {check.name for check in report.failed_checks}
            self.assertIn("accessible_canvases", failed)
            self.assertIn("canvas_fallbacks", failed)


if __name__ == "__main__":
    unittest.main()
