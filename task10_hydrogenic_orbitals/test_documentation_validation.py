"""Tests for the Task 10 documentation integrity report."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from task10_hydrogenic_orbitals.documentation_validation import (
    REPOSITORY_ROOT,
    validate_task10_documentation,
)


def _copy_documentation_fixture(root: Path) -> None:
    shutil.copytree(
        REPOSITORY_ROOT / "task10_hydrogenic_orbitals",
        root / "task10_hydrogenic_orbitals",
    )
    for source_directory in ("data/task10", "figures/task10", "reports/task10"):
        source = REPOSITORY_ROOT / source_directory
        destination = root / source_directory
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)


class DocumentationValidationTests(unittest.TestCase):
    def test_complete_documentation_passes(self) -> None:
        report = validate_task10_documentation()
        self.assertTrue(report.passed)
        self.assertEqual(len(report.checks), 13)
        self.assertEqual(len({check.name for check in report.checks}), 13)

    def test_missing_local_link_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _copy_documentation_fixture(root)
            readme = root / "task10_hydrogenic_orbitals" / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(
                text.replace(
                    "(OFFICIAL_REQUIREMENTS.md)",
                    "(missing-official-requirements.md)",
                ),
                encoding="utf-8",
            )
            report = validate_task10_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn("local_links", {check.name for check in report.failed_checks})

    def test_removed_motion_caveat_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _copy_documentation_fixture(root)
            for filename in ("README.md", "RESULTS_AND_INTERPRETATION.md", "REPRODUCIBILITY.md"):
                path = root / "task10_hydrogenic_orbitals" / filename
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace("not electron motion", "camera interpretation")
                    .replace("not a classical electron path", "a quantum visualization"),
                    encoding="utf-8",
                )
            report = validate_task10_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn("display_interpretation", {check.name for check in report.failed_checks})

    def test_removed_scope_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _copy_documentation_fixture(root)
            for filename in ("README.md", "RESULTS_AND_INTERPRETATION.md"):
                path = root / "task10_hydrogenic_orbitals" / filename
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace("one non-relativistic electron", "one quantum state")
                    .replace("point-Coulomb field", "central potential"),
                    encoding="utf-8",
                )
            report = validate_task10_documentation(root)
            self.assertFalse(report.passed)
            self.assertIn("scope_boundaries", {check.name for check in report.failed_checks})


if __name__ == "__main__":
    unittest.main()
