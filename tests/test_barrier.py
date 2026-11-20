import math

import numpy as np
import pytest

from pyoptionpricing import BarrierOption
from pyoptionpricing.paths import simulate_paths, standard_normals, vanilla_payoff


def make_barrier(barrier_type, barrier=120, spot=100, strike=100, maturity=1.0,
                 rate=0.05, volatility=0.2, option_type="call",
                 n_paths=6_000, n_steps=30, seed=7):
    return BarrierOption(
        spot, strike, maturity, rate, volatility, option_type,
        barrier=barrier, barrier_type=barrier_type,
        n_paths=n_paths, n_steps=n_steps, seed=seed,
    )


def vanilla_price(spot=100, strike=100, maturity=1.0, rate=0.05, volatility=0.2,
                  option_type="call", n_paths=6_000, n_steps=30, seed=7):
    z = standard_normals(n_paths, n_steps, seed)
    paths = simulate_paths(spot, rate, volatility, maturity, z)
    payoff = vanilla_payoff(paths[:, -1], strike, option_type)
    return float(math.exp(-rate * maturity) * payoff.mean())


class TestInOutIdentity:
    @pytest.mark.parametrize("direction", ["up", "down"])
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_knock_in_plus_knock_out_equals_vanilla(self, direction, option_type):
        barrier = 120 if direction == "up" else 80
        shared = dict(barrier=barrier, option_type=option_type)
        knock_in = make_barrier(f"{direction}-and-in", **shared)
        knock_out = make_barrier(f"{direction}-and-out", **shared)
        vanilla = vanilla_price(option_type=option_type)
        assert knock_in.price() + knock_out.price() == pytest.approx(vanilla, abs=1e-8)

    def test_far_up_barrier_is_almost_vanilla(self):
        knock_out = make_barrier("up-and-out", barrier=1_000)
        knock_in = make_barrier("up-and-in", barrier=1_000)
        vanilla = vanilla_price()
        assert knock_in.price() == pytest.approx(0.0, abs=1e-8)
        assert knock_out.price() == pytest.approx(vanilla, abs=1e-8)


class TestContract:
    def test_aliases_and_properties(self):
        option = make_barrier("up_and_out", barrier=130, n_paths=500, n_steps=8, seed=3)
        assert option.barrier == 130
        assert option.barrier_type == "up-and-out"
        assert (option.n_paths, option.n_steps, option.seed) == (500, 8, 3)

    def test_same_seed_is_reproducible(self):
        assert make_barrier("down-and-out", barrier=80).price() == make_barrier(
            "DO", barrier=80
        ).price()

    def test_greeks_are_finite(self):
        greeks = make_barrier("up-and-out", n_paths=1_500, n_steps=12).greeks()
        assert set(greeks) == {"delta", "gamma", "vega", "theta", "rho"}
        assert all(math.isfinite(value) for value in greeks.values())

    def test_standard_error_is_positive(self):
        assert make_barrier("down-and-in", barrier=90).standard_error() > 0


class TestValidation:
    def test_non_positive_barrier_rejected(self):
        with pytest.raises(ValueError, match="Barrier"):
            make_barrier("up-and-out", barrier=0)

    def test_unknown_barrier_type_rejected(self):
        with pytest.raises(ValueError, match="Unknown barrier type"):
            make_barrier("sideways")

    def test_non_string_barrier_type_rejected(self):
        with pytest.raises(ValueError, match="barrier_type"):
            make_barrier(None)

    def test_too_few_steps_rejected(self):
        with pytest.raises(ValueError, match="n_steps"):
            make_barrier("up-and-in", n_steps=1)

    def test_hit_mask_partitions_the_payoff(self):
        knock_in = make_barrier("up-and-in", n_paths=400, n_steps=8)
        knock_out = make_barrier("up-and-out", n_paths=400, n_steps=8)
        total = knock_in._discounted_payoffs() + knock_out._discounted_payoffs()
        paths = knock_in._paths()
        vanilla = math.exp(-knock_in.rate * knock_in.maturity) * vanilla_payoff(
            paths[:, -1], knock_in.strike, knock_in.option_type
        )
        assert np.allclose(total, vanilla)
