"""Immutable numerical configuration for Task 6."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real

from task06_electron_diffraction.constants import M_PER_MM, M_PER_NM


def _integer(value: Integral, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return normalized


def _real(
    value: Real,
    *,
    name: str,
    positive: bool = False,
    non_negative: bool = False,
) -> float:
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


@dataclass(frozen=True)
class SpacingDefinition:
    """One nominal graphite layer-spacing family."""

    identifier: str
    label: str
    spacing_m: float

    def __post_init__(self) -> None:
        for field_name in ("identifier", "label"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty text")
        if not self.identifier.replace("_", "").isalnum():
            raise ValueError("identifier must contain only letters, numbers, or underscores")
        object.__setattr__(
            self,
            "spacing_m",
            _real(self.spacing_m, name="spacing_m", positive=True),
        )

    @property
    def spacing_nm(self) -> float:
        return self.spacing_m / M_PER_NM


DEFAULT_SPACINGS: tuple[SpacingDefinition, ...] = (
    SpacingDefinition("d1", "d₁ = 0.123 nm", 0.123 * M_PER_NM),
    SpacingDefinition("d2", "d₂ = 0.213 nm", 0.213 * M_PER_NM),
)


@dataclass(frozen=True)
class Task06Configuration:
    """Complete deterministic configuration for the Task 6 baseline."""

    schema_version: str = "task06-v1"
    voltage_min_v: float = 1000.0
    voltage_max_v: float = 5000.0
    voltage_step_v: float = 10.0
    tube_radius_m: float = 65.0 * M_PER_MM
    spacings: tuple[SpacingDefinition, ...] = DEFAULT_SPACINGS

    identity_relative_tolerance: float = 5.0e-12
    anchor_relative_tolerance: float = 5.0e-10
    fit_relative_tolerance: float = 1.0e-10
    fit_r_squared_tolerance: float = 1.0e-12
    fit_intercept_tolerance_v_inv_sqrt: float = 1.0e-12
    normalized_residual_relative_tolerance: float = 1.0e-10

    figure_dpi: int = 300
    figure_width_px: int = 2400
    figure_height_px: int = 1500
    summary_width_px: int = 3840
    summary_height_px: int = 2160

    study_runtime_budget_s: float = 2.0
    generation_runtime_budget_s: float = 30.0
    evidence_size_budget_bytes: int = 20 * 1024 * 1024
    figure_size_budget_bytes: int = 60 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.schema_version != "task06-v1":
            raise ValueError("schema_version must be 'task06-v1'")

        for field_name in (
            "voltage_min_v",
            "voltage_max_v",
            "voltage_step_v",
            "tube_radius_m",
        ):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, positive=True),
            )
        if self.voltage_max_v <= self.voltage_min_v:
            raise ValueError("voltage_max_v must exceed voltage_min_v")
        interval_count = (self.voltage_max_v - self.voltage_min_v) / self.voltage_step_v
        if not math.isclose(interval_count, round(interval_count), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("voltage_step_v must exactly partition the voltage interval")

        spacings = tuple(self.spacings)
        if len(spacings) < 1 or any(
            not isinstance(spacing, SpacingDefinition) for spacing in spacings
        ):
            raise TypeError("spacings must contain SpacingDefinition records")
        identifiers = tuple(spacing.identifier for spacing in spacings)
        values = tuple(spacing.spacing_m for spacing in spacings)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("spacing identifiers must be unique")
        if len(set(values)) != len(values):
            raise ValueError("spacing values must be unique")
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError("spacings must be strictly increasing")
        object.__setattr__(self, "spacings", spacings)

        tolerance_fields = (
            "identity_relative_tolerance",
            "anchor_relative_tolerance",
            "fit_relative_tolerance",
            "fit_r_squared_tolerance",
            "fit_intercept_tolerance_v_inv_sqrt",
            "normalized_residual_relative_tolerance",
        )
        for field_name in tolerance_fields:
            object.__setattr__(
                self,
                field_name,
                _real(
                    getattr(self, field_name),
                    name=field_name,
                    non_negative=True,
                ),
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
                _integer(getattr(self, field_name), name=field_name, minimum=1),
            )
        for field_name in ("study_runtime_budget_s", "generation_runtime_budget_s"):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, positive=True),
            )

    @property
    def voltage_count(self) -> int:
        return int(round((self.voltage_max_v - self.voltage_min_v) / self.voltage_step_v)) + 1

    @property
    def spacing_count(self) -> int:
        return len(self.spacings)


DEFAULT_CONFIGURATION = Task06Configuration()


__all__ = [
    "DEFAULT_CONFIGURATION",
    "DEFAULT_SPACINGS",
    "SpacingDefinition",
    "Task06Configuration",
]
