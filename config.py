import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    MODEL_NAME = "gemini-2.5-flash-lite"
    TEMPERATURE = 0       
    
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.getenv(
        "PROJECT_ROOT", 
        os.path.join(_current_dir, "sandbox/example_project")
    )

    MAX_ITERATIONS = 8
    
    LOG_DIR = "logs"

config = Config()