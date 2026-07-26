"""Independent high-precision scalar references for Task 7 validation."""

from __future__ import annotations

from decimal import Decimal, localcontext

from task07_particle_in_box.constants import PLANCK_CONSTANT_J_S_STRING


PI_DECIMAL = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944"
)


def _positive_decimal(value: float, *, name: str) -> Decimal:
    normalized = Decimal(str(value))
    if not normalized.is_finite() or normalized <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return normalized


def reference_energy_j(
    quantum_number: int,
    particle_mass_kg: float,
    box_width_m: float,
) -> float:
    """Return E_n = n^2 h^2/(8ma^2) through a 60-digit Decimal path."""

    if isinstance(quantum_number, bool) or not isinstance(quantum_number, int):
        raise TypeError("quantum_number must be an integer")
    if quantum_number < 1:
        raise ValueError("quantum_number must be positive")
    mass = _positive_decimal(particle_mass_kg, name="particle_mass_kg")
    width = _positive_decimal(box_width_m, name="box_width_m")
    with localcontext() as context:
        context.prec = 60
        n = Decimal(quantum_number)
        h = Decimal(PLANCK_CONSTANT_J_S_STRING)
        return float(n * n * h * h / (Decimal(8) * mass * width * width))


def reference_expected_position_squared_m2(
    quantum_number: int,
    box_width_m: float,
) -> float:
    if isinstance(quantum_number, bool) or not isinstance(quantum_number, int):
        raise TypeError("quantum_number must be an integer")
    if quantum_number < 1:
        raise ValueError("quantum_number must be positive")
    width = _positive_decimal(box_width_m, name="box_width_m")
    with localcontext() as context:
        context.prec = 60
        n = Decimal(quantum_number)
        value = width * width * (
            Decimal(1) / Decimal(3)
            - Decimal(1) / (Decimal(2) * n * n * PI_DECIMAL * PI_DECIMAL)
        )
        return float(value)


def reference_uncertainty_product_over_hbar(quantum_number: int) -> float:
    if isinstance(quantum_number, bool) or not isinstance(quantum_number, int):
        raise TypeError("quantum_number must be an integer")
    if quantum_number < 1:
        raise ValueError("quantum_number must be positive")
    with localcontext() as context:
        context.prec = 60
        n = Decimal(quantum_number)
        value = n * n * PI_DECIMAL * PI_DECIMAL / Decimal(12) - Decimal("0.5")
        return float(value.sqrt())


__all__ = [
    "reference_energy_j",
    "reference_expected_position_squared_m2",
    "reference_uncertainty_product_over_hbar",
]
