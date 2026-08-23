"""Deterministic FakeLLM for tests and CI smoke runs (no network)."""

from langchain_core.messages import AIMessage

from llm.base import LLMStats


class FakeLLM:
    """Alternates between a tool call and plain reasoning; DONE in validate."""

    name = "fake"
    model_name = "fake"

    def __init__(self, never_done: bool = False):
        self._calls = 0
        self._stats = LLMStats()
        self.never_done = never_done

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self._calls += 1
        self._stats.calls += 1
        system = messages[0]["content"]
        if not self.never_done and "Current Phase: validate" in system:
            return AIMessage(content="DONE")
        if self._calls % 2 == 1:
            return AIMessage(
                content="inspecting project",
                tool_calls=[
                    {
                        "name": "list_files",
                        "args": {"path": "."},
                        "id": f"t{self._calls}",
                    }
                ],
            )
        return AIMessage(content="proceeding")

    def stats(self):
        return self._stats
