import pytest

from pyoptionpricing import BlackScholesOption, MonteCarloEuropeanOption


def make_mc(spot=100, strike=100, maturity=1.0, rate=0.05,
            volatility=0.2, option_type="call", n_paths=100_000, seed=42):
    return MonteCarloEuropeanOption(
        spot, strike, maturity, rate, volatility, option_type,
        n_paths=n_paths, seed=seed,
    )


class TestPrices:
    @pytest.mark.parametrize("option_type", ["call", "put"])
    @pytest.mark.parametrize("spot,strike,maturity,rate,volatility", [
        (100, 100, 1.0, 0.05, 0.20),
        (120, 90, 0.5, 0.03, 0.35),
        (80, 110, 2.0, 0.01, 0.15),
    ])
    def test_within_three_standard_errors_of_black_scholes(
        self, spot, strike, maturity, rate, volatility, option_type
    ):
        mc = make_mc(spot, strike, maturity, rate, volatility, option_type)
        bs = BlackScholesOption(spot, strike, maturity, rate, volatility, option_type)
        assert abs(mc.price() - bs.price()) < 3 * mc.standard_error()

    def test_standard_error_is_positive_and_small(self):
        se = make_mc().standard_error()
        assert 0 < se < 0.1

    def test_standard_error_shrinks_with_more_paths(self):
        small = make_mc(n_paths=10_000).standard_error()
        large = make_mc(n_paths=160_000).standard_error()
        # SE scales as 1/sqrt(n): 16x the paths should give about 1/4 the SE.
        assert large / small == pytest.approx(0.25, rel=0.1)


class TestReproducibility:
    def test_same_seed_gives_same_price(self):
        assert make_mc(seed=7).price() == make_mc(seed=7).price()

    def test_different_seeds_give_different_prices(self):
        assert make_mc(seed=1).price() != make_mc(seed=2).price()

    def test_price_is_stable_across_calls(self):
        option = make_mc()
        assert option.price() == option.price()


class TestGreeks:
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_close_to_black_scholes(self, option_type):
        mc = make_mc(option_type=option_type).greeks()
        bs = BlackScholesOption(100, 100, 1.0, 0.05, 0.2, option_type).greeks()
        assert mc["delta"] == pytest.approx(bs["delta"], abs=0.01)
        assert mc["gamma"] == pytest.approx(bs["gamma"], abs=0.002)
        assert mc["vega"] == pytest.approx(bs["vega"], rel=0.03)
        assert mc["theta"] == pytest.approx(bs["theta"], abs=0.2)
        assert mc["rho"] == pytest.approx(bs["rho"], rel=0.03)

    def test_greek_keys_match_black_scholes(self):
        bs_keys = set(BlackScholesOption(100, 100, 1.0, 0.05, 0.2, "call").greeks())
        assert set(make_mc().greeks()) == bs_keys


class TestValidation:
    @pytest.mark.parametrize("n_paths", [0, 1])
    def test_too_few_paths_rejected(self, n_paths):
        with pytest.raises(ValueError):
            make_mc(n_paths=n_paths)

    def test_base_validation_still_applies(self):
        with pytest.raises(ValueError):
            make_mc(volatility=0)

    def test_properties(self):
        option = make_mc(n_paths=1234, seed=9)
        assert option.n_paths == 1234
        assert option.seed == 9
