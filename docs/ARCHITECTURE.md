# AutofixAgent — Architecture

AutofixAgent is a LangGraph-based autonomous repair agent. This document
describes its state machine, tool discipline, security model, observability,
and the failure-handling design that keeps the loop reliable.

## 1. Design goals

1. **Perception before action** — never guess code; observe before modifying.
2. **Reliability over cleverness** — prefer whole-file rewrites over fragile
   regex patches; fall back gracefully when a patch misses.
3. **Bounded execution** — the agent can never stall the loop or escape the
   sandbox it is confined to.
4. **Full auditability** — every thought, action, and observation is logged.

## 2. State machine

`state.py` defines `AgentState` with `phase` as the driver:

```text
analyze_error ──> locate_code ──> propose_fix ──> apply_fix ──> validate ──> done
      ▲                                                               │
      └───────────────────────── failure ────────────────────────────┘
```

`agent/workflow.py` implements the graph:

- **agent node**: invokes the Gemini model with the phase-specific system
  prompt; logs the thought; routes tool calls or advances the phase.
- **tools node**: executes the requested tool(s) and logs every observation,
  closing the thought → action → observation loop.
- **phase routing** (`get_next_phase_logic`): a response without tool calls
  advances to the next phase. In `validate`, a non-`DONE` answer rewinds to
  `analyze_error`, restarting diagnosis with fresh evidence.
- **iteration guard** (`route_logic`): once `iteration_count` reaches
  `MAX_ITERATIONS`, the graph force-stops even if the bug is unresolved.

The graph is built by `create_app(llm)` in `agent/workflow.py`, which takes a
`BaseLLM` instead of hardcoding a vendor, and records every thought, action,
and observation into a structured `trace` list on the state for later report
generation.

## 2.1 LLM provider layer

`llm/base.py` defines the provider contract (`invoke`, `bind_tools`, `stats`)
and `LLMStats` for token/cost accounting. `llm/gemini.py` implements it with:

- tool binding via `langchain-google-genai`;
- exponential-backoff retries (`invoke_with_retry`) for transient failures such
  as rate limits and 5xx errors, with configurable attempts/base delay;
- usage extraction from `usage_metadata` and per-1M-token cost estimation.

`llm/factory.py` is the only place that decides which provider to construct, so
adding e.g. an OpenAI provider means adding a class and a factory branch.

## 3. Tool discipline ("perception-first")

The tool set is intentionally small:

| Tool | Phase focus | Notes |
| --- | --- | --- |
| `list_files` / `find_file` / `grep_text` | Locate | Search-only |
| `read_header` | All | Must precede any modification |
| `write_file` | Fix | Whole-file rewrite, preferred for ≤50-line files |
| `patch_file` | Fix | Literal (regex-escaped) pattern replace for large files |
| `insert_line` | Fix | Line-anchored insertion |
| `run_python_script` | Diagnose / Validate | Bounded by `EXEC_TIMEOUT` |

To mitigate tool-call hallucination:

- prompts forbid guessing and mandate `read_header` before edits;
- `patch_file` escapes regex metacharacters so patterns must match literally;
- on "pattern not found", the model is instructed to stop, re-read the file,
  and switch strategy rather than repeat the same call.

## 4. Security model

`utils/sandbox.py` is the single chokepoint for every file-system tool. The
configured `PROJECT_ROOT` is canonicalized once via `realpath`, and each
requested path is resolved and checked for containment:

```text
resolved == root  OR  resolved.startswith(root + os.sep)
```

This rejects:

- absolute paths (which would discard the root in `os.path.join`);
- `..` traversal that lands outside the root;
- sibling directories that merely *prefix* the root name;
- symlinks whose target lies outside the root (resolved via `realpath`).

Escalation attempts surface as `PermissionError` messages returned to the model
and are recorded in the trace log.

## 5. Observability

`utils/logger.py` emits a three-channel trace for every loop:

- **thought**: the model's free-text reasoning;
- **action**: the tool name and arguments;
- **observation**: the tool's full result (truncated to 300 chars in the
  console, complete in the file).

Each run writes `logs/agent_trace_<timestamp>.log` with structured entries
(`[THOUGHT]`, `[ACTION]`, `[OBSERVATION]`, `[ERROR]`, `[SUCCESS]`) that make a
repair session reproducible and auditable.

## 6. Failure handling

| Failure | Reaction |
| --- | --- |
| Patch pattern not found | Model re-reads the file and switches strategy |
| Validation still failing | Phase rewinds to `analyze_error` with new evidence |
| Subprocess timeout | Tool returns a timeout error; loop continues or hits cap |
| Iteration cap reached | Graph force-stops with an error log |
| Path escape attempt | `PermissionError` returned to the model, logged |

## 7. Docker runtime

`Dockerfile` installs dependencies on `python:3.11-slim` and mounts nothing by
default; `docker-compose.yml` mounts `./sandbox` and `./logs` so the agent can
repair a host-side project while the container provides isolation and
reproducibility. `PROJECT_ROOT` defaults to the bundled `buggy_project` demo
inside the container.

## 7.1 CLI, runner, and repair reports

`autofix/cli.py` parses arguments (`--project`, `--max-iterations`,
`--report`, …), validates the API key, and delegates to
`autofix/runner.py:run_repair()`. The runner:

1. snapshots the target directory before the run;
2. invokes the compiled graph;
3. diffs the snapshot against the post-run state with `difflib`;
4. collects the trace, LLM stats, and final status into a `RunResult`.

`autofix/report.py` renders `RunResult` as a Markdown report (summary table,
per-file diffs, final message, and the thought/action/observation trace) or as
structured JSON under `reports/`.

## 7.2 Benchmark

`benchmarks/benchmark.py` loads `benchmarks/corpus/*/meta.json`, runs the agent
against each injected-bug project, and independently verifies the fix by
re-running `main.py` and checking the expected output — so logic bugs that exit
0 are still caught. It reports per-case status plus aggregate success rate and
writes `reports/benchmark_<timestamp>.{json,md}`. `--smoke` runs the same
pipeline with a deterministic `FakeLLM` for CI without API calls.

## 8. Extension points

- **New tools**: register functions in the `tools` list in `agent/workflow.py`;
  keep them file-system-bound so the sandbox check applies.
- **New phases**: extend `AgentPhase` in `state.py`, add a prompt in
  `agent/prompts.py`, and extend `phase_map` in `agent/workflow.py`.
- **New sandboxes**: set `PROJECT_ROOT` to any directory; containment is
  enforced uniformly.
- **New LLM providers**: implement `BaseLLM` and register it in
  `llm/factory.py`.
- **New corpus cases**: add a folder under `benchmarks/corpus/` with a
  `project/` directory and a `meta.json` (bug type + expected output).
