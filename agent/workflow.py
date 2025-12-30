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
    """Thinking node: allows the LLM to decide what to do next."""
    logger.log_step("Thinking (Gemini)")
    
    messages = state["messages"]
    
    response = llm.invoke(messages)
    
    if response.content:
        logger.log_thought(response.content)
    
    if response.tool_calls:
        for tool in response.tool_calls:
            logger.log_tool_call(tool["name"], tool["args"])
            
    return {"messages": [response], "iteration_count": state.get("iteration_count", 0) + 1}

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

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("agent", should_continue)

app = workflow.compile()