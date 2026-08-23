"""Gemini provider backed by langchain-google-genai."""

from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from llm.base import BaseLLM, LLMStats, invoke_with_retry


# USD per 1M tokens for gemini-2.5-flash (as of 2026-08); adjust freely.
GEMINI_FLASH_PRICING = {"input": 0.30, "output": 2.50}


class GeminiLLM(BaseLLM):
    """Gemini reasoning model with tool binding, retries, and usage tracking."""

    name = "gemini"

    def __init__(
        self,
        *,
        model: str,
        temperature: float,
        api_key: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.model_name = model
        self.temperature = temperature
        self.api_key = api_key
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
        )
        self._tools: list = []
        self._model = self._llm
        self._stats = LLMStats(pricing=GEMINI_FLASH_PRICING)

    def bind_tools(self, tools: list) -> "GeminiLLM":
        self._tools = tools
        self._model = self._llm.bind_tools(tools)
        return self

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        def _call() -> AIMessage:
            response = self._model.invoke(list(messages))
            self._record_usage(response)
            return response

        try:
            return invoke_with_retry(
                _call,
                max_retries=self.max_retries,
                base_delay=self.base_delay,
            )
        except Exception:
            self._stats.failed_calls += 1
            raise

    def _record_usage(self, response: AIMessage) -> None:
        self._stats.calls += 1
        usage = getattr(response, "usage_metadata", None) or {}
        self._stats.prompt_tokens += int(usage.get("prompt_token_count", 0))
        self._stats.completion_tokens += int(usage.get("candidates_token_count", 0))

    def stats(self) -> LLMStats:
        return self._stats
