# UML class diagram

The diagram shows the `pyoptionpricing` class hierarchy, the factory, and the pricing engine. Abstract classes are marked `<<abstract>>`. `_BinomialOption` and `_PathMonteCarlo` are internal base classes that hold shared numerical code.

```mermaid
classDiagram
    direction TB

    class Option {
        <<abstract>>
        -_spot: float
        -_strike: float
        -_maturity: float
        -_rate: float
        -_volatility: float
        -_option_type: str
        +spot / strike / maturity / rate / volatility / option_type (read-only)
        +price()* float
        +greeks()* dict
    }

    class EuropeanOption {
        <<abstract>>
    }
    class AmericanOption {
        <<abstract>>
    }
    class PathDependentOption {
        <<abstract>>
    }

    class BlackScholesOption {
        -_d1() float
        -_d2() float
        +price() float
        +greeks() dict
    }

    class _BinomialOption {
        <<mixin>>
        -_steps: int
        +steps (read-only)
        -_tree(volatility, rate)
        +price() float
        +greeks() dict
    }
    class BinomialEuropeanOption {
        _american = False
    }
    class BinomialAmericanOption {
        _american = True
    }

    class MonteCarloEuropeanOption {
        -_n_paths: int
        -_seed: int
        -_z: ndarray
        -_discounted_payoffs(...)
        +price() float
        +standard_error() float
        +greeks() dict
    }

    class _PathMonteCarlo {
        <<abstract>>
        -_n_paths / _n_steps / _seed
        -_z: ndarray
        -_paths(...)
        -_discounted_payoffs(...)*
        +price() float
        +standard_error() float
        +greeks() dict
    }
    class AsianOption {
        -_discounted_payoffs(...)
    }
    class BarrierOption {
        -_barrier: float
        -_barrier_type: str
        -_hit(paths, spot, barrier)
        -_discounted_payoffs(...)
    }

    class OptionFactory {
        -_MODEL_ALIASES: dict
        -_REGISTRY: dict
        +option_class(model, style)$ type
        +create(model, style, ...)$ Option
        +available()$ list
    }

    class PricingEngine {
        -_option: Option
        +option (read-only)
        +price() float
        +greeks() dict
        +run() dict
    }

    Option <|-- EuropeanOption
    Option <|-- AmericanOption
    Option <|-- PathDependentOption

    EuropeanOption <|-- BlackScholesOption
    EuropeanOption <|-- BinomialEuropeanOption
    EuropeanOption <|-- MonteCarloEuropeanOption
    AmericanOption <|-- BinomialAmericanOption
    _BinomialOption <|-- BinomialEuropeanOption
    _BinomialOption <|-- BinomialAmericanOption

    PathDependentOption <|-- _PathMonteCarlo
    _PathMonteCarlo <|-- AsianOption
    _PathMonteCarlo <|-- BarrierOption

    OptionFactory ..> Option : creates
    PricingEngine o-- Option : prices
```

## Supporting modules (functions, not classes)

| Module | Contents |
| --- | --- |
| `paths.py` | `standard_normals`, `simulate_paths` (discrete GBM), `vanilla_payoff` |
| `implied_vol.py` | `implied_volatility` (Brent's method over any model built by the factory), `volatility_smile` |
| `analysis.py` | `binomial_convergence`, `monte_carlo_convergence`, `payoff_curve`, `sample_paths`, `volatility_surface` |

To regenerate a draft from the code: `pip install pylint && pyreverse -o png -p pyoptionpricing pyoptionpricing`.
