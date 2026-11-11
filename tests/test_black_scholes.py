import math

import pytest

from pyoptionpricing import BlackScholesOption


def make_bs(spot=100, strike=100, maturity=1.0, rate=0.05,
            volatility=0.2, option_type="call"):
    return BlackScholesOption(spot, strike, maturity, rate, volatility, option_type)


class TestKnownValues:
    """S=100, K=100, T=1, r=0.05, sigma=0.2"""

    def test_call_price(self):
        assert make_bs(option_type="call").price() == pytest.approx(10.4506, abs=1e-3)

    def test_put_price(self):
        assert make_bs(option_type="put").price() == pytest.approx(5.5735, abs=1e-3)

    def test_call_greeks(self):
        g = make_bs(option_type="call").greeks()
        assert g["delta"] == pytest.approx(0.6368, abs=1e-3)
        assert g["gamma"] == pytest.approx(0.01876, abs=1e-4)
        assert g["vega"] == pytest.approx(37.524, abs=1e-2)
        assert g["theta"] == pytest.approx(-6.414, abs=1e-2)
        assert g["rho"] == pytest.approx(53.232, abs=1e-2)

    def test_put_greeks(self):
        g = make_bs(option_type="put").greeks()
        assert g["delta"] == pytest.approx(-0.3632, abs=1e-3)
        assert g["gamma"] == pytest.approx(0.01876, abs=1e-4)
        assert g["vega"] == pytest.approx(37.524, abs=1e-2)
        assert g["theta"] == pytest.approx(-1.658, abs=1e-2)
        assert g["rho"] == pytest.approx(-41.890, abs=1e-2)


class TestParity:
    @pytest.mark.parametrize("spot,strike,maturity,rate,vol", [
        (100, 100, 1.0, 0.05, 0.20),
        (120,  90, 0.5, 0.03, 0.35),
        ( 80, 110, 2.0, 0.01, 0.15),
    ])
    def test_put_call_parity(self, spot, strike, maturity, rate, vol):
        call = make_bs(spot, strike, maturity, rate, vol, "call").price()
        put = make_bs(spot, strike, maturity, rate, vol, "put").price()
        expected = spot - strike * math.exp(-rate * maturity)
        assert call - put == pytest.approx(expected, abs=1e-8)


class TestGreekProperties:
    def test_delta_bounds(self):
        call_delta = make_bs(option_type="call").greeks()["delta"]
        put_delta = make_bs(option_type="put").greeks()["delta"]
        assert 0 < call_delta < 1
        assert -1 < put_delta < 0

    def test_gamma_and_vega_same_for_call_and_put(self):
        gc = make_bs(option_type="call").greeks()
        gp = make_bs(option_type="put").greeks()
        assert gc["gamma"] == pytest.approx(gp["gamma"])
        assert gc["vega"] == pytest.approx(gp["vega"])


class TestFiniteDifference:
    """Analytical Greeks should match numerical derivatives of price()."""

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_delta(self, option_type):
        h = 0.01
        up = make_bs(spot=100 + h, option_type=option_type).price()
        down = make_bs(spot=100 - h, option_type=option_type).price()
        numeric = (up - down) / (2 * h)
        analytic = make_bs(option_type=option_type).greeks()["delta"]
        assert analytic == pytest.approx(numeric, rel=1e-3)

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_gamma(self, option_type):
        h = 0.01
        up = make_bs(spot=100 + h, option_type=option_type).price()
        mid = make_bs(spot=100, option_type=option_type).price()
        down = make_bs(spot=100 - h, option_type=option_type).price()
        numeric = (up - 2 * mid + down) / h**2
        analytic = make_bs(option_type=option_type).greeks()["gamma"]
        assert analytic == pytest.approx(numeric, rel=1e-3)

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_vega(self, option_type):
        h = 0.001
        up = make_bs(volatility=0.2 + h, option_type=option_type).price()
        down = make_bs(volatility=0.2 - h, option_type=option_type).price()
        numeric = (up - down) / (2 * h)
        analytic = make_bs(option_type=option_type).greeks()["vega"]
        assert analytic == pytest.approx(numeric, rel=1e-5)

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_rho(self, option_type):
        h = 0.001
        up = make_bs(rate=0.05 + h, option_type=option_type).price()
        down = make_bs(rate=0.05 - h, option_type=option_type).price()
        numeric = (up - down) / (2 * h)
        analytic = make_bs(option_type=option_type).greeks()["rho"]
        assert analytic == pytest.approx(numeric, rel=1e-5)

    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_theta(self, option_type):
        h = 0.001
        up = make_bs(maturity=1.0 + h, option_type=option_type).price()
        down = make_bs(maturity=1.0 - h, option_type=option_type).price()
        numeric = -(up - down) / (2 * h)
        analytic = make_bs(option_type=option_type).greeks()["theta"]
        assert analytic == pytest.approx(numeric, rel=1e-5)


class TestBehaviour:
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_higher_vol_raises_price(self, option_type):
        low = make_bs(volatility=0.1, option_type=option_type).price()
        high = make_bs(volatility=0.4, option_type=option_type).price()
        assert high > low

    def test_deep_in_the_money_call(self):
        price = make_bs(spot=200, strike=100, option_type="call").price()
        intrinsic = 200 - 100 * math.exp(-0.05 * 1.0)
        assert price == pytest.approx(intrinsic, rel=1e-3)

    def test_deep_out_of_the_money_call_near_zero(self):
        price = make_bs(spot=50, strike=100, maturity=0.1, option_type="call").price()
        assert price < 1e-6