"""Workflow graph integration tests with FakeLLM."""

import os
import sys

from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.workflow import create_app  # noqa: E402
from config import config  # noqa: E402
from tests.fake_llm import FakeLLM  # noqa: E402


def _initial_state():
    return {
        "messages": [HumanMessage(content="Task: fix errors")],
        "iteration_count": 0,
        "phase": "analyze_error",
        "trace": [],
    }


def test_graph_reaches_done_with_fake_llm():
    llm = FakeLLM()
    app = create_app(llm)
    final = app.invoke(_initial_state())
    assert final["phase"] == "done"
    assert final["iteration_count"] >= 5
    trace = final["trace"]
    assert any(e["type"] == "thought" for e in trace)
    assert any(e["type"] == "action" for e in trace)
    assert any(e["type"] == "observation" for e in trace)


def test_iteration_cap_force_stops(monkeypatch):
    monkeypatch.setattr(config, "MAX_ITERATIONS", 3)
    llm = FakeLLM(never_done=True)
    app = create_app(llm)
    final = app.invoke(_initial_state())
    assert final["iteration_count"] >= 3
    assert final["phase"] != "done"
