"""Pre-declared ensemble experiments and statistics for BPhO Task 2."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
from scipy import stats

from task02_brownian_motion.brownian_motion import (
    BrownianParameters,
    create_time_grid,
    run_simulation,
)


@dataclass(frozen=True)
class ExperimentDesign:
    """Pre-declared seeds, windows, parameter levels, and thresholds."""

    baseline_seed_start: int = 3_000
    baseline_run_count: int = 64
    comparison_run_count: int = 12
    time_step_run_count: int = 64
    max_time_ps: float = 200.0
    fit_start_ps: float = 20.0
    fit_end_ps: float = 100.0
    bootstrap_resamples: int = 2_000
    bootstrap_seed: int = 202_607_16
    output_time_series_points: int = 2_001
    particle_counts: tuple[int, ...] = (250, 500, 1_000)
    mass_ratios: tuple[float, ...] = (5.0, 10.0, 20.0)
    restitutions: tuple[float, ...] = (0.5, 0.8, 1.0)
    knudsen_parameters: tuple[float, ...] = (7.5, 15.0, 30.0)
    diffusion_r_squared_threshold: float = 0.90
    time_step_relative_difference_threshold: float = 0.25

    def __post_init__(self) -> None:
        """Validate that the design was fully specified before execution."""

        if self.baseline_run_count < 4:
            raise ValueError("baseline_run_count must be at least 4")
        if self.comparison_run_count < 4:
            raise ValueError("comparison_run_count must be at least 4")
        if self.time_step_run_count < 4:
            raise ValueError("time_step_run_count must be at least 4")
        if self.comparison_run_count > self.baseline_run_count:
            raise ValueError(
                "comparison_run_count must not exceed baseline_run_count"
            )
        if self.time_step_run_count > self.baseline_run_count:
            raise ValueError(
                "time_step_run_count must not exceed baseline_run_count"
            )
        if not 0.0 < self.fit_start_ps < self.fit_end_ps < self.max_time_ps:
            raise ValueError("fit window must lie strictly inside the run")
        if self.bootstrap_resamples < 100:
            raise ValueError("bootstrap_resamples must be at least 100")
        if self.output_time_series_points < 100:
            raise ValueError("output_time_series_points must be at least 100")

    @property
    def baseline_seeds(self) -> tuple[int, ...]:
        """All seeds in the primary ensemble."""

        return tuple(
            range(
                self.baseline_seed_start,
                self.baseline_seed_start + self.baseline_run_count,
            )
        )

    @property
    def comparison_seeds(self) -> tuple[int, ...]:
        """Common seeds used for each controlled parameter level."""

        return self.baseline_seeds[: self.comparison_run_count]

    @property
    def time_step_seeds(self) -> tuple[int, ...]:
        """Common seeds used for baseline versus half-step statistics."""

        return self.baseline_seeds[: self.time_step_run_count]


@dataclass(frozen=True)
class SimulationCase:
    """One unique simulation requested by the experiment design."""

    configuration_id: str
    factor_name: str
    factor_value: float
    seed: int
    parameters: BrownianParameters


@dataclass(frozen=True)
class RunRecord:
    """Recorded tracer path and diagnostics from one ensemble member."""

    configuration_id: str
    factor_name: str
    factor_value: float
    seed: int
    times_ps: np.ndarray
    displacement_x_nm: np.ndarray
    displacement_y_nm: np.ndarray
    total_contacts: int
    total_impulses: int
    total_direction_resets: int
    total_small_wall_impacts: int
    total_large_wall_impacts: int
    maximum_collision_passes: int
    maximum_displacement_nm: float
    maximum_residual_penetration_nm: float
    maximum_normalized_momentum_error: float
    maximum_normalized_restitution_error: float
    maximum_normalized_energy_identity_error: float

    @property
    def final_displacement_x_nm(self) -> float:
        """Final horizontal tracer displacement."""

        return float(self.displacement_x_nm[-1])

    @property
    def final_displacement_y_nm(self) -> float:
        """Final vertical tracer displacement."""

        return float(self.displacement_y_nm[-1])

    @property
    def final_displacement_nm(self) -> float:
        """Final radial tracer displacement."""

        return float(
            np.hypot(
                self.final_displacement_x_nm,
                self.final_displacement_y_nm,
            )
        )


@dataclass(frozen=True)
class GroupSummary:
    """Statistical summary for one ensemble or matched subset."""

    summary_id: str
    factor_name: str
    factor_value: float
    run_count: int
    diffusion_coefficient_nm2_per_ps: float
    diffusion_ci_low_nm2_per_ps: float
    diffusion_ci_high_nm2_per_ps: float
    msd_fit_slope_nm2_per_ps: float
    msd_fit_intercept_nm2: float
    msd_fit_r_squared: float
    final_mean_x_nm: float
    final_mean_x_ci_low_nm: float
    final_mean_x_ci_high_nm: float
    final_mean_y_nm: float
    final_mean_y_ci_low_nm: float
    final_mean_y_ci_high_nm: float
    final_rms_displacement_nm: float
    final_spread_difference_nm2: float
    final_spread_difference_ci_low_nm2: float
    final_spread_difference_ci_high_nm2: float
    final_variance_ratio_x_to_y: float
    mean_impulses_per_ps: float
    mean_contacts_per_ps: float
    mean_large_wall_impacts: float
    maximum_displacement_nm: float
    worst_normalized_collision_error: float
    maximum_residual_penetration_nm: float


@dataclass(frozen=True)
class AnalysisCheck:
    """One statistical acceptance claim and its measured evidence."""

    name: str
    passed: bool
    measured: str
    threshold: str
    explanation: str


@dataclass(frozen=True)
class Task2AnalysisReport:
    """Serializable ensemble design, results, checks, and interpretation."""

    design: ExperimentDesign
    checks: tuple[AnalysisCheck, ...]
    summaries: tuple[GroupSummary, ...]
    experiment_summary_ids: dict[str, tuple[str, ...]]
    interpretations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Whether every pre-declared statistical check passed."""

        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "passed": self.passed,
            "design": asdict(self.design),
            "checks": [asdict(check) for check in self.checks],
            "summaries": [asdict(summary) for summary in self.summaries],
            "experiment_summary_ids": {
                name: list(summary_ids)
                for name, summary_ids in self.experiment_summary_ids.items()
            },
            "interpretations": list(self.interpretations),
        }


