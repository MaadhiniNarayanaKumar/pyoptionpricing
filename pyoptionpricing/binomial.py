import math
import numpy as np
from .european import EuropeanOption
from .american import AmericanOption


def _crr_tree(spot, strike, maturity, rate, vol, option_type, steps, american):
    
    dt = maturity/steps
    u = math.exp(vol*math.sqrt(dt))
    d = 1/u
    p = (math.exp(rate * dt)- d) / (u -d)
    disc = math.exp(-rate *dt)

    j = np.arange(steps + 1)
    terminal_spot = spot * u**j * d**(steps - j)
    if option_type == "call":
        values = np.maximum(terminal_spot - strike, 0)
    else:
        values = np.maximum(strike - terminal_spot, 0)

    values_at_2 = values.copy() if steps == 2 else None
    values_at_1 = None
    value_at_0 = None
    for i in range(steps - 1, -1, -1):
        values = disc * (p * values[1:] + (1 - p) * values[:-1])
        if american:
            j = np.arange(i + 1)
            current_spot = spot * u**j * d**(i - j)
            if option_type == "call":
                intrinsic = np.maximum(current_spot - strike, 0)
            else:
                intrinsic = np.maximum(strike - current_spot, 0)
            values = np.maximum(values, intrinsic)

        if i == 2:
            values_at_2 = values.copy()
        elif i == 1:
            values_at_1 = values.copy()
        elif i == 0:
            value_at_0 = values.copy()

    return value_at_0[0], values_at_1, values_at_2, u, d


class _BinomialOption:
    def __init__(self, spot, strike, maturity, rate, volatility, option_type, steps=100):
        super().__init__(spot, strike, maturity, rate, volatility, option_type)
        if steps < 2:
            raise ValueError("steps must be at least 2.")
        self._steps = steps

    @property
    def steps(self):
        return self._steps

    def _tree(self, volatility=None, rate=None):
        return _crr_tree(
            self.spot,
            self.strike,
            self.maturity,
            self.rate if rate is None else rate,
            self.volatility if volatility is None else volatility,
            self.option_type,
            self.steps,
            self._american,
        )

    def price(self):
        return self._tree()[0]

    def greeks(self):
        price, values_at_1, values_at_2, u, d = self._tree()
        dt = self.maturity / self.steps
        delta = (values_at_1[1] - values_at_1[0]) / (self.spot * u - self.spot * d)
        delta_up = (values_at_2[2] - values_at_2[1]) / (self.spot * u**2 - self.spot)
        delta_down = (values_at_2[1] - values_at_2[0]) / (self.spot - self.spot * d**2)
        gamma = (delta_up - delta_down) / (0.5 * (self.spot * u**2 - self.spot * d**2))
        theta = (values_at_2[1] - price) / (2 * dt)

        h = 0.001
        vega_up = type(self)(
            self.spot, self.strike, self.maturity, self.rate,
            self.volatility + h, self.option_type, steps=self.steps,
        ).price()
        vega_down = type(self)(
            self.spot, self.strike, self.maturity, self.rate,
            self.volatility - h, self.option_type, steps=self.steps,
        ).price()
        rho_up = type(self)(
            self.spot, self.strike, self.maturity, self.rate + h,
            self.volatility, self.option_type, steps=self.steps,
        ).price()
        rho_down = type(self)(
            self.spot, self.strike, self.maturity, self.rate - h,
            self.volatility, self.option_type, steps=self.steps,
        ).price()
        vega = (vega_up - vega_down) / (2 * h)
        rho = (rho_up - rho_down) / (2 * h)

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
        }


class BinomialEuropeanOption(_BinomialOption, EuropeanOption):
    _american = False


class BinomialAmericanOption(_BinomialOption, AmericanOption):
    _american = True