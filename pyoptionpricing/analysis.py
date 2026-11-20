import math

import numpy as np

from .black_scholes import BlackScholesOption
from .binomial import BinomialAmericanOption, BinomialEuropeanOption
from .implied_vol import volatility_smile
from .monte_carlo import MonteCarloEuropeanOption
from .paths import simulate_paths, standard_normals, vanilla_payoff

DEFAULT_STEPS = (5, 10, 20, 50, 100, 200, 500, 1000)
DEFAULT_PATH_COUNTS = (500, 1_000, 5_000, 10_000, 50_000, 100_000)


def binomial_convergence(spot, strike, maturity, rate, volatility, option_type,
                         steps_list=DEFAULT_STEPS, american=False):
    """Binomial price for each tree depth, next to the Black-Scholes price.

    For an American option the Black-Scholes value is the European reference,
    so the gap that remains is the early-exercise premium.
    """
    tree_cls = BinomialAmericanOption if american else BinomialEuropeanOption
    reference = BlackScholesOption(
        spot, strike, maturity, rate, volatility, option_type
    ).price()
    points = []
    for steps in steps_list:
        price = tree_cls(
            spot, strike, maturity, rate, volatility, option_type, steps=steps
        ).price()
        points.append({"steps": int(steps), "price": float(price)})
    return {"black_scholes": float(reference), "points": points}


def monte_carlo_convergence(spot, strike, maturity, rate, volatility, option_type,
                            path_counts=DEFAULT_PATH_COUNTS, seed=42):
    """Monte Carlo price and standard error for each path count."""
    reference = BlackScholesOption(
        spot, strike, maturity, rate, volatility, option_type
    ).price()
    points = []
    for n_paths in path_counts:
        option = MonteCarloEuropeanOption(
            spot, strike, maturity, rate, volatility, option_type,
            n_paths=n_paths, seed=seed,
        )
        points.append({
            "n_paths": int(n_paths),
            "price": option.price(),
            "standard_error": option.standard_error(),
        })
    return {"black_scholes": float(reference), "points": points}


def payoff_curve(strike, option_type, premium=0.0, spot_min=None, spot_max=None,
                 n_points=101):
    """Payoff and profit at maturity across a range of terminal spot prices."""
    if strike <= 0:
        raise ValueError("Strike price must be positive.")
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be either 'call' or 'put'.")
    if n_points < 2:
        raise ValueError("n_points must be at least 2.")
    spot_min = 0.5 * strike if spot_min is None else spot_min
    spot_max = 1.5 * strike if spot_max is None else spot_max
    if not 0 <= spot_min < spot_max:
        raise ValueError("Need 0 <= spot_min < spot_max.")

    spots = np.linspace(spot_min, spot_max, n_points)
    payoffs = vanilla_payoff(spots, strike, option_type)
    return [
        {"spot": float(s), "payoff": float(p), "profit": float(p - premium)}
        for s, p in zip(spots, payoffs)
    ]


def sample_paths(spot, maturity, rate, volatility, n_paths=20, n_steps=100, seed=42):
    """A few simulated GBM paths for plotting. Each path starts at the spot."""
    if spot <= 0 or maturity <= 0 or volatility <= 0:
        raise ValueError("spot, maturity and volatility must be positive.")
    z = standard_normals(n_paths, n_steps, seed)
    paths = simulate_paths(spot, rate, volatility, maturity, z)
    paths = np.hstack([np.full((paths.shape[0], 1), float(spot)), paths])
    times = np.linspace(0.0, maturity, n_steps + 1)
    return {"times": times.tolist(), "paths": paths.tolist()}


def volatility_surface(spot, rate, strikes, maturities, option_type="call",
                       model="black_scholes", style="european",
                       atm_vol=0.20, skew=-0.15, **kwargs):
    """Implied-volatility smiles for several maturities.

    The synthetic skew at maturity T is skew / √T, so short-dated smiles are
    steeper than long-dated ones, as in equity markets.
    """
    maturities = [float(t) for t in maturities]
    if not maturities:
        raise ValueError("maturities must not be empty.")
    if any(t <= 0 for t in maturities):
        raise ValueError("Every maturity must be positive.")

    return [
        {
            "maturity": t,
            "smile": volatility_smile(
                strikes, spot, t, rate, option_type=option_type,
                model=model, style=style, atm_vol=atm_vol,
                skew=skew / math.sqrt(t), **kwargs,
            ),
        }
        for t in maturities
    ]
