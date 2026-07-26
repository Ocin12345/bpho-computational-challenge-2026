"""Immutable full-grid analytical study for Task 8."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.models import (
    angle_sweep,
    detector_probabilities,
    mismatch_grid,
    relative_detector_angle_deg,
)


FloatArray = NDArray[np.float64]


def _readonly_float_array(value: object, *, name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class Task08StudyResult:
    """Complete immutable analytical evidence before serialization."""

    schema_version: str

    sweep_theta_deg: FloatArray
    sweep_phi_deg: FloatArray
    sweep_relative_angle_deg: FloatArray
    sweep_detector_a_x: FloatArray
    sweep_detector_a_y: FloatArray
    sweep_detector_b_x: FloatArray
    sweep_detector_b_y: FloatArray
    sweep_classical_match: FloatArray
    sweep_classical_mismatch: FloatArray
    sweep_quantum_match: FloatArray
    sweep_quantum_mismatch: FloatArray
    sweep_signed_difference: FloatArray

    grid_theta_deg: FloatArray
    grid_phi_deg: FloatArray
    grid_relative_angle_deg: FloatArray
    grid_classical_match: FloatArray
    grid_classical_mismatch: FloatArray
    grid_quantum_match: FloatArray
    grid_quantum_mismatch: FloatArray
    grid_signed_difference: FloatArray

    def __post_init__(self) -> None:
        if self.schema_version != "task08-study-v1":
            raise ValueError("invalid Task 8 study schema")
        array_fields = (
            "sweep_theta_deg",
            "sweep_phi_deg",
            "sweep_relative_angle_deg",
            "sweep_detector_a_x",
            "sweep_detector_a_y",
            "sweep_detector_b_x",
            "sweep_detector_b_y",
            "sweep_classical_match",
            "sweep_classical_mismatch",
            "sweep_quantum_match",
            "sweep_quantum_mismatch",
            "sweep_signed_difference",
            "grid_theta_deg",
            "grid_phi_deg",
            "grid_relative_angle_deg",
            "grid_classical_match",
            "grid_classical_mismatch",
            "grid_quantum_match",
            "grid_quantum_mismatch",
            "grid_signed_difference",
        )
        for field_name in array_fields:
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )

        sweep_shape = self.sweep_theta_deg.shape
        if len(sweep_shape) != 1 or sweep_shape[0] < 3:
            raise ValueError("sweep arrays must be one-dimensional and non-trivial")
        for field_name in array_fields[1:12]:
            if getattr(self, field_name).shape != sweep_shape:
                raise ValueError(f"{field_name} has an invalid sweep shape")

        grid_shape = self.grid_theta_deg.shape
        if len(grid_shape) != 2 or min(grid_shape) < 3:
            raise ValueError("grid arrays must be two-dimensional and non-trivial")
        for field_name in array_fields[13:]:
            if getattr(self, field_name).shape != grid_shape:
                raise ValueError(f"{field_name} has an invalid grid shape")

    @property
    def sweep_point_count(self) -> int:
        return int(self.sweep_theta_deg.size)

    @property
    def grid_shape(self) -> tuple[int, int]:
        return (int(self.grid_theta_deg.shape[0]), int(self.grid_theta_deg.shape[1]))


def build_task08_study(
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> Task08StudyResult:
    """Build the approved sweep and full comparison grid."""

    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")

    sweep = angle_sweep(
        configuration.official_theta_deg,
        variable="phi",
        point_count=configuration.sweep_point_count,
        configuration=configuration,
    )
    detector_a = detector_probabilities(sweep.theta_deg)
    detector_b = detector_probabilities(sweep.phi_deg)
    grid = mismatch_grid(configuration=configuration)

    return Task08StudyResult(
        schema_version="task08-study-v1",
        sweep_theta_deg=sweep.theta_deg,
        sweep_phi_deg=sweep.phi_deg,
        sweep_relative_angle_deg=relative_detector_angle_deg(
            sweep.theta_deg,
            sweep.phi_deg,
        ),
        sweep_detector_a_x=detector_a.x,
        sweep_detector_a_y=detector_a.y,
        sweep_detector_b_x=detector_b.x,
        sweep_detector_b_y=detector_b.y,
        sweep_classical_match=sweep.comparison.classical_match,
        sweep_classical_mismatch=sweep.comparison.classical_mismatch,
        sweep_quantum_match=sweep.comparison.quantum_match,
        sweep_quantum_mismatch=sweep.comparison.quantum_mismatch,
        sweep_signed_difference=sweep.comparison.signed_difference,
        grid_theta_deg=grid.theta_deg,
        grid_phi_deg=grid.phi_deg,
        grid_relative_angle_deg=relative_detector_angle_deg(
            grid.theta_deg,
            grid.phi_deg,
        ),
        grid_classical_match=grid.comparison.classical_match,
        grid_classical_mismatch=grid.comparison.classical_mismatch,
        grid_quantum_match=grid.comparison.quantum_match,
        grid_quantum_mismatch=grid.comparison.quantum_mismatch,
        grid_signed_difference=grid.comparison.signed_difference,
    )


__all__ = ["Task08StudyResult", "build_task08_study"]
