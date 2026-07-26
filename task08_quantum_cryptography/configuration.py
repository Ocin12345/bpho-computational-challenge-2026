"""Immutable baseline configuration for the Task 8 visual calculator."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real

from task08_quantum_cryptography.constants import (
    OFFICIAL_PHI_DEG,
    OFFICIAL_THETA_DEG,
    POLARISATION_PERIOD_DEG,
    SIMULATION_DEFAULT_PHOTON_PAIRS,
    SIMULATION_DEFAULT_SEED,
    SIMULATION_MAXIMUM_PHOTON_PAIRS,
    SIMULATION_MINIMUM_PHOTON_PAIRS,
    UINT32_MAXIMUM,
)


def _real(value: Real, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _positive_real(value: Real, *, name: str) -> float:
    normalized = _real(value, name=name)
    if normalized <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return normalized


def _integer(value: Integral, *, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return normalized


@dataclass(frozen=True)
class Task08Configuration:
    """Frozen scientific, interaction and output conventions for Task 8."""

    schema_version: str = "task08-v1"

    angle_minimum_deg: float = -90.0
    angle_maximum_deg: float = 90.0
    angle_step_deg: float = 1.0
    default_theta_deg: float = OFFICIAL_THETA_DEG
    default_phi_deg: float = OFFICIAL_PHI_DEG
    official_theta_deg: float = OFFICIAL_THETA_DEG
    official_phi_deg: float = OFFICIAL_PHI_DEG

    sweep_point_count: int = 361
    heatmap_point_count: int = 181

    probability_absolute_tolerance: float = 5.0e-15
    reference_absolute_tolerance: float = 5.0e-13
    cross_language_absolute_tolerance: float = 5.0e-12

    figure_dpi: int = 300
    figure_width_px: int = 2400
    figure_height_px: int = 1500
    summary_width_px: int = 3840
    summary_height_px: int = 2160
    interaction_latency_budget_ms: float = 100.0
    simulation_runtime_budget_ms: float = 100.0
    study_runtime_budget_s: float = 2.0
    generation_runtime_budget_s: float = 20.0
    evidence_size_budget_bytes: int = 25 * 1024 * 1024
    figure_size_budget_bytes: int = 60 * 1024 * 1024

    simulation_minimum_photon_pairs: int = SIMULATION_MINIMUM_PHOTON_PAIRS
    simulation_maximum_photon_pairs: int = SIMULATION_MAXIMUM_PHOTON_PAIRS
    simulation_default_photon_pairs: int = SIMULATION_DEFAULT_PHOTON_PAIRS
    simulation_default_seed: int = SIMULATION_DEFAULT_SEED

    def __post_init__(self) -> None:
        if self.schema_version != "task08-v1":
            raise ValueError("schema_version must be 'task08-v1'")

        for field_name in (
            "angle_minimum_deg",
            "angle_maximum_deg",
            "default_theta_deg",
            "default_phi_deg",
            "official_theta_deg",
            "official_phi_deg",
        ):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name),
            )

        object.__setattr__(
            self,
            "angle_step_deg",
            _positive_real(self.angle_step_deg, name="angle_step_deg"),
        )
        if self.angle_maximum_deg <= self.angle_minimum_deg:
            raise ValueError("angle_maximum_deg must exceed angle_minimum_deg")
        if not math.isclose(
            self.angle_span_deg,
            POLARISATION_PERIOD_DEG,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ) or not math.isclose(
            self.angle_minimum_deg + self.angle_maximum_deg,
            0.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError(
                "the display range must be one 180-degree period centred on zero"
            )

        for field_name in (
            "default_theta_deg",
            "default_phi_deg",
            "official_theta_deg",
            "official_phi_deg",
        ):
            value = getattr(self, field_name)
            if not self.angle_minimum_deg <= value <= self.angle_maximum_deg:
                raise ValueError(f"{field_name} must lie within the display range")

        step_count = self.angle_span_deg / self.angle_step_deg
        if not math.isclose(
            step_count,
            round(step_count),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError("angle_step_deg must divide the display range exactly")

        for field_name in ("sweep_point_count", "heatmap_point_count"):
            normalized = _integer(getattr(self, field_name), name=field_name, minimum=3)
            if normalized % 2 == 0:
                raise ValueError(f"{field_name} must be odd so zero degrees is sampled")
            object.__setattr__(self, field_name, normalized)

        for field_name in (
            "probability_absolute_tolerance",
            "reference_absolute_tolerance",
            "cross_language_absolute_tolerance",
            "interaction_latency_budget_ms",
            "simulation_runtime_budget_ms",
            "study_runtime_budget_s",
            "generation_runtime_budget_s",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_real(getattr(self, field_name), name=field_name),
            )

        for field_name in (
            "figure_dpi",
            "figure_width_px",
            "figure_height_px",
            "summary_width_px",
            "summary_height_px",
            "evidence_size_budget_bytes",
            "figure_size_budget_bytes",
        ):
            object.__setattr__(
                self,
                field_name,
                _integer(getattr(self, field_name), name=field_name),
            )

        minimum_pairs = _integer(
            self.simulation_minimum_photon_pairs,
            name="simulation_minimum_photon_pairs",
            minimum=2,
        )
        maximum_pairs = _integer(
            self.simulation_maximum_photon_pairs,
            name="simulation_maximum_photon_pairs",
            minimum=minimum_pairs,
        )
        default_pairs = _integer(
            self.simulation_default_photon_pairs,
            name="simulation_default_photon_pairs",
            minimum=minimum_pairs,
        )
        if default_pairs > maximum_pairs:
            raise ValueError(
                "simulation_default_photon_pairs must not exceed the maximum"
            )
        default_seed = _integer(
            self.simulation_default_seed,
            name="simulation_default_seed",
            minimum=0,
        )
        if default_seed > UINT32_MAXIMUM:
            raise ValueError("simulation_default_seed must be an unsigned 32-bit integer")
        object.__setattr__(self, "simulation_minimum_photon_pairs", minimum_pairs)
        object.__setattr__(self, "simulation_maximum_photon_pairs", maximum_pairs)
        object.__setattr__(self, "simulation_default_photon_pairs", default_pairs)
        object.__setattr__(self, "simulation_default_seed", default_seed)

    @property
    def angle_span_deg(self) -> float:
        return self.angle_maximum_deg - self.angle_minimum_deg

    @property
    def sweep_spacing_deg(self) -> float:
        return self.angle_span_deg / (self.sweep_point_count - 1)

    @property
    def heatmap_spacing_deg(self) -> float:
        return self.angle_span_deg / (self.heatmap_point_count - 1)


DEFAULT_CONFIGURATION = Task08Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task08Configuration"]
