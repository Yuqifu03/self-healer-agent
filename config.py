import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # LLM provider used for reasoning ("gemini" is the only bundled provider;
    # the factory in llm/factory.py is the extension point for more).
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    
    MODEL_NAME = "gemini-2.5-flash"
    TEMPERATURE = 0       
    
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root_env = os.getenv(
        "PROJECT_ROOT", 
        os.path.join(_current_dir, "sandbox/example_project")
    )
    PROJECT_ROOT = os.path.abspath(os.path.expanduser(_project_root_env))

    MAX_ITERATIONS = 10

    # Per-execution timeout (seconds) applied to every subprocess launched by
    # the executor tools. Prevents a runaway script from blocking the loop.
    EXEC_TIMEOUT = int(os.getenv("EXEC_TIMEOUT", "30"))

    # Retry policy for transient LLM failures (rate limits, 5xx, timeouts).
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.0"))
    
    LOG_DIR = "logs"
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")

config = Config()
