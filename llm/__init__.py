"""LLM provider layer.

The rest of the codebase talks to ``BaseLLM`` only, so swapping the reasoning
model (Gemini today) for another provider is a factory-level change.
"""

from llm.base import BaseLLM, LLMStats
from llm.factory import build_llm

__all__ = ["BaseLLM", "LLMStats", "build_llm"]
