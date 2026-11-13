from .base import Option


class PricingEngine:
    """Prices any Option through its own price() and greeks() methods."""

    def __init__(self, option):
        if not isinstance(option, Option):
            raise TypeError("PricingEngine expects an Option instance.")
        self._option = option

    @property
    def option(self):
        return self._option

    def price(self):
        return self._option.price()

    def greeks(self):
        return self._option.greeks()

    def run(self):
        """Price, Greeks, and the standard error for simulation-based models."""
        result = {
            "model": type(self._option).__name__,
            "price": self.price(),
            "greeks": self.greeks(),
        }
        if hasattr(self._option, "standard_error"):
            result["standard_error"] = self._option.standard_error()
        return result
