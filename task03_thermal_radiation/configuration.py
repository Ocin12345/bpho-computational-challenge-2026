"""Immutable numerical configuration for Task 3."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real


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
    if normalized < 3:
        raise ValueError(f"{name} must be at least 3")
    return normalized


def _validate_uniform_grid(
    minimum: float,
    maximum: float,
    interval: float,
    *,
    name: str,
) -> None:
    """Require an increasing grid with an inclusive final point."""

    if maximum <= minimum:
        raise ValueError(f"{name} maximum must exceed its minimum")
    intervals = (maximum - minimum) / interval
    nearest = round(intervals)
    tolerance = 1.0e-10 * max(1.0, abs(intervals))
    if not math.isclose(intervals, nearest, rel_tol=0.0, abs_tol=tolerance):
        raise ValueError(
            f"{name} interval must divide its closed range exactly"
        )


@dataclass(frozen=True)
class Task03Configuration:
    """Complete deterministic configuration for the Task 3 baseline."""

    schema_version: int = 1
    planck_temperatures_k: tuple[float, ...] = (4000.0, 5000.0, 6000.0)

    planck_display_min_nm: float = 100.0
    planck_display_max_nm: float = 3000.0
    planck_display_interval_nm: float = 1.0

    planck_peak_min_nm: float = 100.0
    planck_peak_max_nm: float = 3000.0
    planck_peak_interval_nm: float = 0.01

    planck_integration_min_m: float = 1.0e-9
    planck_integration_max_m: float = 1.0e-2
    planck_integration_points: int = 200_001

    einstein_temperature_min_k: float = 0.0
    einstein_temperature_max_k: float = 800.0
    einstein_temperature_interval_k: float = 1.0

    einstein_reduced_temperature_min: float = 0.0
    einstein_reduced_temperature_max: float = 5.0
    einstein_reduced_temperature_points: int = 1001

    wien_peak_relative_tolerance: float = 1.0e-3
    stefan_boltzmann_relative_tolerance: float = 2.0e-3
    exitance_identity_relative_tolerance: float = 1.0e-14
    einstein_bound_relative_slack: float = 1.0e-12
    einstein_monotonic_absolute_slack: float = 1.0e-12
    einstein_anchor_absolute_tolerance: float = 1.0e-12
    einstein_high_temperature_relative_tolerance: float = 1.0e-5
    einstein_normalized_collapse_tolerance: float = 1.0e-12

    def __post_init__(self) -> None:
        """Normalize immutable values and reject ambiguous grids."""

        if isinstance(self.schema_version, bool) or not isinstance(
            self.schema_version, Integral
        ):
            raise TypeError("schema_version must be an integer")
        if self.schema_version <= 0:
            raise ValueError("schema_version must be greater than zero")
        object.__setattr__(self, "schema_version", int(self.schema_version))

        temperatures = tuple(
            _real_value(value, name="planck temperature", positive=True)
            for value in self.planck_temperatures_k
        )
        if len(temperatures) < 2:
            raise ValueError("planck_temperatures_k must contain several values")
        if any(current <= previous for previous, current in zip(
            temperatures,
            temperatures[1:],
        )):
            raise ValueError(
                "planck_temperatures_k must be strictly increasing"
            )
        object.__setattr__(self, "planck_temperatures_k", temperatures)

        positive_fields = (
            "planck_display_min_nm",
            "planck_display_max_nm",
            "planck_display_interval_nm",
            "planck_peak_min_nm",
            "planck_peak_max_nm",
            "planck_peak_interval_nm",
            "planck_integration_min_m",
            "planck_integration_max_m",
            "einstein_temperature_max_k",
            "einstein_temperature_interval_k",
            "einstein_reduced_temperature_max",
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

        non_negative_fields = (
            "einstein_temperature_min_k",
            "einstein_reduced_temperature_min",
            "wien_peak_relative_tolerance",
            "stefan_boltzmann_relative_tolerance",
            "exitance_identity_relative_tolerance",
            "einstein_bound_relative_slack",
            "einstein_monotonic_absolute_slack",
            "einstein_anchor_absolute_tolerance",
            "einstein_high_temperature_relative_tolerance",
            "einstein_normalized_collapse_tolerance",
        )
        for field_name in non_negative_fields:
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
            "planck_integration_points",
            _point_count(
                self.planck_integration_points,
                name="planck_integration_points",
            ),
        )
        object.__setattr__(
            self,
            "einstein_reduced_temperature_points",
            _point_count(
                self.einstein_reduced_temperature_points,
                name="einstein_reduced_temperature_points",
            ),
        )

        _validate_uniform_grid(
            self.planck_display_min_nm,
            self.planck_display_max_nm,
            self.planck_display_interval_nm,
            name="Planck display grid",
        )
        _validate_uniform_grid(
            self.planck_peak_min_nm,
            self.planck_peak_max_nm,
            self.planck_peak_interval_nm,
            name="Planck peak grid",
        )
        if self.planck_integration_max_m <= self.planck_integration_min_m:
            raise ValueError(
                "planck_integration_max_m must exceed its minimum"
            )
        _validate_uniform_grid(
            self.einstein_temperature_min_k,
            self.einstein_temperature_max_k,
            self.einstein_temperature_interval_k,
            name="Einstein temperature grid",
        )
        if (
            self.einstein_reduced_temperature_max
            <= self.einstein_reduced_temperature_min
        ):
            raise ValueError(
                "Einstein reduced-temperature maximum must exceed its minimum"
            )


DEFAULT_CONFIGURATION = Task03Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task03Configuration"]
