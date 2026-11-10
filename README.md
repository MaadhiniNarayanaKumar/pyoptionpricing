# pyoptionpricing

Object-oriented option pricing library. Day 1 covers the abstract contract hierarchy, an analytical Black-Scholes pricer, and a factory. Binomial trees, Monte Carlo, exotics, and the API come next.

## Layout

- `pyoptionpricing/` — pricing library
- `backend/` — FastAPI app (Day 3)
- `frontend/` — Next.js app (Day 4)
- `tests/` — pytest

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Black-Scholes

```python
from pyoptionpricing import BlackScholesOption, OptionFactory

option = BlackScholesOption(
    S=100, K=100, T=1, r=0.05, sigma=0.20, option_type="call"
)
option.price()    # about 10.4506
option.greeks()

same = OptionFactory.create(
    "black_scholes", "european", "call",
    S=100, K=100, T=1, r=0.05, sigma=0.20,
)
```

`S`, `K`, `T`, and `sigma` must be positive. `option_type` is `"call"` or `"put"`.
