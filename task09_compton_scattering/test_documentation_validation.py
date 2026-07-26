"""Tests for the Task 9 documentation integrity report."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from task09_compton_scattering.documentation_validation import (
    REPOSITORY_ROOT,
    validate_task09_documentation,
)


class DocumentationValidationTests(unittest.TestCase):
    def test_complete_documentation_passes(self) -> None:
        report = validate_task09_documentation()
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 11)
        self.assertEqual(len({check.name for check in report.checks}), 11)

    def test_missing_local_link_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(
                REPOSITORY_ROOT / "task09_compton_scattering",
                root / "task09_compton_scattering",
            )
            for source_directory in ("data/task09", "figures/task09"):
                source = REPOSITORY_ROOT / source_directory
                destination = root / source_directory
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination)
            readme = root / "task09_compton_scattering" / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(
                text.replace(
                    "(OFFICIAL_REQUIREMENTS.md)",
                    "(missing-official-requirements.md)",
                ),
                encoding="utf-8",
            )
            report = validate_task09_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn("local_links", {check.name for check in report.failed_checks})

    def test_removed_endpoint_disclosure_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(
                REPOSITORY_ROOT / "task09_compton_scattering",
                root / "task09_compton_scattering",
            )
            for filename in ("README.md", "RESULTS_AND_INTERPRETATION.md"):
                path = root / "task09_compton_scattering" / filename
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace("direction is\nundefined", "direction has no value")
                    .replace("direction is undefined", "direction has no value"),
                    encoding="utf-8",
                )
            report = validate_task09_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn(
                "equations_and_endpoints",
                {check.name for check in report.failed_checks},
            )


if __name__ == "__main__":
    unittest.main()
