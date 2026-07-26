"""Immutable in-memory Task 5 hydrogen-spectrum study."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from task05_hydrogen_spectrum.configuration import (
    DEFAULT_CONFIGURATION,
    Task05Configuration,
)
from task05_hydrogen_spectrum.constants import NANOMETRES_PER_METRE
from task05_hydrogen_spectrum.models import (
    bohr_energy_ev,
    bohr_energy_j,
    series_limit_energy_ev,
    series_limit_wavelength_m,
    transition_energy_ev,
    transition_energy_j,
    transition_frequency_hz,
    transition_wavelength_m,
)
from task05_hydrogen_spectrum.transitions import (
    display_group_for_final,
    enumerate_transition_pairs,
    line_name_for_transition,
    series_name_for_final,
    spectral_region_for_wavelength_nm,
)


IntegerArray = NDArray[np.int64]
FloatArray = NDArray[np.float64]


def _readonly_integer_array(
    value: Any,
    *,
    name: str,
    shape: tuple[int, ...] | None = None,
    positive: bool = False,
) -> IntegerArray:
    raw = np.asarray(value)
    if np.issubdtype(raw.dtype, np.bool_) or not np.issubdtype(
        raw.dtype, np.integer
    ):
        raise TypeError(f"{name} must contain integers")
    array = np.array(value, dtype=np.int64, copy=True)
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, found {array.shape}")
    if positive and np.any(array < 1):
        raise ValueError(f"{name} must be positive")
    array.setflags(write=False)
    return array


def _readonly_float_array(
    value: Any,
    *,
    name: str,
    shape: tuple[int, ...],
    positive: bool = False,
    negative: bool = False,
) -> FloatArray:
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numbers")
    if np.issubdtype(raw.dtype, np.bool_) or np.issubdtype(
        raw.dtype, np.complexfloating
    ):
        raise TypeError(f"{name} must contain real numbers")
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, found {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    if positive and np.any(array <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    if negative and np.any(array >= 0.0):
        raise ValueError(f"{name} must be strictly negative")
    array.setflags(write=False)
    return array


def _text_tuple(
    value: Any,
    *,
    name: str,
    length: int,
    optional: bool = False,
) -> tuple[str | None, ...]:
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be iterable") from exc
    if len(normalized) != length:
        raise ValueError(f"{name} must contain {length} entries")
    for item in normalized:
        if optional and item is None:
            continue
        if not isinstance(item, str) or not item.strip():
            raise TypeError(f"{name} entries must be non-empty text")
    return normalized


@dataclass(frozen=True)
class Task05StudyResult:
    """Complete immutable Bohr levels, emissions, labels, and series limits."""

    levels_n: IntegerArray
    level_energy_ev: FloatArray
    level_energy_j: FloatArray

    initial_n: IntegerArray
    final_n: IntegerArray
    initial_energy_ev: FloatArray
    final_energy_ev: FloatArray
    photon_energy_ev: FloatArray
    photon_energy_j: FloatArray
    frequency_hz: FloatArray
    wavelength_m: FloatArray
    wavelength_nm: FloatArray
    series_names: tuple[str, ...]
    display_groups: tuple[str, ...]
    line_names: tuple[str | None, ...]
    spectral_regions: tuple[str, ...]

    series_limit_final_n: IntegerArray
    series_limit_energy_ev: FloatArray
    series_limit_wavelength_m: FloatArray
    series_limit_wavelength_nm: FloatArray

    def __post_init__(self) -> None:
        levels = _readonly_integer_array(
            self.levels_n,
            name="levels_n",
            positive=True,
        )
        if levels.ndim != 1 or levels.size < 2:
            raise ValueError("levels_n must be a one-dimensional level sequence")
        if not np.array_equal(levels, np.arange(1, levels[-1] + 1)):
            raise ValueError("levels_n must be the exact consecutive sequence from 1")
        object.__setattr__(self, "levels_n", levels)
        level_shape = levels.shape
        for field_name in ("level_energy_ev", "level_energy_j"):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=level_shape,
                    negative=True,
                ),
            )

        expected_pairs = enumerate_transition_pairs(int(levels[-1]))
        transition_shape = (len(expected_pairs),)
        initial = _readonly_integer_array(
            self.initial_n,
            name="initial_n",
            shape=transition_shape,
            positive=True,
        )
        final = _readonly_integer_array(
            self.final_n,
            name="final_n",
            shape=transition_shape,
            positive=True,
        )
        if tuple(zip(initial.tolist(), final.tolist())) != expected_pairs:
            raise ValueError("transition pairs must follow the frozen complete order")
        object.__setattr__(self, "initial_n", initial)
        object.__setattr__(self, "final_n", final)

        for field_name in (
            "initial_energy_ev",
            "final_energy_ev",
            "photon_energy_ev",
            "photon_energy_j",
            "frequency_hz",
            "wavelength_m",
            "wavelength_nm",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=transition_shape,
                    positive=field_name
                    not in {"initial_energy_ev", "final_energy_ev"},
                    negative=field_name
                    in {"initial_energy_ev", "final_energy_ev"},
                ),
            )

        object.__setattr__(
            self,
            "series_names",
            _text_tuple(
                self.series_names,
                name="series_names",
                length=len(expected_pairs),
            ),
        )
        object.__setattr__(
            self,
            "display_groups",
            _text_tuple(
                self.display_groups,
                name="display_groups",
                length=len(expected_pairs),
            ),
        )
        object.__setattr__(
            self,
            "line_names",
            _text_tuple(
                self.line_names,
                name="line_names",
                length=len(expected_pairs),
                optional=True,
            ),
        )
        object.__setattr__(
            self,
            "spectral_regions",
            _text_tuple(
                self.spectral_regions,
                name="spectral_regions",
                length=len(expected_pairs),
            ),
        )

        limits = _readonly_integer_array(
            self.series_limit_final_n,
            name="series_limit_final_n",
            positive=True,
        )
        if limits.ndim != 1 or limits.size < 1:
            raise ValueError("series_limit_final_n must be one-dimensional")
        if not np.array_equal(limits, np.arange(1, limits[-1] + 1)):
            raise ValueError("series-limit levels must be consecutive from 1")
        object.__setattr__(self, "series_limit_final_n", limits)
        limit_shape = limits.shape
        for field_name in (
            "series_limit_energy_ev",
            "series_limit_wavelength_m",
            "series_limit_wavelength_nm",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=limit_shape,
                    positive=True,
                ),
            )


def build_task05_study(
    configuration: Task05Configuration = DEFAULT_CONFIGURATION,
) -> Task05StudyResult:
    """Build the complete deterministic Task 5 study in memory."""

    if not isinstance(configuration, Task05Configuration):
        raise TypeError("configuration must be a Task05Configuration")

    levels = np.arange(1, configuration.maximum_level + 1, dtype=np.int64)
    level_ev = bohr_energy_ev(levels)
    level_j = bohr_energy_j(levels)

    pairs = enumerate_transition_pairs(configuration.maximum_level)
    initial = np.array([pair[0] for pair in pairs], dtype=np.int64)
    final = np.array([pair[1] for pair in pairs], dtype=np.int64)
    photon_ev = transition_energy_ev(initial, final)
    photon_j = transition_energy_j(initial, final)
    frequency = transition_frequency_hz(initial, final)
    wavelength_m = transition_wavelength_m(initial, final)
    wavelength_nm = wavelength_m * NANOMETRES_PER_METRE

    series_names = tuple(series_name_for_final(int(value)) for value in final)
    display_groups = tuple(
        display_group_for_final(int(value)) for value in final
    )
    line_names = tuple(
        line_name_for_transition(int(i), int(f))
        for i, f in zip(initial, final)
    )
    spectral_regions = tuple(
        spectral_region_for_wavelength_nm(
            float(wavelength),
            visible_min_nm=configuration.visible_min_nm,
            visible_max_nm=configuration.visible_max_nm,
        )
        for wavelength in wavelength_nm
    )

    limit_final = np.arange(
        1,
        configuration.highlighted_series_final_max + 1,
        dtype=np.int64,
    )
    limit_energy = series_limit_energy_ev(limit_final)
    limit_wavelength_m = series_limit_wavelength_m(limit_final)

    return Task05StudyResult(
        levels_n=levels,
        level_energy_ev=level_ev,
        level_energy_j=level_j,
        initial_n=initial,
        final_n=final,
        initial_energy_ev=bohr_energy_ev(initial),
        final_energy_ev=bohr_energy_ev(final),
        photon_energy_ev=photon_ev,
        photon_energy_j=photon_j,
        frequency_hz=frequency,
        wavelength_m=wavelength_m,
        wavelength_nm=wavelength_nm,
        series_names=series_names,
        display_groups=display_groups,
        line_names=line_names,
        spectral_regions=spectral_regions,
        series_limit_final_n=limit_final,
        series_limit_energy_ev=limit_energy,
        series_limit_wavelength_m=limit_wavelength_m,
        series_limit_wavelength_nm=limit_wavelength_m * NANOMETRES_PER_METRE,
    )


__all__ = ["Task05StudyResult", "build_task05_study"]
