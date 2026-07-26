"""Immutable numerical configuration for the Task 7 study."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real

from task07_particle_in_box.constants import ELECTRON_MASS_KG, M_PER_NM


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


def _integer_tuple(
    values: tuple[int, ...],
    *,
    name: str,
    minimum: int,
) -> tuple[int, ...]:
    normalized = tuple(
        _integer(value, name=f"{name} item", minimum=minimum) for value in values
    )
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must contain unique values")
    if any(right <= left for left, right in zip(normalized, normalized[1:])):
        raise ValueError(f"{name} must be strictly increasing")
    return normalized


@dataclass(frozen=True)
class Task07Configuration:
    """Complete deterministic configuration for the Task 7 baseline."""

    schema_version: str = "task07-v1"
    particle_identifier: str = "electron"
    particle_label: str = "electron"
    particle_mass_kg: float = ELECTRON_MASS_KG
    box_width_m: float = 1.0 * M_PER_NM
    maximum_quantum_number: int = 10
    density_quantum_numbers: tuple[int, ...] = (1, 2, 3, 4)
    position_point_count: int = 2001
    numerical_grid_sizes: tuple[int, ...] = (100, 200, 400, 800, 1600)
    numerical_state_count: int = 10

    identity_relative_tolerance: float = 5.0e-12
    integral_absolute_tolerance: float = 5.0e-12
    orthogonality_absolute_tolerance: float = 5.0e-12
    anchor_relative_tolerance: float = 5.0e-11
    numerical_energy_relative_tolerance: float = 4.0e-5
    numerical_overlap_minimum: float = 0.999999
    convergence_order_minimum: float = 1.90
    convergence_order_maximum: float = 2.05

    figure_dpi: int = 300
    figure_width_px: int = 2400
    figure_height_px: int = 1500
    summary_width_px: int = 3840
    summary_height_px: int = 2160

    study_runtime_budget_s: float = 5.0
    generation_runtime_budget_s: float = 45.0
    evidence_size_budget_bytes: int = 20 * 1024 * 1024
    figure_size_budget_bytes: int = 80 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.schema_version != "task07-v1":
            raise ValueError("schema_version must be 'task07-v1'")
        for field_name in ("particle_identifier", "particle_label"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty text")
        if not self.particle_identifier.replace("_", "").isalnum():
            raise ValueError("particle_identifier must be portable identifier text")

        for field_name in ("particle_mass_kg", "box_width_m"):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, positive=True),
            )
        for field_name in (
            "maximum_quantum_number",
            "position_point_count",
            "numerical_state_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _integer(getattr(self, field_name), name=field_name, minimum=1),
            )
        if self.position_point_count < 3:
            raise ValueError("position_point_count must include at least one interior point")
        if self.position_point_count % 2 == 0:
            raise ValueError("position_point_count must be odd so x=a/2 is sampled")

        density_states = _integer_tuple(
            tuple(self.density_quantum_numbers),
            name="density_quantum_numbers",
            minimum=1,
        )
        numerical_grids = _integer_tuple(
            tuple(self.numerical_grid_sizes),
            name="numerical_grid_sizes",
            minimum=3,
        )
        if density_states[-1] > self.maximum_quantum_number:
            raise ValueError("density states must be within the modelled energy range")
        if self.numerical_state_count > self.maximum_quantum_number:
            raise ValueError("numerical_state_count cannot exceed maximum_quantum_number")
        if self.numerical_state_count >= numerical_grids[0]:
            raise ValueError("every numerical grid must exceed the requested state count")
        object.__setattr__(self, "density_quantum_numbers", density_states)
        object.__setattr__(self, "numerical_grid_sizes", numerical_grids)

        for field_name in (
            "identity_relative_tolerance",
            "integral_absolute_tolerance",
            "orthogonality_absolute_tolerance",
            "anchor_relative_tolerance",
            "numerical_energy_relative_tolerance",
            "numerical_overlap_minimum",
            "convergence_order_minimum",
            "convergence_order_maximum",
        ):
            object.__setattr__(
                self,
                field_name,
                _real(getattr(self, field_name), name=field_name, non_negative=True),
            )
        if not 0.0 < self.numerical_overlap_minimum <= 1.0:
            raise ValueError("numerical_overlap_minimum must lie in (0, 1]")
        if self.convergence_order_maximum <= self.convergence_order_minimum:
            raise ValueError("convergence order maximum must exceed minimum")

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
    def quantum_numbers(self) -> tuple[int, ...]:
        return tuple(range(1, self.maximum_quantum_number + 1))

    @property
    def box_width_nm(self) -> float:
        return self.box_width_m / M_PER_NM


DEFAULT_CONFIGURATION = Task07Configuration()


__all__ = ["DEFAULT_CONFIGURATION", "Task07Configuration"]
