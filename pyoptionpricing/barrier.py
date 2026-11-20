import math

import numpy as np

from .path_dependent import _PathMonteCarlo
from .paths import vanilla_payoff


_BARRIER_TYPES = {
    "up-and-out": "up-and-out",
    "up-out": "up-and-out",
    "uo": "up-and-out",
    "up-and-in": "up-and-in",
    "up-in": "up-and-in",
    "ui": "up-and-in",
    "down-and-out": "down-and-out",
    "down-out": "down-and-out",
    "do": "down-and-out",
    "down-and-in": "down-and-in",
    "down-in": "down-and-in",
    "di": "down-and-in",
}


def normalize_barrier_type(barrier_type):
    if not isinstance(barrier_type, str):
        raise ValueError("barrier_type must be a string.")
    key = barrier_type.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in key:
        key = key.replace("--", "-")
    canonical = _BARRIER_TYPES.get(key)
    if canonical is None:
        raise ValueError(
            f"Unknown barrier type '{barrier_type}'. "
            "Expected up-and-out, up-and-in, down-and-out, or down-and-in."
        )
    return canonical


class BarrierOption(_PathMonteCarlo):
    """Single-barrier option priced by Monte Carlo with discrete monitoring.

    The barrier is checked at S0 and at every simulated spot. A knock-out pays
    the vanilla terminal payoff only if the barrier was not touched. A knock-in
    pays it only if the barrier was touched. On the same paths, knock-in plus
    knock-out equals the vanilla European payoff.
    """

    def __init__(self, spot, strike, maturity, rate, volatility, option_type,
                 barrier, barrier_type, n_paths=20_000, n_steps=50, seed=42):
        super().__init__(
            spot, strike, maturity, rate, volatility, option_type,
            n_paths=n_paths, n_steps=n_steps, seed=seed,
        )
        if barrier <= 0:
            raise ValueError("Barrier must be positive.")
        self._barrier = float(barrier)
        self._barrier_type = normalize_barrier_type(barrier_type)

    @property
    def barrier(self):
        return self._barrier

    @property
    def barrier_type(self):
        return self._barrier_type

    def _hit(self, paths, spot, barrier):
        direction = self.barrier_type.split("-")[0]
        if direction == "up":
            return (spot >= barrier) | np.any(paths >= barrier, axis=1)
        return (spot <= barrier) | np.any(paths <= barrier, axis=1)

    def _discounted_payoffs(self, spot=None, maturity=None, rate=None, volatility=None):
        paths = self._paths(spot, maturity, rate, volatility)
        spot = self.spot if spot is None else spot
        maturity = self.maturity if maturity is None else maturity
        rate = self.rate if rate is None else rate
        vanilla = vanilla_payoff(paths[:, -1], self.strike, self.option_type)
        hit = self._hit(paths, spot, self.barrier)
        knocked_out = self.barrier_type.endswith("out")
        payoff = np.where(hit, 0.0, vanilla) if knocked_out else np.where(hit, vanilla, 0.0)
        return math.exp(-rate * maturity) * payoff
