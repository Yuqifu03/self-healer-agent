from typing import Literal
# 替换导入：由 OpenAI 切换为 Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from state import AgentState
from config import config
from utils.logger import logger
from tools.explorer_tools import list_files, find_file, grep_text, read_header
from tools.editor_tools import write_file, patch_file, insert_line
from tools.executor_tools import run_python_script

# 1. 定义并绑定工具集
tools = [
    list_files, find_file, grep_text, read_header,
    write_file, patch_file, insert_line,
    run_python_script
]

# 初始化 Gemini 模型并绑定工具
# 注意：Google API Key 会自动从环境变量或 config 对象中读取
llm = ChatGoogleGenerativeAI(
    model=config.MODEL_NAME,
    temperature=config.TEMPERATURE,
    google_api_key=config.GOOGLE_API_KEY
).bind_tools(tools)

# 2. 定义节点函数
def call_model(state: AgentState):
    """思考节点：让 LLM 决定下一步做什么"""
    logger.log_step("Thinking (Gemini)")
    
    messages = state["messages"]
    
    # 调用模型
    response = llm.invoke(messages)
    
    if response.content:
        logger.log_thought(response.content)
    
    if response.tool_calls:
        for tool in response.tool_calls:
            logger.log_tool_call(tool["name"], tool["args"])
            
    return {"messages": [response], "iteration_count": state.get("iteration_count", 0) + 1}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """条件路由：判断是继续执行工具还是结束任务"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if state.get("iteration_count", 0) >= config.MAX_ITERATIONS:
        logger.log_error("Max iterations reached. Force stopping.")
        return "__end__"

    if not last_message.tool_calls:
        logger.log_success("Gemini has provided a final answer.")
        return "__end__"
    
    return "tools"

# 3. 构建图形 (Graph) - 逻辑保持不变
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("agent", should_continue)

app = workflow.compile()