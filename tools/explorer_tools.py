import os
import subprocess
from typing import Optional

from config import config
import os
BASE_DIR = os.path.abspath(config.PROJECT_ROOT)

def _check_path(path: str):
    joined_path = os.path.join(BASE_DIR, path)
    full_path = os.path.abspath(joined_path)

    if not full_path.startswith(BASE_DIR):
        raise PermissionError(f"Access denied: {path} is outside the allowed sandbox: {BASE_DIR}")
    
    return full_path

def list_files(path: str = ".", recursive: bool = False) -> str:
    """List files in the specified directory. Set recursive=True to see all subdirectories."""
    try:
        target = _check_path(path)
        if recursive:
            res = []
            for root, dirs, files in os.walk(target):
                rel_path = os.path.relpath(root, target)
                prefix = "" if rel_path == "." else rel_path + "/"
                for f in files:
                    res.append(f"{prefix}{f}")
            return "\n".join(res) if res else "Directory is empty."
        else:
            files = os.listdir(target)
            return "\n".join(files) if files else "Directory is empty."
    except Exception as e:
        return f"Error listing files: {str(e)}"

def find_file(name: str, path: str = ".") -> str:
    """Search for files matching a specific name pattern within a directory."""
    try:
        target = _check_path(path)
        cmd = ["find", target, "-name", f"*{name}*", "-not", "-path", "*/.*"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.stdout:
            paths = [os.path.relpath(p, BASE_DIR) for p in result.stdout.strip().split('\n')]
            return "\n".join(paths)
        return f"No files found matching '{name}'."
    except Exception as e:
        return f"Error finding file: {str(e)}"

def grep_text(pattern: str, path: str = ".", file_type: str = "*") -> str:
    """Search for a specific text pattern/string inside files (similar to the grep command)."""
    try:
        target = _check_path(path)
        cmd = ["grep", "-rnI", f"--include={file_type}", pattern, target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.stdout:
            lines = result.stdout.split('\n')
            if len(lines) > 50:
                return "\n".join(lines[:50]) + f"\n... (Total {len(lines)} matches found, showing first 50)"
            return result.stdout
        return f"No matches found for '{pattern}'."
    except Exception as e:
        return f"Error running grep: {str(e)}"

def read_header(path: str, line_count: int = 20) -> str:
    """Read the first few lines of a file to understand its content and structure."""
    try:
        target = _check_path(path)
        if not os.path.isfile(target):
            return f"Error: {path} is not a file."
            
        with open(target, 'r', encoding='utf-8') as f:
            header = [next(f) for _ in range(line_count)]
        return "".join(header)
    except StopIteration:
        with open(target, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading header: {str(e)}"