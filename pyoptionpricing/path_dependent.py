import math
from abc import abstractmethod

from .base import Option
from .paths import simulate_paths, standard_normals, validate_simulation


class PathDependentOption(Option):
    """payoff depends on the full price path, not just the final price"""


class _PathMonteCarlo(PathDependentOption):
    """Shared seeded path simulation, price, standard error, and finite-difference Greeks."""

    def __init__(self, spot, strike, maturity, rate, volatility, option_type,
                 n_paths=20_000, n_steps=50, seed=42):
        super().__init__(spot, strike, maturity, rate, volatility, option_type)
        self._n_paths, self._n_steps = validate_simulation(n_paths, n_steps)
        self._seed = seed
        self._z = standard_normals(self._n_paths, self._n_steps, seed)

    @property
    def n_paths(self):
        return self._n_paths

    @property
    def n_steps(self):
        return self._n_steps

    @property
    def seed(self):
        return self._seed

    def _paths(self, spot=None, maturity=None, rate=None, volatility=None):
        return simulate_paths(
            self.spot if spot is None else spot,
            self.rate if rate is None else rate,
            self.volatility if volatility is None else volatility,
            self.maturity if maturity is None else maturity,
            self._z,
        )

    @abstractmethod
    def _discounted_payoffs(self, spot=None, maturity=None, rate=None, volatility=None):
        """Discounted payoff on each stored path, so bumps reuse the same normals."""

    def price(self):
        return float(self._discounted_payoffs().mean())

    def standard_error(self):
        payoffs = self._discounted_payoffs()
        return float(payoffs.std(ddof=1) / math.sqrt(self.n_paths))

    def greeks(self):
        # Bumped prices reuse the same normals so the noise mostly cancels.
        def p(**kwargs):
            return self._discounted_payoffs(**kwargs).mean()

        S, T, r, sigma = self.spot, self.maturity, self.rate, self.volatility
        dS = 0.01 * S
        h = 0.001
        dT = min(h, T / 2)

        up, mid, down = p(spot=S + dS), p(), p(spot=S - dS)
        delta = (up - down) / (2 * dS)
        gamma = (up - 2 * mid + down) / dS**2
        vega = (p(volatility=sigma + h) - p(volatility=sigma - h)) / (2 * h)
        rho = (p(rate=r + h) - p(rate=r - h)) / (2 * h)
        theta = -(p(maturity=T + dT) - p(maturity=T - dT)) / (2 * dT)

        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "vega": float(vega),
            "theta": float(theta),
            "rho": float(rho),
        }
