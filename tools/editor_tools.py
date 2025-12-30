import os
import re
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

def write_file(path: str, content: str) -> str:
    """Write or overwrite a file with new content. Use this to create new files or fully rewrite existing ones."""
    try:
        target = _check_path(path)
        
        os.makedirs(os.path.dirname(target), exist_ok=True)
        
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def patch_file(path: str, pattern: str, replacement: str, count: int = 1) -> str:
    """Apply a regex-based replacement to a file. Ideal for fixing specific lines without rewriting the whole file."""
    try:
        target = _check_path(path)
        if not os.path.exists(target):
            return f"Error: File {path} not found."

        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()

        if not re.search(pattern, content, flags=re.MULTILINE | re.DOTALL):
            return f"Error: Pattern '{pattern}' not found in {path}. No changes made."

        new_content = re.sub(
            pattern, 
            replacement, 
            content, 
            count=count, 
            flags=re.MULTILINE | re.DOTALL
        )

        with open(target, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Successfully patched {path}."
    except Exception as e:
        return f"Error patching file: {str(e)}"

def insert_line(path: str, line_number: int, content: str) -> str:
    """Insert a new line of text at a specific line number in the file."""
    try:
        target = _check_path(path)
        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        idx = max(0, line_number - 1)
        lines.insert(idx, content + "\n")
        
        with open(target, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return f"Successfully inserted line at {line_number} in {path}."
    except Exception as e:
        return f"Error inserting line: {str(e)}"