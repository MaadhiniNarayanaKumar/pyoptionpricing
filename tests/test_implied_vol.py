import math

import pytest

from pyoptionpricing import (
    BlackScholesOption,
    BinomialEuropeanOption,
    MonteCarloEuropeanOption,
    OptionFactory,
    implied_volatility,
    volatility_smile,
)


PARAMS = dict(spot=100, strike=100, maturity=1.0, rate=0.05, option_type="call")


def _market(volatility, model="black_scholes", style="european", **kwargs):
    params = {**PARAMS, **kwargs, "volatility": volatility}
    return OptionFactory.create(model, style, **params).price()


class TestRoundTrip:
    def test_black_scholes_recovers_volatility(self):
        price = BlackScholesOption(volatility=0.2, **PARAMS).price()
        iv = implied_volatility(price, "black_scholes", "european", **PARAMS)
        assert iv == pytest.approx(0.2, abs=1e-6)

    def test_binomial_recovers_volatility(self):
        price = BinomialEuropeanOption(volatility=0.2, steps=50, **PARAMS).price()
        iv = implied_volatility(
            price, "binomial", "european", steps=50, **PARAMS
        )
        assert iv == pytest.approx(0.2, abs=1e-3)

    def test_monte_carlo_recovers_volatility(self):
        price = MonteCarloEuropeanOption(
            volatility=0.2, n_paths=4_000, seed=11, **PARAMS
        ).price()
        iv = implied_volatility(
            price, "monte_carlo", "european", n_paths=4_000, seed=11, **PARAMS
        )
        assert iv == pytest.approx(0.2, abs=1e-3)

    def test_put_round_trip(self):
        price = _market(0.3, option_type="put")
        iv = implied_volatility(
            price, "bs", "european",
            spot=100, strike=100, maturity=1.0, rate=0.05, option_type="put",
        )
        assert iv == pytest.approx(0.3, abs=1e-6)


class TestSmile:
    def test_flat_skew_is_recovered(self):
        strikes = [80, 90, 100, 110, 120]
        smile = volatility_smile(
            strikes, spot=100, maturity=1.0, rate=0.05, atm_vol=0.2, skew=0.0
        )
        assert [point["strike"] for point in smile] == strikes
        for point in smile:
            assert point["implied_vol"] == pytest.approx(0.2, abs=1e-6)
            assert point["market_price"] > 0

    def test_negative_skew_raises_low_strike_vol(self):
        smile = volatility_smile(
            [80, 100, 120], spot=100, maturity=1.0, rate=0.05,
            atm_vol=0.2, skew=-0.15,
        )
        low, atm, high = [point["implied_vol"] for point in smile]
        assert low == pytest.approx(0.2 - 0.15 * math.log(80 / 100), abs=1e-6)
        assert low > atm > high

    def test_supplied_market_prices_are_inverted(self):
        price = _market(0.25)
        smile = volatility_smile(
            [100], spot=100, maturity=1.0, rate=0.05,
            market_prices=[price], skew=0.4,
        )
        assert smile[0]["market_price"] == price
        assert smile[0]["implied_vol"] == pytest.approx(0.25, abs=1e-6)


class TestValidation:
    def test_negative_market_price_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            implied_volatility(-1, "black_scholes", "european", **PARAMS)

    def test_price_above_the_model_range_rejected(self):
        with pytest.raises(ValueError, match="no-arbitrage"):
            implied_volatility(500, "black_scholes", "european", **PARAMS)

    def test_price_below_intrinsic_rejected(self):
        with pytest.raises(ValueError, match="no-arbitrage"):
            implied_volatility(
                1.0, "black_scholes", "european",
                spot=100, strike=50, maturity=1.0, rate=0.0, option_type="call",
            )

    def test_passing_volatility_is_rejected(self):
        with pytest.raises(ValueError, match="solves for it"):
            implied_volatility(10, "black_scholes", "european", volatility=0.2, **PARAMS)

    def test_empty_strikes_rejected(self):
        with pytest.raises(ValueError, match="strikes"):
            volatility_smile([], spot=100, maturity=1.0, rate=0.05)

    def test_market_prices_must_match_strikes(self):
        with pytest.raises(ValueError, match="one price per strike"):
            volatility_smile(
                [90, 100], spot=100, maturity=1.0, rate=0.05, market_prices=[10]
            )

    def test_skew_that_drives_volatility_negative_rejected(self):
        with pytest.raises(ValueError, match="not positive"):
            volatility_smile(
                [500], spot=100, maturity=1.0, rate=0.05, atm_vol=0.05, skew=-0.5
            )
