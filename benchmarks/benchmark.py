#!/usr/bin/env python3
"""Batch self-healing benchmark over the injected-bug corpus.

Usage:
    python benchmarks/benchmark.py                 # real run (needs API key)
    python benchmarks/benchmark.py --smoke         # plumbing check, no LLM calls
    python benchmarks/benchmark.py --limit 3       # quick subset
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage  # noqa: E402

from autofix.runner import run_repair  # noqa: E402
from config import config  # noqa: E402
from llm.base import LLMStats  # noqa: E402

DEFAULT_TASK = (
    "Explore the project directory, find the main entry point, run it, "
    "and fix any errors you encounter."
)


class FakeLLM:
    """Deterministic stand-in that exercises the graph without network calls."""

    name = "fake"
    model_name = "fake-smoke"

    def __init__(self):
        self._calls = 0
        self._stats = LLMStats()

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self._calls += 1
        self._stats.calls += 1
        system = messages[0]["content"]
        if "Current Phase: validate" in system:
            return AIMessage(content="DONE")
        if self._calls % 2 == 1:
            return AIMessage(
                content="inspecting project",
                tool_calls=[
                    {"name": "list_files", "args": {"path": "."}, "id": f"t{self._calls}"}
                ],
            )
        return AIMessage(content="proceeding")

    def stats(self):
        return self._stats


def load_corpus(corpus_dir: Path):
    cases = []
    for meta_path in sorted(corpus_dir.glob("*/meta.json")):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["project"] = str(meta_path.parent / "project")
        cases.append(meta)
    return cases


def verify_case(case: dict) -> dict:
    """Post-run correctness check: script must exit 0 and match expected output."""
    project = case["project"]
    timeout = int(case.get("exec_timeout", 10))
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(project, "main.py")],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        expected = case.get("expected_output")
        passed = result.returncode == 0 and (
            expected is None or expected in stdout
        )
        return {
            "passed": passed,
            "exit_code": result.returncode,
            "output_tail": (stdout + stderr).strip()[-300:],
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "exit_code": None,
            "output_tail": "<timeout>",
        }


def run_case(app, llm, case: dict, max_iterations: int) -> dict:
    if case.get("exec_timeout"):
        config.EXEC_TIMEOUT = int(case["exec_timeout"])
    result = run_repair(
        app,
        llm,
        project_root=case["project"],
        task=DEFAULT_TASK,
        max_iterations=max_iterations,
    )
    verification = verify_case(case)
    return {
        "id": case["id"],
        "name": case["name"],
        "bug_type": case["bug_type"],
        "agent_status": result.status,
        "iterations": result.iterations,
        "duration_s": result.duration_s,
        "passed": verification["passed"],
        "exit_code": verification["exit_code"],
        "output_tail": verification["output_tail"],
        "llm_stats": result.llm_stats,
    }


def build_markdown(results: list, total_duration_s: float, smoke: bool) -> str:
    passed = sum(1 for r in results if r["passed"])
    lines = [
        "# AutofixAgent Benchmark Results",
        "",
        f"- Mode: {'smoke (fake LLM, plumbing check only)' if smoke else 'real (Gemini)'}",
        f"- Cases: {len(results)}",
        f"- Passed: {passed} / {len(results)}",
        f"- Success rate: {passed / len(results) * 100:.1f}%",
        f"- Total duration: {total_duration_s:.1f}s",
        "",
        "| Case | Bug type | Agent status | Iterations | Duration (s) | Passed |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['bug_type']} | {r['agent_status']} | "
            f"{r['iterations']} | {r['duration_s']:.1f} | "
            f"{'✅' if r['passed'] else '❌'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "benchmarks" / "corpus"),
        help="Directory containing bug-case folders with meta.json",
    )
    parser.add_argument("--max-iterations", type=int, default=config.MAX_ITERATIONS)
    parser.add_argument("--limit", type=int, default=None, help="Run first N cases")
    parser.add_argument("--smoke", action="store_true", help="Use FakeLLM, no API calls")
    parser.add_argument("--model", default=None, help="Override LLM model")
    parser.add_argument(
        "--report-dir", default=config.REPORTS_DIR, help="Output directory"
    )
    args = parser.parse_args(argv)

    cases = load_corpus(Path(args.corpus))
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        print(f"No cases found under {args.corpus}", file=sys.stderr)
        return 2

    if args.smoke:
        from agent.workflow import create_app

        print(f"[smoke] running {len(cases)} cases with FakeLLM (no API calls)")
        results = []
        total_start = time.monotonic()
        for case in cases:
            llm = FakeLLM()
            app = create_app(llm)
            row = run_case(app, llm, case, args.max_iterations)
            results.append(row)
            print(
                f"  {row['id']:<22} agent={row['agent_status']:<14} "
                f"passed={row['passed']} iterations={row['iterations']}"
            )
        total_duration_s = time.monotonic() - total_start
    else:
        if not config.GOOGLE_API_KEY:
            print(
                "[ERROR] GOOGLE_API_KEY is not set. "
                "Copy .env.example to .env and fill it in.",
                file=sys.stderr,
            )
            return 2

        from agent.workflow import create_app, tools
        from llm.factory import build_llm

        llm = build_llm(model=args.model, tools=tools)
        app = create_app(llm)

        print(f"[benchmark] running {len(cases)} cases with {llm.name}")
        results = []
        total_start = time.monotonic()
        for case in cases:
            row = run_case(app, llm, case, args.max_iterations)
            results.append(row)
            print(
                f"  {row['id']:<22} agent={row['agent_status']:<14} "
                f"passed={row['passed']} iterations={row['iterations']} "
                f"({row['duration_s']:.1f}s)"
            )
        total_duration_s = time.monotonic() - total_start
        stats = llm.stats()
        print(
            f"\nLLM usage: {stats.calls} calls, {stats.total_tokens} tokens, "
            f"${stats.estimated_cost_usd:.6f}"
        )

    os.makedirs(args.report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(args.report_dir, f"benchmark_{timestamp}.json")
    md_path = os.path.join(args.report_dir, f"benchmark_{timestamp}.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mode": "smoke" if args.smoke else "real",
                "total_duration_s": round(total_duration_s, 2),
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(results, total_duration_s, args.smoke))

    passed = sum(1 for r in results if r["passed"])
    print(
        f"\nResults: {passed}/{len(results)} passed "
        f"({passed / len(results) * 100:.1f}%) in {total_duration_s:.1f}s"
    )
    print(f"Report: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
