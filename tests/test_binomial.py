import math

import pytest

from pyoptionpricing import (
    BinomialAmericanOption,
    BinomialEuropeanOption,
    BlackScholesOption,
)


def make_euro(spot=100, strike=100, maturity=1.0, rate=0.05,
              volatility=0.2, option_type="call", steps=500):
    return BinomialEuropeanOption(
        spot, strike, maturity, rate, volatility, option_type, steps=steps
    )


def make_amer(spot=100, strike=100, maturity=1.0, rate=0.05,
              volatility=0.2, option_type="call", steps=500):
    return BinomialAmericanOption(
        spot, strike, maturity, rate, volatility, option_type, steps=steps
    )


class TestPrices:
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_matches_black_scholes(self, option_type):
        tree_price = make_euro(option_type=option_type, steps=1000).price()
        bs_price = BlackScholesOption(
            100, 100, 1.0, 0.05, 0.2, option_type
        ).price()
        assert tree_price == pytest.approx(bs_price, abs=0.01)

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_converges_within_tolerance(self, option_type):
        tree_price = make_euro(option_type=option_type, steps=1000).price()
        bs_price = BlackScholesOption(
            100, 100, 1.0, 0.05, 0.2, option_type
        ).price()
        assert abs(tree_price - bs_price) < 0.01

    @pytest.mark.parametrize("spot,strike,maturity,rate,volatility", [
        (100, 100, 1.0, 0.05, 0.2),
        (120, 90, 0.5, 0.03, 0.35),
        (80, 110, 2.0, 0.01, 0.15),
    ])
    def test_european_put_call_parity(
        self, spot, strike, maturity, rate, volatility
    ):
        call = make_euro(
            spot, strike, maturity, rate, volatility, "call"
        ).price()
        put = make_euro(
            spot, strike, maturity, rate, volatility, "put"
        ).price()
        expected = spot - strike * math.exp(-rate * maturity)
        assert call - put == pytest.approx(expected, abs=1e-8)

    @pytest.mark.parametrize("spot,strike,maturity,rate,volatility", [
        (100, 100, 1.0, 0.05, 0.2),
        (100, 110, 1.0, 0.05, 0.2),
        (80, 100, 2.0, 0.03, 0.25),
    ])
    def test_american_put_is_at_least_european_put(
        self, spot, strike, maturity, rate, volatility
    ):
        american = make_amer(
            spot, strike, maturity, rate, volatility, "put"
        ).price()
        european = make_euro(
            spot, strike, maturity, rate, volatility, "put"
        ).price()
        assert american >= european

    def test_in_the_money_american_put_is_strictly_more_valuable(self):
        american = make_amer(spot=100, strike=110, rate=0.05, option_type="put")
        european = make_euro(spot=100, strike=110, rate=0.05, option_type="put")
        assert american.price() > european.price()

    def test_american_call_equals_european_call_without_dividends(self):
        american = make_amer(option_type="call").price()
        european = make_euro(option_type="call").price()
        assert american == pytest.approx(european, abs=1e-8)

    @pytest.mark.parametrize("option_type,spot,strike", [
        ("call", 200, 100),
        ("put", 50, 100),
    ])
    def test_american_price_is_at_least_intrinsic(
        self, option_type, spot, strike
    ):
        option = make_amer(
            spot=spot, strike=strike, option_type=option_type
        )
        intrinsic = (
            max(spot - strike, 0)
            if option_type == "call"
            else max(strike - spot, 0)
        )
        assert option.price() >= intrinsic


class TestGreeks:
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_matches_black_scholes(self, option_type):
        tree_greeks = make_euro(option_type=option_type).greeks()
        bs_greeks = BlackScholesOption(
            100, 100, 1.0, 0.05, 0.2, option_type
        ).greeks()
        assert tree_greeks["delta"] == pytest.approx(
            bs_greeks["delta"], abs=0.005
        )
        assert tree_greeks["gamma"] == pytest.approx(
            bs_greeks["gamma"], abs=0.001
        )
        assert tree_greeks["vega"] == pytest.approx(
            bs_greeks["vega"], rel=0.01
        )
        assert tree_greeks["rho"] == pytest.approx(
            bs_greeks["rho"], rel=0.01
        )
        assert tree_greeks["theta"] == pytest.approx(
            bs_greeks["theta"], abs=0.1
        )

    def test_greek_keys_match_black_scholes(self):
        tree_keys = set(make_euro().greeks())
        bs_keys = set(BlackScholesOption(
            100, 100, 1.0, 0.05, 0.2, "call"
        ).greeks())
        assert tree_keys == bs_keys


class TestValidation:
    @pytest.mark.parametrize("option_class", [
        BinomialEuropeanOption,
        BinomialAmericanOption,
    ])
    def test_steps_must_be_at_least_two(self, option_class):
        with pytest.raises(ValueError):
            option_class(100, 100, 1.0, 0.05, 0.2, "call", steps=1)

    @pytest.mark.parametrize("option_class", [
        BinomialEuropeanOption,
        BinomialAmericanOption,
    ])
    def test_steps_property(self, option_class):
        option = option_class(100, 100, 1.0, 0.05, 0.2, "call", steps=17)
        assert option.steps == 17
