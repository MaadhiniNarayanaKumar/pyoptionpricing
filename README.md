# OptionPricing

An object-oriented Python library and web platform for interactive option valuation and Greeks analysis.

**Course:** Object-Oriented Programming II (22:839:615:40), Master of Quantitative Finance, Rutgers University
**Professor:** Dr. Hseu-Ming Chen
**Author:** Maadhini Narayanakumar

---

## Overview

**Live demo:** https://pyoptionpricingui.vercel.app · **API docs:** https://pyoptionpricing.vercel.app/docs

`pyoptionpricing` is a modular Python library that prices vanilla and path-dependent options through a single, model-independent interface. Client code can price any option with `price()` and `greeks()` without knowing whether the underlying method is Black-Scholes, a Binomial Tree or Monte Carlo.

The library is exposed through a FastAPI backend and explored through a Next.js frontend, where you can enter parameters once, compare pricing models side by side, and visualize Greeks, payoffs, convergence and implied volatility.

> Live market data feeds are out of scope. The volatility surface is built from synthetic market prices.

## Features

- Black-Scholes pricing with analytical Greeks (Delta, Gamma, Theta, Vega, Rho) for European calls and puts
- Binomial Tree (CRR) pricing for European and American options
- Monte Carlo pricing for European options, with standard error estimation
- Monte Carlo pricing for path-dependent options (Asian and Barrier)
- Implied volatility via root finding (Brent's method), working across all pricing models
- Implied volatility smile/surface across strikes
- Side-by-side model comparison (Black-Scholes vs Binomial vs Monte Carlo)
- American vs European price comparison
- Binomial convergence chart against the Black-Scholes price
- Payoff diagrams and simulated price path visualization
- Input validation with meaningful error messages
- Swagger/OpenAPI documentation

## OOP Design

```
Option (abstract)
├── EuropeanOption (abstract)
│   ├── BlackScholesOption
│   ├── BinomialEuropeanOption
│   └── MonteCarloEuropeanOption
├── AmericanOption (abstract)
│   └── BinomialAmericanOption
└── PathDependentOption (abstract)
    ├── AsianOption
    └── BarrierOption
```

| Principle | How it is demonstrated |
| --- | --- |
| Abstraction | `Option` and its abstract subclasses define a common `price()` / `greeks()` interface and hide implementation details |
| Inheritance | Concrete option classes extend the shared behavior of their parents |
| Polymorphism | `PricingEngine` prices any `Option` object through the same interface |
| Encapsulation | Tree nodes, probabilities, simulated paths and intermediate math are internal to each class |
| Factory pattern | `OptionFactory` builds the right option object from model, exercise style, option type and extra parameters (e.g. barrier level) |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Core library | Python, NumPy, SciPy |
| Backend | FastAPI, Pydantic, Swagger/OpenAPI |
| Frontend | Next.js, React, TypeScript, Recharts |
| Testing | pytest, pytest-cov |
| Deployment | Vercel (backend and frontend, as two projects) |

## Project Structure

```
.
├── pyoptionpricing/     # Core OOP library
├── backend/             # FastAPI application
├── frontend/            # Next.js application
├── tests/               # pytest test suite
├── docs/                # UML and architecture diagrams, report
├── pyproject.toml
└── README.md
```

## Getting Started

### Install the package

pip install git+https://github.com/MaadhiniNarayanaKumar/pyoptionpricing.git

To run the API as well: `pip install "pyoptionpricing[api] @ git+https://github.com/MaadhiniNarayanaKumar/pyoptionpricing.git"`

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Set up the Python environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"        # or: pip install -r requirements-dev.txt
```

The library itself depends only on NumPy and SciPy, so `pip install .` is enough to use it from Python. The `api` extra (`pip install ".[api]"`) adds FastAPI, Pydantic and Uvicorn for the backend, and `dev` adds the test tools.

### 3. Run the backend

```bash
uvicorn backend.main:app --reload
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 4. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

- App: http://localhost:3000

## Usage Example

```python
from pyoptionpricing import OptionFactory, PricingEngine

option = OptionFactory.create(
    model="black_scholes",
    style="european",
    option_type="call",
    spot=100, strike=100, maturity=1.0, rate=0.05, volatility=0.20,
)

engine = PricingEngine(option)
print(engine.price())     # ~10.4506
print(engine.greeks())    # delta, gamma, theta, vega, rho
print(engine.run())       # model name, price, Greeks (+ standard error for Monte Carlo)
```

Swapping `model="binomial"` or `model="monte_carlo"` requires no other change to the client code.

### Demo script

```bash
python demo.py
```

This walks through one example per feature: Black-Scholes and parity, validation, every model through the factory and engine, binomial convergence, American vs European, Monte Carlo error, Asian and Barrier, implied volatility, and the smile.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/price` | Price an option with the chosen model (plus standard error for simulations) |
| POST | `/greeks` | Compute Greeks |
| POST | `/compare` | Price the same contract with every model side by side |
| POST | `/convergence` | Binomial price by tree depth and Monte Carlo price by path count, against Black-Scholes |
| POST | `/payoff` | Payoff and profit at maturity across terminal spot prices |
| POST | `/paths` | Sample simulated GBM price paths |
| POST | `/implied-vol` | Implied volatility from a market price, with any model |
| POST | `/vol-surface` | Implied volatility across strikes and maturities from synthetic skewed prices |
| GET | `/models` | Supported (model, style) pairs and the extra inputs each needs |
| GET | `/health` | Health check |

Every request takes `spot`, `strike`, `maturity`, `rate`, `volatility`, `option_type`, `model` and `style`. Model-specific inputs are optional (`steps`; `n_paths`, `n_steps`, `seed`; `barrier`, `barrier_type`) and are ignored by models that do not use them. Invalid inputs return HTTP 422 with a readable message.

Full request and response schemas are available in Swagger at `/docs`. Allowed frontend origins can be set with `FRONTEND_ORIGINS` (comma-separated, default `http://localhost:3000`).

## Testing

```bash
pytest --cov=pyoptionpricing --cov=backend --cov-report=term-missing
```

The suite covers the library and every API endpoint. Current coverage is about 99%.

Correctness checks include:

- Put-call parity
- Binomial Tree convergence to Black-Scholes
- Greeks validated against finite-difference bumps
- Monte Carlo prices within standard error of Black-Scholes
- American put price at least the European put price
- Barrier knock-in plus knock-out equals the vanilla price
- Asian call price at most the European call price

Target coverage: 80%+

## Documentation

- [UML class diagram](docs/uml.md)
- [Architecture and request flow](docs/architecture.md)
- [Final report](docs/report.md): OOP principles mapped to classes and files, results, challenges

## Deployment

Both parts run on Vercel as two separate projects from this one repository.

### Backend (FastAPI on Vercel)

Create a Vercel project from the repository with **Root Directory** left at the repository root and **Framework Preset** set to FastAPI (or Other). No build command is needed.

- `pyproject.toml` sets `[tool.vercel] entrypoint = "backend.main:app"`. Vercel installs from `pyproject.toml` and ignores `requirements.txt` when both exist, and its `uv sync --no-dev` skips optional extras. So the API packages are also listed in the `api` dependency group, which `[tool.uv] default-groups` installs. Keep that group in step with the `api` extra.
- `vercel.json` sets the function timeout and leaves the frontend, tests and docs out of the bundle.
- Set the environment variable `FRONTEND_ORIGINS` to the frontend's URL (comma-separated for more than one), for example `https://your-frontend.vercel.app`. Redeploy after changing it.
- Vercel gives each deployment its own URL, so you can also set `FRONTEND_ORIGIN_REGEX` to a pattern that matches all of them, for example `https://pyoptionpricing-.*-maadhinis-projects\.vercel\.app`.

With the Vercel CLI instead of Git:

```bash
npm i -g vercel
vercel          # preview deployment
vercel --prod   # production deployment
```

Check it with `https://<your-backend>.vercel.app/health` and `https://<your-backend>.vercel.app/docs`.

### Frontend (Next.js on Vercel)

Create a second project with **Root Directory** set to `frontend`, and set `NEXT_PUBLIC_API_URL` to the backend URL.

### Links

- **Backend:** https://pyoptionpricing.vercel.app (Swagger docs at https://pyoptionpricing.vercel.app/docs)
- **Frontend / demo:** https://pyoptionpricingui.vercel.app

## Deliverables

- `pyoptionpricing` package with the full option hierarchy
- Black-Scholes, Binomial and Monte Carlo pricing models plus Asian/Barrier options
- Implied volatility and volatility surface utilities
- FastAPI backend with Swagger documentation
- Next.js frontend with convergence and volatility charts
- Test suite with coverage report
- UML and system architecture diagrams (`docs/`)
- Final report

## Roadmap

- Variance reduction for Monte Carlo (antithetic and control variates)
- Volatility surface across maturities
- Scheduled data ingestion and calibration (e.g. Airflow)

## License

Released under the MIT License. See [LICENSE](LICENSE). Developed as coursework at Rutgers University.
