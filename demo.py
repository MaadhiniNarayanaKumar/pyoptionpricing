"""Walk through one example per feature of pyoptionpricing.

Run from the project root:  python demo.py
"""

import math

from pyoptionpricing import (
    AsianOption,
    BarrierOption,
    BlackScholesOption,
    OptionFactory,
    PricingEngine,
    binomial_convergence,
    implied_volatility,
    volatility_smile,
)

S, K, T, R, VOL = 100, 100, 1.0, 0.05, 0.20


def section(title):
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


def show_greeks(greeks):
    print("  " + "  ".join(f"{name}={value:+.4f}" for name, value in greeks.items()))


section("1. Black-Scholes: price, Greeks and put-call parity")
call = BlackScholesOption(S, K, T, R, VOL, "call")
put = BlackScholesOption(S, K, T, R, VOL, "put")
print(f"  call = {call.price():.4f}   put = {put.price():.4f}")
show_greeks(call.greeks())
print(f"  C - P = {call.price() - put.price():.6f}   S - K·e^(-rT) = {S - K * math.exp(-R * T):.6f}")

section("2. Input validation")
try:
    BlackScholesOption(-100, K, T, R, VOL, "call")
except ValueError as err:
    print(f"  ValueError: {err}")

section("3. Factory + polymorphic PricingEngine: one loop, every model")
for model, style in OptionFactory.available():
    extra = {"barrier": 120, "barrier_type": "up-and-out"} if model == "barrier" else {}
    option = OptionFactory.create(model, style, S, K, T, R, VOL, "put", **extra)
    result = PricingEngine(option).run()
    se = f" ± {result['standard_error']:.4f}" if "standard_error" in result else ""
    print(f"  {result['model']:<26} {style:<9} put = {result['price']:.4f}{se}")

section("4. Binomial convergence to Black-Scholes")
conv = binomial_convergence(S, K, T, R, VOL, "call")
for point in conv["points"]:
    print(f"  {point['steps']:>5} steps: {point['price']:.4f}   error {point['price'] - conv['black_scholes']:+.4f}")

section("5. American vs European put (early-exercise premium)")
euro = OptionFactory.create("binomial", "european", S, K, T, R, VOL, "put", steps=500).price()
amer = OptionFactory.create("binomial", "american", S, K, T, R, VOL, "put", steps=500).price()
print(f"  European {euro:.4f}   American {amer:.4f}   premium {amer - euro:.4f}")

section("6. Monte Carlo with standard error")
mc = OptionFactory.create("mc", "european", S, K, T, R, VOL, "call", n_paths=200_000, seed=7)
print(f"  MC = {mc.price():.4f} ± {mc.standard_error():.4f}   BS = {call.price():.4f}")

section("7. Exotics: Asian and Barrier")
asian = AsianOption(S, K, T, R, VOL, "call")
print(f"  Asian call = {asian.price():.4f}  (≤ European call {call.price():.4f})")
out = BarrierOption(S, K, T, R, VOL, "call", barrier=120, barrier_type="up-and-out")
knock_in = BarrierOption(S, K, T, R, VOL, "call", barrier=120, barrier_type="up-and-in")
print(f"  up-and-out = {out.price():.4f}   up-and-in = {knock_in.price():.4f}   sum = {out.price() + knock_in.price():.4f}")

section("8. Implied volatility (any model)")
market = call.price()
print(f"  from BS price {market:.4f}:  σ_BS = {implied_volatility(market, 'bs', 'european', 'call', S, K, T, R):.6f}")
print(f"  same price, binomial model: σ_tree = "
      f"{implied_volatility(market, 'binomial', 'european', 'call', S, K, T, R, steps=500):.6f}")
try:
    implied_volatility(150, "bs", "european", "call", S, K, T, R)
except ValueError as err:
    print(f"  price 150 rejected: {str(err)[:70]}…")

section("9. Volatility smile from synthetic skewed prices")
for point in volatility_smile([80, 90, 100, 110, 120], S, T, R, skew=-0.15):
    bar = "#" * round(point["implied_vol"] * 100)
    print(f"  K={point['strike']:>5.0f}  IV={point['implied_vol']:.2%}  {bar}")

print("\nAPI:  uvicorn backend.main:app --reload   (Swagger at http://localhost:8000/docs)")
print("UI:   cd frontend && npm run dev          (http://localhost:3000)")
