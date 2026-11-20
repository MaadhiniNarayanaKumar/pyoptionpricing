import math

from scipy.optimize import brentq

from .black_scholes import BlackScholesOption
from .factory import OptionFactory


_VOL_LOW = 0.001
_VOL_HIGH = 5.0


def implied_volatility(market_price, model, style, option_type,
                       spot, strike, maturity, rate, **kwargs):
    """Volatility that matches market_price, using the chosen model's price().

    Solves model_price(σ) − market_price = 0 with Brent's method on a
    bracket inside [0.001, 5]. The option is built through OptionFactory,
    so the same solver works for Black-Scholes, the binomial tree, and
    Monte Carlo. Volatilities whose model price is not finite are skipped.
    That happens when a binomial tree's risk-neutral probability leaves
    (0, 1). Monte Carlo needs a fixed seed in kwargs or the objective is noisy.
    """
    if "volatility" in kwargs:
        raise ValueError("Pass the market price, not a volatility. implied_volatility solves for it.")
    if market_price is None or not math.isfinite(market_price):
        raise ValueError("Market price must be a finite number.")
    if market_price < 0:
        raise ValueError("Market price must be non-negative.")

    def model_price(sigma):
        option = OptionFactory.create(
            model, style,
            spot, strike, maturity, rate, sigma, option_type,
            **kwargs,
        )
        return float(option.price())

    def usable_price(sigma):
        # A tiny volatility makes the CRR risk-neutral probability leave (0, 1),
        # and the tree price explodes. Skip those volatilities.
        try:
            price = model_price(sigma)
        except ValueError:
            return None
        if not math.isfinite(price) or price < 0 or price > max(spot, strike) * 2:
            return None
        return price

    sigmas = []
    sigma = _VOL_LOW
    while True:
        sigmas.append(sigma)
        if sigma >= _VOL_HIGH:
            break
        sigma = min(_VOL_HIGH, sigma * 2)

    priced = [(sigma, usable_price(sigma)) for sigma in sigmas]
    priced = [(sigma, price) for sigma, price in priced if price is not None]
    if len(priced) < 2:
        raise ValueError(
            "Model prices are not finite for volatilities between "
            f"{_VOL_LOW} and {_VOL_HIGH}."
        )

    for sigma, price in priced:
        if price == market_price:
            return sigma

    bracket = None
    for (left, left_price), (right, right_price) in zip(priced, priced[1:]):
        if (left_price - market_price) * (right_price - market_price) <= 0:
            bracket = (left, right)
            break
    if bracket is None:
        prices = [price for _, price in priced]
        raise ValueError(
            f"Market price {market_price} is outside the prices this model can produce "
            f"for volatilities between {priced[0][0]} and {priced[-1][0]} "
            f"(model prices {min(prices):.4f} to {max(prices):.4f}). "
            "That is outside no-arbitrage bounds for this contract."
        )

    return float(brentq(
        lambda sigma: model_price(sigma) - market_price, bracket[0], bracket[1]
    ))


def _skewed_volatility(strike, spot, atm_vol, skew):
    """σ(K) = σ_atm + skew · ln(K / S). Negative skew raises vol at low strikes."""
    sigma = atm_vol + skew * math.log(strike / spot)
    if sigma <= 0:
        raise ValueError(
            f"Skewed volatility at strike {strike} is {sigma}, which is not positive. "
            "Use strikes closer to the spot or a smaller skew."
        )
    return sigma


def volatility_smile(strikes, spot, maturity, rate, option_type="call",
                     model="black_scholes", style="european",
                     atm_vol=0.20, skew=-0.15, market_prices=None, **kwargs):
    """Implied volatility at each strike.

    When market_prices is omitted, prices are Black-Scholes prices from a
    skewed volatility, σ(K) = atm_vol + skew · ln(K / spot). Each price is
    then inverted with implied_volatility. The returned points are what a
    smile chart plots: strike on the x-axis and implied_vol on the y-axis.
    """
    strikes = [float(strike) for strike in strikes]
    if not strikes:
        raise ValueError("strikes must not be empty.")
    if any(strike <= 0 for strike in strikes):
        raise ValueError("Every strike must be positive.")

    if market_prices is None:
        market_prices = []
        for strike in strikes:
            sigma = _skewed_volatility(strike, spot, atm_vol, skew)
            price = BlackScholesOption(
                spot, strike, maturity, rate, sigma, option_type
            ).price()
            market_prices.append(price)
    else:
        market_prices = [float(price) for price in market_prices]
        if len(market_prices) != len(strikes):
            raise ValueError("market_prices must have one price per strike.")

    smile = []
    for strike, market_price in zip(strikes, market_prices):
        iv = implied_volatility(
            market_price, model, style, option_type,
            spot, strike, maturity, rate, **kwargs,
        )
        smile.append({
            "strike": strike,
            "market_price": market_price,
            "implied_vol": iv,
        })
    return smile
