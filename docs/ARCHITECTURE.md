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

## 8. Extension points

- **New tools**: register functions in the `tools` list in `agent/workflow.py`;
  keep them file-system-bound so the sandbox check applies.
- **New phases**: extend `AgentPhase` in `state.py`, add a prompt in
  `agent/prompts.py`, and extend `phase_map` in `agent/workflow.py`.
- **New sandboxes**: set `PROJECT_ROOT` to any directory; containment is
  enforced uniformly.
