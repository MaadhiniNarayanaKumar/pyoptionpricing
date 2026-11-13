from .black_scholes import BlackScholesOption
from .binomial import BinomialEuropeanOption, BinomialAmericanOption
from .monte_carlo import MonteCarloEuropeanOption


class OptionFactory:
    """Builds the right Option subclass from a (model, style) pair."""

    _MODEL_ALIASES = {
        "black_scholes": "black_scholes",
        "black-scholes": "black_scholes",
        "bs": "black_scholes",
        "binomial": "binomial",
        "crr": "binomial",
        "monte_carlo": "monte_carlo",
        "monte-carlo": "monte_carlo",
        "mc": "monte_carlo",
    }

    _REGISTRY = {
        ("black_scholes", "european"): BlackScholesOption,
        ("binomial", "european"): BinomialEuropeanOption,
        ("binomial", "american"): BinomialAmericanOption,
        ("monte_carlo", "european"): MonteCarloEuropeanOption,
    }

    @classmethod
    def create(cls, model, style, spot, strike, maturity, rate,
               volatility, option_type, **kwargs):
        model_key = cls._MODEL_ALIASES.get(model.lower())
        if model_key is None:
            raise ValueError(f"Unknown model '{model}'.")

        style_key = style.lower()
        option_cls = cls._REGISTRY.get((model_key, style_key))
        if option_cls is None:
            supported = sorted(s for m, s in cls._REGISTRY if m == model_key)
            raise ValueError(
                f"Model '{model}' does not support style '{style}'. "
                f"Supported styles: {supported}."
            )

        return option_cls(
            spot, strike, maturity, rate, volatility, option_type, **kwargs
        )

    @classmethod
    def available(cls):
        """List of supported (model, style) pairs, useful for the API later."""
        return sorted(cls._REGISTRY)