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
    initial_state = {
        "messages": [
            HumanMessage(content=f"Task: {task}")
        ],
        "iteration_count": 0,
        "phase": "analyze_error",
    }

    logger.log_step("Initializing FileAgent-SelfHealer")
    print(f"Targeting Project: {config.PROJECT_ROOT}")

    try:
        final_state = app.invoke(initial_state)
        logger.log_success("Workflow completed.")
        print(final_state["messages"][-1].content)
    except Exception as e:
        logger.log_error(f"Execution failed: {str(e)}")


if __name__ == "__main__":
    demo_task = "Explore the project directory, find the main entry point, run it, and fix any errors you encounter."
    
    run_agent(demo_task)