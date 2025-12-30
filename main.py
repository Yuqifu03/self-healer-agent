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

def run_agent(task: str):
    """Initializes and executes the FileAgent-SelfHealer workflow."""
    
    # 1. Prepare Initial State with full keys defined in state.py
    # We pass the project root to the prompt template to set the system's persona
    prompt_template = get_system_prompt(config.PROJECT_ROOT)
    
    # Initialize state with default values matching AgentState
    initial_state = {
        "messages": [
            HumanMessage(content=f"Task: {task}")
        ],
        "current_file": "",
        "last_error": "",
        "iteration_count": 0,
        "is_fixed": False
    }

    logger.log_step("Initializing FileAgent-SelfHealer")
    print(f"Targeting Project: {config.PROJECT_ROOT}")

    # 2. Execute the Graph
    try:
        # The invoke method starts the LangGraph workflow
        final_state = app.invoke(initial_state)
        
        # 3. Final Summary Output
        logger.log_success("Workflow completed.")
        final_response = final_state["messages"][-1].content
        print(f"\n{'='*20} FINAL AGENT REPORT {'='*20}")
        print(final_response)
        
    except Exception as e:
        logger.log_error(f"Execution failed: {str(e)}")

if __name__ == "__main__":
    # --- NO AUTOMATIC FILE CREATION ---
    # The agent will now rely on existing files in your sandbox/example_project/ directory.
    
    # Generic task that forces the agent to use list_files and run_python_script
    demo_task = "Explore the project directory, find the main entry point, run it, and fix any errors you encounter."
    
    run_agent(demo_task)