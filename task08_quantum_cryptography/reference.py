"""Independent scalar double-angle references and exact Task 8 anchors."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real


def _finite_scalar(value: Real, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def reference_classical_mismatch(
    theta_deg: Real,
    phi_deg: Real,
) -> float:
    """Use (1-cos(2theta)cos(2phi))/2, not the production equation."""

    theta = math.radians(_finite_scalar(theta_deg, name="theta_deg"))
    phi = math.radians(_finite_scalar(phi_deg, name="phi_deg"))
    return (1.0 - math.cos(2.0 * theta) * math.cos(2.0 * phi)) / 2.0


def reference_quantum_mismatch(
    theta_deg: Real,
    phi_deg: Real,
) -> float:
    """Use (1-cos(2(phi-theta)))/2, not the production equation."""

    theta = math.radians(_finite_scalar(theta_deg, name="theta_deg"))
    phi = math.radians(_finite_scalar(phi_deg, name="phi_deg"))
    return (1.0 - math.cos(2.0 * (phi - theta))) / 2.0


@dataclass(frozen=True)
class ExactReferenceCase:
    """One named angle pair with exact rational mismatch probabilities."""

    identifier: str
    label: str
    theta_deg: int
    phi_deg: int
    classical_mismatch: Fraction
    quantum_mismatch: Fraction

    def __post_init__(self) -> None:
        for field_name in ("identifier", "label"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty text")
        if not self.identifier.replace("_", "").isalnum():
            raise ValueError("identifier must be portable identifier text")
        for field_name in ("theta_deg", "phi_deg"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
        for field_name in ("classical_mismatch", "quantum_mismatch"):
            value = getattr(self, field_name)
            if not isinstance(value, Fraction):
                raise TypeError(f"{field_name} must be a Fraction")
            if not Fraction(0, 1) <= value <= Fraction(1, 1):
                raise ValueError(f"{field_name} must lie within [0, 1]")

    @property
    def signed_difference(self) -> Fraction:
        return self.quantum_mismatch - self.classical_mismatch


REFERENCE_CASES = (
    ExactReferenceCase(
        "official_example",
        "Official BPhO example",
        -30,
        30,
        Fraction(3, 8),
        Fraction(3, 4),
    ),
    ExactReferenceCase(
        "common_reference_axis",
        "Common reference axis",
        0,
        0,
        Fraction(0, 1),
        Fraction(0, 1),
    ),
    ExactReferenceCase(
        "aligned_diagonal_axes",
        "Aligned diagonal axes",
        45,
        45,
        Fraction(1, 2),
        Fraction(0, 1),
    ),
    ExactReferenceCase(
        "maximum_positive_contrast",
        "Maximum positive contrast",
        -45,
        45,
        Fraction(1, 2),
        Fraction(1, 1),
    ),
    ExactReferenceCase(
        "perpendicular_reference_axes",
        "Perpendicular reference axes",
        0,
        90,
        Fraction(1, 1),
        Fraction(1, 1),
    ),
)


__all__ = [
    "ExactReferenceCase",
    "REFERENCE_CASES",
    "reference_classical_mismatch",
    "reference_quantum_mismatch",
]
