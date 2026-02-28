"""LiteLLM wrapper with PolitOS defaults."""

import litellm

from src.core.config import LLMConfig, load_config


def _model_id(cfg: LLMConfig) -> str:
    """Build the LiteLLM model identifier from config."""
    provider = cfg.provider
    model = cfg.model
    # LiteLLM expects provider/model for some providers
    if provider in ("claude", "anthropic"):
        return model  # litellm recognises claude model names directly
    if provider == "openai":
        return model
    if "/" in model:
        return model
    return f"{provider}/{model}"


def completion(
    messages: list[dict[str, str]],
    *,
    config: LLMConfig | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Call LiteLLM completion with PolitOS defaults. Returns the response text."""
    if config is None:
        config = load_config().llm

    model = _model_id(config)
    temp = temperature if temperature is not None else config.temperature
    tokens = max_tokens if max_tokens is not None else config.max_tokens

    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
        )
    except Exception:
        # Try fallback model if configured
        if config.fallback:
            response = litellm.completion(
                model=config.fallback,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
        else:
            raise

    return response.choices[0].message.content
