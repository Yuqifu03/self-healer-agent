"""Provider-agnostic LLM interface and call statistics."""

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Sequence

from langchain_core.messages import AIMessage, BaseMessage


@dataclass
class LLMStats:
    """Accumulated usage across all LLM calls in one run."""

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    failed_calls: int = 0
    pricing: dict = field(default_factory=dict)  # e.g. {"input": 0.30, "output": 2.50}

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Estimated cost in USD based on per-1M-token prices."""
        cost = 0.0
        if "input" in self.pricing:
            cost += self.prompt_tokens / 1_000_000 * self.pricing["input"]
        if "output" in self.pricing:
            cost += self.completion_tokens / 1_000_000 * self.pricing["output"]
        return round(cost, 6)


class BaseLLM(ABC):
    """Interface every reasoning provider must implement."""

    name: str = "base"

    @abstractmethod
    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        """Send a message list and return the model's reply."""

    @abstractmethod
    def bind_tools(self, tools: list) -> "BaseLLM":
        """Bind tool schemas to the underlying model (no-op if unsupported)."""

    @abstractmethod
    def stats(self) -> LLMStats:
        """Return accumulated usage/cost statistics."""


def invoke_with_retry(
    fn: Callable[[], AIMessage],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable: Callable[[Exception], bool] = lambda exc: True,
) -> AIMessage:
    """Call ``fn`` with exponential backoff and jitter on transient failures.

    Raises the last exception after ``max_retries`` attempts.
    """
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:
            attempt += 1
            if attempt >= max_retries or not retryable(exc):
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            time.sleep(delay)
