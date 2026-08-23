"""Provider factory: the only place that decides which LLM backend to use."""

from config import config
from llm.base import BaseLLM
from llm.gemini import GeminiLLM


def build_llm(*, model: str | None = None, tools: list | None = None) -> BaseLLM:
    """Build the configured LLM provider, optionally with bound tools."""
    provider = (config.LLM_PROVIDER or "gemini").lower()

    if provider == "gemini":
        llm: BaseLLM = GeminiLLM(
            model=model or config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            api_key=config.GOOGLE_API_KEY or "",
            max_retries=config.LLM_MAX_RETRIES,
            base_delay=config.LLM_RETRY_BASE_DELAY,
        )
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Supported providers: gemini"
        )

    if tools:
        llm.bind_tools(tools)
    return llm
