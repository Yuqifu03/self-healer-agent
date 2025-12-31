from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from state import AgentState
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

def call_model(state: AgentState):
    time.sleep(12)
    phase = state.get("phase", "analyze_error")
    messages = state.get("messages", [])
    
    if messages and messages[-1].type == "ai" and not messages[-1].tool_calls:
        phase_map = {
            "analyze_error": "locate_code",
            "locate_code": "propose_fix",
            "propose_fix": "apply_fix",
            "apply_fix": "validate"
        }
        if phase in phase_map:
            old_phase = phase
            phase = phase_map[phase]
            logger.log_step(f"--- Phase Transition: {old_phase} -> {phase} ---")

    logger.log_step(f"Agent Phase: {phase}")
    system_prompt = PHASE_SYSTEM_PROMPTS.get(phase, "")

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

    updates = {
        "messages": [response],
        "iteration_count": state["iteration_count"] + 1,
        "phase": phase  
    }

    if phase in {"analyze_error", "validate"} and response.content:
        updates["last_error"] = response.content

    if response.tool_calls:
        for tool in response.tool_calls:
            if "path" in tool["args"]:
                updates["current_file"] = tool["args"]["path"]
                break

    if phase == "validate":
        updates["is_fixed"] = bool(response.content and "DONE" in response.content)

    if "No fix is needed" in response.content or "DONE" in response.content:
        updates["phase"] = "done"
    
    return updates

# def call_model(state: AgentState):
#     """Thinking node: allows the LLM to decide what to do next."""
#     logger.log_step("Thinking (Gemini)")
    
#     messages = state["messages"]
    
#     response = llm.invoke(messages)
    
#     if response.content:
#         logger.log_thought(response.content)
    
#     if response.tool_calls:
#         for tool in response.tool_calls:
#             logger.log_tool_call(tool["name"], tool["args"])
            
#     return {"messages": [response], "iteration_count": state.get("iteration_count", 0) + 1}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Conditional routing: determines whether to continue executing tools or terminate the task."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if state.get("iteration_count", 0) >= config.MAX_ITERATIONS:
        logger.log_error("Max iterations reached. Force stopping.")
        return "__end__"

    if not last_message.tool_calls:
        logger.log_success("Gemini has provided a final answer.")
        return "__end__"
    
    return "tools"

def route_by_phase(state: AgentState) -> Literal["tools", "agent", "__end__"]:
    if state.get("phase") == "done":
        return "__end__"
    messages = state["messages"]
    last_message = messages[-1]

    if state["iteration_count"] >= config.MAX_ITERATIONS:
        logger.log_error("Max iterations reached.")
        return "__end__"

    if last_message.tool_calls:
        return "tools"

    phase = state["phase"]
    if phase == "validate":
        if "DONE" in (last_message.content or ""):
            return "__end__"
        else:
            return "__end__"

    return "agent"


workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("agent", route_by_phase)

app = workflow.compile()