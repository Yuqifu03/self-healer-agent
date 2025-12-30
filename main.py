# main.py
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent.workflow import app
from agent.prompts import get_system_prompt
from config import config
from utils.logger import logger

# Ensure environment variables are loaded from the .env file
load_dotenv()

# main.py
def run_agent(task: str):
    """Initializes and executes the FileAgent-SelfHealer workflow."""
    
    # 1. 获取包含所有战略原则的 Prompt 模板
    prompt_template = get_system_prompt('./')
    
    # 2. 关键修复：将模板渲染成具体的 SystemMessage
    # 使用 .format_messages 转换成 LangChain 可识别的消息列表
    full_messages = prompt_template.format_messages(messages=[
        HumanMessage(content=f"Task: {task}")
    ])
    
    # 3. 将包含 System Prompt 的消息流传入初始状态
    initial_state = {
        "messages": full_messages,
        "current_file": "",
        "last_error": "",
        "iteration_count": 0,
        "is_fixed": False
    }

    logger.log_step("Initializing FileAgent-SelfHealer")
    print(f"Targeting Project: {config.PROJECT_ROOT}")

    # 运行工作流
    try:
        final_state = app.invoke(initial_state)
        logger.log_success("Workflow completed.")
        print(final_state["messages"][-1].content)
    except Exception as e:
        logger.log_error(f"Execution failed: {str(e)}")

if __name__ == "__main__":
    # --- NO AUTOMATIC FILE CREATION ---
    # The agent will now rely on existing files in your sandbox/example_project/ directory.
    
    # Generic task that forces the agent to use list_files and run_python_script
    demo_task = "Explore the project directory, find the main entry point, run it, and fix any errors you encounter."
    
    run_agent(demo_task)