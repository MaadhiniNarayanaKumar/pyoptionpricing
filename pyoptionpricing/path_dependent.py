from .base import Option

class PathDependentOption(Option):
    """payoff depends on the full price path, not just the final price"""