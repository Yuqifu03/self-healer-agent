import subprocess
import os
import sys
from typing import List
from langchain_core.tools import tool

from config import config
from utils.sandbox import check_path as _check_path_impl, resolve_sandbox_root

BASE_DIR = resolve_sandbox_root(config.PROJECT_ROOT)

def _check_path(path: str) -> str:
    """Resolve a path relative to the sandbox root, rejecting escapes."""
    return _check_path_impl(BASE_DIR, path)

@tool
def run_python_script(script_path: str, script_args: List[str] = None) -> str:
    """
    Execute a Python script and return its STDOUT and STDERR. 
    
    Args:
        script_path: The relative path to the python script to run.
        script_args: A list of string arguments to pass to the script (e.g., ["arg1", "arg2"]).
    """
    # Use an empty list if no arguments are provided to ensure a clean schema
    if script_args is None:
        script_args = []
        
    try:
        target_script = _check_path(script_path)
        if not os.path.exists(target_script):
            return f"Error: File {script_path} not found."

        cmd = [sys.executable, target_script]
        cmd.extend(script_args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.EXEC_TIMEOUT,
            cwd=BASE_DIR
        )

        output = []
        if result.stdout:
            output.append(f"--- STDOUT ---\n{result.stdout}")
        
        if result.stderr:
            output.append(f"--- STDERR (Potential Bugs) ---\n{result.stderr}")
        
        if not result.stdout and not result.stderr:
            return "Script executed successfully with no output."
        
        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return (
            f"Error: Script execution timed out "
            f"(limit: {config.EXEC_TIMEOUT}s)."
        )
    except Exception as e:
        return f"Error during execution: {str(e)}"
