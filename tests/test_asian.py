import math

import pytest

from pyoptionpricing import AsianOption, BlackScholesOption, PricingEngine


def make_asian(spot=100, strike=100, maturity=1.0, rate=0.05, volatility=0.2,
               option_type="call", n_paths=8_000, n_steps=40, seed=1):
    return AsianOption(
        spot, strike, maturity, rate, volatility, option_type,
        n_paths=n_paths, n_steps=n_steps, seed=seed,
    )


class TestPrice:
    def test_asian_call_is_at_most_the_european_call(self):
        asian = make_asian()
        european = BlackScholesOption(100, 100, 1.0, 0.05, 0.2, "call")
        assert asian.price() <= european.price()

    def test_price_is_positive_and_reproducible(self):
        first = make_asian()
        second = make_asian()
        assert first.price() > 0
        assert first.price() == second.price()
        assert first.price() == first.price()

    def test_standard_error_is_positive(self):
        assert make_asian().standard_error() > 0

    def test_put_payoff_is_not_the_call(self):
        assert make_asian(option_type="put").price() != make_asian().price()

    def test_engine_reports_standard_error(self):
        result = PricingEngine(make_asian(n_paths=1_000, n_steps=8)).run()
        assert result["model"] == "AsianOption"
        assert result["standard_error"] > 0


class TestGreeks:
    def test_keys_are_finite(self):
        greeks = make_asian(n_paths=2_000, n_steps=15).greeks()
        assert set(greeks) == {"delta", "gamma", "vega", "theta", "rho"}
        assert all(math.isfinite(value) for value in greeks.values())

    def test_call_delta_is_between_zero_and_one(self):
        delta = make_asian(n_paths=4_000, n_steps=20).greeks()["delta"]
        assert 0 < delta < 1


class TestValidation:
    @pytest.mark.parametrize("n_paths", [0, 1])
    def test_too_few_paths_rejected(self, n_paths):
        with pytest.raises(ValueError, match="n_paths"):
            make_asian(n_paths=n_paths)

    @pytest.mark.parametrize("n_steps", [0, 1])
    def test_too_few_steps_rejected(self, n_steps):
        with pytest.raises(ValueError, match="n_steps"):
            make_asian(n_steps=n_steps)

    def test_base_validation_still_applies(self):
        with pytest.raises(ValueError):
            make_asian(spot=0)
