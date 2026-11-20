from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MarketInputs(BaseModel):
    """Contract and model choice shared by every request, without volatility."""

    spot: float = Field(100.0, gt=0, description="Current price of the underlying")
    strike: float = Field(100.0, gt=0)
    maturity: float = Field(1.0, gt=0, description="Time to maturity in years")
    rate: float = Field(0.05, ge=-0.5, le=1.0, description="Continuously compounded rate")
    option_type: Literal["call", "put"] = "call"
    model: str = Field("black_scholes", description="black_scholes, binomial, monte_carlo, asian or barrier")
    style: str = Field("european", description="european or american")

    steps: Optional[int] = Field(None, ge=2, le=5000, description="Binomial tree steps")
    n_paths: Optional[int] = Field(None, ge=2, le=500_000, description="Monte Carlo paths")
    n_steps: Optional[int] = Field(None, ge=2, le=1000, description="Time steps per path")
    seed: Optional[int] = Field(None, ge=0)
    barrier: Optional[float] = Field(None, gt=0)
    barrier_type: Optional[str] = Field(None, description="up-and-out, up-and-in, down-and-out or down-and-in")

    def model_kwargs(self):
        """Model-specific inputs that were actually supplied."""
        fields = ("steps", "n_paths", "n_steps", "seed", "barrier", "barrier_type")
        return {name: getattr(self, name) for name in fields if getattr(self, name) is not None}


class OptionRequest(MarketInputs):
    volatility: float = Field(0.20, gt=0, le=5.0)


class ConvergenceRequest(OptionRequest):
    steps_list: Optional[List[int]] = Field(None, description="Tree depths to price")
    path_counts: Optional[List[int]] = Field(None, description="Monte Carlo path counts to price")


class PayoffRequest(OptionRequest):
    premium: Optional[float] = Field(
        None, ge=0, description="Premium paid. Defaults to the chosen model's price."
    )
    spot_min: Optional[float] = Field(None, ge=0)
    spot_max: Optional[float] = Field(None, gt=0)
    n_points: int = Field(101, ge=2, le=1001)


class PathsRequest(OptionRequest):
    n_display: int = Field(20, ge=1, le=200, description="Number of paths to return")


class ImpliedVolRequest(MarketInputs):
    market_price: float = Field(..., ge=0)


class VolSurfaceRequest(BaseModel):
    spot: float = Field(100.0, gt=0)
    rate: float = Field(0.05, ge=-0.5, le=1.0)
    option_type: Literal["call", "put"] = "call"
    model: str = "black_scholes"
    style: str = "european"
    strikes: Optional[List[float]] = Field(None, description="Defaults to 70% to 130% of spot")
    maturities: Optional[List[float]] = Field(None, description="Defaults to [0.25, 0.5, 1, 2]")
    atm_vol: float = Field(0.20, gt=0, le=5.0)
    skew: float = Field(-0.15, ge=-2.0, le=2.0)
    steps: Optional[int] = Field(None, ge=2, le=2000)
