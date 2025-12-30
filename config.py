import os
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()

class Config:
    # --- API 配置 ---
    # 添加 Google API Key
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    MODEL_NAME = "gemini-2.5-flash"
    TEMPERATURE = 0       
    
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.getenv(
        "PROJECT_ROOT", 
        os.path.join(_current_dir, "sandbox/example_project")
    )

    # 最大自愈循环次数
    MAX_ITERATIONS = 8
    
    LOG_DIR = "logs"

# 实例化配置对象
config = Config()