"""Repair report artifact tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autofix.report import build_json_report, build_markdown_report, write_report  # noqa: E402
from autofix.runner import RunResult  # noqa: E402


def _sample_result() -> RunResult:
    return RunResult(
        project_root="/tmp/project",
        task="run and fix errors",
        model="fake",
        status="done",
        iterations=6,
        duration_s=1.23,
        trace=[
            {"ts": "2026-08-22T10:00:00", "type": "phase_enter", "phase": "analyze_error"},
            {"ts": "2026-08-22T10:00:01", "type": "action", "tool": "list_files", "args": {"path": "."}},
            {"ts": "2026-08-22T10:00:02", "type": "observation", "content": "main.py"},
        ],
        diffs=[
            {
                "path": "main.py",
                "status": "modified",
                "diff": "--- a/main.py\n+++ b/main.py\n-print('bad')\n+print('good')",
            }
        ],
        final_message="Fixed.",
        llm_stats={
            "calls": 7,
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "total_tokens": 1200,
            "estimated_cost_usd": 0.0008,
        },
    )


def test_markdown_report_contains_key_sections():
    md = build_markdown_report(_sample_result())
    assert "# AutofixAgent Repair Report" in md
    assert "## Summary" in md
    assert "## Files Changed" in md
    assert "## Thought / Action / Observation Trace" in md
    assert "main.py" in md
    assert "[action] list_files" in md


def test_json_report_structure():
    data = build_json_report(_sample_result())
    assert data["status"] == "done"
    assert data["diffs"][0]["path"] == "main.py"
    assert len(data["trace"]) == 3


def test_write_report_md_and_json(tmp_path):
    md_path = str(tmp_path / "repair.md")
    json_path = str(tmp_path / "repair.json")
    assert write_report(_sample_result(), md_path, "md").endswith("repair.md")
    assert write_report(_sample_result(), json_path, "json").endswith("repair.json")
    assert os.path.exists(md_path)
    assert os.path.exists(json_path)
