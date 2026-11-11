import math
from scipy.stats import norm
from .european import EuropeanOption

#_d1(self): d1 = [ ln(S/K) + (r + σ²/2) · T ] / ( σ · √T )
# _d2(self): d2 = d1 − σ · √T

class BlackScholesOption(EuropeanOption):
    """Class for Black-Scholes option pricing model."""
    
    def _d1(self):
        """Calculate d1 for the Black-Scholes formula."""
        S = self.spot
        K = self.strike
        r = self.rate
        sigma = self.volatility
        T = self.maturity
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    def _d2(self):
        """Calculate d2 for the Black-Scholes formula."""
        return self._d1() - self.volatility * math.sqrt(self.maturity)

    def price(self):
        #Call: S · N(d1) − K · e^(−rT) · N(d2)
        # Put: K · e^(−rT) · N(−d2) − S · N(−d1)
        d1 = self._d1()
        d2 = self._d2()
        call_price = self.spot * norm.cdf(d1) - self.strike * math.exp(-self.rate * self.maturity) * norm.cdf(d2)
        put_price = self.strike * math.exp(-self.rate * self.maturity) * norm.cdf(-d2) - self.spot * norm.cdf(-d1)
        return call_price if self.option_type == "call" else put_price

    def greeks(self):
        
        # Delta	N(d1)	N(d1) − 1
        # Gamma	φ(d1) / (S · σ · √T)	same as call
        # Vega	S · φ(d1) · √T	same as call
        # Theta	−S · φ(d1) · σ / (2√T) − r · K · e^(−rT) · N(d2)	−S · φ(d1) · σ / (2√T) + r · K · e^(−rT) · N(−d2)
        # Rho	K · T · e^(−rT) · N(d2)	−K · T · e^(−rT) · N(−d2)
        d1 = self._d1()
        d2 = self._d2()
        delta = norm.cdf(d1) if self.option_type == "call" else norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (self.spot * self.volatility * math.sqrt(self.maturity))
        vega = self.spot * norm.pdf(d1) * math.sqrt(self.maturity)
        theta = (-self.spot * norm.pdf(d1) * self.volatility / (2 * math.sqrt(self.maturity)) - self.rate * self.strike * math.exp(-self.rate * self.maturity) * norm.cdf(d2)) if self.option_type == "call" else (-self.spot * norm.pdf(d1) * self.volatility / (2 * math.sqrt(self.maturity)) + self.rate * self.strike * math.exp(-self.rate * self.maturity) * norm.cdf(-d2))
        rho = self.strike * self.maturity * math.exp(-self.rate * self.maturity) * norm.cdf(d2) if self.option_type == "call" else -self.strike * self.maturity * math.exp(-self.rate * self.maturity) * norm.cdf(-d2)

        return {
            "delta": delta,
            "gamma": gamma,
            "vega": vega,
            "theta": theta,
            "rho": rho
        }
