# pyoptionpricing: final report

**Course:** Object-Oriented Programming II (22:839:615:40), Master of Quantitative Finance, Rutgers University

**Author:** Maadhini Narayanakumar

## 1. Summary

`pyoptionpricing` is an object-oriented Python library that prices European, American and path-dependent options through one interface: every option has `price()` and `greeks()`. Three pricing methods sit behind that interface: the Black-Scholes formula, a Cox-Ross-Rubinstein binomial tree, and Monte Carlo simulation. Arithmetic Asian and single-barrier options are built on a shared path simulator. Implied volatility is found with Brent's method and works with any model.

The library is served by a FastAPI backend with eight endpoints and used through a Next.js dashboard. Both are deployed on Vercel: the dashboard at https://pyoptionspricing.maadhini.com and the API (with Swagger docs) at https://pyoptionpricing.vercel.app/docs. The dashboard shows prices and Greeks, a model comparison, and charts of payoff, convergence, simulated paths and the volatility smile.

## 2. Mapping OOP principles to the code

| Principle | Where | How |
| --- | --- | --- |
| **Abstraction** | `pyoptionpricing/base.py` (`Option`) | `Option` is an `ABC` with `price()` and `greeks()` declared as `@abstractmethod`. Callers depend on this contract, not on any pricing method. `EuropeanOption`, `AmericanOption` and `PathDependentOption` (`european.py`, `american.py`, `path_dependent.py`) are also abstract, so none of the four can be instantiated (tested in `tests/test_base.py`). |
| **Inheritance** | `black_scholes.py`, `binomial.py`, `monte_carlo.py`, `path_dependent.py`, `asian.py`, `barrier.py` | Every concrete class inherits validation and read-only properties from `Option`. `BinomialEuropeanOption` and `BinomialAmericanOption` share all tree code through the `_BinomialOption` base and differ only in the class attribute `_american`. `AsianOption` and `BarrierOption` inherit path simulation, pricing, standard error and Greeks from `_PathMonteCarlo`. |
| **Polymorphism** | `engine.py` (`PricingEngine`), `implied_vol.py`, `backend/main.py` | `PricingEngine` accepts any `Option` and calls `price()` and `greeks()` without knowing the concrete class. `implied_volatility` calls the option's own `price()` inside the root finder, so one solver works for Black-Scholes, binomial and Monte Carlo. The `/compare` endpoint loops over six different classes with identical code. |
| **Encapsulation** | `base.py`, `binomial.py`, `monte_carlo.py`, `path_dependent.py`, `barrier.py` | Inputs are stored in underscore attributes and exposed through getter-only properties, so `option.spot = 200` raises `AttributeError`. The constructor rejects invalid inputs, so an option object is always valid. Internal details are private: the tree (`_crr_tree`, `_tree`), the stored random normals (`_z`), `_d1`/`_d2`, and the barrier-hit mask (`_hit`). |
| **Factory pattern** | `factory.py` (`OptionFactory`) | `OptionFactory.create(model, style, ...)` maps a `(model, style)` pair to a class through a registry dictionary, accepts aliases (`"bs"`, `"crr"`, `"mc"`), and passes model-specific arguments such as `steps` and `barrier` through. The API and the implied-vol solver build every option through it. Adding a model takes one registry entry. |
| **Template method** | `path_dependent.py` (`_PathMonteCarlo`) | The base class fixes the algorithm (simulate paths, then discount payoffs, then average, plus standard error and bump-and-reprice Greeks). Subclasses override only `_discounted_payoffs`. |

The class diagram is in [`uml.md`](uml.md). The three-layer architecture and request flow are in [`architecture.md`](architecture.md).

## 3. Models

**Black-Scholes** (`black_scholes.py`). Closed-form price with \(d_1 = [\ln(S/K) + (r + \sigma^2/2)T]/(\sigma\sqrt T)\) and \(d_2 = d_1 - \sigma\sqrt T\). All five Greeks are analytical, with separate call and put formulas for theta and rho.

**Binomial tree** (`binomial.py`). CRR parameters \(u = e^{\sigma\sqrt{\Delta t}}\), \(d = 1/u\), \(p = (e^{r\Delta t} - d)/(u - d)\), with NumPy-vectorised backward induction. The American class takes the larger of the continuation value and the exercise value at every node. Delta, gamma and theta are read from the first two levels of the tree. Vega and rho use central bump-and-reprice.

