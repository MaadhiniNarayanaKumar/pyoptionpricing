import math

import pytest

from pyoptionpricing import (
    binomial_convergence,
    monte_carlo_convergence,
    payoff_curve,
    sample_paths,
    volatility_surface,
)

ARGS = (100, 100, 1.0, 0.05, 0.2, "call")


class TestConvergence:
    def test_binomial_error_shrinks(self):
        result = binomial_convergence(*ARGS, steps_list=[10, 1000])
        errors = [abs(p["price"] - result["black_scholes"]) for p in result["points"]]
        assert errors[1] < errors[0]
        assert errors[1] < 0.01

    def test_american_put_stays_above_european_reference(self):
        result = binomial_convergence(100, 100, 1.0, 0.05, 0.2, "put",
                                      steps_list=[200], american=True)
        assert result["points"][0]["price"] > result["black_scholes"]

    def test_monte_carlo_standard_error_shrinks(self):
        points = monte_carlo_convergence(*ARGS, path_counts=[1_000, 100_000])["points"]
        assert points[1]["standard_error"] < points[0]["standard_error"] / 5


class TestPayoffCurve:
    def test_call_shape(self):
        points = payoff_curve(100, "call", premium=10, spot_min=80, spot_max=120, n_points=5)
        assert [p["payoff"] for p in points] == [0, 0, 0, 10, 20]
        assert [p["profit"] for p in points] == [-10, -10, -10, 0, 10]

    def test_put_default_range(self):
        points = payoff_curve(100, "put", n_points=3)
        assert [p["spot"] for p in points] == [50, 100, 150]
        assert [p["payoff"] for p in points] == [50, 0, 0]

    @pytest.mark.parametrize("kwargs", [
        dict(strike=0, option_type="call"),
        dict(strike=100, option_type="banana"),
        dict(strike=100, option_type="call", n_points=1),
        dict(strike=100, option_type="call", spot_min=120, spot_max=80),
    ])
    def test_invalid_inputs(self, kwargs):
        with pytest.raises(ValueError):
            payoff_curve(**kwargs)


class TestSamplePaths:
    def test_shape_and_start(self):
        result = sample_paths(100, 1.0, 0.05, 0.2, n_paths=4, n_steps=10, seed=1)
        assert len(result["times"]) == 11
        assert result["times"][-1] == pytest.approx(1.0)
        assert all(len(path) == 11 and path[0] == 100 for path in result["paths"])

    def test_reproducible(self):
        a = sample_paths(100, 1.0, 0.05, 0.2, seed=3)
        b = sample_paths(100, 1.0, 0.05, 0.2, seed=3)
        assert a == b

    def test_invalid_inputs(self):
        with pytest.raises(ValueError):
            sample_paths(-1, 1.0, 0.05, 0.2)


class TestVolatilitySurface:
    def test_short_maturity_smile_is_steeper(self):
        surface = volatility_surface(100, 0.05, [80, 100, 120], [0.25, 4.0])
        def slope(smile):
            return smile[0]["implied_vol"] - smile[-1]["implied_vol"]
        assert slope(surface[0]["smile"]) > slope(surface[1]["smile"]) > 0

    def test_skew_scales_with_root_maturity(self):
        surface = volatility_surface(100, 0.05, [80], [0.25], skew=-0.1)
        expected = 0.2 - 0.1 / math.sqrt(0.25) * math.log(0.8)
        assert surface[0]["smile"][0]["implied_vol"] == pytest.approx(expected, abs=1e-6)

    @pytest.mark.parametrize("maturities", [[], [0], [-1]])
    def test_invalid_maturities(self, maturities):
        with pytest.raises(ValueError):
            volatility_surface(100, 0.05, [100], maturities)
