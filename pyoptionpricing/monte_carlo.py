import math
import numpy as np
from .european import EuropeanOption

# S_T = S · exp[(r − σ²/2)·T + σ·√T·Z]
# price = e^(−rT) · mean(payoff), standard error = e^(−rT) · std(payoff) / √n


class MonteCarloEuropeanOption(EuropeanOption):
    """European option priced by simulating the terminal spot price."""

    def __init__(self, spot, strike, maturity, rate, volatility, option_type,
                 n_paths=100_000, seed=42):
        super().__init__(spot, strike, maturity, rate, volatility, option_type)
        if n_paths < 2:
            raise ValueError("n_paths must be at least 2.")
        self._n_paths = int(n_paths)
        self._seed = seed
        self._z = np.random.default_rng(seed).standard_normal(self._n_paths)

    @property
    def n_paths(self):
        return self._n_paths

    @property
    def seed(self):
        return self._seed

    def _discounted_payoffs(self, spot=None, maturity=None, rate=None, volatility=None):
        S = self.spot if spot is None else spot
        T = self.maturity if maturity is None else maturity
        r = self.rate if rate is None else rate
        sigma = self.volatility if volatility is None else volatility

        terminal_spot = S * np.exp((r - 0.5 * sigma**2) * T + sigma * math.sqrt(T) * self._z)
        if self.option_type == "call":
            payoff = np.maximum(terminal_spot - self.strike, 0)
        else:
            payoff = np.maximum(self.strike - terminal_spot, 0)
        return math.exp(-r * T) * payoff

    def price(self):
        return float(self._discounted_payoffs().mean())

    def standard_error(self):
        return float(self._discounted_payoffs().std(ddof=1) / math.sqrt(self.n_paths))

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
