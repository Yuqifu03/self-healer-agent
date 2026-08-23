"""High-level repair runner shared by the CLI and the benchmark."""

import difflib
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage

from config import config
from utils.sandbox import resolve_sandbox_root


@dataclass
class RunResult:
    project_root: str
    task: str
    model: str
    status: str  # done | failed | max_iterations | error
    iterations: int
    duration_s: float
    trace: List[dict]
    diffs: List[dict]
    final_message: str
    llm_stats: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == "done"


def snapshot_dir(project_root: str) -> Dict[str, str]:
    """Read every source file under ``project_root`` into a rel-path -> content map."""
    root = resolve_sandbox_root(project_root)
    files: Dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d != "__pycache__" and not d.startswith(".")
        ]
        for filename in filenames:
            if filename.endswith(".pyc"):
                continue
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    files[rel_path] = f.read()
            except OSError:
                continue
    return files


def diff_snapshots(before: Dict[str, str], after: Dict[str, str]) -> List[dict]:
    """Return per-file unified diffs for added/modified/deleted files."""
    changes: List[dict] = []
    for rel_path in sorted(set(before) | set(after)):
        old_content = before.get(rel_path)
        new_content = after.get(rel_path)
        if old_content == new_content:
            continue
        if old_content is None:
            changes.append({"path": rel_path, "status": "added", "diff": new_content})
        elif new_content is None:
            changes.append({"path": rel_path, "status": "deleted", "diff": old_content})
        else:
            diff = "\n".join(
                difflib.unified_diff(
                    old_content.splitlines(),
                    new_content.splitlines(),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    lineterm="",
                )
            )
            changes.append({"path": rel_path, "status": "modified", "diff": diff})
    return changes


def run_repair(
    app,
    llm,
    *,
    project_root: str,
    task: str,
    max_iterations: int,
) -> RunResult:
    """Run the agent against ``project_root`` and collect a structured result."""
    config.PROJECT_ROOT = project_root
    before = snapshot_dir(project_root)

    initial_state = {
        "messages": [HumanMessage(content=f"Task: {task}")],
        "iteration_count": 0,
        "phase": "analyze_error",
        "trace": [],
    }

    start = time.monotonic()
    error: Optional[str] = None
    try:
        final_state = app.invoke(initial_state)
    except Exception as exc:  # e.g. LLM API failure after retries
        error = f"{type(exc).__name__}: {exc}"
        final_state = initial_state

    duration_s = round(time.monotonic() - start, 2)
    trace = list(final_state.get("trace", []))
    iterations = final_state.get("iteration_count", 0)
    phase = final_state.get("phase", "analyze_error")

    if error:
        status = "error"
    elif phase == "done":
        status = "done"
    elif iterations >= max_iterations:
        status = "max_iterations"
    else:
        status = "failed"

    last_message = final_state.get("messages", [None])[-1]
    final_message = ""
    if isinstance(last_message, AIMessage) and last_message.content:
        final_message = str(last_message.content)

    after = snapshot_dir(project_root)
    stats = llm.stats()

    return RunResult(
        project_root=project_root,
        task=task,
        model=getattr(llm, "model_name", llm.name),
        status=status,
        iterations=iterations,
        duration_s=duration_s,
        trace=trace,
        diffs=diff_snapshots(before, after),
        final_message=final_message,
        llm_stats={
            "calls": stats.calls,
            "prompt_tokens": stats.prompt_tokens,
            "completion_tokens": stats.completion_tokens,
            "total_tokens": stats.total_tokens,
            "estimated_cost_usd": stats.estimated_cost_usd,
        },
        error=error,
    )
