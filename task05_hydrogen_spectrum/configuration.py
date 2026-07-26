"""Immutable numerical configuration for Task 5."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real


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
class Task05Configuration:
    """Complete deterministic configuration for the Task 5 baseline."""

    schema_version: str = "task05-v1"
    maximum_level: int = 10
    highlighted_series_final_max: int = 5
    visible_min_nm: float = 380.0
    visible_max_nm: float = 750.0

    level_energy_tolerance_ev: float = 5.0e-12
    transition_energy_tolerance_ev: float = 5.0e-12
    energy_wavelength_relative_tolerance: float = 5.0e-13
    frequency_wavelength_relative_tolerance: float = 5.0e-13
    rydberg_wavelength_relative_tolerance: float = 5.0e-13
    named_line_relative_tolerance: float = 5.0e-12
    series_limit_relative_tolerance: float = 5.0e-12

    study_runtime_budget_s: float = 2.0
    generation_runtime_budget_s: float = 15.0
    evidence_size_budget_bytes: int = 10 * 1024 * 1024
    figure_size_budget_bytes: int = 15 * 1024 * 1024

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str):
            raise TypeError("schema_version must be text")
        if self.schema_version != "task05-v1":
            raise ValueError("schema_version must be 'task05-v1'")

        maximum = _integer(self.maximum_level, name="maximum_level", minimum=2)
        highlighted = _integer(
            self.highlighted_series_final_max,
            name="highlighted_series_final_max",
            minimum=1,
        )
        if highlighted >= maximum:
            raise ValueError(
                "highlighted_series_final_max must be below maximum_level"
            )
        object.__setattr__(self, "maximum_level", maximum)
        object.__setattr__(self, "highlighted_series_final_max", highlighted)

        for field_name in ("visible_min_nm", "visible_max_nm"):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, positive=True),
            )
        if self.visible_max_nm <= self.visible_min_nm:
            raise ValueError("visible_max_nm must exceed visible_min_nm")

        tolerance_fields = (
            "level_energy_tolerance_ev",
            "transition_energy_tolerance_ev",
            "energy_wavelength_relative_tolerance",
            "frequency_wavelength_relative_tolerance",
            "rydberg_wavelength_relative_tolerance",
            "named_line_relative_tolerance",
            "series_limit_relative_tolerance",
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
            "study_runtime_budget_s",
            "generation_runtime_budget_s",
        ):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, positive=True),
            )
        for field_name in (
            "evidence_size_budget_bytes",
            "figure_size_budget_bytes",
        ):
            object.__setattr__(
                self,
                field_name,
                _integer(getattr(self, field_name), name=field_name, minimum=1),
            )

    @property
    def expected_transition_count(self) -> int:
        """Return the number of downward pairs through ``maximum_level``."""

        return self.maximum_level * (self.maximum_level - 1) // 2


DEFAULT_CONFIGURATION = Task05Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task05Configuration"]
