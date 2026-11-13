import pytest

from pyoptionpricing import (
    OptionFactory,
    BlackScholesOption,
    BinomialEuropeanOption,
    BinomialAmericanOption,
    MonteCarloEuropeanOption,
)

PARAMS = dict(spot=100, strike=100, maturity=1.0, rate=0.05,
              volatility=0.2, option_type="call")


class TestDispatch:
    @pytest.mark.parametrize("model,style,expected", [
        ("black_scholes", "european", BlackScholesOption),
        ("binomial", "european", BinomialEuropeanOption),
        ("binomial", "american", BinomialAmericanOption),
        ("monte_carlo", "european", MonteCarloEuropeanOption),
    ])
    def test_returns_correct_class(self, model, style, expected):
        option = OptionFactory.create(model, style, **PARAMS)
        assert type(option) is expected

    @pytest.mark.parametrize("model", ["bs", "BS", "Black-Scholes", "black_scholes"])
    def test_black_scholes_aliases(self, model):
        option = OptionFactory.create(model, "European", **PARAMS)
        assert isinstance(option, BlackScholesOption)

    def test_crr_alias(self):
        option = OptionFactory.create("crr", "american", **PARAMS)
        assert isinstance(option, BinomialAmericanOption)


class TestPassThrough:
    def test_parameters_are_forwarded(self):
        option = OptionFactory.create("black_scholes", "european",
                                      spot=110, strike=95, maturity=0.5,
                                      rate=0.03, volatility=0.25,
                                      option_type="put")
        assert (option.spot, option.strike, option.maturity) == (110, 95, 0.5)
        assert (option.rate, option.volatility, option.option_type) == (0.03, 0.25, "put")

    def test_steps_forwarded_to_binomial(self):
        option = OptionFactory.create("binomial", "european", steps=37, **PARAMS)
        assert option.steps == 37

    def test_monte_carlo_kwargs_forwarded(self):
        option = OptionFactory.create("mc", "european", n_paths=500, seed=3, **PARAMS)
        assert (option.n_paths, option.seed) == (500, 3)

    def test_price_matches_direct_construction(self):
        via_factory = OptionFactory.create("black_scholes", "european", **PARAMS).price()
        direct = BlackScholesOption(**PARAMS).price()
        assert via_factory == pytest.approx(direct)


class TestErrors:
    def test_unknown_model(self):
        with pytest.raises(ValueError, match="Unknown model"):
            OptionFactory.create("heston", "european", **PARAMS)

    def test_unsupported_style(self):
        with pytest.raises(ValueError, match="does not support style"):
            OptionFactory.create("black_scholes", "american", **PARAMS)

    def test_monte_carlo_american_not_supported(self):
        with pytest.raises(ValueError, match="does not support style"):
            OptionFactory.create("monte_carlo", "american", **PARAMS)

    def test_unknown_style(self):
        with pytest.raises(ValueError):
            OptionFactory.create("binomial", "bermudan", **PARAMS)

    def test_input_validation_still_applies(self):
        with pytest.raises(ValueError):
            OptionFactory.create("binomial", "european",
                                 **{**PARAMS, "spot": -1})

    def test_irrelevant_kwarg_rejected(self):
        with pytest.raises(TypeError):
            OptionFactory.create("black_scholes", "european", steps=100, **PARAMS)


def test_available_lists_supported_pairs():
    assert ("binomial", "american") in OptionFactory.available()
    assert ("black_scholes", "american") not in OptionFactory.available()