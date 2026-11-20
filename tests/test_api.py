import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

BASE = dict(spot=100, strike=100, maturity=1.0, rate=0.05,
            volatility=0.2, option_type="call")
NO_VOL = {k: v for k, v in BASE.items() if k != "volatility"}


def post(path, **body):
    return client.post(path, json=body)


class TestPriceAndGreeks:
    def test_black_scholes_price(self):
        r = post("/price", **BASE)
        assert r.status_code == 200
        assert r.json()["price"] == pytest.approx(10.4506, abs=1e-3)
        assert "standard_error" not in r.json()

    def test_monte_carlo_price_has_standard_error(self):
        r = post("/price", **BASE, model="monte_carlo", n_paths=20_000)
        assert r.status_code == 200
        assert r.json()["standard_error"] > 0

    def test_binomial_american_put(self):
        euro = post("/price", **{**BASE, "option_type": "put"}, model="binomial").json()
        amer = post("/price", **{**BASE, "option_type": "put"},
                    model="binomial", style="american").json()
        assert amer["price"] >= euro["price"]

    def test_irrelevant_inputs_are_ignored(self):
        r = post("/price", **BASE, model="black_scholes", steps=10, n_paths=50)
        assert r.status_code == 200

    def test_greeks(self):
        r = post("/greeks", **BASE)
        assert r.status_code == 200
        assert set(r.json()["greeks"]) == {"delta", "gamma", "vega", "theta", "rho"}

    def test_barrier_price(self):
        r = post("/price", **BASE, model="barrier", barrier=130,
                 barrier_type="up-and-out", n_paths=5_000)
        assert r.status_code == 200
        assert 0 < r.json()["price"] < 10.4506


class TestErrors:
    def test_negative_spot_is_422(self):
        assert post("/price", **{**BASE, "spot": -1}).status_code == 422

    def test_bad_option_type_is_422(self):
        assert post("/price", **{**BASE, "option_type": "banana"}).status_code == 422

    def test_unknown_model_message(self):
        r = post("/price", **BASE, model="heston")
        assert r.status_code == 422
        assert "Unknown model" in r.json()["detail"]

    def test_unsupported_style_message(self):
        r = post("/price", **BASE, style="american")
        assert r.status_code == 422
        assert "does not support style" in r.json()["detail"]

    def test_barrier_without_level(self):
        r = post("/price", **BASE, model="barrier")
        assert r.status_code == 422
        assert "barrier" in r.json()["detail"]


class TestCompare:
    def test_vanilla_models_without_barrier(self):
        r = post("/compare", **BASE, n_paths=5_000)
        assert r.status_code == 200
        models = [(x["model"], x["style"]) for x in r.json()["results"]]
        assert ("black_scholes", "european") in models
        assert ("binomial", "american") in models
        assert all(m != "barrier" for m, _ in models)

    def test_includes_barrier_when_given(self):
        r = post("/compare", **BASE, n_paths=5_000, barrier=120, barrier_type="up-and-out")
        models = [x["model"] for x in r.json()["results"]]
        assert "barrier" in models

    def test_european_models_agree(self):
        results = post("/compare", **BASE).json()["results"]
        prices = {(x["model"], x["style"]): x["price"] for x in results}
        bs = prices[("black_scholes", "european")]
        assert prices[("binomial", "european")] == pytest.approx(bs, abs=0.05)
        assert prices[("monte_carlo", "european")] == pytest.approx(bs, abs=0.15)


class TestCharts:
    def test_convergence(self):
        r = post("/convergence", **BASE, steps_list=[10, 100, 1000], path_counts=[1000, 10_000])
        body = r.json()
        assert r.status_code == 200
        assert [p["steps"] for p in body["binomial"]["points"]] == [10, 100, 1000]
        assert len(body["monte_carlo"]["points"]) == 2
        last = body["binomial"]["points"][-1]["price"]
        assert last == pytest.approx(body["binomial"]["black_scholes"], abs=0.01)

    def test_convergence_defaults(self):
        r = post("/convergence", **BASE)
        assert r.status_code == 200
        assert len(r.json()["binomial"]["points"]) > 3

    def test_payoff_uses_model_price_as_premium(self):
        body = post("/payoff", **BASE, n_points=11).json()
        assert body["premium"] == pytest.approx(10.4506, abs=1e-3)
        assert len(body["points"]) == 11

    def test_payoff_with_explicit_premium(self):
        body = post("/payoff", **BASE, premium=5, spot_min=90, spot_max=110, n_points=3).json()
        assert [p["profit"] for p in body["points"]] == pytest.approx([-5, -5, 5])

    def test_paths_shape(self):
        body = post("/paths", **BASE, n_display=3, n_steps=10, barrier=120).json()
        assert len(body["times"]) == 11
        assert len(body["paths"]) == 3
        assert all(path[0] == 100 for path in body["paths"])
        assert body["barrier"] == 120


class TestImpliedVol:
    def test_round_trip(self):
        r = post("/implied-vol", **NO_VOL, market_price=10.450583572185565)
        assert r.status_code == 200
        assert r.json()["implied_vol"] == pytest.approx(0.2, abs=1e-6)

    def test_with_binomial_model(self):
        r = post("/implied-vol", **NO_VOL, market_price=10.45, model="binomial", steps=200)
        assert r.status_code == 200
        assert r.json()["implied_vol"] == pytest.approx(0.2, abs=0.005)

    def test_price_out_of_bounds(self):
        r = post("/implied-vol", **NO_VOL, market_price=500)
        assert r.status_code == 422
        assert "no-arbitrage" in r.json()["detail"]

    def test_vol_surface_defaults(self):
        body = post("/vol-surface").json()
        assert len(body["surface"]) == 4
        assert len(body["surface"][0]["smile"]) == len(body["strikes"])

    def test_vol_surface_flat_skew(self):
        body = post("/vol-surface", strikes=[90, 100, 110], maturities=[1.0], skew=0.0).json()
        ivs = [p["implied_vol"] for p in body["surface"][0]["smile"]]
        assert ivs == pytest.approx([0.2, 0.2, 0.2], abs=1e-6)


class TestMeta:
    def test_health(self):
        assert client.get("/health").json() == {"status": "ok"}

    def test_models_lists_required_barrier_inputs(self):
        models = {(m["model"], m["style"]): m for m in client.get("/models").json()}
        barrier = models[("barrier", "european")]["parameters"]
        assert barrier["barrier"]["required"] is True
        assert models[("binomial", "american")]["parameters"]["steps"]["default"] == 100

    def test_cors_allows_frontend(self):
        r = client.options(
            "/price",
            headers={"Origin": "http://localhost:3000",
                     "Access-Control-Request-Method": "POST"},
        )
        assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
