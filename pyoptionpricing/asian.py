import math

from .path_dependent import _PathMonteCarlo
from .paths import vanilla_payoff


class AsianOption(_PathMonteCarlo):
    """Arithmetic-average Asian option priced by Monte Carlo.

    The average is the mean of the simulated spots. S0 is not included.
    A call pays max(average − K, 0) and a put pays max(K − average, 0).
    """

    def _discounted_payoffs(self, spot=None, maturity=None, rate=None, volatility=None):
        paths = self._paths(spot, maturity, rate, volatility)
        maturity = self.maturity if maturity is None else maturity
        rate = self.rate if rate is None else rate
        average = paths.mean(axis=1)
        payoff = vanilla_payoff(average, self.strike, self.option_type)
        return math.exp(-rate * maturity) * payoff