def build_experiment_cases(
    design: ExperimentDesign,
) -> tuple[SimulationCase, ...]:
    """Create 224 unique default-design cases without baseline duplication."""

    baseline_template = BrownianParameters(
        max_time_ps=design.max_time_ps,
    )
    baseline_step = create_time_grid(baseline_template).step_size_ps
    cases: list[SimulationCase] = []

    def add_cases(
        configuration_id: str,
        factor_name: str,
        factor_value: float,
        template: BrownianParameters,
        seeds: Iterable[int],
    ) -> None:
        for seed in seeds:
            cases.append(
                SimulationCase(
                    configuration_id=configuration_id,
                    factor_name=factor_name,
                    factor_value=float(factor_value),
                    seed=seed,
                    parameters=replace(template, seed=seed),
                )
            )

    add_cases(
        "baseline",
        "baseline",
        1.0,
        baseline_template,
        design.baseline_seeds,
    )
    add_cases(
        "time_step_half",
        "time_step_factor",
        2.0,
        replace(
            baseline_template,
            requested_time_step_ps=baseline_step / 2.0,
        ),
        design.time_step_seeds,
    )

    for particle_count in design.particle_counts:
        if particle_count == baseline_template.n_small:
            continue
        add_cases(
            f"particle_count_{particle_count}",
            "particle_count",
            float(particle_count),
            replace(baseline_template, n_small=particle_count),
            design.comparison_seeds,
        )

    baseline_mass_ratio = (
        baseline_template.large_mass_kg / baseline_template.small_mass_kg
    )
    for mass_ratio in design.mass_ratios:
        if np.isclose(mass_ratio, baseline_mass_ratio):
            continue
        add_cases(
            f"mass_ratio_{mass_ratio:g}",
            "mass_ratio",
            mass_ratio,
            replace(
                baseline_template,
                large_mass_kg=(
                    mass_ratio * baseline_template.small_mass_kg
                ),
            ),
            design.comparison_seeds,
        )

    for restitution in design.restitutions:
        if np.isclose(restitution, baseline_template.restitution):
            continue
        add_cases(
            f"restitution_{restitution:g}",
            "restitution",
            restitution,
            replace(baseline_template, restitution=restitution),
            design.comparison_seeds,
        )

    for knudsen_parameter in design.knudsen_parameters:
        if np.isclose(
            knudsen_parameter,
            baseline_template.knudsen_parameter,
        ):
            continue
        add_cases(
            f"knudsen_{knudsen_parameter:g}",
            "knudsen_parameter",
            knudsen_parameter,
            replace(
                baseline_template,
                knudsen_parameter=knudsen_parameter,
            ),
            design.comparison_seeds,
        )

    unique_keys = {
        (case.configuration_id, case.seed) for case in cases
    }
    if len(unique_keys) != len(cases):
        raise RuntimeError("experiment design contains duplicate cases")
    return tuple(cases)


def _execute_case(case: SimulationCase) -> RunRecord:
    """Run one case in a worker process."""

    result = run_simulation(case.parameters, max_frames=2)
    displacement = (
        result.large_positions_nm - result.large_positions_nm[0]
    )
    diagnostics = result.diagnostics
    return RunRecord(
        configuration_id=case.configuration_id,
        factor_name=case.factor_name,
        factor_value=case.factor_value,
        seed=case.seed,
        times_ps=result.time_grid.times_ps,
        displacement_x_nm=displacement[:, 0],
        displacement_y_nm=displacement[:, 1],
        total_contacts=diagnostics.total_contacts,
        total_impulses=diagnostics.total_impulses,
        total_direction_resets=diagnostics.total_direction_resets,
        total_small_wall_impacts=diagnostics.total_small_wall_impacts,
        total_large_wall_impacts=diagnostics.total_large_wall_impacts,
        maximum_collision_passes=int(
            np.max(diagnostics.collision_passes_per_step)
        ),
        maximum_displacement_nm=diagnostics.maximum_displacement_nm,
        maximum_residual_penetration_nm=(
            diagnostics.maximum_residual_penetration_nm
        ),
        maximum_normalized_momentum_error=(
            diagnostics.maximum_normalized_momentum_error
        ),
        maximum_normalized_restitution_error=(
            diagnostics.maximum_normalized_restitution_error
        ),
        maximum_normalized_energy_identity_error=(
            diagnostics.maximum_normalized_energy_identity_error
        ),
    )


