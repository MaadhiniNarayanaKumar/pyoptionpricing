"""One factory call builds any registered option and forwards exotic parameters."""

import pytest

from pyoptionpricing import (
    BlackScholesOption,
    OptionFactory,
    OptionInputError,
    PathDependentOption,
)
from pyoptionpricing.base import Greeks


class _StubBarrier(PathDependentOption):
    def __init__(
        self,
        S,
        K,
        T,
        r,
        sigma,
        option_type,
        barrier,
        knock_type,
        q=0.0,
    ):
        super().__init__(S, K, T, r, sigma, option_type, q=q)
        self.barrier = barrier
        self.knock_type = knock_type

    def price(self) -> float:
        return 0.0

    def greeks(self) -> Greeks:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)


@pytest.fixture
def registry_snapshot():
    saved = dict(OptionFactory._registry)
    yield
    OptionFactory._registry.clear()
    OptionFactory._registry.update(saved)


def test_factory_builds_black_scholes_call():
    option = OptionFactory.create(
        "black_scholes",
        "european",
        "call",
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
    )
    assert isinstance(option, BlackScholesOption)
    assert option.price() == pytest.approx(10.4506, abs=1e-4)


def test_factory_accepts_aliases_and_case():
    option = OptionFactory.create(
        " BS ",
        "European",
        "Put",
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
    )
    assert isinstance(option, BlackScholesOption)
    assert option.option_type == "put"


@pytest.mark.parametrize("model", ["", "  ", None, 1])
def test_model_must_be_a_name(model):
    with pytest.raises(ValueError, match="model"):
        OptionFactory.create(
            model,
            "european",
            "call",
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=0.20,
        )


def test_unknown_model_names_the_registry():
    with pytest.raises(ValueError, match="black_scholes/european"):
        OptionFactory.create(
            "binomial",
            "american",
            "put",
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=0.20,
        )


def test_factory_routes_barrier_and_knock_type(registry_snapshot):
    OptionFactory.register("monte_carlo", "barrier", _StubBarrier)
    option = OptionFactory.create(
        "monte_carlo",
        "barrier",
        "call",
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
        barrier=120,
        knock_type="up-and-out",
    )
    assert isinstance(option, _StubBarrier)
    assert option.barrier == 120
    assert option.knock_type == "up-and-out"


def test_black_scholes_rejects_unused_exotic_params():
    with pytest.raises(TypeError):
        OptionFactory.create(
            "black_scholes",
            "european",
            "call",
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=0.20,
            barrier=120,
        )


def test_factory_still_validates_inputs():
    with pytest.raises(OptionInputError, match="sigma"):
        OptionFactory.create(
            "black_scholes",
            "european",
            "call",
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=-0.2,
        )
