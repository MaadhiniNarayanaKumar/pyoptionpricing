import math

import numpy as np


def validate_simulation(n_paths, n_steps):
    """Shared checks for Monte Carlo path counts."""
    if n_paths < 2:
        raise ValueError("n_paths must be at least 2.")
    if n_steps < 2:
        raise ValueError("n_steps must be at least 2.")
    return int(n_paths), int(n_steps)


def standard_normals(n_paths, n_steps, seed):
    """Seeded standard normals with shape (n_paths, n_steps)."""
    n_paths, n_steps = validate_simulation(n_paths, n_steps)
    return np.random.default_rng(seed).standard_normal((n_paths, n_steps))


def simulate_paths(spot, rate, volatility, maturity, z):
    """Discrete geometric Brownian motion. Each row is one path and omits S0.

    S grows by exp[(r − σ²/2) dt + σ√dt · Z] at every step.
    """
    n_steps = z.shape[1]
    dt = maturity / n_steps
    increments = (rate - 0.5 * volatility**2) * dt + volatility * math.sqrt(dt) * z
    return spot * np.exp(np.cumsum(increments, axis=1))


def vanilla_payoff(level, strike, option_type):
    """Call or put payoff on a price level (a terminal spot or an average)."""
    if option_type == "call":
        return np.maximum(level - strike, 0.0)
    return np.maximum(strike - level, 0.0)
