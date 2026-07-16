"""Immutable numerical configuration for the Task 4 baseline."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Final


_FREQUENCY_STOP_HZ: Final[float] = 2.4e15
_WAVELENGTH_STOP_NM: Final[float] = 700.0


def _real_value(
    value: Real,
    *,
    name: str,
    positive: bool = False,
    non_negative: bool = False,
) -> float:
    """Validate and normalize one real configuration value."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if positive and normalized <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    if non_negative and normalized < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _point_count(value: Integral, *, name: str) -> int:
    """Validate a numerical-grid point count."""

    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 2:
        raise ValueError(f"{name} must be at least 2")
    return normalized


def _byte_budget(value: Integral, *, name: str) -> int:
    """Validate a positive integer byte budget."""

    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return normalized


@dataclass(frozen=True)
class Task04Configuration:
    """Complete deterministic configuration for the Task 4 baseline."""

    schema_version: str = "task04-v1"

    frequency_start_hz: float = 4.0e14
    frequency_step_hz: float = 1.0e12
    frequency_points: int = 2001

    wavelength_start_nm: float = 150.0
    wavelength_step_nm: float = 0.25
    wavelength_points: int = 2201

    visible_min_nm: float = 380.0
    visible_max_nm: float = 750.0

    boundary_clamp_tolerance_v: float = 5.0e-12
    energy_identity_tolerance_ev: float = 5.0e-12
    gradient_relative_tolerance: float = 5.0e-13
    cutoff_relative_tolerance: float = 5.0e-13
    threshold_voltage_tolerance_v: float = 5.0e-12
    coordinate_consistency_tolerance_v: float = 1.0e-11
    physical_bound_slack_v: float = 1.0e-12
    monotonic_slack_v: float = 1.0e-12
    anchor_tolerance_v: float = 5.0e-12

    study_runtime_budget_s: float = 2.0
    generation_runtime_budget_s: float = 15.0
    evidence_size_budget_bytes: int = 10 * 1024 * 1024
    figure_size_budget_bytes: int = 10 * 1024 * 1024

    def __post_init__(self) -> None:
        """Normalize values and reject ambiguous or drifting grids."""

        if not isinstance(self.schema_version, str):
            raise TypeError("schema_version must be text")
        if self.schema_version != "task04-v1":
            raise ValueError("schema_version must be 'task04-v1'")

        positive_fields = (
            "frequency_start_hz",
            "frequency_step_hz",
            "wavelength_start_nm",
            "wavelength_step_nm",
            "visible_min_nm",
            "visible_max_nm",
            "study_runtime_budget_s",
            "generation_runtime_budget_s",
        )
        for field_name in positive_fields:
            object.__setattr__(
                self,
                field_name,
                _real_value(
                    getattr(self, field_name),
                    name=field_name,
                    positive=True,
                ),
            )

        tolerance_fields = (
            "boundary_clamp_tolerance_v",
            "energy_identity_tolerance_ev",
            "gradient_relative_tolerance",
            "cutoff_relative_tolerance",
            "threshold_voltage_tolerance_v",
            "coordinate_consistency_tolerance_v",
            "physical_bound_slack_v",
            "monotonic_slack_v",
            "anchor_tolerance_v",
        )
        for field_name in tolerance_fields:
            object.__setattr__(
                self,
                field_name,
                _real_value(
                    getattr(self, field_name),
                    name=field_name,
                    non_negative=True,
                ),
            )

        object.__setattr__(
            self,
            "frequency_points",
            _point_count(self.frequency_points, name="frequency_points"),
        )
        object.__setattr__(
            self,
            "wavelength_points",
            _point_count(self.wavelength_points, name="wavelength_points"),
        )
        object.__setattr__(
            self,
            "evidence_size_budget_bytes",
            _byte_budget(
                self.evidence_size_budget_bytes,
                name="evidence_size_budget_bytes",
            ),
        )
        object.__setattr__(
            self,
            "figure_size_budget_bytes",
            _byte_budget(
                self.figure_size_budget_bytes,
                name="figure_size_budget_bytes",
            ),
        )

        if self.visible_max_nm <= self.visible_min_nm:
            raise ValueError("visible_max_nm must exceed visible_min_nm")

        if not math.isclose(
            self.frequency_stop_hz,
            _FREQUENCY_STOP_HZ,
            rel_tol=0.0,
            abs_tol=1.0e-12 * self.frequency_step_hz,
        ):
            raise ValueError(
                "frequency start, step, and count must end at 2.4e15 Hz"
            )
        if not math.isclose(
            self.wavelength_stop_nm,
            _WAVELENGTH_STOP_NM,
            rel_tol=0.0,
            abs_tol=1.0e-12 * self.wavelength_step_nm,
        ):
            raise ValueError(
                "wavelength start, step, and count must end at 700 nm"
            )

    @property
    def frequency_stop_hz(self) -> float:
        """Return the inclusive frequency-grid endpoint."""

        return self.frequency_start_hz + (
            self.frequency_points - 1
        ) * self.frequency_step_hz

    @property
    def wavelength_stop_nm(self) -> float:
        """Return the inclusive wavelength-grid endpoint."""

        return self.wavelength_start_nm + (
            self.wavelength_points - 1
        ) * self.wavelength_step_nm


DEFAULT_CONFIGURATION = Task04Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task04Configuration"]