def execute_cases(
    cases: Sequence[SimulationCase],
    *,
    workers: int | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    cache_directory: Path | str | None = None,
) -> tuple[RunRecord, ...]:
    """Execute cases sequentially or with spawn-safe worker processes."""

    if workers is None:
        workers = min(4, os.cpu_count() or 1)
    if workers < 1:
        raise ValueError("workers must be at least 1")
    records: list[RunRecord] = []
    total = len(cases)
    pending_cases: list[SimulationCase] = []
    cache_paths: dict[tuple[str, int], Path] = {}

    for case in cases:
        cache_path = (
            None
            if cache_directory is None
            else _case_cache_path(case, Path(cache_directory))
        )
        if cache_path is not None and cache_path.is_file():
            records.append(_load_cached_record(cache_path))
            if progress_callback is not None:
                progress_callback(
                    len(records),
                    total,
                    f"{case.configuration_id} (cached)",
                )
        else:
            pending_cases.append(case)
            if cache_path is not None:
                cache_paths[(case.configuration_id, case.seed)] = cache_path

    if workers == 1:
        for case in pending_cases:
            record = _execute_case(case)
            records.append(record)
            cache_path = cache_paths.get(
                (case.configuration_id, case.seed)
            )
            if cache_path is not None:
                _write_cached_record(record, cache_path)
            if progress_callback is not None:
                progress_callback(
                    len(records),
                    total,
                    case.configuration_id,
                )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_cases = {
                executor.submit(_execute_case, case): case
                for case in pending_cases
            }
            for future in as_completed(future_cases):
                case = future_cases[future]
                record = future.result()
                records.append(record)
                cache_path = cache_paths.get(
                    (case.configuration_id, case.seed)
                )
                if cache_path is not None:
                    _write_cached_record(record, cache_path)
                if progress_callback is not None:
                    progress_callback(
                        len(records),
                        total,
                        case.configuration_id,
                    )

    records.sort(key=lambda record: (record.configuration_id, record.seed))
    return tuple(records)


def _case_cache_path(
    case: SimulationCase,
    directory: Path,
) -> Path:
    """Return a parameter-sensitive cache path for one expensive run."""

    parameter_payload = json.dumps(
        asdict(case.parameters),
        sort_keys=True,
        separators=(",", ":"),
    )
    fingerprint = hashlib.sha256(
        f"analysis-cache-v1:{parameter_payload}".encode("utf-8")
    ).hexdigest()[:16]
    return directory / (
        f"{case.configuration_id}_seed-{case.seed}_{fingerprint}.npz"
    )


def _write_cached_record(record: RunRecord, path: Path) -> None:
    """Atomically cache one tracer path and its diagnostics."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp.npz")
    np.savez_compressed(
        temporary_path,
        configuration_id=np.array(record.configuration_id),
        factor_name=np.array(record.factor_name),
        factor_value=np.array(record.factor_value),
        seed=np.array(record.seed),
        times_ps=record.times_ps,
        displacement_x_nm=record.displacement_x_nm,
        displacement_y_nm=record.displacement_y_nm,
        total_contacts=np.array(record.total_contacts),
        total_impulses=np.array(record.total_impulses),
        total_direction_resets=np.array(record.total_direction_resets),
        total_small_wall_impacts=np.array(
            record.total_small_wall_impacts
        ),
        total_large_wall_impacts=np.array(
            record.total_large_wall_impacts
        ),
        maximum_collision_passes=np.array(
            record.maximum_collision_passes
        ),
        maximum_displacement_nm=np.array(
            record.maximum_displacement_nm
        ),
        maximum_residual_penetration_nm=np.array(
            record.maximum_residual_penetration_nm
        ),
        maximum_normalized_momentum_error=np.array(
            record.maximum_normalized_momentum_error
        ),
        maximum_normalized_restitution_error=np.array(
            record.maximum_normalized_restitution_error
        ),
        maximum_normalized_energy_identity_error=np.array(
            record.maximum_normalized_energy_identity_error
        ),
    )
    temporary_path.replace(path)


def _load_cached_record(path: Path) -> RunRecord:
    """Load one record without allowing pickled objects."""

    with np.load(path, allow_pickle=False) as cached:
        return RunRecord(
            configuration_id=str(cached["configuration_id"]),
            factor_name=str(cached["factor_name"]),
            factor_value=float(cached["factor_value"]),
            seed=int(cached["seed"]),
            times_ps=cached["times_ps"],
            displacement_x_nm=cached["displacement_x_nm"],
            displacement_y_nm=cached["displacement_y_nm"],
            total_contacts=int(cached["total_contacts"]),
            total_impulses=int(cached["total_impulses"]),
            total_direction_resets=int(cached["total_direction_resets"]),
            total_small_wall_impacts=int(
                cached["total_small_wall_impacts"]
            ),
            total_large_wall_impacts=int(
                cached["total_large_wall_impacts"]
            ),
            maximum_collision_passes=int(
                cached["maximum_collision_passes"]
            ),
            maximum_displacement_nm=float(
                cached["maximum_displacement_nm"]
            ),
            maximum_residual_penetration_nm=float(
                cached["maximum_residual_penetration_nm"]
            ),
            maximum_normalized_momentum_error=float(
                cached["maximum_normalized_momentum_error"]
            ),
            maximum_normalized_restitution_error=float(
                cached["maximum_normalized_restitution_error"]
            ),
            maximum_normalized_energy_identity_error=float(
                cached["maximum_normalized_energy_identity_error"]
            ),
        )


def _mean_confidence_interval(
    values: np.ndarray,
    *,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Return mean and two-sided Student-t confidence interval."""

    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("confidence interval requires at least two values")
    mean = float(np.mean(values))
    standard_error = float(stats.sem(values))
    critical = float(
        stats.t.ppf((1.0 + confidence) / 2.0, len(values) - 1)
    )
    half_width = critical * standard_error
    return mean, mean - half_width, mean + half_width