**Monte Carlo** (`monte_carlo.py`). Exact terminal sampling \(S_T = S e^{(r - \sigma^2/2)T + \sigma\sqrt T Z}\) with a seeded NumPy generator. The normals are drawn once in the constructor, so every bumped price for the Greeks reuses the same random numbers (common random numbers). This removes most of the noise from the finite differences.

**Path-dependent** (`paths.py`, `path_dependent.py`, `asian.py`, `barrier.py`). Discrete GBM paths. The Asian payoff uses the arithmetic average of the simulated prices. The barrier is checked at \(S_0\) and at every step, in four variants (up/down × in/out).

**Implied volatility** (`implied_vol.py`). The solver scans \(\sigma \in [0.001, 5]\) on a doubling grid to find a bracket, then calls `scipy.optimize.brentq`. It raises a clear error when the market price is outside the prices the model can produce, which means it breaks no-arbitrage bounds. The volatility smile (`implied_vol.py`) and surface (`analysis.py`) use synthetic prices from \(\sigma(K, T) = \sigma_{ATM} + (\text{skew}/\sqrt T)\ln(K/S)\).

## 4. Results

Inputs: \(S = K = 100\), \(T = 1\), \(r = 5\%\), \(\sigma = 20\%\).

| Contract | Black-Scholes | Binomial (500 steps) | Monte Carlo (100k paths) |
| --- | --- | --- | --- |
| European call | 10.4506 | 10.4466 | 10.4205 (s.e. 0.0468) |
| European put | 5.5735 | 5.5695 | 5.6122 (s.e. 0.0275) |
| American put | n/a | 6.0888 | n/a |

- Put-call parity holds to \(10^{-8}\) for both Black-Scholes and the tree.

- The American put is worth 0.52 more than the European put (the early-exercise premium). The American call equals the European call, as theory predicts with no dividends.

- Binomial convergence: 10.806 (5 steps), 10.253 (10), 10.431 (100), 10.449 (1000). The error oscillates with the number of steps while shrinking, so the tests use tolerances rather than requiring the error to fall at every step.

- Asian call: 5.88 (s.e. 0.06), well below the European call, because averaging reduces volatility.

- Up-and-out call with barrier 120: 1.48. Up-and-in: 8.90. Their sum equals the vanilla Monte Carlo price on the same paths.

- Implied volatility recovers \(\sigma = 0.2000\) from the Black-Scholes price, and 0.2001 when the binomial tree is the model.

### 4.1 Sample output

Output of `python demo.py` (inputs S = K = 100, T = 1, r = 5%, σ = 20% unless stated; the demo uses its own path counts and seeds, so its Monte Carlo values differ slightly from the table above):

```text

1. Black-Scholes: price, Greeks and put-call parity

  call = 10.4506   put = 5.5735

  delta=+0.6368  gamma=+0.0188  vega=+37.5240  theta=-6.4140  rho=+53.2325

  C - P = 4.877058   S - K·e^(-rT) = 4.877058

2. Input validation

  ValueError: Spot price must be positive.

3. Factory + polymorphic PricingEngine: one loop, every model

  AsianOption                european  put = 3.3578 ± 0.0373

  BarrierOption              european  put = 5.3814 ± 0.0606

  BinomialAmericanOption     american  put = 6.0824

  BinomialEuropeanOption     european  put = 5.5536

  BlackScholesOption         european  put = 5.5735

  MonteCarloEuropeanOption   european  put = 5.6122 ± 0.0275

4. Binomial convergence to Black-Scholes

      5 steps: 10.8059   error +0.3554

     10 steps: 10.2534   error -0.1972

    100 steps: 10.4306   error -0.0200

   1000 steps: 10.4486   error -0.0020

5. American vs European put (early-exercise premium)

  European 5.5695   American 6.0888   premium 0.5193

6. Monte Carlo with standard error

  MC = 10.4479 ± 0.0329   BS = 10.4506

7. Exotics: Asian and Barrier

  Asian call = 5.8822  (≤ European call 10.4506)

  up-and-out = 1.4836   up-and-in = 8.9031   sum = 10.3867

8. Implied volatility (any model)

  from BS price 10.4506:  σ_BS = 0.200000

  same price, binomial model: σ_tree = 0.200107

9. Volatility smile from synthetic skewed prices

  K=   80  IV=23.35%

  K=   90  IV=21.58%

  K=  100  IV=20.00%

  K=  110  IV=18.57%

  K=  120  IV=17.27%

```

Example API call (`POST /price` with a Black-Scholes European call) and response:

```json

{"model": "black_scholes", "style": "european", "price": 10.450583572185565}

```

## 5. Testing

