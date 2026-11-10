"""Abstract option contracts and the shared Greek result."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyoptionpricing.validation import require_finite, require_option_type, require_positive


@dataclass(frozen=True)
class Greeks:
    """Sensitivities of the option price.

    Units are per 1.0 change in the input, not per percent.
    ``theta`` is the derivative with respect to calendar time, in price per year.
    """

    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

    def as_dict(self) -> dict[str, float]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "rho": self.rho,
        }


class Option(ABC):
    """A priced option contract.

    Subclasses implement ``price`` and ``greeks``. Construction validates the
    shared market and contract inputs so every model rejects the same bad data.
    """

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str,
        q: float = 0.0,
    ) -> None:
        self.S = require_positive("S", S)
        self.K = require_positive("K", K)
        self.T = require_positive("T", T)
        self.r = require_finite("r", r)
        self.sigma = require_positive("sigma", sigma)
        self.option_type = require_option_type(option_type)
        self.q = require_finite("q", q)

    @abstractmethod
    def price(self) -> float:
        """Present value of the option."""

    @abstractmethod
    def greeks(self) -> Greeks:
        """Delta, gamma, theta, vega, and rho."""

    def with_params(self, **overrides: float | str) -> Option:
        """Return a new contract of the same type with inputs replaced."""
        params: dict[str, float | str] = {
            "S": self.S,
            "K": self.K,
            "T": self.T,
            "r": self.r,
            "sigma": self.sigma,
            "option_type": self.option_type,
            "q": self.q,
        }
        params.update(overrides)
        return type(self)(**params)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"S={self.S}, K={self.K}, T={self.T}, r={self.r}, "
            f"sigma={self.sigma}, option_type={self.option_type!r}, q={self.q})"
        )


class EuropeanOption(Option):
    """European exercise: the payoff can be taken only at expiry."""

    @property
    def style(self) -> str:
        return "european"


class AmericanOption(Option):
    """American exercise: the holder may exercise at any time up to expiry."""

    @property
    def style(self) -> str:
        return "american"


class PathDependentOption(Option):
    """Payoff depends on the path of the underlying, not only on the terminal spot."""

    @property
    def style(self) -> str:
        return "path_dependent"

