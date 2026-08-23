"""Command-line interface: `python -m autofix` or the `autofix` console script."""

import argparse
import os
import sys
from datetime import datetime

from autofix import __version__
from autofix.report import write_report
from autofix.runner import run_repair
from config import config
from utils.logger import logger

DEFAULT_TASK = (
    "Explore the project directory, find the main entry point, run it, "
    "and fix any errors you encounter."
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="autofix",
        description="Autonomous codebase self-healing agent (AutofixAgent).",
    )
    parser.add_argument(
        "--project",
        default=config.PROJECT_ROOT,
        help="Sandbox project directory to repair (default: %(default)s)",
    )
    parser.add_argument(
        "--task",
        default=DEFAULT_TASK,
        help="Task given to the agent (default: run and fix errors)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=config.MAX_ITERATIONS,
        help="Hard cap on workflow iterations (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the LLM model name (default: from config)",
    )
    parser.add_argument(
        "--exec-timeout",
        type=int,
        default=None,
        help="Per-subprocess timeout in seconds (default: from config)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Path for the repair report; format follows the extension "
        "(.md or .json). Default: reports/repair_<timestamp>.md",
    )
    parser.add_argument(
        "--report-format",
        choices=("md", "json"),
        default=None,
        help="Force report format instead of inferring from the extension",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing a repair report artifact",
    )
    parser.add_argument("--version", action="version", version=f"autofix {__version__}")
    return parser.parse_args(argv)


def resolve_report_format(report_path, forced_format) -> str:
    """Infer the report format from the file extension unless forced."""
    if forced_format:
        return forced_format
    if report_path and report_path.endswith(".json"):
        return "json"
    return "md"


def _check_api_key() -> bool:
    if config.GOOGLE_API_KEY:
        return True
    print(
        "\n[ERROR] GOOGLE_API_KEY is not set.\n"
        "\nTo run AutofixAgent you need a Google Gemini API key:\n"
        "  1. cp .env.example .env\n"
        "  2. edit .env and set GOOGLE_API_KEY=your_gemini_api_key_here\n"
        "  3. re-run the command\n",
        file=sys.stderr,
    )
    return False


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.exec_timeout is not None:
        config.EXEC_TIMEOUT = args.exec_timeout

    project_root = os.path.abspath(args.project)
    config.PROJECT_ROOT = project_root

    if not _check_api_key():
        return 2

    from agent.workflow import create_app, tools
    from llm.factory import build_llm

    llm = build_llm(model=args.model, tools=tools)
    app = create_app(llm)

    logger.log_step("Initializing AutofixAgent")
    print(f"Targeting Project: {project_root}")

    result = run_repair(
        app,
        llm,
        project_root=project_root,
        task=args.task,
        max_iterations=args.max_iterations,
    )

    status_icon = "✅" if result.is_success else "❌"
    print(
        f"\n{status_icon} Status: {result.status} | "
        f"iterations: {result.iterations} | duration: {result.duration_s}s"
    )
    if result.llm_stats:
        stats = result.llm_stats
        print(
            f"LLM: {stats['calls']} calls, {stats['total_tokens']} tokens, "
            f"${stats['estimated_cost_usd']:.6f}"
        )
    if result.error:
        logger.log_error(f"Execution failed: {result.error}")

    if not args.no_report:
        fmt = resolve_report_format(args.report, args.report_format)
        report_path = args.report or os.path.join(
            config.REPORTS_DIR,
            f"repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}",
        )
        written = write_report(result, report_path, fmt)
        print(f"Report written to: {written}")

    return 0 if result.is_success else 1
