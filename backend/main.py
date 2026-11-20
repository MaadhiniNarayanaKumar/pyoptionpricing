import inspect
import os

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pyoptionpricing import (
    OptionFactory,
    PricingEngine,
    binomial_convergence,
    implied_volatility,
    monte_carlo_convergence,
    payoff_curve,
    sample_paths,
    volatility_surface,
)

from .schemas import (
    ConvergenceRequest,
    ImpliedVolRequest,
    OptionRequest,
    PathsRequest,
    PayoffRequest,
    VolSurfaceRequest,
)

app = FastAPI(
    title="pyoptionpricing API",
    description="Option prices, Greeks, model comparison and implied volatility.",
    version="0.1.0",
)

_origins = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
# Vercel gives every deployment its own URL, so a regex can allow them all.
# Example: FRONTEND_ORIGIN_REGEX=https://pyoptionpricing-.*-maadhinis-projects\.vercel\.app
_origin_regex = os.environ.get("FRONTEND_ORIGIN_REGEX") or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _origins.split(",") if origin.strip()],
    allow_origin_regex=_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

_BASE_PARAMS = {"self", "spot", "strike", "maturity", "rate", "volatility", "option_type"}

COMPARE_MODELS = [
    ("black_scholes", "european"),
    ("binomial", "european"),
    ("binomial", "american"),
    ("monte_carlo", "european"),
    ("asian", "european"),
    ("barrier", "european"),
]


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


def _extra_params(model, style):
    option_cls = OptionFactory.option_class(model, style)
    params = inspect.signature(option_cls.__init__).parameters
    return {name: p for name, p in params.items() if name not in _BASE_PARAMS}


def _model_kwargs(model, style, supplied):
    """Keep only the inputs this model accepts, and require the ones it needs."""
    extra = _extra_params(model, style)
    missing = [
        name for name, p in extra.items()
        if p.default is inspect.Parameter.empty and name not in supplied
    ]
    if missing:
        raise ValueError(f"Model '{model}' requires: {', '.join(missing)}.")
    return {name: value for name, value in supplied.items() if name in extra}


def _build(req: OptionRequest, model=None, style=None):
    model = model or req.model
    style = style or req.style
    return OptionFactory.create(
        model, style,
        req.spot, req.strike, req.maturity, req.rate, req.volatility, req.option_type,
        **_model_kwargs(model, style, req.model_kwargs()),
    )


def _result(option, model, style):
    run = PricingEngine(option).run()
    return {**run, "class": run["model"], "model": model, "style": style}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models")
def models():
    """Supported (model, style) pairs and the extra inputs each one takes."""
    return [
        {
            "model": model,
            "style": style,
            "class": OptionFactory.option_class(model, style).__name__,
            "parameters": {
                name: {"required": p.default is inspect.Parameter.empty,
                       "default": None if p.default is inspect.Parameter.empty else p.default}
                for name, p in _extra_params(model, style).items()
            },
        }
        for model, style in OptionFactory.available()
    ]


@app.post("/price")
def price(req: OptionRequest):
    engine = PricingEngine(_build(req))
    result = {"model": req.model, "style": req.style, "price": engine.price()}
    if hasattr(engine.option, "standard_error"):
        result["standard_error"] = engine.option.standard_error()
    return result


@app.post("/greeks")
def greeks(req: OptionRequest):
    return {"model": req.model, "style": req.style, "greeks": PricingEngine(_build(req)).greeks()}


@app.post("/compare")
def compare(req: OptionRequest):
    """Every model on the same contract. Barrier is included only when a barrier is given."""
    supplied = req.model_kwargs()
    results = []
    for model, style in COMPARE_MODELS:
        if model == "barrier" and not {"barrier", "barrier_type"} <= supplied.keys():
            continue
        results.append(_result(_build(req, model, style), model, style))
    return {"results": results}


@app.post("/convergence")
def convergence(req: ConvergenceRequest):
    common = (req.spot, req.strike, req.maturity, req.rate, req.volatility, req.option_type)
    binomial_args = {"american": req.style.lower() == "american"}
    if req.steps_list:
        binomial_args["steps_list"] = req.steps_list
    mc_args = {"seed": 42 if req.seed is None else req.seed}
    if req.path_counts:
        mc_args["path_counts"] = req.path_counts
    return {
        "binomial": binomial_convergence(*common, **binomial_args),
        "monte_carlo": monte_carlo_convergence(*common, **mc_args),
    }


@app.post("/payoff")
def payoff(req: PayoffRequest):
    """Vanilla payoff and profit at maturity. The premium defaults to the chosen model's price."""
    premium = req.premium if req.premium is not None else _build(req).price()
    points = payoff_curve(
        req.strike, req.option_type, premium=premium,
        spot_min=req.spot_min, spot_max=req.spot_max, n_points=req.n_points,
    )
    return {"premium": premium, "strike": req.strike, "points": points}


@app.post("/paths")
def paths(req: PathsRequest):
    simulated = sample_paths(
        req.spot, req.maturity, req.rate, req.volatility,
        n_paths=req.n_display,
        n_steps=req.n_steps or 100,
        seed=42 if req.seed is None else req.seed,
    )
    return {**simulated, "strike": req.strike, "barrier": req.barrier}


@app.post("/implied-vol")
def implied_vol(req: ImpliedVolRequest):
    iv = implied_volatility(
        req.market_price, req.model, req.style, req.option_type,
        req.spot, req.strike, req.maturity, req.rate,
        **_model_kwargs(req.model, req.style, req.model_kwargs()),
    )
    return {"implied_vol": iv, "market_price": req.market_price, "model": req.model}


@app.post("/vol-surface")
def vol_surface(req: VolSurfaceRequest):
    strikes = req.strikes or np.linspace(0.7 * req.spot, 1.3 * req.spot, 13).round(2).tolist()
    maturities = req.maturities or [0.25, 0.5, 1.0, 2.0]
    supplied = {"steps": req.steps} if req.steps is not None else {}
    surface = volatility_surface(
        req.spot, req.rate, strikes, maturities,
        option_type=req.option_type, model=req.model, style=req.style,
        atm_vol=req.atm_vol, skew=req.skew,
        **_model_kwargs(req.model, req.style, supplied),
    )
    return {"strikes": strikes, "surface": surface}
