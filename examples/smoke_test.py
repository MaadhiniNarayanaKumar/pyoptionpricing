"""Smoke tests for the installed pyoptionpricing package.
Run from any folder that does NOT contain the project source:  python smoke_test.py
"""
import math
import pyoptionpricing
from pyoptionpricing import (
    OptionFactory, PricingEngine, BlackScholesOption,
    implied_volatility, volatility_smile,
)

S, K, T, R, VOL = 100, 100, 1.0, 0.05, 0.20
passed = failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS  {name}  {detail}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


def make(model, style="european", option_type="call", **kw):
    return OptionFactory.create(model, style, S, K, T, R, VOL, option_type, **kw)


print("installed from:", pyoptionpricing.__file__, "\n")

# 1. Black-Scholes price and put-call parity
call, put = make("black_scholes").price(), make("black_scholes", option_type="put").price()
check("1  BS call = 10.4506", abs(call - 10.4506) < 1e-3, f"({call:.4f})")
check("1  BS put = 5.5735", abs(put - 5.5735) < 1e-3, f"({put:.4f})")
check("1  put-call parity", abs((call - put) - (S - K * math.exp(-R * T))) < 1e-8)

# 2. Greeks
g = PricingEngine(make("black_scholes")).greeks()
check("2  five Greeks returned", set(g) == {"delta", "gamma", "vega", "theta", "rho"})
check("2  call delta = 0.6368", abs(g["delta"] - 0.6368) < 1e-3, f"({g['delta']:.4f})")

# 3. Binomial converges to Black-Scholes
b = make("binomial", steps=500).price()
check("3  binomial(500) within 0.01 of BS", abs(b - call) < 0.01, f"({b:.4f})")

# 4. American put >= European put
am = make("binomial", "american", "put", steps=200).price()
eu = make("binomial", "european", "put", steps=200).price()
check("4  American put >= European put", am >= eu, f"({am:.4f} vs {eu:.4f})")

# 5. Monte Carlo within 3 standard errors, and reproducible with a seed
mc = make("monte_carlo", n_paths=100_000, seed=42)
check("5  MC within 3 s.e. of BS", abs(mc.price() - call) < 3 * mc.standard_error(),
      f"({mc.price():.4f} +/- {mc.standard_error():.4f})")
check("5  same seed, same price",
      make("monte_carlo", n_paths=5000, seed=1).price() == make("monte_carlo", n_paths=5000, seed=1).price())

# 6. Asian call is worth less than the European call
asian = make("asian", n_paths=20_000, n_steps=50, seed=42).price()
check("6  Asian call < European call", asian < call, f"({asian:.4f} < {call:.4f})")

# 7. Barrier: knock-in + knock-out = vanilla
kw = dict(barrier=120, n_paths=50_000, n_steps=50, seed=7)
ko, ki = make("barrier", barrier_type="up-and-out", **kw), make("barrier", barrier_type="up-and-in", **kw)
check("7  up-and-in + up-and-out = vanilla (within 0.2 of BS)",
      abs(ko.price() + ki.price() - call) < 0.2, f"({ko.price():.3f} + {ki.price():.3f})")

# 8. Implied volatility round trip and smile
iv = implied_volatility(call, "black_scholes", "european", "call", S, K, T, R)
check("8  implied vol recovers 20%", abs(iv - VOL) < 1e-6, f"({iv:.6f})")
smile = volatility_smile([80, 100, 120], spot=S, maturity=T, rate=R, atm_vol=0.2, skew=-0.15)
vols = [p["implied_vol"] for p in smile]
check("8  smile: low strike vol > ATM vol > high strike vol", vols[0] > vols[1] > vols[2],
      "(" + ", ".join(f"{v:.3f}" for v in vols) + ")")

# 9. Engine.run and factory aliases
run = PricingEngine(make("mc", n_paths=5000, seed=3)).run()
check("9  engine.run has price, greeks and standard_error",
      {"price", "greeks", "standard_error"} <= set(run))
check("9  aliases bs / crr / mc work",
      type(make("bs")).__name__ == "BlackScholesOption" and type(make("crr")).__name__ == "BinomialEuropeanOption")

# 10. Invalid input is rejected with a clear error
for label, fn in [
    ("negative spot", lambda: BlackScholesOption(-1, K, T, R, VOL, "call")),
    ("bad option type", lambda: BlackScholesOption(S, K, T, R, VOL, "banana")),
    ("unknown model", lambda: OptionFactory.create("heston", "european", S, K, T, R, VOL, "call")),
    ("impossible market price", lambda: implied_volatility(500, "black_scholes", "european", "call", S, K, T, R)),
]:
    try:
        fn()
        check(f"10 {label} raises ValueError", False, "(no error)")
    except ValueError as err:
        check(f"10 {label} raises ValueError", True, f"({str(err)[:50]}...)")

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
