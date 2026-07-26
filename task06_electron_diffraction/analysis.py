"""Immutable assembly and fit analysis for the complete Task 6 study."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    Task06Configuration,
)
from task06_electron_diffraction.constants import (
    DEG_PER_RAD,
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
)
from task06_electron_diffraction.models import (
    bragg_angle_rad,
    bragg_ratio,
    caliper_diameter_m,
    electron_momentum_kg_m_s,
    electron_wavelength_m,
    maximum_bragg_order,
    maximum_screen_order,
    photo_ring_radius_m,
    scattering_angle_rad,
    screen_visible,
)
from task06_electron_diffraction.orders import (
    enumerate_order_indices,
    order_status_labels,
)


FloatArray = NDArray[np.float64]
IntegerArray = NDArray[np.int64]
BooleanArray = NDArray[np.bool_]


def _readonly_float_array(value: object, *, name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    array.setflags(write=False)
    return array


def _readonly_integer_array(value: object, *, name: str) -> IntegerArray:
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.integer):
        raise TypeError(f"{name} must contain integers")
    array = np.array(value, dtype=np.int64, copy=True)
    array.setflags(write=False)
    return array


def _readonly_boolean_array(value: object, *, name: str) -> BooleanArray:
    raw = np.asarray(value)
    if raw.dtype != np.bool_:
        raise TypeError(f"{name} must contain booleans")
    array = np.array(value, dtype=np.bool_, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class SpacingFitResult:
    """One immutable first-order or normalized all-order line fit."""

    spacing_id: str
    fit_kind: str
    order_n: int | None
    point_count: int
    constrained_gradient_v_inv_sqrt: float
    unconstrained_gradient_v_inv_sqrt: float
    unconstrained_intercept_v_inv_sqrt: float
    r_squared: float
    recovered_spacing_m: float
    maximum_absolute_residual_v_inv_sqrt: float
    horizontal_variable: str
    vertical_variable: str

    def __post_init__(self) -> None:
        if not isinstance(self.spacing_id, str) or not self.spacing_id:
            raise ValueError("spacing_id must be non-empty text")
        if self.fit_kind not in {"first_order", "all_order_normalized"}:
            raise ValueError("invalid fit_kind")
        if self.fit_kind == "first_order":
            if isinstance(self.order_n, bool) or self.order_n != 1:
                raise ValueError("first_order fit must use order_n=1")
        elif self.order_n is not None:
            raise ValueError("all_order_normalized fit must use order_n=None")
        if isinstance(self.point_count, bool) or not isinstance(self.point_count, int):
            raise TypeError("point_count must be an integer")
        if self.point_count < 2:
            raise ValueError("point_count must be at least two")
        for field_name in (
            "constrained_gradient_v_inv_sqrt",
            "unconstrained_gradient_v_inv_sqrt",
            "unconstrained_intercept_v_inv_sqrt",
            "r_squared",
            "recovered_spacing_m",
            "maximum_absolute_residual_v_inv_sqrt",
        ):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
            object.__setattr__(self, field_name, value)
        if self.constrained_gradient_v_inv_sqrt <= 0.0:
            raise ValueError("constrained gradient must be positive")
        if self.recovered_spacing_m <= 0.0:
            raise ValueError("recovered spacing must be positive")
        if self.maximum_absolute_residual_v_inv_sqrt < 0.0:
            raise ValueError("maximum residual must be non-negative")
        for field_name in ("horizontal_variable", "vertical_variable"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be non-empty text")


@dataclass(frozen=True)
class Task06StudyResult:
    """Complete immutable voltage sweep, order catalogue, and fit results."""

    schema_version: str
    voltages_v: FloatArray
    momenta_kg_m_s: FloatArray
    wavelengths_m: FloatArray
    spacing_ids: tuple[str, ...]
    spacing_labels: tuple[str, ...]
    spacings_m: FloatArray
    maximum_bragg_orders: IntegerArray
    maximum_screen_orders: IntegerArray
    voltage_indices: IntegerArray
    spacing_indices: IntegerArray
    orders_n: IntegerArray
    bragg_ratios_q: FloatArray
    theta_rad: FloatArray
    phi_rad: FloatArray
    photo_radii_m: FloatArray
    caliper_diameters_m: FloatArray
    screen_visible_flags: BooleanArray
    order_statuses: tuple[str, ...]
    first_order_fits: tuple[SpacingFitResult, ...]
    normalized_fits: tuple[SpacingFitResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "task06-study-v1":
            raise ValueError("invalid Task 6 study schema")

        for field_name in ("voltages_v", "momenta_kg_m_s", "wavelengths_m"):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )
        if self.voltages_v.ndim != 1 or self.voltages_v.size < 2:
            raise ValueError("voltage sweep must be a one-dimensional array")
        if self.momenta_kg_m_s.shape != self.voltages_v.shape:
            raise ValueError("momentum shape must match voltage shape")
        if self.wavelengths_m.shape != self.voltages_v.shape:
            raise ValueError("wavelength shape must match voltage shape")
        if np.any(self.voltages_v <= 0.0) or np.any(self.momenta_kg_m_s <= 0.0):
            raise ValueError("voltages and momenta must be positive")
        if np.any(self.wavelengths_m <= 0.0):
            raise ValueError("wavelengths must be positive")

        spacing_ids = tuple(self.spacing_ids)
        spacing_labels = tuple(self.spacing_labels)
        if not spacing_ids or len(set(spacing_ids)) != len(spacing_ids):
            raise ValueError("spacing_ids must be unique and non-empty")
        if len(spacing_labels) != len(spacing_ids):
            raise ValueError("spacing label count must match identifiers")
        if any(not isinstance(value, str) or not value for value in spacing_ids + spacing_labels):
            raise ValueError("spacing identifiers and labels must be non-empty text")
        object.__setattr__(self, "spacing_ids", spacing_ids)
        object.__setattr__(self, "spacing_labels", spacing_labels)
        object.__setattr__(
            self,
            "spacings_m",
            _readonly_float_array(self.spacings_m, name="spacings_m"),
        )
        if self.spacings_m.shape != (len(spacing_ids),) or np.any(self.spacings_m <= 0.0):
            raise ValueError("spacings_m must be one positive value per spacing")

        expected_maximum_shape = (self.voltages_v.size, self.spacings_m.size)
        for field_name in ("maximum_bragg_orders", "maximum_screen_orders"):
            object.__setattr__(
                self,
                field_name,
                _readonly_integer_array(getattr(self, field_name), name=field_name),
            )
            if getattr(self, field_name).shape != expected_maximum_shape:
                raise ValueError(f"{field_name} has the wrong shape")

        catalogue_integer_fields = ("voltage_indices", "spacing_indices", "orders_n")
        for field_name in catalogue_integer_fields:
            object.__setattr__(
                self,
                field_name,
                _readonly_integer_array(getattr(self, field_name), name=field_name),
            )
        catalogue_float_fields = (
            "bragg_ratios_q",
            "theta_rad",
            "phi_rad",
            "photo_radii_m",
            "caliper_diameters_m",
        )
        for field_name in catalogue_float_fields:
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )
        object.__setattr__(
            self,
            "screen_visible_flags",
            _readonly_boolean_array(
                self.screen_visible_flags,
                name="screen_visible_flags",
            ),
        )

        catalogue_size = self.orders_n.size
        for field_name in catalogue_integer_fields + catalogue_float_fields + (
            "screen_visible_flags",
        ):
            if getattr(self, field_name).shape != (catalogue_size,):
                raise ValueError(f"{field_name} must match the catalogue length")
        if catalogue_size < 1:
            raise ValueError("order catalogue must not be empty")
        if np.any(self.voltage_indices < 0) or np.any(
            self.voltage_indices >= self.voltages_v.size
        ):
            raise ValueError("voltage_indices are out of bounds")
        if np.any(self.spacing_indices < 0) or np.any(
            self.spacing_indices >= self.spacings_m.size
        ):
            raise ValueError("spacing_indices are out of bounds")
        if np.any(self.orders_n < 1):
            raise ValueError("orders_n must be positive")

        statuses = tuple(self.order_statuses)
        if len(statuses) != catalogue_size or any(
            status not in {"forward_screen", "back_scattering"}
            for status in statuses
        ):
            raise ValueError("order_statuses must be controlled labels per record")
        object.__setattr__(self, "order_statuses", statuses)

        for field_name in ("first_order_fits", "normalized_fits"):
            values = tuple(getattr(self, field_name))
            if len(values) != self.spacings_m.size or any(
                not isinstance(value, SpacingFitResult) for value in values
            ):
                raise TypeError(f"{field_name} must contain one fit per spacing")
            object.__setattr__(self, field_name, values)

    @property
    def catalogue_size(self) -> int:
        return int(self.orders_n.size)

    @property
    def forward_screen_count(self) -> int:
        return int(np.count_nonzero(self.screen_visible_flags))

    @property
    def theta_deg(self) -> FloatArray:
        values = np.asarray(self.theta_rad * DEG_PER_RAD, dtype=np.float64)
        values.setflags(write=False)
        return values

    @property
    def phi_deg(self) -> FloatArray:
        values = np.asarray(self.phi_rad * DEG_PER_RAD, dtype=np.float64)
        values.setflags(write=False)
        return values


def _line_fit(
    *,
    spacing_id: str,
    spacing_m: float,
    fit_kind: str,
    order_n: int | None,
    x: FloatArray,
    y: FloatArray,
) -> SpacingFitResult:
    x_values = np.asarray(x, dtype=np.float64)
    y_values = np.asarray(y, dtype=np.float64)
    if x_values.shape != y_values.shape or x_values.ndim != 1 or x_values.size < 2:
        raise ValueError("fit arrays must be matching one-dimensional arrays")
    denominator = float(np.dot(x_values, x_values))
    if denominator <= 0.0:
        raise ValueError("fit horizontal values must not all be zero")
    constrained_gradient = float(np.dot(x_values, y_values) / denominator)
    unconstrained_gradient, unconstrained_intercept = np.polyfit(x_values, y_values, 1)
    predicted = constrained_gradient * x_values
    residuals = y_values - predicted
    total_sum_squares = float(np.sum(np.square(y_values - np.mean(y_values))))
    residual_sum_squares = float(np.sum(np.square(residuals)))
    r_squared = 1.0 - residual_sum_squares / total_sum_squares
    order_factor = float(order_n) if order_n is not None else 1.0
    recovered_spacing = (
        order_factor
        * PLANCK_CONSTANT_J_S
        * constrained_gradient
        / (2.0 * math.sqrt(2.0 * ELECTRON_MASS_KG * ELEMENTARY_CHARGE_C))
    )
    return SpacingFitResult(
        spacing_id=spacing_id,
        fit_kind=fit_kind,
        order_n=order_n,
        point_count=int(x_values.size),
        constrained_gradient_v_inv_sqrt=constrained_gradient,
        unconstrained_gradient_v_inv_sqrt=float(unconstrained_gradient),
        unconstrained_intercept_v_inv_sqrt=float(unconstrained_intercept),
        r_squared=float(r_squared),
        recovered_spacing_m=float(recovered_spacing),
        maximum_absolute_residual_v_inv_sqrt=float(np.max(np.abs(residuals))),
        horizontal_variable="sin(phi/2)",
        vertical_variable=(
            "1/sqrt(V)" if fit_kind == "first_order" else "n/sqrt(V)"
        ),
    )


def build_task06_study(
    configuration: Task06Configuration = DEFAULT_CONFIGURATION,
) -> Task06StudyResult:
    """Build the complete immutable Task 6 baseline study."""

    if not isinstance(configuration, Task06Configuration):
        raise TypeError("configuration must be a Task06Configuration")

    voltages = np.linspace(
        configuration.voltage_min_v,
        configuration.voltage_max_v,
        configuration.voltage_count,
        dtype=np.float64,
    )
    momenta = electron_momentum_kg_m_s(voltages)
    wavelengths = electron_wavelength_m(voltages)
    spacings = np.asarray(
        [spacing.spacing_m for spacing in configuration.spacings],
        dtype=np.float64,
    )

    voltage_grid = voltages[:, np.newaxis]
    spacing_grid = spacings[np.newaxis, :]
    bragg_maximum = maximum_bragg_order(voltage_grid, spacing_grid)
    screen_maximum = maximum_screen_order(voltage_grid, spacing_grid)
    voltage_indices, spacing_indices, orders = enumerate_order_indices(bragg_maximum)
    record_voltages = voltages[voltage_indices]
    record_spacings = spacings[spacing_indices]

    ratios = bragg_ratio(record_voltages, record_spacings, orders)
    theta = bragg_angle_rad(record_voltages, record_spacings, orders)
    phi = scattering_angle_rad(record_voltages, record_spacings, orders)
    photo_radii = photo_ring_radius_m(
        record_voltages,
        record_spacings,
        orders,
        configuration.tube_radius_m,
    )
    caliper_diameters = caliper_diameter_m(
        record_voltages,
        record_spacings,
        orders,
        configuration.tube_radius_m,
    )
    visibility = screen_visible(record_voltages, record_spacings, orders)

    first_order_fits: list[SpacingFitResult] = []
    normalized_fits: list[SpacingFitResult] = []
    inverse_sqrt_voltage = 1.0 / np.sqrt(voltages)
    for spacing_index, spacing_definition in enumerate(configuration.spacings):
        first_order_x = bragg_ratio(voltages, spacing_definition.spacing_m, 1)
        first_order_fits.append(
            _line_fit(
                spacing_id=spacing_definition.identifier,
                spacing_m=spacing_definition.spacing_m,
                fit_kind="first_order",
                order_n=1,
                x=first_order_x,
                y=inverse_sqrt_voltage,
            )
        )

        family_mask = spacing_indices == spacing_index
        normalized_fits.append(
            _line_fit(
                spacing_id=spacing_definition.identifier,
                spacing_m=spacing_definition.spacing_m,
                fit_kind="all_order_normalized",
                order_n=None,
                x=ratios[family_mask],
                y=(
                    orders[family_mask].astype(np.float64)
                    / np.sqrt(record_voltages[family_mask])
                ),
            )
        )

    return Task06StudyResult(
        schema_version="task06-study-v1",
        voltages_v=voltages,
        momenta_kg_m_s=momenta,
        wavelengths_m=wavelengths,
        spacing_ids=tuple(spacing.identifier for spacing in configuration.spacings),
        spacing_labels=tuple(spacing.label for spacing in configuration.spacings),
        spacings_m=spacings,
        maximum_bragg_orders=bragg_maximum,
        maximum_screen_orders=screen_maximum,
        voltage_indices=voltage_indices,
        spacing_indices=spacing_indices,
        orders_n=orders,
        bragg_ratios_q=ratios,
        theta_rad=theta,
        phi_rad=phi,
        photo_radii_m=photo_radii,
        caliper_diameters_m=caliper_diameters,
        screen_visible_flags=visibility,
        order_statuses=order_status_labels(visibility),
        first_order_fits=tuple(first_order_fits),
        normalized_fits=tuple(normalized_fits),
    )


__all__ = ["SpacingFitResult", "Task06StudyResult", "build_task06_study"]
