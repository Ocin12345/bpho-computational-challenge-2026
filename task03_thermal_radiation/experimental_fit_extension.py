"""Copper heat-capacity fitting extension for BPhO Task 3.

The baseline compares Einstein curves at chosen characteristic temperatures.
This module makes the comparison quantitative: a Debye lattice term, a linear
electronic term and the leading thermodynamic ``Cp - Cv`` dilation term are fit
to the critically evaluated copper reference values published by White and
Collocott (J. Phys. Chem. Ref. Data 13, 1251-1257, 1984, DOI
10.1063/1.555728).  The source table combines selected calorimetry data and is
kept verbatim below; it is not synthetic data.

The fitted model is deliberately modest,

    Cp(T) = Cv_D(T, theta_D) + gamma*T + A*T*Cv_D(T, theta_D)^2,

where the last term is a compact Gruneisen-style representation of thermal
expansion.  It is a comparison model, not a claim that theta_D is exactly
temperature independent over the complete 1--300 K interval.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from task03_thermal_radiation.debye_extension import debye_molar_heat_capacity
from task03_thermal_radiation.models import einstein_molar_heat_capacity


FloatArray = NDArray[np.float64]

# Table 2, copper Cp values in J mol^-1 K^-1.  Cv entries are intentionally not
# copied because the extension fits the directly recommended constant-pressure
# values and models Cp-Cv explicitly.
COPPER_REFERENCE_TEMPERATURE_K = np.asarray(
    [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35,
        40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 220, 240,
        260, 280, 300,
    ],
    dtype=np.float64,
)
COPPER_REFERENCE_CP_J_MOL_K = np.asarray(
    [
        0.000743, 0.00177, 0.00337, 0.00582, 0.00943, 0.0145, 0.0213,
        0.0301, 0.0414, 0.0555, 0.0936, 0.149, 0.225, 0.328, 0.462,
        0.963, 1.693, 2.64, 3.74, 6.15, 8.595, 10.86, 12.85, 14.56,
        16.01, 18.25, 19.87, 21.05, 21.94, 22.63, 23.17, 23.60,
        23.94, 24.22, 24.45,
    ],
    dtype=np.float64,
)


@dataclass(frozen=True)
class HeatCapacityFit:
    """One weighted reference-data fit and its diagnostics."""

    model: str
    characteristic_temperature_k: float
    electronic_gamma_j_mol_k2: float
    dilation_coefficient_mol_per_j: float
    predicted_cp_j_mol_k: FloatArray
    residuals_j_mol_k: FloatArray
    reduced_chi_squared: float
    rms_error_j_mol_k: float
    maximum_relative_error: float


def copper_reference_uncertainty_j_mol_k(
    temperature_k: ArrayLike = COPPER_REFERENCE_TEMPERATURE_K,
    cp_j_mol_k: ArrayLike = COPPER_REFERENCE_CP_J_MOL_K,
) -> FloatArray:
    """Return conservative one-sigma uncertainties from the source discussion.

    White and Collocott estimate errors below 100 K below 1%, and errors from
    100--300 K around 0.3%.  A small absolute floor prevents the first few
    millikelvin-scale values from receiving unbounded statistical leverage.
    """

    temperature = np.asarray(temperature_k, dtype=np.float64)
    capacity = np.asarray(cp_j_mol_k, dtype=np.float64)
    if temperature.shape != capacity.shape or temperature.ndim != 1:
        raise ValueError("temperature and capacity must be matching 1D arrays")
    if np.any(~np.isfinite(temperature)) or np.any(temperature <= 0.0):
        raise ValueError("temperature must be finite and positive")
    if np.any(~np.isfinite(capacity)) or np.any(capacity <= 0.0):
        raise ValueError("capacity must be finite and positive")
    relative = np.where(temperature < 100.0, 0.01, 0.003)
    return np.maximum(relative * capacity, 2.0e-5)


def lattice_plus_electronic_cp(
    temperature_k: ArrayLike,
    characteristic_temperature_k: float,
    electronic_gamma_j_mol_k2: float,
    dilation_coefficient_mol_per_j: float,
    *,
    model: str = "debye",
) -> FloatArray:
    """Evaluate the fitted Cp model for either a Debye or Einstein lattice."""

    temperature = np.asarray(temperature_k, dtype=np.float64)
    if np.any(~np.isfinite(temperature)) or np.any(temperature < 0.0):
        raise ValueError("temperature_k must be finite and non-negative")
    theta = float(characteristic_temperature_k)
    gamma = float(electronic_gamma_j_mol_k2)
    dilation = float(dilation_coefficient_mol_per_j)
    if not np.isfinite(theta) or theta <= 0.0:
        raise ValueError("characteristic_temperature_k must be positive")
    if not np.isfinite(gamma) or gamma < 0.0:
        raise ValueError("electronic_gamma_j_mol_k2 must be non-negative")
    if not np.isfinite(dilation) or dilation < 0.0:
        raise ValueError("dilation_coefficient_mol_per_j must be non-negative")
    if model == "debye":
        lattice = debye_molar_heat_capacity(temperature, theta)
    elif model == "einstein":
        lattice = einstein_molar_heat_capacity(temperature, theta)
    else:
        raise ValueError("model must be 'debye' or 'einstein'")
    return np.asarray(
        lattice + gamma * temperature + dilation * temperature * lattice**2,
        dtype=np.float64,
    )


def fit_copper_heat_capacity(*, model: str = "debye") -> HeatCapacityFit:
    """Fit the chosen lattice model to the published 1--300 K copper table."""

    if model not in {"debye", "einstein"}:
        raise ValueError("model must be 'debye' or 'einstein'")
    temperature = COPPER_REFERENCE_TEMPERATURE_K
    observed = COPPER_REFERENCE_CP_J_MOL_K
    sigma = copper_reference_uncertainty_j_mol_k()

    initial_theta = 340.0 if model == "debye" else 260.0

    def weighted_residual(parameters: FloatArray) -> FloatArray:
        predicted = lattice_plus_electronic_cp(
            temperature,
            parameters[0],
            parameters[1],
            parameters[2],
            model=model,
        )
        return np.asarray((predicted - observed) / sigma, dtype=np.float64)

    optimization = least_squares(
        weighted_residual,
        x0=np.asarray([initial_theta, 7.0e-4, 1.0e-6]),
        bounds=(
            np.asarray([100.0, 0.0, 0.0]),
            np.asarray([1000.0, 0.01, 2.0e-5]),
        ),
        xtol=1.0e-13,
        ftol=1.0e-13,
        gtol=1.0e-13,
        max_nfev=5000,
    )
    if not optimization.success:
        raise RuntimeError(f"heat-capacity fit failed: {optimization.message}")
    theta, gamma, dilation = (float(value) for value in optimization.x)
    predicted = lattice_plus_electronic_cp(
        temperature, theta, gamma, dilation, model=model
    )
    residuals = np.asarray(predicted - observed, dtype=np.float64)
    dof = len(temperature) - 3
    relative = np.abs(residuals) / observed
    for array in (predicted, residuals):
        array.setflags(write=False)
    return HeatCapacityFit(
        model=model,
        characteristic_temperature_k=theta,
        electronic_gamma_j_mol_k2=gamma,
        dilation_coefficient_mol_per_j=dilation,
        predicted_cp_j_mol_k=predicted,
        residuals_j_mol_k=residuals,
        reduced_chi_squared=float(np.sum((residuals / sigma) ** 2) / dof),
        rms_error_j_mol_k=float(np.sqrt(np.mean(residuals**2))),
        maximum_relative_error=float(np.max(relative)),
    )


__all__ = [
    "COPPER_REFERENCE_CP_J_MOL_K",
    "COPPER_REFERENCE_TEMPERATURE_K",
    "HeatCapacityFit",
    "copper_reference_uncertainty_j_mol_k",
    "fit_copper_heat_capacity",
    "lattice_plus_electronic_cp",
]
