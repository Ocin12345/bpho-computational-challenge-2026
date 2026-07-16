"""Immutable in-memory studies for Task 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from task04_photoelectric_effect.configuration import (
    DEFAULT_CONFIGURATION,
    Task04Configuration,
)
from task04_photoelectric_effect.constants import (
    ELECTRONVOLT_J,
    METRES_PER_NANOMETRE,
    NANOMETRES_PER_METRE,
)
from task04_photoelectric_effect.materials import (
    OFFICIAL_MATERIALS,
    PhotoelectricMaterial,
    validate_material_collection,
)
from task04_photoelectric_effect.models import (
    cutoff_frequency_hz,
    cutoff_wavelength_m,
    emission_possible_from_frequency,
    emission_possible_from_wavelength,
    linear_stopping_voltage_from_frequency,
    linear_stopping_voltage_from_wavelength,
    physical_stopping_voltage_from_frequency,
    physical_stopping_voltage_from_wavelength,
)


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def _readonly_float_array(
    value: Any,
    *,
    name: str,
    shape: tuple[int, ...] | None = None,
    positive: bool = False,
    non_negative: bool = False,
) -> FloatArray:
    """Copy one finite float array and mark it read-only."""

    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real numbers, not complex values")
    array = np.array(value, dtype=np.float64, copy=True)
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, found {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    if positive and np.any(array <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    if non_negative and np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    array.setflags(write=False)
    return array


def _readonly_bool_array(
    value: Any,
    *,
    name: str,
    shape: tuple[int, ...],
) -> BoolArray:
    """Copy one strictly boolean array and mark it read-only."""

    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.bool_):
        raise TypeError(f"{name} must contain boolean values")
    array = np.array(value, dtype=np.bool_, copy=True)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, found {array.shape}")
    array.setflags(write=False)
    return array


def _readonly_physical_array(
    value: Any,
    mask: BoolArray,
    *,
    name: str,
) -> FloatArray:
    """Copy a physical voltage array with exact mask/NaN semantics."""

    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real numbers, not complex values")
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != mask.shape:
        raise ValueError(
            f"{name} must have shape {mask.shape}, found {array.shape}"
        )
    if np.any(~np.isfinite(array[mask])):
        raise ValueError(f"{name} must be finite throughout the emission domain")
    if np.any(array[mask] < 0.0):
        raise ValueError(f"{name} must be non-negative in the emission domain")
    if np.any(~np.isnan(array[~mask])):
        raise ValueError(f"{name} must be NaN outside the emission domain")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class Task04StudyResult:
    """Complete immutable frequency and wavelength comparison."""

    materials: tuple[PhotoelectricMaterial, ...]
    work_functions_ev: FloatArray
    work_functions_j: FloatArray
    cutoff_frequencies_hz: FloatArray
    cutoff_wavelengths_nm: FloatArray

    frequency_hz: FloatArray
    frequency_linear_voltage_v: FloatArray
    frequency_emission_mask: BoolArray
    frequency_physical_voltage_v: FloatArray

    wavelength_m: FloatArray
    wavelength_nm: FloatArray
    wavelength_linear_voltage_v: FloatArray
    wavelength_emission_mask: BoolArray
    wavelength_physical_voltage_v: FloatArray

    def __post_init__(self) -> None:
        """Defensively copy arrays and enforce structural invariants."""

        materials = validate_material_collection(self.materials)
        object.__setattr__(self, "materials", materials)
        material_count = len(materials)

        one_material_shape = (material_count,)
        for field_name in (
            "work_functions_ev",
            "work_functions_j",
            "cutoff_frequencies_hz",
            "cutoff_wavelengths_nm",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=one_material_shape,
                    positive=True,
                ),
            )

        frequency_hz = _readonly_float_array(
            self.frequency_hz,
            name="frequency_hz",
            positive=True,
        )
        if frequency_hz.ndim != 1 or frequency_hz.size < 2:
            raise ValueError("frequency_hz must be a one-dimensional grid")
        if np.any(np.diff(frequency_hz) <= 0.0):
            raise ValueError("frequency_hz must be strictly increasing")
        object.__setattr__(self, "frequency_hz", frequency_hz)

        frequency_shape = (material_count, frequency_hz.size)
        frequency_linear = _readonly_float_array(
            self.frequency_linear_voltage_v,
            name="frequency_linear_voltage_v",
            shape=frequency_shape,
        )
        frequency_mask = _readonly_bool_array(
            self.frequency_emission_mask,
            name="frequency_emission_mask",
            shape=frequency_shape,
        )
        frequency_physical = _readonly_physical_array(
            self.frequency_physical_voltage_v,
            frequency_mask,
            name="frequency_physical_voltage_v",
        )
        object.__setattr__(
            self,
            "frequency_linear_voltage_v",
            frequency_linear,
        )
        object.__setattr__(self, "frequency_emission_mask", frequency_mask)
        object.__setattr__(
            self,
            "frequency_physical_voltage_v",
            frequency_physical,
        )

        wavelength_m = _readonly_float_array(
            self.wavelength_m,
            name="wavelength_m",
            positive=True,
        )
        wavelength_nm = _readonly_float_array(
            self.wavelength_nm,
            name="wavelength_nm",
            positive=True,
        )
        if wavelength_m.ndim != 1 or wavelength_m.size < 2:
            raise ValueError("wavelength_m must be a one-dimensional grid")
        if wavelength_nm.ndim != 1 or wavelength_nm.size != wavelength_m.size:
            raise ValueError("wavelength_nm must match the wavelength_m grid")
        if np.any(np.diff(wavelength_m) <= 0.0):
            raise ValueError("wavelength_m must be strictly increasing")
        if np.any(np.diff(wavelength_nm) <= 0.0):
            raise ValueError("wavelength_nm must be strictly increasing")
        object.__setattr__(self, "wavelength_m", wavelength_m)
        object.__setattr__(self, "wavelength_nm", wavelength_nm)

        wavelength_shape = (material_count, wavelength_m.size)
        wavelength_linear = _readonly_float_array(
            self.wavelength_linear_voltage_v,
            name="wavelength_linear_voltage_v",
            shape=wavelength_shape,
        )
        wavelength_mask = _readonly_bool_array(
            self.wavelength_emission_mask,
            name="wavelength_emission_mask",
            shape=wavelength_shape,
        )
        wavelength_physical = _readonly_physical_array(
            self.wavelength_physical_voltage_v,
            wavelength_mask,
            name="wavelength_physical_voltage_v",
        )
        object.__setattr__(
            self,
            "wavelength_linear_voltage_v",
            wavelength_linear,
        )
        object.__setattr__(self, "wavelength_emission_mask", wavelength_mask)
        object.__setattr__(
            self,
            "wavelength_physical_voltage_v",
            wavelength_physical,
        )


def build_task04_study(
    configuration: Task04Configuration = DEFAULT_CONFIGURATION,
    materials: tuple[PhotoelectricMaterial, ...] = OFFICIAL_MATERIALS,
) -> Task04StudyResult:
    """Build the complete deterministic Task 4 study in memory."""

    if not isinstance(configuration, Task04Configuration):
        raise TypeError("configuration must be a Task04Configuration")
    normalized_materials = validate_material_collection(materials)

    frequency_hz = configuration.frequency_start_hz + np.arange(
        configuration.frequency_points,
        dtype=np.float64,
    ) * configuration.frequency_step_hz
    wavelength_nm = configuration.wavelength_start_nm + np.arange(
        configuration.wavelength_points,
        dtype=np.float64,
    ) * configuration.wavelength_step_nm
    wavelength_m = wavelength_nm * METRES_PER_NANOMETRE

    work_functions_ev = np.array(
        [material.work_function_ev for material in normalized_materials],
        dtype=np.float64,
    )
    work_functions_j = work_functions_ev * ELECTRONVOLT_J
    cutoff_frequencies = cutoff_frequency_hz(work_functions_ev)
    cutoff_wavelengths_nm = (
        cutoff_wavelength_m(work_functions_ev) * NANOMETRES_PER_METRE
    )

    material_column = work_functions_ev[:, np.newaxis]
    frequency_row = frequency_hz[np.newaxis, :]
    wavelength_row = wavelength_m[np.newaxis, :]

    frequency_linear = linear_stopping_voltage_from_frequency(
        frequency_row,
        material_column,
    )
    frequency_mask = emission_possible_from_frequency(
        frequency_row,
        material_column,
    )
    frequency_physical = physical_stopping_voltage_from_frequency(
        frequency_row,
        material_column,
    )

    wavelength_linear = linear_stopping_voltage_from_wavelength(
        wavelength_row,
        material_column,
    )
    wavelength_mask = emission_possible_from_wavelength(
        wavelength_row,
        material_column,
    )
    wavelength_physical = physical_stopping_voltage_from_wavelength(
        wavelength_row,
        material_column,
    )

    return Task04StudyResult(
        materials=normalized_materials,
        work_functions_ev=work_functions_ev,
        work_functions_j=work_functions_j,
        cutoff_frequencies_hz=cutoff_frequencies,
        cutoff_wavelengths_nm=cutoff_wavelengths_nm,
        frequency_hz=frequency_hz,
        frequency_linear_voltage_v=frequency_linear,
        frequency_emission_mask=frequency_mask,
        frequency_physical_voltage_v=frequency_physical,
        wavelength_m=wavelength_m,
        wavelength_nm=wavelength_nm,
        wavelength_linear_voltage_v=wavelength_linear,
        wavelength_emission_mask=wavelength_mask,
        wavelength_physical_voltage_v=wavelength_physical,
    )


__all__ = ["Task04StudyResult", "build_task04_study"]