The suite has 11 test files. It covers the library, the analysis helpers and every API endpoint (through FastAPI's `TestClient`). Run it with:

```bash

pytest --cov=pyoptionpricing --cov=backend --cov-report=term-missing

```

Coverage is about 99% (target: 80%). The required correctness checks are all present:

| Check | Test |
| --- | --- |
| Put-call parity | `test_black_scholes.py::TestParity`, `test_binomial.py::test_european_put_call_parity` |
| Binomial convergence | `test_binomial.py::test_converges_within_tolerance`, `test_analysis.py::test_binomial_error_shrinks` |
| Greeks vs finite differences | `test_black_scholes.py::TestFiniteDifference` (all five Greeks, calls and puts) |
| Monte Carlo within standard error | `test_monte_carlo.py::test_within_three_standard_errors_of_black_scholes` |
| American ≥ European | `test_binomial.py::test_american_put_is_at_least_european_put` |
| Barrier in + out = vanilla | `test_barrier.py::test_knock_in_plus_knock_out_equals_vanilla` |
| Invalid inputs | `test_base.py::TestValidation`, plus validation tests in each module and `test_api.py::TestErrors` |

## 6. Challenges

- **Packaging.** `ModuleNotFoundError` for the package itself, a failing editable install with no `pyproject.toml`, and pytest not finding the package from other directories. A `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]` fixed all three.

- **Validation and encapsulation.** The first checks used `< 0`, which accepted zero. Attributes only became read-only after switching to getter-only properties. Testing the abstract base constructor needed a minimal concrete `DummyOption`.

- **Consistent Greek units.** Theta is per year, and vega and rho are per 1.00 change, across all models. This lets the comparison table line up and lets the tests compare tree and Monte Carlo Greeks with Black-Scholes directly.

- **Monte Carlo noise in Greeks and tests.** Finite-difference Greeks are pure noise if each bump draws new random numbers. The normals are drawn once in the constructor and reused for every bump, which removes most of the noise. The same seed also makes tests repeatable, so "within 3 standard errors of Black-Scholes" does not fail at random. The implied-vol solver needs a fixed seed for the same reason, or the objective changes on every call.

- **Binomial prices breaking at tiny volatility.** The first implied-vol solver bracketed \(\sigma\) over \([0.001, 5]\). For the binomial model, \(\sigma = 0.001\) pushes the risk-neutral probability \(p\) outside (0, 1), and the tree returned an absurdly large price (of order \(10^{65}\) or more, depending on the number of steps). Brent's method then saw no sign change and reported the market price as impossible. The solver now scans a doubling grid of volatilities, drops points where the model price is not finite, and only then brackets the root.

- **Binomial convergence is not monotone.** The tree price oscillates around the Black-Scholes value as steps grow (10.806 at 5 steps, 10.253 at 10, 10.431 at 100). A test that demands the error fall at every step fails. The convergence tests check a tolerance at larger step counts instead.

- **Path-dependent conventions.** Asian and barrier prices depend on choices the course text does not fix. The Asian average uses the simulated spots and leaves out \(S_0\). The barrier is checked at \(S_0\) and at every step, so monitoring is discrete and prices differ from the continuous-barrier closed form. The knock-in plus knock-out identity holds to \(10^{-8}\) only because both options, and the vanilla reference, use the same stored normals.

- **Units between the UI and the API.** The form takes rate and volatility in percent (4.330 and 20), and the API takes decimals (0.0433 and 0.20). Vega and rho look large because they are per 1.00 change in \(\sigma\) or \(r\), not per percentage point. The form converts percentages in one function (`toRequest`), and the cards label each Greek's unit, so screen values can be checked against the library directly.

- **Documentation drifting from the code.** The README example once built `PricingEngine()` and passed the option to `price()`. The real constructor takes the option, so `PricingEngine(option).price()` is correct and the old example raised `TypeError`. The README now matches the code, and `demo.py` runs the documented usage.

- **Keeping routes thin.** The API reads the constructor signature of the class the factory resolves. That way it can forward only the inputs each model accepts without hard-coding a list per model.

## 7. Limitations and future work

- Monte Carlo has no variance reduction yet (antithetic variates or a control variate using the Black-Scholes price).

- Barrier monitoring is discrete. A continuous-monitoring correction (Broadie-Glasserman-Kou) would move prices closer to the closed form.

- Greeks for Asian and barrier options come from bump-and-reprice on a fixed set of random draws. They are noisy, and barrier delta and gamma can be unstable because the payoff is discontinuous.

- The CRR tree is unreliable at extreme inputs (very low volatility, high rates or few steps), where the risk-neutral probability leaves (0, 1).

- Only arithmetic Asian options and single barriers are supported. There are no geometric averages, double barriers or rebates.

- The surface uses synthetic prices. Calibrating to live option chains is out of scope.

- No American Monte Carlo (Longstaff-Schwartz) and no dividends.

- The API is a prototype with no authentication or rate limiting.

## 8. Development notes and AI use

I used AI tools while building this project. This section states how, so the work can be assessed fairly.

### Timeline

| Date | Work |
| --- | --- |
| Oct 4 – Nov 10 | Research and planning|
| Nov 10 | Project setup. A first version generated with Cursor (option hierarchy, validation, Black-Scholes) was reverted, and I restarted from a smaller base. |
| Nov 11 | Binomial European and American options, with Copilot assistance. |
| Nov 13 | Monte Carlo pricing, factory and engine, with tests. |
| Nov 19 | Asian and barrier options, implied volatility, analysis helpers, FastAPI backend, Next.js frontend, documentation. |

### AI Assistance and Individual Contributions

AI tools, including Cursor, GitHub Copilot, and Claude, were used as supporting tools throughout the development process.

Their assistance included:

- Reviewing code and suggesting improvements.

- Explaining implementation details and helping clarify concepts.

- Assisting with debugging and troubleshooting errors.

- Supporting Git workflows, including commit-related issues and `.gitignore` configuration.

- Providing suggestions for code comments and documentation.

- Reviewing and refining parts of this report.

GitHub Copilot also assisted with the implementation of the binomial European and American option pricing methods, as acknowledged in the relevant commit.

An initial library draft generated using Cursor was reverted, and the library was subsequently rebuilt step by step.

The overall design, development, integration, testing, and verification of the project were carried out by me.

### How I Tested the Work

- Ran the full automated test suite to verify the correctness of the pricing models and core functionality.

- Compared binomial tree and Monte Carlo option prices against analytical Black-Scholes values.

- Tested backend API endpoints to verify request handling, response formats, input validation, and error handling.

- Tested frontend UI components to check layout, navigation, user interactions, and the display of pricing results.

- Verified frontend and backend integration to ensure API requests and responses were handled correctly.

- Tested different option parameters, including strike prices, volatility, maturity, and interest rates, to check the consistency of pricing outputs.

- Checked edge cases and invalid inputs to verify that the application handled errors appropriately.

- Reviewed the final implementation and Git history to verify changes, commits, and the overall project structure.

## 9. Code inventory and sources of code

### Programs in this submission

| Part | Files | Purpose |
| --- | --- | --- |
| Core library | `pyoptionpricing/` (`base.py`, `european.py`, `american.py`, `path_dependent.py`, `black_scholes.py`, `binomial.py`, `monte_carlo.py`, `asian.py`, `barrier.py`, `paths.py`, `factory.py`, `engine.py`, `implied_vol.py`, `analysis.py`) | Option classes, pricing models, factory, engine, implied volatility, chart data |
| Backend | `backend/main.py`, `backend/schemas.py` | FastAPI app and request schemas |
| Frontend | `frontend/src/` (components, `lib/`, app pages) | Next.js dashboard |
| Tests | `tests/` (11 files) | pytest suite |
| Demo and examples | `demo.py`, `examples/` | Sample output and example API requests |
| Documentation | `README.md`, `docs/` | Setup, report, UML, architecture |

### Code and ideas not written by me

| Source | Used for |
| --- | --- |
| NumPy | Arrays, random numbers, vectorised math |
| SciPy | `scipy.stats.norm` (normal CDF and PDF), `scipy.optimize.brentq` (root finding) |
| FastAPI, Pydantic, Uvicorn | Backend API, validation, server |
| pytest, pytest-cov, httpx | Testing and coverage |
| Next.js, React, TypeScript, Recharts, Tailwind CSS, ESLint | Frontend framework, charts, styling, linting |
| Geist and Geist Mono fonts (Google Fonts, loaded through `next/font`) | Frontend typography |
| Next.js starter template (`create-next-app`) | Initial frontend scaffolding. Unused starter files (default images, template README) were removed. |
| Black-Scholes (1973), Cox-Ross-Rubinstein (1979), Brent's method | Published algorithms, implemented in this project |
| AI tools (Cursor, GitHub Copilot, Claude) | See section 8 for exactly where they were used |

All code in this repository other than the sources listed above was written or edited by me, with the AI assistance described in section 8.