def summarize_records(
    records: Sequence[RunRecord],
    *,
    summary_id: str,
    factor_name: str,
    factor_value: float,
    design: ExperimentDesign,
    bootstrap_seed_offset: int = 0,
) -> GroupSummary:
    """Calculate pre-declared ensemble statistics for equal-grid records."""

    if len(records) < 4:
        raise ValueError("an ensemble summary requires at least four runs")
    reference_times = records[0].times_ps
    if not all(
        np.array_equal(record.times_ps, reference_times)
        for record in records[1:]
    ):
        raise ValueError("all records in one summary must share a time grid")

    displacement_x = np.stack(
        [record.displacement_x_nm for record in records]
    )
    displacement_y = np.stack(
        [record.displacement_y_nm for record in records]
    )
    squared_radius = displacement_x**2 + displacement_y**2
    mean_squared_displacement = np.mean(squared_radius, axis=0)
    fit_mask = (
        (reference_times >= design.fit_start_ps)
        & (reference_times <= design.fit_end_ps)
    )
    fit_times = reference_times[fit_mask]
    if np.count_nonzero(fit_mask) < 3:
        raise ValueError("fit window contains fewer than three time points")
    centred_times = fit_times - np.mean(fit_times)
    denominator = float(np.dot(centred_times, centred_times))
    per_run_slopes = (
        np.einsum(
            "ij,j->i",
            squared_radius[:, fit_mask],
            centred_times,
            optimize=True,
        )
        / denominator
    )
    per_run_diffusion = per_run_slopes / 4.0
    diffusion = float(np.mean(per_run_diffusion))

    rng = np.random.default_rng(
        design.bootstrap_seed + bootstrap_seed_offset
    )
    bootstrap_indices = rng.integers(
        0,
        len(records),
        size=(design.bootstrap_resamples, len(records)),
    )
    bootstrap_diffusion = np.mean(
        per_run_diffusion[bootstrap_indices],
        axis=1,
    )
    diffusion_low, diffusion_high = np.percentile(
        bootstrap_diffusion,
        [2.5, 97.5],
    )

    fit_msd = mean_squared_displacement[fit_mask]
    slope = float(np.dot(fit_msd, centred_times) / denominator)
    intercept = float(np.mean(fit_msd) - slope * np.mean(fit_times))
    predicted = intercept + slope * fit_times
    residual_sum = float(np.sum((fit_msd - predicted) ** 2))
    total_sum = float(np.sum((fit_msd - np.mean(fit_msd)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0

    final_x = displacement_x[:, -1]
    final_y = displacement_y[:, -1]
    mean_x, mean_x_low, mean_x_high = _mean_confidence_interval(final_x)
    mean_y, mean_y_low, mean_y_high = _mean_confidence_interval(final_y)
    spread_difference = final_x**2 - final_y**2
    spread, spread_low, spread_high = _mean_confidence_interval(
        spread_difference
    )
    variance_y = float(np.var(final_y, ddof=1))
    variance_ratio = (
        float(np.var(final_x, ddof=1)) / variance_y
        if variance_y > 0.0
        else float("inf")
    )

    worst_collision_error = max(
        max(
            record.maximum_normalized_momentum_error,
            record.maximum_normalized_restitution_error,
            record.maximum_normalized_energy_identity_error,
        )
        for record in records
    )
    return GroupSummary(
        summary_id=summary_id,
        factor_name=factor_name,
        factor_value=float(factor_value),
        run_count=len(records),
        diffusion_coefficient_nm2_per_ps=diffusion,
        diffusion_ci_low_nm2_per_ps=float(diffusion_low),
        diffusion_ci_high_nm2_per_ps=float(diffusion_high),
        msd_fit_slope_nm2_per_ps=slope,
        msd_fit_intercept_nm2=intercept,
        msd_fit_r_squared=r_squared,
        final_mean_x_nm=mean_x,
        final_mean_x_ci_low_nm=mean_x_low,
        final_mean_x_ci_high_nm=mean_x_high,
        final_mean_y_nm=mean_y,
        final_mean_y_ci_low_nm=mean_y_low,
        final_mean_y_ci_high_nm=mean_y_high,
        final_rms_displacement_nm=float(
            np.sqrt(np.mean(final_x**2 + final_y**2))
        ),
        final_spread_difference_nm2=spread,
        final_spread_difference_ci_low_nm2=spread_low,
        final_spread_difference_ci_high_nm2=spread_high,
        final_variance_ratio_x_to_y=variance_ratio,
        mean_impulses_per_ps=float(
            np.mean([record.total_impulses for record in records])
            / design.max_time_ps
        ),
        mean_contacts_per_ps=float(
            np.mean([record.total_contacts for record in records])
            / design.max_time_ps
        ),
        mean_large_wall_impacts=float(
            np.mean(
                [record.total_large_wall_impacts for record in records]
            )
        ),
        maximum_displacement_nm=max(
            record.maximum_displacement_nm for record in records
        ),
        worst_normalized_collision_error=worst_collision_error,
        maximum_residual_penetration_nm=max(
            record.maximum_residual_penetration_nm for record in records
        ),
    )


def _intervals_overlap(
    first_low: float,
    first_high: float,
    second_low: float,
    second_high: float,
) -> bool:
    """Return whether two closed intervals overlap."""

    return max(first_low, second_low) <= min(first_high, second_high)


def _records_for(
    records: Sequence[RunRecord],
    configuration_id: str,
    seeds: Sequence[int],
) -> tuple[RunRecord, ...]:
    """Select one configuration and ordered seed subset."""

    by_seed = {
        record.seed: record
        for record in records
        if record.configuration_id == configuration_id
    }
    selected = tuple(by_seed[seed] for seed in seeds)
    if len(selected) != len(seeds):
        raise RuntimeError("one or more requested ensemble records are missing")
    return selected


def _parameter_interpretation(
    experiment_name: str,
    summaries: Sequence[GroupSummary],
) -> str:
    """Describe the measured endpoint trend without assuming monotonicity."""

    ordered = sorted(summaries, key=lambda summary: summary.factor_value)
    first = ordered[0]
    last = ordered[-1]
    relative_change = (
        (last.diffusion_coefficient_nm2_per_ps
         - first.diffusion_coefficient_nm2_per_ps)
        / abs(first.diffusion_coefficient_nm2_per_ps)
        if first.diffusion_coefficient_nm2_per_ps != 0.0
        else float("nan")
    )
    direction = "increased" if relative_change >= 0.0 else "decreased"
    return (
        f"Across the declared {experiment_name} range, fitted D {direction} "
        f"by {abs(relative_change):.1%} from the lowest to highest level. "
        "The three reported confidence intervals should be inspected before "
        "claiming a monotonic physical trend."
    )


def analyze_records(
    records: Sequence[RunRecord],
    design: ExperimentDesign,
) -> tuple[
    Task2AnalysisReport,
    dict[str, tuple[GroupSummary, ...]],
]:
    """Create all summaries, checks, and interpretations from completed runs."""

    baseline_all_records = _records_for(
        records,
        "baseline",
        design.baseline_seeds,
    )
    baseline_comparison_records = _records_for(
        records,
        "baseline",
        design.comparison_seeds,
    )
    baseline_time_records = _records_for(
        records,
        "baseline",
        design.time_step_seeds,
    )
    half_time_records = _records_for(
        records,
        "time_step_half",
        design.time_step_seeds,
    )

    summaries: list[GroupSummary] = []

    def summarize(
        selected: Sequence[RunRecord],
        *,
        summary_id: str,
        factor_name: str,
        factor_value: float,
    ) -> GroupSummary:
        summary = summarize_records(
            selected,
            summary_id=summary_id,
            factor_name=factor_name,
            factor_value=factor_value,
            design=design,
            bootstrap_seed_offset=len(summaries) * 10_000,
        )
        summaries.append(summary)
        return summary

    baseline = summarize(
        baseline_all_records,
        summary_id=f"baseline_{design.baseline_run_count}",
        factor_name="baseline",
        factor_value=1.0,
    )
    baseline_comparison = summarize(
        baseline_comparison_records,
        summary_id="baseline_comparison_12",
        factor_name="baseline",
        factor_value=1.0,
    )
    baseline_time = summarize(
        baseline_time_records,
        summary_id=f"time_step_baseline_{design.time_step_run_count}",
        factor_name="time_step_factor",
        factor_value=1.0,
    )
    half_time = summarize(
        half_time_records,
        summary_id=f"time_step_half_{design.time_step_run_count}",
        factor_name="time_step_factor",
        factor_value=2.0,
    )

    first_half = summarize(
        baseline_all_records[: design.baseline_run_count // 2],
        summary_id="independent_seed_half_a",
        factor_name="seed_half",
        factor_value=1.0,
    )
    second_half = summarize(
        baseline_all_records[design.baseline_run_count // 2 :],
        summary_id="independent_seed_half_b",
        factor_name="seed_half",
        factor_value=2.0,
    )

    variant_configuration_ids = {
        "particle_count": (
            ("particle_count_250", 250.0),
            ("particle_count_500", 500.0),
        ),
        "mass_ratio": (
            ("mass_ratio_5", 5.0),
            ("mass_ratio_20", 20.0),
        ),
        "restitution": (
            ("restitution_0.5", 0.5),
            ("restitution_0.8", 0.8),
        ),
        "knudsen_parameter": (
            ("knudsen_7.5", 7.5),
            ("knudsen_30", 30.0),
        ),
    }
    baseline_values = {
        "particle_count": 1_000.0,
        "mass_ratio": 10.0,
        "restitution": 1.0,
        "knudsen_parameter": 15.0,
    }
    experiment_summaries: dict[str, tuple[GroupSummary, ...]] = {}
    for factor_name, configurations in variant_configuration_ids.items():
        factor_summaries = [
            summarize(
                _records_for(
                    records,
                    configuration_id,
                    design.comparison_seeds,
                ),
                summary_id=f"{factor_name}_{factor_value:g}",
                factor_name=factor_name,
                factor_value=factor_value,
            )
            for configuration_id, factor_value in configurations
        ]
        factor_baseline = replace(
            baseline_comparison,
            summary_id=(
                f"{factor_name}_{baseline_values[factor_name]:g}"
            ),
            factor_name=factor_name,
            factor_value=baseline_values[factor_name],
        )
        summaries.append(factor_baseline)
        factor_summaries.append(factor_baseline)
        factor_summaries.sort(key=lambda item: item.factor_value)
        experiment_summaries[factor_name] = tuple(factor_summaries)

    baseline_mean_x_includes_zero = (
        baseline.final_mean_x_ci_low_nm
        <= 0.0
        <= baseline.final_mean_x_ci_high_nm
    )
    baseline_mean_y_includes_zero = (
        baseline.final_mean_y_ci_low_nm
        <= 0.0
        <= baseline.final_mean_y_ci_high_nm
    )
    isotropy_includes_zero = (
        baseline.final_spread_difference_ci_low_nm2
        <= 0.0
        <= baseline.final_spread_difference_ci_high_nm2
    )
    time_step_relative_difference = (
        abs(
            half_time.diffusion_coefficient_nm2_per_ps
            - baseline_time.diffusion_coefficient_nm2_per_ps
        )
        / abs(baseline_time.diffusion_coefficient_nm2_per_ps)
    )
    time_step_intervals_overlap = _intervals_overlap(
        baseline_time.diffusion_ci_low_nm2_per_ps,
        baseline_time.diffusion_ci_high_nm2_per_ps,
        half_time.diffusion_ci_low_nm2_per_ps,
        half_time.diffusion_ci_high_nm2_per_ps,
    )
    seed_half_intervals_overlap = _intervals_overlap(
        first_half.diffusion_ci_low_nm2_per_ps,
        first_half.diffusion_ci_high_nm2_per_ps,
        second_half.diffusion_ci_low_nm2_per_ps,
        second_half.diffusion_ci_high_nm2_per_ps,
    )
    physical_displacement_limit = (
        BrownianParameters().max_step_fraction
        * BrownianParameters().small_radius_nm
    )

    checks = (
        AnalysisCheck(
            name="mean_horizontal_displacement_consistent_with_zero",
            passed=baseline_mean_x_includes_zero,
            measured=(
                f"mean {baseline.final_mean_x_nm:.6f} nm, 95% CI "
                f"[{baseline.final_mean_x_ci_low_nm:.6f}, "
                f"{baseline.final_mean_x_ci_high_nm:.6f}]"
            ),
            threshold="95% CI includes zero",
            explanation="The model has no preferred horizontal direction.",
        ),
        AnalysisCheck(
            name="mean_vertical_displacement_consistent_with_zero",
            passed=baseline_mean_y_includes_zero,
            measured=(
                f"mean {baseline.final_mean_y_nm:.6f} nm, 95% CI "
                f"[{baseline.final_mean_y_ci_low_nm:.6f}, "
                f"{baseline.final_mean_y_ci_high_nm:.6f}]"
            ),
            threshold="95% CI includes zero",
            explanation="The model has no preferred vertical direction.",
        ),
        AnalysisCheck(
            name="horizontal_vertical_spreading_consistent",
            passed=isotropy_includes_zero,
            measured=(
                f"mean x^2-y^2 {baseline.final_spread_difference_nm2:.6f} "
                f"nm^2, 95% CI "
                f"[{baseline.final_spread_difference_ci_low_nm2:.6f}, "
                f"{baseline.final_spread_difference_ci_high_nm2:.6f}]"
            ),
            threshold="95% CI includes zero",
            explanation=(
                "A paired squared-spread difference tests isotropy without "
                "assuming equal independent variances."
            ),
        ),
        AnalysisCheck(
            name="positive_intermediate_diffusion",
            passed=baseline.diffusion_ci_low_nm2_per_ps > 0.0,
            measured=(
                f"D={baseline.diffusion_coefficient_nm2_per_ps:.6e} "
                f"nm^2/ps, bootstrap 95% CI "
                f"[{baseline.diffusion_ci_low_nm2_per_ps:.6e}, "
                f"{baseline.diffusion_ci_high_nm2_per_ps:.6e}]"
            ),
            threshold="lower confidence limit > 0",
            explanation=(
                f"The fitting window was fixed at {design.fit_start_ps:g}-"
                f"{design.fit_end_ps:g} ps before running."
            ),
        ),
        AnalysisCheck(
            name="approximately_linear_intermediate_msd",
            passed=(
                baseline.msd_fit_r_squared
                >= design.diffusion_r_squared_threshold
            ),
            measured=f"R^2={baseline.msd_fit_r_squared:.6f}",
            threshold=(
                f"R^2 >= {design.diffusion_r_squared_threshold:.2f}"
            ),
            explanation="The same pre-declared window is used for every group.",
        ),
        AnalysisCheck(
            name="ensemble_time_step_stability",
            passed=(
                time_step_relative_difference
                < design.time_step_relative_difference_threshold
                and time_step_intervals_overlap
            ),
            measured=(
                f"relative D difference {time_step_relative_difference:.3%}; "
                f"95% CIs overlap={time_step_intervals_overlap}"
            ),
            threshold=(
                f"difference < "
                f"{design.time_step_relative_difference_threshold:.0%} "
                "and confidence intervals overlap"
            ),
            explanation=(
                f"The same {design.time_step_run_count} seeds are compared "
                "at aligned baseline and half steps."
            ),
        ),
        AnalysisCheck(
            name="independent_seed_halves_reproduce_diffusion",
            passed=(
                first_half.diffusion_ci_low_nm2_per_ps > 0.0
                and second_half.diffusion_ci_low_nm2_per_ps > 0.0
                and seed_half_intervals_overlap
            ),
            measured=(
                f"D_A={first_half.diffusion_coefficient_nm2_per_ps:.6e}, "
                f"D_B={second_half.diffusion_coefficient_nm2_per_ps:.6e}; "
                f"95% CIs overlap={seed_half_intervals_overlap}"
            ),
            threshold="both positive with overlapping confidence intervals",
            explanation=(
                f"The {design.baseline_run_count} baseline seeds are split "
                "before interpretation."
            ),
        ),
        AnalysisCheck(
            name="all_ensemble_runs_numerically_valid",
            passed=all(
                record.maximum_displacement_nm
                <= physical_displacement_limit
                and record.maximum_residual_penetration_nm
                <= 1.0e-9
                * (
                    BrownianParameters().small_radius_nm
                    + BrownianParameters().large_radius_nm
                )
                and max(
                    record.maximum_normalized_momentum_error,
                    record.maximum_normalized_restitution_error,
                    record.maximum_normalized_energy_identity_error,
                )
                < 1.0e-12
                for record in records
            ),
            measured=f"{len(records)} unique runs checked",
            threshold=(
                "displacement, penetration, momentum, restitution, and "
                "energy limits all pass"
            ),
            explanation=(
                "No invalid run is silently omitted or rerun with a different "
                "numerical setting."
            ),
        ),
    )

    interpretations = tuple(
        _parameter_interpretation(name, values)
        for name, values in experiment_summaries.items()
    ) + (
        (
            "An initial 32-run baseline and 16-run time-step comparison "
            "failed the unchanged linearity and 25% stability checks. The "
            "automatic step was refined and both main ensembles were expanded "
            "to 64 before this final analysis."
        ),
        (
            f"The baseline diffusion estimate is based on "
            f"{design.baseline_run_count} runs; parameter comparisons use "
            f"the same {design.comparison_run_count} seeds at every level."
        ),
        (
            "These effective diffusion coefficients describe this finite, "
            "two-dimensional stochastic model rather than a real fluid."
        ),
    )
    experiment_summary_ids = {
        name: tuple(summary.summary_id for summary in values)
        for name, values in experiment_summaries.items()
    }
    experiment_summary_ids["time_step_factor"] = (
        baseline_time.summary_id,
        half_time.summary_id,
    )
    report = Task2AnalysisReport(
        design=design,
        checks=checks,
        summaries=tuple(summaries),
        experiment_summary_ids=experiment_summary_ids,
        interpretations=interpretations,
    )
    return report, experiment_summaries


def run_statistical_analysis(
    design: ExperimentDesign | None = None,
    *,
    workers: int | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    cache_directory: Path | str | None = None,
) -> tuple[
    Task2AnalysisReport,
    tuple[RunRecord, ...],
    dict[str, tuple[GroupSummary, ...]],
]:
    """Execute every unique case and calculate the complete Step 8 report."""

    if design is None:
        design = ExperimentDesign()
    cases = build_experiment_cases(design)
    records = execute_cases(
        cases,
        workers=workers,
        progress_callback=progress_callback,
        cache_directory=cache_directory,
    )
    report, experiment_summaries = analyze_records(records, design)
    return report, records, experiment_summaries


def _baseline_time_series_rows(
    records: Sequence[RunRecord],
    design: ExperimentDesign,
) -> list[dict[str, float]]:
    """Create baseline mean, confidence-band, and MSD rows."""

    baseline = _records_for(records, "baseline", design.baseline_seeds)
    times = baseline[0].times_ps
    displacement_x = np.stack(
        [record.displacement_x_nm for record in baseline]
    )
    displacement_y = np.stack(
        [record.displacement_y_nm for record in baseline]
    )
    squared_radius = displacement_x**2 + displacement_y**2
    critical = float(
        stats.t.ppf(0.975, len(baseline) - 1)
    )

    def mean_and_half_width(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mean = np.mean(values, axis=0)
        half_width = critical * stats.sem(values, axis=0)
        return mean, half_width

    mean_x, half_x = mean_and_half_width(displacement_x)
    mean_y, half_y = mean_and_half_width(displacement_y)
    msd, half_msd = mean_and_half_width(squared_radius)
    output_indices = np.unique(
        np.rint(
            np.linspace(
                0,
                len(times) - 1,
                min(design.output_time_series_points, len(times)),
            )
        ).astype(np.int64)
    )
    return [
        {
            "time_ps": float(times[index]),
            "mean_x_nm": float(mean_x[index]),
            "mean_x_ci_low_nm": float(mean_x[index] - half_x[index]),
            "mean_x_ci_high_nm": float(mean_x[index] + half_x[index]),
            "mean_y_nm": float(mean_y[index]),
            "mean_y_ci_low_nm": float(mean_y[index] - half_y[index]),
            "mean_y_ci_high_nm": float(mean_y[index] + half_y[index]),
            "msd_nm2": float(msd[index]),
            "msd_ci_low_nm2": float(msd[index] - half_msd[index]),
            "msd_ci_high_nm2": float(msd[index] + half_msd[index]),
        }
        for index in output_indices
    ]


def write_analysis_outputs(
    report: Task2AnalysisReport,
    records: Sequence[RunRecord],
    experiment_summaries: dict[str, tuple[GroupSummary, ...]],
    output_directory: Path | str,
) -> tuple[Path, Path, Path, Path, Path]:
    """Save JSON and reproducible CSV evidence for Step 8 and later figures."""

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / "analysis_report.json"
    summary_path = directory / "ensemble_summary.csv"
    comparison_path = directory / "experiment_comparisons.csv"
    time_series_path = directory / "baseline_msd.csv"
    run_metrics_path = directory / "run_metrics.csv"

    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report.to_dict(), handle, indent=2)
        handle.write("\n")

    summary_rows = [asdict(summary) for summary in report.summaries]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(summary_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    comparison_rows: list[dict[str, Any]] = []
    for experiment_name, summaries in experiment_summaries.items():
        for summary in summaries:
            comparison_rows.append(
                {
                    "experiment": experiment_name,
                    **asdict(summary),
                }
            )
    with comparison_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(comparison_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(comparison_rows)

    time_series_rows = _baseline_time_series_rows(
        records,
        report.design,
    )
    with time_series_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(time_series_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(time_series_rows)

    run_rows = [
        {
            "configuration_id": record.configuration_id,
            "factor_name": record.factor_name,
            "factor_value": record.factor_value,
            "seed": record.seed,
            "final_displacement_x_nm": record.final_displacement_x_nm,
            "final_displacement_y_nm": record.final_displacement_y_nm,
            "final_displacement_nm": record.final_displacement_nm,
            "total_contacts": record.total_contacts,
            "total_impulses": record.total_impulses,
            "total_direction_resets": record.total_direction_resets,
            "total_small_wall_impacts": record.total_small_wall_impacts,
            "total_large_wall_impacts": record.total_large_wall_impacts,
            "maximum_collision_passes": record.maximum_collision_passes,
            "maximum_displacement_nm": record.maximum_displacement_nm,
            "maximum_residual_penetration_nm": (
                record.maximum_residual_penetration_nm
            ),
            "maximum_normalized_momentum_error": (
                record.maximum_normalized_momentum_error
            ),
            "maximum_normalized_restitution_error": (
                record.maximum_normalized_restitution_error
            ),
            "maximum_normalized_energy_identity_error": (
                record.maximum_normalized_energy_identity_error
            ),
        }
        for record in records
    ]
    with run_metrics_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(run_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(run_rows)

    return (
        report_path,
        summary_path,
        comparison_path,
        time_series_path,
        run_metrics_path,
    )
