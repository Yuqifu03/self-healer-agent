"""Retry helper and usage/cost statistics tests."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.base import LLMStats, invoke_with_retry  # noqa: E402


class FlakyCaller:
    def __init__(self, failures_before_success: int):
        self.attempts = 0
        self.failures = failures_before_success

    def __call__(self):
        self.attempts += 1
        if self.attempts <= self.failures:
            raise RuntimeError("transient failure")
        return "ok"


def test_retry_succeeds_after_transient_failures():
    caller = FlakyCaller(failures_before_success=2)
    result = invoke_with_retry(caller, max_retries=3, base_delay=0)
    assert result == "ok"
    assert caller.attempts == 3


def test_retry_raises_after_max_attempts():
    caller = FlakyCaller(failures_before_success=99)
    with pytest.raises(RuntimeError):
        invoke_with_retry(caller, max_retries=2, base_delay=0)
    assert caller.attempts == 2


def test_non_retryable_failure_raises_immediately():
    caller = FlakyCaller(failures_before_success=99)
    with pytest.raises(RuntimeError):
        invoke_with_retry(
            caller,
            max_retries=5,
            base_delay=0,
            retryable=lambda exc: False,
        )
    assert caller.attempts == 1


def test_llm_stats_cost_estimate():
    stats = LLMStats(pricing={"input": 0.30, "output": 2.50})
    stats.prompt_tokens = 1_000_000
    stats.completion_tokens = 1_000_000
    assert stats.total_tokens == 2_000_000
    assert stats.estimated_cost_usd == pytest.approx(2.80)
