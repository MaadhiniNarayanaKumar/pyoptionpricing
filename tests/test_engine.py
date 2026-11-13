import pytest

from pyoptionpricing import (
    BlackScholesOption,
    BinomialAmericanOption,
    MonteCarloEuropeanOption,
    OptionFactory,
    PricingEngine,
)

PARAMS = dict(spot=100, strike=100, maturity=1.0, rate=0.05,
              volatility=0.2, option_type="put")


@pytest.mark.parametrize("model,style", OptionFactory.available())
def test_engine_works_with_every_model(model, style):
    option = OptionFactory.create(model, style, **PARAMS)
    engine = PricingEngine(option)
    assert engine.price() == pytest.approx(option.price())
    assert engine.greeks() == pytest.approx(option.greeks())


def test_run_returns_price_and_greeks():
    result = PricingEngine(BlackScholesOption(**PARAMS)).run()
    assert result["model"] == "BlackScholesOption"
    assert result["price"] == pytest.approx(5.5735, abs=1e-3)
    assert set(result["greeks"]) == {"delta", "gamma", "vega", "theta", "rho"}
    assert "standard_error" not in result


def test_run_includes_standard_error_for_monte_carlo():
    result = PricingEngine(MonteCarloEuropeanOption(**PARAMS)).run()
    assert result["standard_error"] > 0


def test_option_property():
    option = BinomialAmericanOption(**PARAMS)
    assert PricingEngine(option).option is option


def test_rejects_non_option():
    with pytest.raises(TypeError):
        PricingEngine("not an option")
