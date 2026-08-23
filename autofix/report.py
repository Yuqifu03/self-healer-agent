"""Repair report generation (Markdown and JSON artifacts)."""

import json
import os
from typing import Dict

from autofix.runner import RunResult


def _format_trace_entry(entry: dict) -> str:
    kind = entry.get("type")
    if kind == "phase_enter":
        return f"[phase] entering '{entry.get('phase')}'"
    if kind == "phase":
        return f"[phase] {entry.get('from')} -> {entry.get('to')}"
    if kind == "thought":
        return f"[thought] {entry.get('content', '')}"
    if kind == "action":
        args = json.dumps(entry.get("args", {}), ensure_ascii=False)
        return f"[action] {entry.get('tool')}({args})"
    if kind == "observation":
        return f"[observation] {entry.get('content', '')}"
    return f"[{kind}] {json.dumps(entry, ensure_ascii=False)}"


def build_markdown_report(result: RunResult) -> str:
    lines = [
        "# AutofixAgent Repair Report",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Project | `{result.project_root}` |",
        f"| Model | {result.model} |",
        f"| Status | {result.status} |",
        f"| Iterations | {result.iterations} |",
        f"| Duration | {result.duration_s}s |",
        f"| LLM calls | {result.llm_stats.get('calls', 0)} |",
        f"| Tokens | {result.llm_stats.get('total_tokens', 0)} "
        f"(prompt {result.llm_stats.get('prompt_tokens', 0)} / "
        f"completion {result.llm_stats.get('completion_tokens', 0)}) |",
        f"| Est. cost | ${result.llm_stats.get('estimated_cost_usd', 0.0):.6f} |",
        "",
        f"**Task**: {result.task}",
        "",
    ]

    if result.error:
        lines += ["## Error", "", f"```text\n{result.error}\n```", ""]

    lines += ["## Files Changed", ""]
    if result.diffs:
        for change in result.diffs:
            lines += [
                f"### `{change['path']}` ({change['status']})",
                "",
                "```diff",
                change["diff"],
                "```",
                "",
            ]
    else:
        lines += ["No files changed.", ""]

    if result.final_message:
        lines += ["## Final Agent Message", "", f"> {result.final_message}", ""]

    lines += ["## Thought / Action / Observation Trace", ""]
    if result.trace:
        for entry in result.trace:
            lines += [f"- `{entry.get('ts', '')}` {_format_trace_entry(entry)}"]
    else:
        lines += ["No trace recorded.", ""]

    return "\n".join(lines) + "\n"


def build_json_report(result: RunResult) -> Dict:
    return {
        "project_root": result.project_root,
        "task": result.task,
        "model": result.model,
        "status": result.status,
        "iterations": result.iterations,
        "duration_s": result.duration_s,
        "llm_stats": result.llm_stats,
        "error": result.error,
        "diffs": result.diffs,
        "final_message": result.final_message,
        "trace": result.trace,
    }


def write_report(result: RunResult, path: str, fmt: str) -> str:
    """Write the report artifact; returns the absolute path written."""
    fmt = fmt.lower()
    if fmt not in ("md", "json"):
        raise ValueError(f"Unsupported report format: {fmt}")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if fmt == "md":
        content = build_markdown_report(result)
    else:
        content = json.dumps(build_json_report(result), indent=2, ensure_ascii=False)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content + ("\n" if fmt == "json" else ""))
    return os.path.abspath(path)
