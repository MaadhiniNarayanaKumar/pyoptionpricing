"""Shared checks for contract inputs."""

from __future__ import annotations

import math

from pyoptionpricing.exceptions import OptionInputError


def require_finite(name: str, value: object) -> float:
    """Return ``value`` as a finite float.

    Bools are rejected because ``bool`` is a subclass of ``int``.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OptionInputError(f"{name} must be a real number, got {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise OptionInputError(f"{name} must be finite, got {value!r}.")
    return number


def require_positive(name: str, value: object) -> float:
    """Return ``value`` as a finite float that is strictly greater than zero."""
    number = require_finite(name, value)
    if number <= 0:
        raise OptionInputError(f"{name} must be positive, got {number}.")
    return number


def require_option_type(value: object) -> str:
    """Normalize an option type to ``'call'`` or ``'put'``."""
    if not isinstance(value, str):
        raise OptionInputError(
            f"option_type must be 'call' or 'put', got {value!r}."
        )
    normalized = value.strip().lower()
    if normalized not in {"call", "put"}:
        raise OptionInputError(
            f"option_type must be 'call' or 'put', got {value!r}."
        )
    return normalized
