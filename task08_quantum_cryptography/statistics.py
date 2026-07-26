"""Reproducible finite-photon binomial sampling for the Task 8 extension."""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Literal

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import (
    CLASSICAL_STREAM_SALT,
    QUANTUM_STREAM_SALT,
    UINT32_MAXIMUM,
    UINT32_MODULUS,
    WILSON_95_Z,
)
from task08_quantum_cryptography.models import mismatch_comparison


ModelName = Literal["classical", "quantum"]
MULBERRY32_INCREMENT = 0x6D2B79F5
UINT32_MASK = UINT32_MAXIMUM


def _integer(value: Integral, *, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return normalized


def _uint32(value: Integral, *, name: str = "seed") -> int:
    normalized = _integer(value, name=name)
    if normalized > UINT32_MAXIMUM:
        raise ValueError(f"{name} must be an unsigned 32-bit integer")
    return normalized


def _probability(value: Real, *, name: str = "probability") -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{name} must lie within [0, 1]")
    return normalized


def _real_scalar(value: Real, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


@dataclass(frozen=True)
class WilsonInterval:
    """Two-sided 95% Wilson score interval for one binomial fraction."""

    lower: float
    upper: float

    def __post_init__(self) -> None:
        lower = _probability(self.lower, name="lower")
        upper = _probability(self.upper, name="upper")
        if lower > upper:
            raise ValueError("Wilson interval lower bound must not exceed upper bound")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)


@dataclass(frozen=True)
class FinitePhotonSample:
    """One model's observed and theoretical finite-photon summaries."""

    model: ModelName
    stream_seed: int
    photon_pairs: int
    mismatches: int
    matches: int
    theoretical_probability: float
    observed_probability: float
    expected_mismatches: float
    standard_deviation_count: float
    standardized_residual: float | None
    wilson_interval: WilsonInterval

    def __post_init__(self) -> None:
        if self.model not in ("classical", "quantum"):
            raise ValueError("model must be 'classical' or 'quantum'")
        stream_seed = _uint32(self.stream_seed, name="stream_seed")
        photon_pairs = _integer(self.photon_pairs, name="photon_pairs", minimum=1)
        mismatches = _integer(self.mismatches, name="mismatches")
        matches = _integer(self.matches, name="matches")
        if mismatches + matches != photon_pairs:
            raise ValueError("mismatches and matches must sum to photon_pairs")
        if mismatches > photon_pairs or matches > photon_pairs:
            raise ValueError("sample count exceeds photon_pairs")
        theoretical = _probability(
            self.theoretical_probability,
            name="theoretical_probability",
        )
        observed = _probability(self.observed_probability, name="observed_probability")
        if not math.isclose(observed, mismatches / photon_pairs, abs_tol=1.0e-15):
            raise ValueError("observed_probability must equal mismatches/photon_pairs")
        expected = float(self.expected_mismatches)
        deviation = float(self.standard_deviation_count)
        if not math.isfinite(expected) or not 0.0 <= expected <= photon_pairs:
            raise ValueError("expected_mismatches is invalid")
        if not math.isfinite(deviation) or deviation < 0.0:
            raise ValueError("standard_deviation_count is invalid")
        residual = self.standardized_residual
        if residual is not None and not math.isfinite(float(residual)):
            raise ValueError("standardized_residual must be finite or None")
        if not isinstance(self.wilson_interval, WilsonInterval):
            raise TypeError("wilson_interval must be a WilsonInterval")
        object.__setattr__(self, "stream_seed", stream_seed)
        object.__setattr__(self, "photon_pairs", photon_pairs)
        object.__setattr__(self, "mismatches", mismatches)
        object.__setattr__(self, "matches", matches)
        object.__setattr__(self, "theoretical_probability", theoretical)
        object.__setattr__(self, "observed_probability", observed)
        object.__setattr__(self, "expected_mismatches", expected)
        object.__setattr__(self, "standard_deviation_count", deviation)
        if residual is not None:
            object.__setattr__(self, "standardized_residual", float(residual))


@dataclass(frozen=True)
class FinitePhotonExperiment:
    """Paired classical and quantum samples at one calculator setting."""

    theta_deg: float
    phi_deg: float
    photon_pairs: int
    seed: int
    classical: FinitePhotonSample
    quantum: FinitePhotonSample

    def __post_init__(self) -> None:
        theta = _real_scalar(self.theta_deg, name="theta_deg")
        phi = _real_scalar(self.phi_deg, name="phi_deg")
        photon_pairs = _integer(self.photon_pairs, name="photon_pairs", minimum=1)
        seed = _uint32(self.seed)
        if not isinstance(self.classical, FinitePhotonSample) or not isinstance(
            self.quantum,
            FinitePhotonSample,
        ):
            raise TypeError("classical and quantum must be FinitePhotonSample values")
        if self.classical.model != "classical" or self.quantum.model != "quantum":
            raise ValueError("sample models are assigned incorrectly")
        if (
            self.classical.photon_pairs != photon_pairs
            or self.quantum.photon_pairs != photon_pairs
        ):
            raise ValueError("both samples must use the experiment photon count")
        object.__setattr__(self, "theta_deg", theta)
        object.__setattr__(self, "phi_deg", phi)
        object.__setattr__(self, "photon_pairs", photon_pairs)
        object.__setattr__(self, "seed", seed)


def _mulberry32_stream(seed: Integral) -> Iterator[int]:
    state = _uint32(seed)
    while True:
        state = (state + MULBERRY32_INCREMENT) & UINT32_MASK
        value = state
        value = ((value ^ (value >> 15)) * (value | 1)) & UINT32_MASK
        value ^= (
            value + (((value ^ (value >> 7)) * (value | 61)) & UINT32_MASK)
        ) & UINT32_MASK
        value &= UINT32_MASK
        yield (value ^ (value >> 14)) & UINT32_MASK


def mulberry32_uint32_sequence(seed: Integral, count: Integral) -> tuple[int, ...]:
    """Return exact unsigned Mulberry32 outputs for cross-language validation."""

    normalized_count = _integer(count, name="count")
    stream = _mulberry32_stream(seed)
    return tuple(next(stream) for _ in range(normalized_count))


def mulberry32_uniform_sequence(seed: Integral, count: Integral) -> tuple[float, ...]:
    """Return deterministic uniform values in the half-open interval [0, 1)."""

    return tuple(
        value / UINT32_MODULUS
        for value in mulberry32_uint32_sequence(seed, count)
    )


def derived_stream_seed(seed: Integral, model: ModelName) -> int:
    """Derive one independent model stream from the displayed seed."""

    normalized = _uint32(seed)
    if model == "classical":
        salt = CLASSICAL_STREAM_SALT
    elif model == "quantum":
        salt = QUANTUM_STREAM_SALT
    else:
        raise ValueError("model must be 'classical' or 'quantum'")
    return (normalized ^ salt) & UINT32_MASK


def advance_seed(seed: Integral) -> int:
    """Advance an unsigned 32-bit seed with wraparound."""

    return (_uint32(seed) + 1) & UINT32_MASK


def binomial_mismatch_count(
    photon_pairs: Integral,
    probability: Real,
    seed: Integral,
) -> int:
    """Count exact Bernoulli mismatches using one deterministic stream."""

    count = _integer(photon_pairs, name="photon_pairs", minimum=1)
    threshold = _probability(probability)
    stream = _mulberry32_stream(seed)
    return sum(next(stream) / UINT32_MODULUS < threshold for _ in range(count))


def wilson_interval(
    mismatches: Integral,
    photon_pairs: Integral,
    *,
    z_value: Real = WILSON_95_Z,
) -> WilsonInterval:
    """Return a two-sided Wilson score interval for a binomial fraction."""

    count = _integer(photon_pairs, name="photon_pairs", minimum=1)
    observed_count = _integer(mismatches, name="mismatches")
    if observed_count > count:
        raise ValueError("mismatches must not exceed photon_pairs")
    z = _real_scalar(z_value, name="z_value")
    if z <= 0.0:
        raise ValueError("z_value must be greater than zero")
    observed = observed_count / count
    z_squared = z * z
    denominator = 1.0 + z_squared / count
    center = (observed + z_squared / (2.0 * count)) / denominator
    half_width = (
        z
        * math.sqrt(
            observed * (1.0 - observed) / count
            + z_squared / (4.0 * count * count)
        )
        / denominator
    )
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    if math.isclose(lower, 0.0, rel_tol=0.0, abs_tol=1.0e-15):
        lower = 0.0
    if math.isclose(upper, 1.0, rel_tol=0.0, abs_tol=1.0e-15):
        upper = 1.0
    return WilsonInterval(lower=lower, upper=upper)


def _model_sample(
    model: ModelName,
    theoretical_probability: float,
    photon_pairs: int,
    displayed_seed: int,
) -> FinitePhotonSample:
    stream_seed = derived_stream_seed(displayed_seed, model)
    mismatches = binomial_mismatch_count(
        photon_pairs,
        theoretical_probability,
        stream_seed,
    )
    expected = photon_pairs * theoretical_probability
    deviation = math.sqrt(
        photon_pairs
        * theoretical_probability
        * (1.0 - theoretical_probability)
    )
    residual = None if deviation == 0.0 else (mismatches - expected) / deviation
    return FinitePhotonSample(
        model=model,
        stream_seed=stream_seed,
        photon_pairs=photon_pairs,
        mismatches=mismatches,
        matches=photon_pairs - mismatches,
        theoretical_probability=theoretical_probability,
        observed_probability=mismatches / photon_pairs,
        expected_mismatches=expected,
        standard_deviation_count=deviation,
        standardized_residual=residual,
        wilson_interval=wilson_interval(mismatches, photon_pairs),
    )


def simulate_finite_photon_experiment(
    theta_deg: Real,
    phi_deg: Real,
    photon_pairs: Integral = DEFAULT_CONFIGURATION.simulation_default_photon_pairs,
    seed: Integral = DEFAULT_CONFIGURATION.simulation_default_seed,
    *,
    configuration: Task08Configuration = DEFAULT_CONFIGURATION,
) -> FinitePhotonExperiment:
    """Simulate reproducible classical and quantum finite-photon counts."""

    if not isinstance(configuration, Task08Configuration):
        raise TypeError("configuration must be a Task08Configuration")
    theta = _real_scalar(theta_deg, name="theta_deg")
    phi = _real_scalar(phi_deg, name="phi_deg")
    count = _integer(photon_pairs, name="photon_pairs", minimum=1)
    if not (
        configuration.simulation_minimum_photon_pairs
        <= count
        <= configuration.simulation_maximum_photon_pairs
    ):
        raise ValueError("photon_pairs lies outside the configured simulation range")
    displayed_seed = _uint32(seed)
    comparison = mismatch_comparison(theta, phi)
    classical_probability = float(comparison.classical_mismatch)
    quantum_probability = float(comparison.quantum_mismatch)
    return FinitePhotonExperiment(
        theta_deg=theta,
        phi_deg=phi,
        photon_pairs=count,
        seed=displayed_seed,
        classical=_model_sample(
            "classical",
            classical_probability,
            count,
            displayed_seed,
        ),
        quantum=_model_sample(
            "quantum",
            quantum_probability,
            count,
            displayed_seed,
        ),
    )


__all__ = [
    "FinitePhotonExperiment",
    "FinitePhotonSample",
    "MULBERRY32_INCREMENT",
    "WilsonInterval",
    "advance_seed",
    "binomial_mismatch_count",
    "derived_stream_seed",
    "mulberry32_uint32_sequence",
    "mulberry32_uniform_sequence",
    "simulate_finite_photon_experiment",
    "wilson_interval",
]
