import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
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
    
    LOG_DIR = "logs"

config = Config()
