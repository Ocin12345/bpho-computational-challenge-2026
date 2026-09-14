"""Monte Carlo material and detector response extension for BPhO Task 9.

The official model treats one free stationary electron and returns exact
two-body kinematics.  This extension samples the Klein--Nishina angle law and
then layers four explicitly separated effects: a binding-energy loss,
impulse-approximation Doppler broadening, an optional second Compton scatter,
and a Gaussian detector energy response.  The layers can all be set to zero,
in which case the event energies agree exactly with the validated core model.

The bound-electron momentum and detector terms are phenomenological teaching
models, not a Geant4-class material transport calculation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task09_compton_scattering.constants import ELECTRON_REST_ENERGY_KEV
from task09_compton_scattering.models import compton_kinematics


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


@dataclass(frozen=True)
class DetectorResponseConfiguration:
    incident_energy_kev: float = 200.0
    event_count: int = 50_000
    binding_energy_kev: float = 0.284
    doppler_sigma_fraction: float = 0.012
    multiple_scatter_probability: float = 0.18
    detector_noise_fwhm_kev: float = 0.75
    detector_stochastic_fwhm_sqrt_kev: float = 0.055
    detector_constant_fwhm_fraction: float = 0.006
    seed: int = 2026

    def __post_init__(self) -> None:
        energy = float(self.incident_energy_kev)
        if not np.isfinite(energy) or not 10.0 <= energy <= 2000.0:
            raise ValueError("incident_energy_kev must lie between 10 and 2000")
        object.__setattr__(self, "incident_energy_kev", energy)
        if isinstance(self.event_count, bool) or int(self.event_count) < 100:
            raise ValueError("event_count must be an integer of at least 100")
        object.__setattr__(self, "event_count", int(self.event_count))
        for name in (
            "binding_energy_kev",
            "doppler_sigma_fraction",
            "detector_noise_fwhm_kev",
            "detector_stochastic_fwhm_sqrt_kev",
            "detector_constant_fwhm_fraction",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, value)
        probability = float(self.multiple_scatter_probability)
        if not np.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("multiple_scatter_probability must lie in [0,1]")
        object.__setattr__(self, "multiple_scatter_probability", probability)
        if isinstance(self.seed, bool) or int(self.seed) < 0:
            raise ValueError("seed must be a non-negative integer")
        object.__setattr__(self, "seed", int(self.seed))


@dataclass(frozen=True)
class ComptonDetectorEvents:
    """Read-only event arrays and detector-level summary statistics."""

    first_scatter_angle_deg: FloatArray
    second_scatter_angle_deg: FloatArray
    ideal_single_scatter_energy_kev: FloatArray
    material_exit_energy_kev: FloatArray
    measured_energy_kev: FloatArray
    detector_fwhm_kev: FloatArray
    multiple_scatter_mask: BoolArray
    measured_mean_energy_kev: float
    measured_standard_deviation_kev: float
    multiple_scatter_fraction: float


def sample_klein_nishina_angles_deg(
    incident_energy_kev: float,
    event_count: int,
    rng: np.random.Generator,
) -> FloatArray:
    """Sample polar angles by exact rejection from a uniform solid angle."""

    energy = float(incident_energy_kev)
    count = int(event_count)
    if energy <= 0.0 or count < 1:
        raise ValueError("energy and event_count must be positive")
    return _sample_variable_energy_angles_deg(
        np.full(count, energy, dtype=np.float64), rng
    )


def _sample_variable_energy_angles_deg(
    incident_energy_kev: FloatArray,
    rng: np.random.Generator,
) -> FloatArray:
    """Vectorized Klein--Nishina rejection sampler for per-event energies."""

    energies = np.asarray(incident_energy_kev, dtype=np.float64)
    if (
        energies.ndim != 1
        or np.any(~np.isfinite(energies))
        or np.any(energies <= 0.0)
    ):
        raise ValueError("incident energies must be a positive finite 1D array")
    angles = np.empty(energies.shape, dtype=np.float64)
    remaining = np.arange(len(energies), dtype=np.int64)
    while remaining.size:
        cosine = rng.uniform(-1.0, 1.0, remaining.size)
        alpha = energies[remaining] / ELECTRON_REST_ENERGY_KEV
        ratio = 1.0 / (1.0 + alpha * (1.0 - cosine))
        weight = 0.5 * ratio**2 * (
            ratio + 1.0 / ratio - (1.0 - cosine**2)
        )
        accepted = rng.random(remaining.size) <= weight
        angles[remaining[accepted]] = np.degrees(np.arccos(cosine[accepted]))
        remaining = remaining[~accepted]
    return angles


def detector_fwhm_kev(
    energy_kev: FloatArray,
    configuration: DetectorResponseConfiguration,
) -> FloatArray:
    """Return quadrature sum of noise, stochastic and constant resolution."""

    energy = np.asarray(energy_kev, dtype=np.float64)
    if np.any(~np.isfinite(energy)) or np.any(energy < 0.0):
        raise ValueError("energy_kev must be finite and non-negative")
    return np.sqrt(
        configuration.detector_noise_fwhm_kev**2
        + configuration.detector_stochastic_fwhm_sqrt_kev**2 * energy
        + (configuration.detector_constant_fwhm_fraction * energy) ** 2
    )


def simulate_detector_response(
    configuration: DetectorResponseConfiguration = DetectorResponseConfiguration(),
) -> ComptonDetectorEvents:
    """Generate a deterministic-seed detector event sample."""

    if not isinstance(configuration, DetectorResponseConfiguration):
        raise TypeError("configuration must be DetectorResponseConfiguration")
    rng = np.random.default_rng(configuration.seed)
    count = configuration.event_count
    first_angle = sample_klein_nishina_angles_deg(
        configuration.incident_energy_kev, count, rng
    )
    ideal = np.asarray(
        compton_kinematics(
            configuration.incident_energy_kev, first_angle
        ).scattered_energy_kev,
        dtype=np.float64,
    )
    exit_energy = np.maximum(ideal - configuration.binding_energy_kev, 1.0e-9)
    if configuration.doppler_sigma_fraction:
        angular_scale = np.sqrt(np.maximum(1.0 - np.cos(np.radians(first_angle)), 0.0))
        sigma = configuration.doppler_sigma_fraction * exit_energy * angular_scale
        exit_energy = np.maximum(exit_energy + rng.normal(0.0, sigma), 1.0e-9)

    multiple = rng.random(count) < configuration.multiple_scatter_probability
    second_angle = np.full(count, np.nan, dtype=np.float64)
    if np.any(multiple):
        indices = np.flatnonzero(multiple)
        sampled_second = _sample_variable_energy_angles_deg(exit_energy[indices], rng)
        second_angle[indices] = sampled_second
        exit_energy[indices] = np.asarray(
            compton_kinematics(
                exit_energy[indices], sampled_second
            ).scattered_energy_kev,
            dtype=np.float64,
        )

    fwhm = detector_fwhm_kev(exit_energy, configuration)
    sigma_detector = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    measured = np.maximum(exit_energy + rng.normal(0.0, sigma_detector), 0.0)
    for array in (first_angle, second_angle, ideal, exit_energy, measured, fwhm, multiple):
        array.setflags(write=False)
    return ComptonDetectorEvents(
        first_scatter_angle_deg=first_angle,
        second_scatter_angle_deg=second_angle,
        ideal_single_scatter_energy_kev=ideal,
        material_exit_energy_kev=exit_energy,
        measured_energy_kev=measured,
        detector_fwhm_kev=fwhm,
        multiple_scatter_mask=multiple,
        measured_mean_energy_kev=float(np.mean(measured)),
        measured_standard_deviation_kev=float(np.std(measured, ddof=1)),
        multiple_scatter_fraction=float(np.mean(multiple)),
    )


__all__ = [
    "ComptonDetectorEvents",
    "DetectorResponseConfiguration",
    "detector_fwhm_kev",
    "sample_klein_nishina_angles_deg",
    "simulate_detector_response",
]
