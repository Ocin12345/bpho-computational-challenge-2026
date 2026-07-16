"""Authoritative Einstein-material inputs from the official Task 3 slide."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real


def _source_text(value: str, *, name: str) -> str:
    """Return a non-empty source label without silently changing it."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _positive_source_value(value: Real, *, name: str) -> float:
    """Return one finite, strictly positive source value as a float."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if normalized <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    return normalized


@dataclass(frozen=True)
class EinsteinMaterial:
    """One immutable row from the official seven-solid reference table."""

    name: str
    symbol: str
    debye_temperature_k: float
    official_frequency_1e13_hz: float

    def __post_init__(self) -> None:
        """Validate source identity and physical values at construction."""

        object.__setattr__(self, "name", _source_text(self.name, name="name"))
        object.__setattr__(
            self,
            "symbol",
            _source_text(self.symbol, name="symbol"),
        )
        object.__setattr__(
            self,
            "debye_temperature_k",
            _positive_source_value(
                self.debye_temperature_k,
                name="debye_temperature_k",
            ),
        )
        object.__setattr__(
            self,
            "official_frequency_1e13_hz",
            _positive_source_value(
                self.official_frequency_1e13_hz,
                name="official_frequency_1e13_hz",
            ),
        )


OFFICIAL_MATERIALS: tuple[EinsteinMaterial, ...] = (
    EinsteinMaterial("Gold", "Au", 170.0, 0.2855),
    EinsteinMaterial("Copper", "Cu", 343.5, 0.5769),
    EinsteinMaterial("Titanium", "Ti", 420.0, 0.7054),
    EinsteinMaterial("Aluminium", "Al", 428.0, 0.7188),
    EinsteinMaterial("Iron", "Fe", 470.0, 0.7893),
    EinsteinMaterial("Silicon", "Si", 645.0, 1.0832),
    EinsteinMaterial("Carbon", "C", 2230.0, 3.7451),
)


__all__ = ["EinsteinMaterial", "OFFICIAL_MATERIALS"]
