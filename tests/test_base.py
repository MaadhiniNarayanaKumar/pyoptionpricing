import pytest

from pyoptionpricing import (
    Option,
    EuropeanOption,
    AmericanOption,
    PathDependentOption,
)


class DummyOption(Option):
    """Minimal concrete subclass, only used so we can test Option's constructor."""

    def price(self):
        return 0.0

    def greeks(self):
        return {}


def make_dummy(**overrides):
    """Build a valid DummyOption, changing only the fields you pass in."""
    params = dict(
        spot=100, strike=100, maturity=1.0,
        rate=0.05, volatility=0.2, option_type="call",
    )
    params.update(overrides)
    return DummyOption(**params)


class TestAbstractClasses:
    @pytest.mark.parametrize(
        "cls", [Option, EuropeanOption, AmericanOption, PathDependentOption]
    )
    def test_cannot_instantiate(self, cls):
        with pytest.raises(TypeError):
            cls(100, 100, 1.0, 0.05, 0.2, "call")


class TestConstruction:
    def test_valid_option_stores_values(self):
        opt = make_dummy()
        assert opt.spot == 100
        assert opt.strike == 100
        assert opt.maturity == 1.0
        assert opt.rate == 0.05
        assert opt.volatility == 0.2
        assert opt.option_type == "call"

    def test_option_type_is_case_insensitive(self):
        assert make_dummy(option_type="PUT").option_type == "put"

    def test_negative_rate_is_allowed(self):
        make_dummy(rate=-0.01)   # should not raise


class TestValidation:
    @pytest.mark.parametrize("field", ["spot", "strike", "maturity", "volatility"])
    @pytest.mark.parametrize("bad_value", [0, -1])
    def test_non_positive_values_rejected(self, field, bad_value):
        with pytest.raises(ValueError):
            make_dummy(**{field: bad_value})

    def test_invalid_option_type_rejected(self):
        with pytest.raises(ValueError):
            make_dummy(option_type="banana")


class TestEncapsulation:
    def test_properties_are_read_only(self):
        opt = make_dummy()
        with pytest.raises(AttributeError):
            opt.spot = 200