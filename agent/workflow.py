from datetime import datetime
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from agent.prompts import PHASE_SYSTEM_PROMPTS
from config import config
from llm.base import BaseLLM
from state import AgentPhase, AgentState
from tools.editor_tools import insert_line, patch_file, write_file
from tools.executor_tools import run_python_script
from tools.explorer_tools import find_file, grep_text, list_files, read_header
from utils.logger import logger

tools = [
    list_files, find_file, grep_text, read_header,
    write_file, patch_file, insert_line,
    run_python_script,
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _append_trace(state: AgentState, entry: dict) -> None:
    trace = state.setdefault("trace", [])
    trace.append({"ts": _now(), **entry})


def get_next_phase_logic(state: AgentState, response) -> AgentPhase:
    """Advance the state machine after an agent step (tool call or reasoning)."""
    current_phase = state.get("phase", "analyze_error")

    if response.tool_calls:
        return current_phase

    if current_phase == "validate":
        if response.content and "DONE" in response.content:
            return "done"
        logger.log_error("Validation failed. Rewinding to analyze_error...")
        return "analyze_error"

    phase_map = {
        "analyze_error": "locate_code",
        "locate_code": "propose_fix",
        "propose_fix": "apply_fix",
        "apply_fix": "validate",
    }

    next_phase = phase_map.get(current_phase, current_phase)
    if next_phase != current_phase:
        logger.log_step(f"--- Phase Transition: {current_phase} -> {next_phase} ---")
        _append_trace(state, {"type": "phase", "from": current_phase, "to": next_phase})
    return next_phase


def route_logic(state: AgentState) -> Literal["tools", "agent", "end"]:
    last_message = state["messages"][-1]

    if state["iteration_count"] >= config.MAX_ITERATIONS:
        logger.log_error("Max iterations reached. Force stopping.")
        return "end"

    if last_message.tool_calls:
        return "tools"

    if state.get("phase") == "done":
        logger.log_success("Task accomplished.")
        return "end"

    return "agent"


def create_app(llm: BaseLLM):
    """Build the compiled LangGraph state machine around an LLM provider."""
    tool_node = ToolNode(tools)

    def call_model(state: AgentState):
        phase = state.get("phase", "analyze_error")
        messages = state.get("messages", [])

        logger.log_step(f"Agent Phase: {phase}")
        _append_trace(state, {"type": "phase_enter", "phase": phase})

        system_prompt = (
            f"{PHASE_SYSTEM_PROMPTS.get(phase, '')}\n\n"
            f"[IMPORTANT] Current Phase: {phase}"
        )
        formatted_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        response = llm.invoke(formatted_messages)

        if response.content:
            logger.log_thought(response.content)
            _append_trace(state, {"type": "thought", "content": response.content})
        if response.tool_calls:
            for tool_call in response.tool_calls:
                logger.log_tool_call(tool_call["name"], tool_call["args"])
                _append_trace(
                    state,
                    {
                        "type": "action",
                        "tool": tool_call["name"],
                        "args": tool_call["args"],
                    },
                )

        next_phase = get_next_phase_logic(state, response)

        updates = {
            "messages": [response],
            "iteration_count": state["iteration_count"] + 1,
            "phase": next_phase,
        }

        if response.tool_calls:
            for tool_call in response.tool_calls:
                if "path" in tool_call["args"]:
                    updates["current_file"] = tool_call["args"]["path"]
                    break

        return updates

    def run_tools(state: AgentState, run_config: RunnableConfig | None = None):
        """Execute tool calls and record every observation for full-chain tracing."""
        result = tool_node.invoke(state, config=run_config)
        for message in result.get("messages", []):
            logger.log_observation(message.content)
            _append_trace(state, {"type": "observation", "content": message.content})
        return result

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", run_tools)
    workflow.set_entry_point("agent")
    workflow.add_edge("tools", "agent")
    workflow.add_conditional_edges(
        "agent",
        route_logic,
        {"tools": "tools", "agent": "agent", "end": END},
    )
    return workflow.compile()


_app = None


def get_app():
    """Lazily build (once) the default application using the configured provider."""
    global _app
    if _app is None:
        from llm.factory import build_llm

        _app = create_app(build_llm(tools=tools))
    return _app


def __getattr__(name: str):
    # Backwards-compatible lazy access: `from agent.workflow import app`.
    if name == "app":
        return get_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
