"""Immutable scientific and output configuration for Task 9."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Iterable, Tuple

from task09_compton_scattering.constants import (
    OFFICIAL_INCIDENT_ENERGIES_KEV,
    PHOTON_SCATTERING_ANGLE_MAX_DEG,
    PHOTON_SCATTERING_ANGLE_MIN_DEG,
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


def _energy_tuple(values: Iterable[Real]) -> Tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("incident_energies_kev must be an iterable of real numbers")
    try:
        normalized = tuple(
            _positive_real(value, name="incident_energy_kev") for value in values
        )
    except TypeError as exc:
        raise TypeError(
            "incident_energies_kev must be an iterable of real numbers"
        ) from exc
    if not normalized:
        raise ValueError("incident_energies_kev must not be empty")
    if any(right <= left for left, right in zip(normalized, normalized[1:])):
        raise ValueError("incident_energies_kev must be strictly increasing")
    return normalized


@dataclass(frozen=True)
class Task09Configuration:
    """Frozen kinematic grid, tolerances and evidence-output conventions."""

    schema_version: str = "task09-v1"

    incident_energies_kev: Tuple[float, ...] = OFFICIAL_INCIDENT_ENERGIES_KEV
    default_incident_energy_kev: float = 200.0
    minimum_interactive_energy_kev: float = 1.0
    maximum_interactive_energy_kev: float = 5_000.0

    angle_minimum_deg: float = PHOTON_SCATTERING_ANGLE_MIN_DEG
    angle_maximum_deg: float = PHOTON_SCATTERING_ANGLE_MAX_DEG
    angle_point_count: int = 721
    browser_angle_point_count: int = 361

    numerical_absolute_tolerance: float = 5.0e-13
    numerical_relative_tolerance: float = 5.0e-12
    conservation_relative_tolerance: float = 2.0e-12
    cross_language_relative_tolerance: float = 1.0e-11
    cross_section_relative_tolerance: float = 5.0e-11
    cross_section_quadrature_order: int = 256

    figure_dpi: int = 300
    figure_width_px: int = 2400
    figure_height_px: int = 1500
    summary_width_px: int = 3840
    summary_height_px: int = 2160
    animation_width_px: int = 1600
    animation_height_px: int = 900
    animation_dpi: int = 160
    animation_frames_per_second: int = 18
    animation_frame_count: int = 73
    interaction_latency_budget_ms: float = 100.0
    study_runtime_budget_s: float = 2.0
    generation_runtime_budget_s: float = 20.0
    figure_size_budget_bytes: int = 60 * 1024 * 1024
    evidence_size_budget_bytes: int = 25 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.schema_version != "task09-v1":
            raise ValueError("schema_version must be 'task09-v1'")

        energies = _energy_tuple(self.incident_energies_kev)
        object.__setattr__(self, "incident_energies_kev", energies)

        for field_name in (
            "default_incident_energy_kev",
            "minimum_interactive_energy_kev",
            "maximum_interactive_energy_kev",
            "numerical_absolute_tolerance",
            "numerical_relative_tolerance",
            "conservation_relative_tolerance",
            "cross_language_relative_tolerance",
            "cross_section_relative_tolerance",
            "interaction_latency_budget_ms",
            "study_runtime_budget_s",
            "generation_runtime_budget_s",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_real(getattr(self, field_name), name=field_name),
            )

        if self.maximum_interactive_energy_kev <= self.minimum_interactive_energy_kev:
            raise ValueError(
                "maximum_interactive_energy_kev must exceed the minimum"
            )
        if not (
            self.minimum_interactive_energy_kev
            <= self.default_incident_energy_kev
            <= self.maximum_interactive_energy_kev
        ):
            raise ValueError("default_incident_energy_kev must lie in the energy range")
        if energies[0] < self.minimum_interactive_energy_kev or (
            energies[-1] > self.maximum_interactive_energy_kev
        ):
            raise ValueError("official energies must lie in the interactive range")

        for field_name in ("angle_minimum_deg", "angle_maximum_deg"):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name),
            )
        if not math.isclose(
            self.angle_minimum_deg,
            PHOTON_SCATTERING_ANGLE_MIN_DEG,
            rel_tol=0.0,
            abs_tol=0.0,
        ) or not math.isclose(
            self.angle_maximum_deg,
            PHOTON_SCATTERING_ANGLE_MAX_DEG,
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise ValueError("Task 9 angle range must be exactly 0 to 180 degrees")

        for field_name in ("angle_point_count", "browser_angle_point_count"):
            count = _integer(getattr(self, field_name), name=field_name, minimum=3)
            if count % 2 == 0:
                raise ValueError(f"{field_name} must be odd so 90 degrees is sampled")
            object.__setattr__(self, field_name, count)

        quadrature_order = _integer(
            self.cross_section_quadrature_order,
            name="cross_section_quadrature_order",
            minimum=32,
        )
        if quadrature_order % 2 != 0:
            raise ValueError("cross_section_quadrature_order must be even")
        object.__setattr__(self, "cross_section_quadrature_order", quadrature_order)

        for field_name in (
            "figure_dpi",
            "figure_width_px",
            "figure_height_px",
            "summary_width_px",
            "summary_height_px",
            "animation_width_px",
            "animation_height_px",
            "animation_dpi",
            "animation_frames_per_second",
            "animation_frame_count",
            "figure_size_budget_bytes",
            "evidence_size_budget_bytes",
        ):
            object.__setattr__(
                self,
                field_name,
                _integer(getattr(self, field_name), name=field_name),
            )
        if self.summary_width_px * 9 != self.summary_height_px * 16:
            raise ValueError("summary dimensions must have an exact 16:9 ratio")
        if self.animation_width_px * 9 != self.animation_height_px * 16:
            raise ValueError("animation dimensions must have an exact 16:9 ratio")
        if self.animation_frame_count < 3:
            raise ValueError("animation_frame_count must be at least three")

    @property
    def angle_span_deg(self) -> float:
        return self.angle_maximum_deg - self.angle_minimum_deg

    @property
    def angle_spacing_deg(self) -> float:
        return self.angle_span_deg / (self.angle_point_count - 1)

    @property
    def browser_angle_spacing_deg(self) -> float:
        return self.angle_span_deg / (self.browser_angle_point_count - 1)


DEFAULT_CONFIGURATION = Task09Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task09Configuration"]
