from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from state import AgentState, AgentPhase
from config import config
from utils.logger import logger
from tools.explorer_tools import list_files, find_file, grep_text, read_header
from tools.editor_tools import write_file, patch_file, insert_line
from tools.executor_tools import run_python_script
from agent.prompts import PHASE_SYSTEM_PROMPTS
import time

tools = [
    list_files, find_file, grep_text, read_header,
    write_file, patch_file, insert_line,
    run_python_script
]

llm = ChatGoogleGenerativeAI(
    model=config.MODEL_NAME,
    temperature=config.TEMPERATURE,
    google_api_key=config.GOOGLE_API_KEY
).bind_tools(tools)


def get_next_phase_logic(state: AgentState, response) -> AgentPhase:
    current_phase = state.get("phase", "analyze_error")
    
    if response.tool_calls:
        return current_phase

    if current_phase == "validate":
        if response.content and "DONE" in response.content:
            return "done"
        else:
            logger.log_error("Validation failed. Rewinding to analyze_error...")
            return "analyze_error"

    phase_map = {
        "analyze_error": "locate_code",
        "locate_code": "propose_fix",
        "propose_fix": "apply_fix",
        "apply_fix": "validate",
    }
    
    next_p = phase_map.get(current_phase, current_phase)
    if next_p != current_phase:
        logger.log_step(f"--- Phase Transition: {current_phase} -> {next_p} ---")
    return next_p

def call_model(state: AgentState):
    time.sleep(1)

    phase = state.get("phase", "analyze_error")
    messages = state.get("messages", [])

    logger.log_step(f"Agent Phase: {phase}")

    system_prompt = f"{PHASE_SYSTEM_PROMPTS.get(phase, '')}\n\n[IMPORTANT] Current Phase: {phase}"
    
    formatted_messages = [
        {"role": "system", "content": system_prompt},
        *messages
    ]

    response = llm.invoke(formatted_messages)

    if response.content:
        logger.log_thought(response.content)
    if response.tool_calls:
        for tool in response.tool_calls:
            logger.log_tool_call(tool["name"], tool["args"])

    next_phase = get_next_phase_logic(state, response)

    updates = {
        "messages": [response],
        "iteration_count": state["iteration_count"] + 1,
        "phase": next_phase
    }

    if response.tool_calls:
        for tool in response.tool_calls:
            if "path" in tool["args"]:
                updates["current_file"] = tool["args"]["path"]
                break
    
    return updates

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

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_edge("tools", "agent")

workflow.add_conditional_edges(
    "agent",
    route_logic,
    {
        "tools": "tools",
        "agent": "agent",
        "end": END
    }
)

app = workflow.compile()