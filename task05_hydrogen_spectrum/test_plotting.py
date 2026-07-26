from __future__ import annotations

import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt

from task05_hydrogen_spectrum.analysis import build_task05_study
from task05_hydrogen_spectrum.generate_task05 import FIGURE_FILENAMES
from task05_hydrogen_spectrum.plotting import (
    EXPECTED_PNG_DIMENSIONS,
    create_balmer_visible_spectrum_figure,
    create_bohr_energy_level_figure,
    create_hydrogen_series_convergence_figure,
    create_hydrogen_validation_figure,
    create_photon_energy_vs_wavelength_figure,
    create_task05_summary_figure,
    generate_task05_figures,
)
from task05_hydrogen_spectrum.validation import (
    Task05ValidationReport,
    validate_task05,
)


class Task05PlottingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task05_study()
        cls.report = validate_task05(cls.study)

    def test_public_factories_require_and_accept_validated_evidence(self) -> None:
        factories = (
            create_photon_energy_vs_wavelength_figure,
            create_bohr_energy_level_figure,
            create_balmer_visible_spectrum_figure,
            create_hydrogen_series_convergence_figure,
            create_hydrogen_validation_figure,
            create_task05_summary_figure,
        )
        for factory in factories:
            with self.subTest(factory=factory.__name__):
                figure = factory(self.study, self.report)
                self.assertGreater(len(figure.axes), 0)
                plt.close(figure)

    def test_public_factory_rejects_a_failing_report(self) -> None:
        failing_check = replace(self.report.checks[0], passed=False)
        failing_report = Task05ValidationReport(
            self.report.schema_version,
            (failing_check, *self.report.checks[1:]),
        )
        with self.assertRaisesRegex(RuntimeError, "passing report"):
            create_task05_summary_figure(self.study, failing_report)

    def test_generation_writes_every_verified_png_and_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = generate_task05_figures(Path(temporary) / "figures")
            self.assertTrue(result.report.passed)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                FIGURE_FILENAMES,
            )
            for path in result.output_paths:
                self.assertGreater(path.stat().st_size, 1000)
                if path.suffix == ".png":
                    content = path.read_bytes()
                    self.assertTrue(content.startswith(b"\x89PNG\r\n\x1a\n"))
                    self.assertEqual(
                        struct.unpack(">II", content[16:24]),
                        EXPECTED_PNG_DIMENSIONS[path.name],
                    )
                else:
                    text = path.read_text(encoding="utf-8")
                    self.assertIn("<svg", text)
                    self.assertNotIn("<dc:date>", text)

    def test_repeated_figure_generation_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "figures"
            first = generate_task05_figures(directory)
            first_bytes = {path.name: path.read_bytes() for path in first.output_paths}
            second = generate_task05_figures(directory)
            second_bytes = {path.name: path.read_bytes() for path in second.output_paths}
            self.assertEqual(first_bytes, second_bytes)

    def test_late_failure_restores_every_existing_figure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "figures"
            directory.mkdir()
            originals: dict[str, bytes] = {}
            for index, filename in enumerate(FIGURE_FILENAMES):
                content = f"figure-sentinel-{index}".encode()
                (directory / filename).write_bytes(content)
                originals[filename] = content

            from task05_hydrogen_spectrum import plotting as module

            real_replace = module._replace_path
            calls = 0

            def failing_replace(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 8:
                    raise OSError("injected late figure failure")
                real_replace(source, destination)

            with patch.object(module, "_replace_path", side_effect=failing_replace):
                with self.assertRaisesRegex(OSError, "injected late figure failure"):
                    generate_task05_figures(directory)
            self.assertEqual(
                {
                    filename: (directory / filename).read_bytes()
                    for filename in FIGURE_FILENAMES
                },
                originals,
            )


if __name__ == "__main__":
    unittest.main()
