import logging
import os
import sys
from datetime import datetime
from colorama import Fore, Style, init

# 初始化 colorama，autoreset=True 会在每次打印后自动重置颜色
init(autoreset=True)

class AgentLogger:
    def __init__(self, log_dir="logs"):
        # 创建日志文件夹
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建以时间命名的日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"agent_trace_{timestamp}.log")
        
        # 基础配置
        self.logger = logging.getLogger("FileAgent")
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器（记录最完整的信息，不带颜色标签）
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def log_step(self, step_name: str):
        """记录 LangGraph 节点的切换"""
        divider = "═" * 60
        msg = f"\n{divider}\n[ENTER STEP]: {step_name}\n{divider}"
        print(f"{Fore.MAGENTA}{Style.BRIGHT}{msg}")
        self.logger.info(f"--- STEP: {step_name} ---")

    def log_thought(self, thought: str):
        """记录 Agent 的推理过程"""
        print(f"{Fore.CYAN}💭 [THOUGHT]: {Style.RESET_ALL}{thought}")
        self.logger.info(f"[THOUGHT] {thought}")

    def log_tool_call(self, tool_name: str, args: dict):
        """记录工具调用"""
        msg = f"🛠️ [ACTION]: Using tool [{tool_name}] with args: {args}"
        print(f"{Fore.YELLOW}{msg}")
        self.logger.info(f"[ACTION] {tool_name} | Args: {args}")

    def log_observation(self, observation: str):
        """记录工具执行后的反馈"""
        # 终端只显示前 300 个字符，防止刷屏；日志文件记录完整内容
        preview = (observation[:300] + "...") if len(observation) > 300 else observation
        print(f"{Fore.GREEN}👁️ [OBSERVATION]: {Style.RESET_ALL}{preview}")
        self.logger.info(f"[OBSERVATION] {observation}")

    def log_error(self, error_msg: str):
        """记录系统级错误"""
        print(f"{Fore.RED}{Style.BRIGHT}❌ [SYSTEM ERROR]: {error_msg}")
        self.logger.error(f"[ERROR] {error_msg}")

    def log_success(self, final_msg: str):
        """记录任务完成"""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ [SUCCESS]: {final_msg}")
        self.logger.info(f"[SUCCESS] {final_msg}")

# 创建全局单例对象，方便其他模块调用
logger = AgentLogger()