import logging
import os
import sys
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

class AgentLogger:
    def __init__(self, log_dir="logs"):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"agent_trace_{timestamp}.log")
        
        self.logger = logging.getLogger("FileAgent")
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def log_step(self, step_name: str):
        """Log transitions between LangGraph nodes"""
        divider = "═" * 60
        msg = f"\n{divider}\n[ENTER STEP]: {step_name}\n{divider}"
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{msg}")
        self.logger.info(f"--- STEP: {step_name} ---")

    def log_thought(self, thought: str):
        """Log the agent's reasoning process"""
        print(f"{Fore.CYAN}💭 [THOUGHT]: {Style.RESET_ALL}{thought}")
        self.logger.info(f"[THOUGHT] {thought}")

    def log_tool_call(self, tool_name: str, args: dict):
        """Log tool invocations"""
        msg = f"🛠️ [ACTION]: Using tool [{tool_name}] with args: {args}"
        print(f"{Fore.YELLOW}{msg}")
        self.logger.info(f"[ACTION] {tool_name} | Args: {args}")

    def log_observation(self, observation: str):
        """Log feedback/results after tool execution"""
        preview = (observation[:300] + "...") if len(observation) > 300 else observation
        print(f"{Fore.GREEN}👁️ [OBSERVATION]: {Style.RESET_ALL}{preview}")
        self.logger.info(f"[OBSERVATION] {observation}")

    def log_error(self, error_msg: str):
        """Log system-level errors"""
        print(f"{Fore.RED}{Style.BRIGHT}❌ [SYSTEM ERROR]: {error_msg}")
        self.logger.error(f"[ERROR] {error_msg}")

    def log_success(self, final_msg: str):
        """Log successful task completion"""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ [SUCCESS]: {final_msg}")
        self.logger.info(f"[SUCCESS] {final_msg}")

logger = AgentLogger()