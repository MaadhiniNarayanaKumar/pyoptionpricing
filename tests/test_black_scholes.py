"""Known Black-Scholes values, put-call parity, and finite-difference Greeks."""

import math

import pytest

from pyoptionpricing import BlackScholesOption

SPOT = dict(S=100, K=100, T=1, r=0.05, sigma=0.20, q=0.0)
CALL_PRICE = 10.450583572186
PUT_PRICE = 5.573526022257


def _option(option_type="call", **overrides):
    params = dict(SPOT, option_type=option_type)
    params.update(overrides)
    return BlackScholesOption(**params)


def test_greeks_export_as_a_dict():
    greeks = _option("call").greeks()
    assert greeks.as_dict() == {
        "delta": greeks.delta,
        "gamma": greeks.gamma,
        "theta": greeks.theta,
        "vega": greeks.vega,
        "rho": greeks.rho,
    }


def test_call_matches_known_value():
    assert _option("call").price() == pytest.approx(10.4506, abs=1e-4)
    assert _option("call").price() == pytest.approx(CALL_PRICE, abs=1e-9)


def test_put_matches_known_value():
    assert _option("put").price() == pytest.approx(PUT_PRICE, abs=1e-9)


@pytest.mark.parametrize(
    "overrides",
    [{}, {"q": 0.03}, {"r": 0.01, "q": 0.02, "S": 120, "K": 90, "sigma": 0.35, "T": 0.4}],
)
def test_put_call_parity(overrides):
    call = _option("call", **overrides)
    put = _option("put", **overrides)
    forward_diff = call.S * math.exp(-call.q * call.T) - call.K * math.exp(-call.r * call.T)
    assert call.price() - put.price() == pytest.approx(forward_diff, abs=1e-10)


def test_call_and_put_greeks_match_central_differences():
    _assert_greeks_match(_option("call"))
    _assert_greeks_match(_option("put"))


def test_dividend_greeks_match_central_differences():
    _assert_greeks_match(_option("call", q=0.04, S=110, K=105, T=0.75, sigma=0.25))
    _assert_greeks_match(_option("put", q=0.04, S=110, K=105, T=0.75, sigma=0.25))


def test_delta_call_minus_delta_put_is_discounted_dividend():
    call = _option("call", q=0.02)
    put = _option("put", q=0.02)
    expected = math.exp(-call.q * call.T)
    assert call.greeks().delta - put.greeks().delta == pytest.approx(expected, abs=1e-12)


def _assert_greeks_match(option: BlackScholesOption) -> None:
    analytical = option.greeks()
    bumped = {
        "delta": _central(option, "S", 1e-4),
        "vega": _central(option, "sigma", 1e-4),
        "rho": _central(option, "r", 1e-4),
        "theta": -_central(option, "T", 1e-4),
        "gamma": _second(option, "S", 1e-2),
    }
    assert analytical.delta == pytest.approx(bumped["delta"], abs=1e-6)
    assert analytical.vega == pytest.approx(bumped["vega"], abs=1e-4)
    assert analytical.rho == pytest.approx(bumped["rho"], abs=1e-4)
    assert analytical.theta == pytest.approx(bumped["theta"], abs=1e-4)
    assert analytical.gamma == pytest.approx(bumped["gamma"], abs=1e-6)
    assert analytical.gamma > 0
    assert analytical.vega > 0


def _central(option: BlackScholesOption, name: str, step: float) -> float:
    up = option.with_params(**{name: getattr(option, name) + step}).price()
    down = option.with_params(**{name: getattr(option, name) - step}).price()
    return (up - down) / (2.0 * step)


def _second(option: BlackScholesOption, name: str, step: float) -> float:
    mid = option.price()
    up = option.with_params(**{name: getattr(option, name) + step}).price()
    down = option.with_params(**{name: getattr(option, name) - step}).price()
    return (up - 2.0 * mid + down) / (step * step)
