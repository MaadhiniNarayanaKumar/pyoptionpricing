# Architecture

The system has three layers. Each layer depends only on the one below it.

```mermaid
flowchart LR
    subgraph Browser
        UI["Next.js app<br/>(React, TypeScript, Recharts)<br/>frontend/src"]
        API_TS["api.ts<br/>single fetch client"]
        UI --> API_TS
    end

    subgraph Server["FastAPI service (backend/)"]
        ROUTES["main.py routes<br/>/price /greeks /compare /convergence<br/>/payoff /paths /implied-vol /vol-surface"]
        SCHEMAS["schemas.py<br/>Pydantic request models"]
        ROUTES --- SCHEMAS
    end

    subgraph Library["pyoptionpricing (pure Python)"]
        FACTORY["OptionFactory"]
        ENGINE["PricingEngine"]
        MODELS["Option hierarchy<br/>Black-Scholes, Binomial,<br/>Monte Carlo, Asian, Barrier"]
        TOOLS["implied_vol.py, analysis.py, paths.py"]
        FACTORY --> MODELS
        ENGINE --> MODELS
        TOOLS --> FACTORY
    end

    API_TS -- "HTTP JSON (CORS)" --> ROUTES
    ROUTES --> FACTORY
    ROUTES --> ENGINE
    ROUTES --> TOOLS
```

## Request flow (`POST /price`)

```mermaid
sequenceDiagram
    participant U as Browser (Dashboard)
    participant A as api.ts
    participant R as FastAPI /price
    participant F as OptionFactory
    participant O as Option subclass
    participant E as PricingEngine

    U->>A: getPrice(request)
    A->>R: POST /price (JSON)
    R->>R: Pydantic validation (422 on bad input)
    R->>F: create(model, style, ..., **model kwargs)
    F->>O: construct (validates inputs, ValueError -> 422)
    R->>E: PricingEngine(option).price()
    E->>O: price()
    O-->>E: float
    R-->>A: {"model", "style", "price", "standard_error"?}
    A-->>U: PriceResponse
```

## Design rules

- **No model logic in routes.** Each route checks the request, builds options through `OptionFactory`, and calls library functions. All maths lives in `pyoptionpricing`.
- **Model-specific inputs are filtered automatically.** The API reads the constructor signature of the class that the factory resolves. It passes only the inputs that class accepts (for example `steps` for binomial, `barrier` for barrier options) and reports any required inputs that are missing.
- **One error format.** Pydantic validation errors and library `ValueError`s both return HTTP 422. The frontend shows field-level errors under the matching input, and other messages above the button.
- **One fetch client.** Every frontend call goes through `frontend/src/lib/api.ts`.
