"""Abstract contracts cannot be constructed, and bad inputs fail clearly."""

import math

import pytest

from pyoptionpricing import (
    AmericanOption,
    EuropeanOption,
    Option,
    OptionInputError,
    PathDependentOption,
)
from pyoptionpricing.base import Greeks


class _PricedEuropean(EuropeanOption):
    def price(self) -> float:
        return 1.0

    def greeks(self) -> Greeks:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)


def _valid(**overrides):
    params = dict(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
    params.update(overrides)
    return params


@pytest.mark.parametrize(
    "cls",
    [Option, EuropeanOption, AmericanOption, PathDependentOption],
)
def test_abstract_options_cannot_be_instantiated(cls):
    with pytest.raises(TypeError):
        cls(**_valid())


def test_concrete_subclass_accepts_call_and_put():
    call = _PricedEuropean(**_valid(option_type=" Call "))
    put = _PricedEuropean(**_valid(option_type="PUT"))
    assert call.option_type == "call"
    assert put.option_type == "put"
    assert call.style == "european"


@pytest.mark.parametrize("name", ["S", "K", "T", "sigma"])
@pytest.mark.parametrize("bad", [0, -1, -0.01])
def test_market_inputs_must_be_positive(name, bad):
    with pytest.raises(OptionInputError, match="must be positive"):
        _PricedEuropean(**_valid(**{name: bad}))


@pytest.mark.parametrize("name", ["S", "K", "T", "r", "sigma", "q"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, "100", None, True, False])
def test_non_numeric_inputs_are_rejected(name, bad):
    with pytest.raises(OptionInputError, match="must be"):
        _PricedEuropean(**_valid(**{name: bad}))


@pytest.mark.parametrize("bad", ["straddle", "", " ", 1, None])
def test_option_type_must_be_call_or_put(bad):
    with pytest.raises(OptionInputError, match="option_type"):
        _PricedEuropean(**_valid(option_type=bad))


class _PricedAmerican(AmericanOption):
    def price(self) -> float:
        return 0.0

    def greeks(self) -> Greeks:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)


class _PricedPath(PathDependentOption):
    def price(self) -> float:
        return 0.0

    def greeks(self) -> Greeks:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)


def test_styles_and_repr():
    european = _PricedEuropean(**_valid())
    assert european.style == "european"
    assert _PricedAmerican(**_valid()).style == "american"
    assert _PricedPath(**_valid()).style == "path_dependent"
    assert repr(european) == (
        "_PricedEuropean(S=100.0, K=100.0, T=1.0, r=0.05, "
        "sigma=0.2, option_type='call', q=0.0)"
    )


def test_rates_may_be_negative_and_dividend_yield_defaults_to_zero():
    option = _PricedEuropean(**_valid(r=-0.01, q=-0.02))
    assert option.r == -0.01
    assert option.q == -0.02
    assert _PricedEuropean(**_valid()).q == 0.0
