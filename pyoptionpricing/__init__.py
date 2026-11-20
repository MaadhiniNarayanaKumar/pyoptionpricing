from .base import Option                 # abstract base: inputs, validation, price()/greeks()
from .european import EuropeanOption     # exercise only at maturity
from .american import AmericanOption     # exercise any time

from .path_dependent import PathDependentOption  # payoff depends on price path
from .black_scholes import BlackScholesOption   # closed form price and Greeks

from .binomial import BinomialEuropeanOption, BinomialAmericanOption  # CRR tree
from .monte_carlo import MonteCarloEuropeanOption                   # simulation

from .asian import AsianOption             # average price payoff
from .barrier import BarrierOption         # barrier-based payoff
from .factory import OptionFactory         # creates an option from model/style/type
from .engine import PricingEngine          # prices any Option through one interface
from .implied_vol import implied_volatility, volatility_smile      # vol from market price; smile

from .analysis import (
    binomial_convergence,          # tree price vs number of steps
    monte_carlo_convergence,       # mc price vs number of paths
    payoff_curve,                  # payoff vs spot price at maturity
    sample_paths,                  # sample paths
    volatility_surface,            # volatility surface
)