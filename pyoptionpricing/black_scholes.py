"""Analytical Black-Scholes-Merton prices and Greeks."""

from __future__ import annotations

import math

from scipy.stats import norm

from pyoptionpricing.base import EuropeanOption, Greeks


class BlackScholesOption(EuropeanOption):
    """European option priced with the Black-Scholes-Merton closed form.

    ``q`` is a continuous dividend yield. Greeks are analytical.
    Vega is dV/dσ for σ in decimal form. Theta is dV/dt per year.
    """

    def price(self) -> float:
        d1, d2 = self._d1_d2()
        discount_r = math.exp(-self.r * self.T)
        discount_q = math.exp(-self.q * self.T)
        if self.option_type == "call":
            return self.S * discount_q * norm.cdf(d1) - self.K * discount_r * norm.cdf(d2)
        return self.K * discount_r * norm.cdf(-d2) - self.S * discount_q * norm.cdf(-d1)

    def greeks(self) -> Greeks:
        d1, d2 = self._d1_d2()
        sqrt_t = math.sqrt(self.T)
        discount_r = math.exp(-self.r * self.T)
        discount_q = math.exp(-self.q * self.T)
        pdf_d1 = norm.pdf(d1)

        gamma = discount_q * pdf_d1 / (self.S * self.sigma * sqrt_t)
        vega = self.S * discount_q * pdf_d1 * sqrt_t
        time_decay = -discount_q * self.S * pdf_d1 * self.sigma / (2.0 * sqrt_t)

        if self.option_type == "call":
            delta = discount_q * norm.cdf(d1)
            theta = time_decay - self.r * self.K * discount_r * norm.cdf(d2)
            theta += self.q * self.S * discount_q * norm.cdf(d1)
            rho = self.K * self.T * discount_r * norm.cdf(d2)
        else:
            delta = discount_q * (norm.cdf(d1) - 1.0)
            theta = time_decay + self.r * self.K * discount_r * norm.cdf(-d2)
            theta -= self.q * self.S * discount_q * norm.cdf(-d1)
            rho = -self.K * self.T * discount_r * norm.cdf(-d2)

        return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)

    def _d1_d2(self) -> tuple[float, float]:
        vol_sqrt_t = self.sigma * math.sqrt(self.T)
        d1 = (
            math.log(self.S / self.K)
            + (self.r - self.q + 0.5 * self.sigma * self.sigma) * self.T
        ) / vol_sqrt_t
        return d1, d1 - vol_sqrt_t
