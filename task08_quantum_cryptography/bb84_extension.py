"""Finite-key BB84 protocol simulator for BPhO Task 8.

The official mismatch calculator is preserved.  This extension follows actual
prepare-and-measure BB84 stages: random bases, optional intercept--resend Eve,
loss and dark counts, sifting, parameter estimation, an explicitly idealized
error-reconciliation leakage budget, and Toeplitz-hash privacy amplification.

This is an auditable educational simulator, not a composable security proof.
In particular reconciliation is modelled as perfect correction plus a declared
leakage cost; it does not implement an industrial Cascade or LDPC transcript.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.signal import fftconvolve


BitArray = NDArray[np.uint8]


@dataclass(frozen=True)
class BB84Configuration:
    photon_count: int = 50_000
    eve_intercept_probability: float = 0.0
    channel_bit_flip_probability: float = 0.0
    detection_efficiency: float = 1.0
    dark_count_probability: float = 0.0
    parameter_estimation_fraction: float = 0.20
    reconciliation_efficiency: float = 1.15
    qber_abort_threshold: float = 0.11
    security_failure_probability: float = 1.0e-6
    security_margin_bits: int = 64
    seed: int = 2026

    def __post_init__(self) -> None:
        if isinstance(self.photon_count, bool) or int(self.photon_count) < 100:
            raise ValueError("photon_count must be an integer of at least 100")
        object.__setattr__(self, "photon_count", int(self.photon_count))
        for name in (
            "eve_intercept_probability",
            "channel_bit_flip_probability",
            "detection_efficiency",
            "dark_count_probability",
            "parameter_estimation_fraction",
            "qber_abort_threshold",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
            object.__setattr__(self, name, value)
        if not 0.0 < self.parameter_estimation_fraction < 1.0:
            raise ValueError("parameter_estimation_fraction must lie in (0,1)")
        if self.reconciliation_efficiency < 1.0:
            raise ValueError("reconciliation_efficiency must be at least one")
        if not 0.0 < self.security_failure_probability < 1.0:
            raise ValueError("security_failure_probability must lie in (0,1)")
        if isinstance(self.security_margin_bits, bool) or int(self.security_margin_bits) < 0:
            raise ValueError("security_margin_bits must be a non-negative integer")
        object.__setattr__(self, "security_margin_bits", int(self.security_margin_bits))
        if isinstance(self.seed, bool) or int(self.seed) < 0:
            raise ValueError("seed must be a non-negative integer")
        object.__setattr__(self, "seed", int(self.seed))


@dataclass(frozen=True)
class BB84Result:
    """Protocol transcript summary and final privacy-amplified keys."""

    transmitted_photons: int
    detected_photons: int
    sifted_bits: int
    test_bits: int
    reconciled_bits: int
    intercepted_photons: int
    qber_test: float
    qber_reconciled_raw: float
    phase_error_upper_bound: float
    reconciliation_leakage_bits: int
    secret_key_bits: int
    eve_known_fraction_before_privacy_amplification: float
    aborted: bool
    abort_reason: str
    alice_secret_key: BitArray
    bob_secret_key: BitArray
    privacy_seed: BitArray


def binary_entropy(probability: float) -> float:
    """Return binary Shannon entropy in bits."""

    probability = float(probability)
    if not np.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0,1]")
    if probability in {0.0, 1.0}:
        return 0.0
    return float(
        -probability * np.log2(probability)
        - (1.0 - probability) * np.log2(1.0 - probability)
    )


def toeplitz_hash(input_bits: BitArray, output_length: int, seed_bits: BitArray) -> BitArray:
    """Apply a binary universal-2 Toeplitz hash using FFT convolution."""

    bits = np.asarray(input_bits, dtype=np.uint8)
    seed = np.asarray(seed_bits, dtype=np.uint8)
    if bits.ndim != 1 or np.any(bits > 1):
        raise ValueError("input_bits must be a one-dimensional binary array")
    if isinstance(output_length, bool) or not 0 <= int(output_length) <= len(bits):
        raise ValueError("output_length must be between zero and input length")
    length = int(output_length)
    required_seed = len(bits) + length - 1
    if seed.ndim != 1 or len(seed) != required_seed or np.any(seed > 1):
        raise ValueError("seed_bits has the wrong binary Toeplitz length")
    if length == 0:
        return np.empty(0, dtype=np.uint8)
    convolution = fftconvolve(
        bits.astype(np.float64), seed.astype(np.float64), mode="full"
    )
    integers = np.rint(convolution).astype(np.int64)
    return np.asarray(integers[len(bits) - 1 : len(bits) - 1 + length] % 2, dtype=np.uint8)


def _readonly(bits: BitArray) -> BitArray:
    result = np.asarray(bits, dtype=np.uint8)
    result.setflags(write=False)
    return result


def simulate_bb84(configuration: BB84Configuration = BB84Configuration()) -> BB84Result:
    """Run one seeded BB84 protocol transcript."""

    if not isinstance(configuration, BB84Configuration):
        raise TypeError("configuration must be a BB84Configuration")
    rng = np.random.default_rng(configuration.seed)
    count = configuration.photon_count
    alice_bits = rng.integers(0, 2, count, dtype=np.uint8)
    alice_bases = rng.integers(0, 2, count, dtype=np.uint8)

    intercepted = rng.random(count) < configuration.eve_intercept_probability
    eve_bases = rng.integers(0, 2, count, dtype=np.uint8)
    eve_random = rng.integers(0, 2, count, dtype=np.uint8)
    eve_outcomes = np.where(eve_bases == alice_bases, alice_bits, eve_random).astype(np.uint8)
    signal_bases = np.where(intercepted, eve_bases, alice_bases).astype(np.uint8)
    signal_bits = np.where(intercepted, eve_outcomes, alice_bits).astype(np.uint8)

    photon_click = rng.random(count) < configuration.detection_efficiency
    dark_click = (~photon_click) & (
        rng.random(count) < configuration.dark_count_probability
    )
    detected = photon_click | dark_click
    bob_bases = rng.integers(0, 2, count, dtype=np.uint8)
    bob_random = rng.integers(0, 2, count, dtype=np.uint8)
    bob_bits = np.where(bob_bases == signal_bases, signal_bits, bob_random).astype(np.uint8)
    bob_bits[dark_click] = rng.integers(0, 2, int(np.count_nonzero(dark_click)), dtype=np.uint8)
    channel_flips = rng.random(count) < configuration.channel_bit_flip_probability
    bob_bits[photon_click & channel_flips] ^= np.uint8(1)

    sift_mask = detected & (alice_bases == bob_bases)
    sift_indices = np.flatnonzero(sift_mask)
    sifted_count = int(len(sift_indices))
    empty = _readonly(np.empty(0, dtype=np.uint8))
    if sifted_count < 20:
        return BB84Result(
            transmitted_photons=count,
            detected_photons=int(np.count_nonzero(detected)),
            sifted_bits=sifted_count,
            test_bits=0,
            reconciled_bits=0,
            intercepted_photons=int(np.count_nonzero(intercepted)),
            qber_test=1.0,
            qber_reconciled_raw=1.0,
            phase_error_upper_bound=0.5,
            reconciliation_leakage_bits=0,
            secret_key_bits=0,
            eve_known_fraction_before_privacy_amplification=0.0,
            aborted=True,
            abort_reason="too few sifted detections",
            alice_secret_key=empty,
            bob_secret_key=empty,
            privacy_seed=empty,
        )

    test_count = max(1, int(round(configuration.parameter_estimation_fraction * sifted_count)))
    test_locations = np.sort(rng.choice(sifted_count, size=test_count, replace=False))
    test_mask_local = np.zeros(sifted_count, dtype=bool)
    test_mask_local[test_locations] = True
    key_indices = sift_indices[~test_mask_local]
    test_indices = sift_indices[test_mask_local]
    qber_test = float(np.mean(alice_bits[test_indices] != bob_bits[test_indices]))
    qber_raw = float(np.mean(alice_bits[key_indices] != bob_bits[key_indices]))

    phase_margin = np.sqrt(
        np.log(1.0 / configuration.security_failure_probability)
        / (2.0 * test_count)
    )
    phase_upper = min(0.5, qber_test + float(phase_margin))
    leakage = int(
        np.ceil(
            configuration.reconciliation_efficiency
            * len(key_indices)
            * binary_entropy(min(qber_test, 0.5))
        )
    )
    privacy_cost = int(np.ceil(len(key_indices) * binary_entropy(phase_upper)))
    secret_length = max(
        0,
        len(key_indices)
        - leakage
        - privacy_cost
        - configuration.security_margin_bits,
    )
    abort_reason = ""
    aborted = False
    if qber_test > configuration.qber_abort_threshold:
        aborted = True
        abort_reason = "parameter-estimation QBER exceeds threshold"
        secret_length = 0
    elif secret_length == 0:
        aborted = True
        abort_reason = "finite-key privacy bound leaves no secret bits"

    eve_knows = intercepted[key_indices] & (eve_bases[key_indices] == alice_bases[key_indices])
    eve_known_fraction = float(np.mean(eve_knows)) if len(key_indices) else 0.0
    if secret_length:
        # Ideal reconciliation makes Bob's corrected string match Alice's while
        # the publicly leaked syndrome length is paid above.
        corrected_alice = alice_bits[key_indices]
        corrected_bob = corrected_alice.copy()
        privacy_seed = rng.integers(
            0, 2, len(corrected_alice) + secret_length - 1, dtype=np.uint8
        )
        alice_secret = toeplitz_hash(corrected_alice, secret_length, privacy_seed)
        bob_secret = toeplitz_hash(corrected_bob, secret_length, privacy_seed)
    else:
        privacy_seed = np.empty(0, dtype=np.uint8)
        alice_secret = np.empty(0, dtype=np.uint8)
        bob_secret = np.empty(0, dtype=np.uint8)
    return BB84Result(
        transmitted_photons=count,
        detected_photons=int(np.count_nonzero(detected)),
        sifted_bits=sifted_count,
        test_bits=test_count,
        reconciled_bits=int(len(key_indices)),
        intercepted_photons=int(np.count_nonzero(intercepted)),
        qber_test=qber_test,
        qber_reconciled_raw=qber_raw,
        phase_error_upper_bound=phase_upper,
        reconciliation_leakage_bits=leakage,
        secret_key_bits=secret_length,
        eve_known_fraction_before_privacy_amplification=eve_known_fraction,
        aborted=aborted,
        abort_reason=abort_reason,
        alice_secret_key=_readonly(alice_secret),
        bob_secret_key=_readonly(bob_secret),
        privacy_seed=_readonly(privacy_seed),
    )


__all__ = [
    "BB84Configuration",
    "BB84Result",
    "binary_entropy",
    "simulate_bb84",
    "toeplitz_hash",
]
