"""Build a registered option from a model name, exercise style, and parameters."""

from __future__ import annotations

from pyoptionpricing.base import Option

_MODEL_ALIASES = {
    "bs": "black_scholes",
    "black-scholes": "black_scholes",
    "black_scholes": "black_scholes",
}


class OptionFactory:
    """Registry of ``(model, style)`` constructors.

    ``create`` forwards ``option_type`` and every extra keyword, including
    exotic inputs such as ``barrier`` and ``knock_type``, to the option class.
    """

    _registry: dict[tuple[str, str], type[Option]] = {}

    @classmethod
    def register(cls, model: str, style: str, option_cls: type[Option]) -> None:
        key = (_normalize_token("model", model), _normalize_token("style", style))
        cls._registry[key] = option_cls

    @classmethod
    def create(cls, model: str, style: str, option_type: str, **params: object) -> Option:
        key = (_canonical_model(model), _normalize_token("style", style))
        try:
            option_cls = cls._registry[key]
        except KeyError:
            registered = ", ".join(
                f"{registered_model}/{registered_style}"
                for registered_model, registered_style in sorted(cls._registry)
            ) or "(none)"
            raise ValueError(
                f"No option registered for model={model!r}, style={style!r}. "
                f"Registered: {registered}"
            ) from None
        return option_cls(option_type=option_type, **params)

    @classmethod
    def registered(cls) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(cls._registry))


def _normalize_token(label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string, got {value!r}")
    return value.strip().lower().replace(" ", "_")


def _canonical_model(model: object) -> str:
    normalized = _normalize_token("model", model)
    return _MODEL_ALIASES.get(normalized, normalized)


def _register_builtin_models() -> None:
    from pyoptionpricing.black_scholes import BlackScholesOption

    OptionFactory.register("black_scholes", "european", BlackScholesOption)


_register_builtin_models()
