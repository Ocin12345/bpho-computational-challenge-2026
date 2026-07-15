"""Tests for the Task 1 statistical validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from task01_random_walk.statistical_analysis import (  # noqa: E402
    analyse_endpoints,
    create_endpoint_distribution_figure,
    create_validation_figure,
    run_statistical_analysis,
    save_analysis_figures,
    save_statistics_csv,
    simulate_endpoints,
)


class StatisticalAnalysisTests(unittest.TestCase):
    """Verify reproducibility, calculations, and evidence outputs."""

    def test_endpoint_simulation_is_reproducible(self) -> None:
        first = simulate_endpoints(
            500,
            100,
            1.0,
            rng=np.random.default_rng(44),
            batch_size=125,
        )
        second = simulate_endpoints(
            500,
            100,
            1.0,
            rng=np.random.default_rng(44),
            batch_size=125,
        )

        self.assertEqual(first.shape, (500, 2))
        np.testing.assert_array_equal(first, second)

    def test_endpoint_analysis_matches_known_values(self) -> None:
        endpoints = np.array(
            [
                [1.0, 0.0],
                [-1.0, 0.0],
                [0.0, 1.0],
                [0.0, -1.0],
            ]
        )
        statistics = analyse_endpoints(endpoints, n_steps=1, step_size=1.0)

        self.assertEqual(statistics.mean_x, 0.0)
        self.assertEqual(statistics.mean_y, 0.0)
        self.assertAlmostEqual(statistics.mean_squared_displacement, 1.0)
        self.assertAlmostEqual(statistics.theoretical_msd, 1.0)
        self.assertAlmostEqual(statistics.msd_ratio, 1.0)

    def test_fixed_seed_analysis_agrees_with_theory(self) -> None:
        result = run_statistical_analysis(
            (10, 50, 100),
            n_walks=5_000,
            step_size=1.0,
            seed=2026,
            reference_n_steps=100,
            batch_size=500,
        )

        for statistics in result.statistics:
            with self.subTest(n_steps=statistics.n_steps):
                self.assertLess(abs(statistics.msd_ratio - 1.0), 0.06)
                self.assertLess(abs(statistics.variance_ratio_x - 1.0), 0.08)
                self.assertLess(abs(statistics.variance_ratio_y - 1.0), 0.08)

    def test_figures_have_expected_panels_and_equal_endpoint_axes(self) -> None:
        result = run_statistical_analysis(
            (10, 50),
            n_walks=500,
            step_size=1.0,
            seed=9,
            reference_n_steps=50,
            batch_size=250,
        )
        validation_figure = create_validation_figure(result)
        endpoint_figure = create_endpoint_distribution_figure(result)
        self.addCleanup(plt.close, validation_figure)
        self.addCleanup(plt.close, endpoint_figure)

        self.assertEqual(len(validation_figure.axes), 4)
        self.assertEqual(endpoint_figure.axes[0].get_aspect(), 1.0)
        self.assertIn(
            "Endpoint distribution",
            endpoint_figure.axes[0].get_title(loc="left"),
        )

    def test_csv_and_figure_files_are_saved(self) -> None:
        result = run_statistical_analysis(
            (10, 20),
            n_walks=500,
            step_size=1.0,
            seed=10,
            reference_n_steps=20,
            batch_size=250,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            figure_paths = save_analysis_figures(
                result,
                validation_stem=root / "validation",
                endpoint_stem=root / "endpoints",
                dpi=80,
            )
            csv_path = save_statistics_csv(result, root / "statistics.csv")

            for path in figure_paths:
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 5_000)
            self.assertTrue(csv_path.is_file())
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("theoretical_msd", csv_text)
            self.assertEqual(len(csv_text.strip().splitlines()), 3)

    def test_invalid_analysis_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_statistical_analysis(
                (10, 20),
                n_walks=100,
                reference_n_steps=30,
            )
        with self.assertRaises(ValueError):
            simulate_endpoints(
                1,
                10,
                1.0,
                rng=np.random.default_rng(1),
            )


if __name__ == "__main__":
    unittest.main()
