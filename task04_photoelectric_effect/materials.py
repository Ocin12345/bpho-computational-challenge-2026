"""Authoritative metal work functions from the official Task 4 slide."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Iterable


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
class PhotoelectricMaterial:
    """One immutable row from the official nine-metal reference table."""

    name: str
    symbol: str
    work_function_ev: float

    def __post_init__(self) -> None:
        """Validate source identity and the supplied work function."""

        object.__setattr__(self, "name", _source_text(self.name, name="name"))
        object.__setattr__(
            self,
            "symbol",
            _source_text(self.symbol, name="symbol"),
        )
        object.__setattr__(
            self,
            "work_function_ev",
            _positive_source_value(
                self.work_function_ev,
                name="work_function_ev",
            ),
        )


def validate_material_collection(
    materials: Iterable[PhotoelectricMaterial],
) -> tuple[PhotoelectricMaterial, ...]:
    """Return an immutable non-empty collection with unique symbols."""

    try:
        normalized = tuple(materials)
    except TypeError as exc:
        raise TypeError("materials must be an iterable of material records") from exc
    if not normalized:
        raise ValueError("materials must contain at least one record")
    if any(not isinstance(item, PhotoelectricMaterial) for item in normalized):
        raise TypeError("materials must contain only PhotoelectricMaterial records")
    symbols = tuple(item.symbol for item in normalized)
    if len(set(symbols)) != len(symbols):
        raise ValueError("material symbols must be unique")
    return normalized


OFFICIAL_MATERIALS: tuple[PhotoelectricMaterial, ...] = (
    PhotoelectricMaterial("Silver", "Ag", 4.3),
    PhotoelectricMaterial("Aluminium", "Al", 4.3),
    PhotoelectricMaterial("Gold", "Au", 5.1),
    PhotoelectricMaterial("Copper", "Cu", 4.7),
    PhotoelectricMaterial("Tin", "Sn", 4.4),
    PhotoelectricMaterial("Lead", "Pb", 4.3),
    PhotoelectricMaterial("Tungsten", "W", 4.5),
    PhotoelectricMaterial("Nickel", "Ni", 4.6),
    PhotoelectricMaterial("Sodium", "Na", 2.4),
)

validate_material_collection(OFFICIAL_MATERIALS)


__all__ = [
    "OFFICIAL_MATERIALS",
    "PhotoelectricMaterial",
    "validate_material_collection",
]
