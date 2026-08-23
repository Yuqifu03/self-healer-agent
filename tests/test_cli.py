"""CLI parsing and report-format resolution tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autofix.cli import parse_args, resolve_report_format  # noqa: E402
from config import config  # noqa: E402


def test_parse_args_defaults():
    args = parse_args([])
    assert args.project == config.PROJECT_ROOT
    assert args.max_iterations == config.MAX_ITERATIONS
    assert args.report is None
    assert args.report_format is None
    assert args.no_report is False


def test_parse_args_overrides():
    args = parse_args(
        [
            "--project",
            "sandbox/buggy_project",
            "--max-iterations",
            "5",
            "--report",
            "out/repair.md",
        ]
    )
    assert args.project == "sandbox/buggy_project"
    assert args.max_iterations == 5
    assert args.report == "out/repair.md"


def test_resolve_report_format_from_extension():
    assert resolve_report_format("out/repair.json", None) == "json"
    assert resolve_report_format("out/repair.md", None) == "md"


def test_resolve_report_format_forced():
    assert resolve_report_format("out/repair.json", "md") == "md"
