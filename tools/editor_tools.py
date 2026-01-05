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
    """Replaces exact literal text patterns within a file.
    
    IMPORTANT FOR THE AGENT:
    1. EXACT MATCHING: The 'pattern' must EXACTLY match the text in the file, including leading spaces (indentation), 
       trailing punctuation, and quotes. If the file has 4 spaces of indentation, your pattern must also have 4 spaces.
    2. LITERAL STRINGS: Do NOT use regex syntax (like .* or \d) in 'pattern'. The tool automatically escapes all 
       special characters. Provide the code snippet exactly as it appears.
    3. SCOPE: Only the 'pattern' itself is replaced. Surrounding text and indentation outside the pattern are preserved.
    4. MULTI-LINE: Supports multi-line patterns.
    
    Args:
        path: The absolute or relative path to the target file.
        pattern: The exact string/code snippet to search for.
        replacement: The string to replace the pattern with.
        count: Maximum number of occurrences to replace (default is 1).
    """
    try:
        target_abs_path = _check_path(path)

        if not os.path.exists(target_abs_path):
            return f"Error: File '{path}' not found in project root."

        with open(target_abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        safe_pattern = re.escape(pattern)

        if not re.search(safe_pattern, content, flags=re.DOTALL):
            return f"Error: The exact pattern was not found in {path}. Please verify the exact indentation and spacing."

        new_content = re.sub(
            safe_pattern, 
            replacement, 
            content, 
            count=count, 
            flags=re.DOTALL
        )

        with open(target_abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Successfully patched {path}."
    except PermissionError as pe:
        return str(pe)
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