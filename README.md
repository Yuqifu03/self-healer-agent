# AutofixAgent — Self-Healing Codebase Agent

<p align="center">
  <b>An autonomous AI agent that explores, diagnoses, and repairs Python codebases inside a secure sandbox.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-6--Phase%20State%20Machine-10b981" alt="LangGraph 6-phase state machine">
  <img src="https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-7c3aed" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Sandbox-Path%20Level%20Escape%20Safe-ef4444" alt="Path-level sandbox">
  <img src="https://img.shields.io/badge/Runtime-Docker-2496ED" alt="Docker">
</p>

AutofixAgent is an open-source side project that turns a **"Think → Act → Loop"**
repair cycle into a production-minded tool: given a buggy Python codebase, it
diagnoses the failure, locates the responsible code, proposes and applies a
minimal fix, then re-runs the program to verify the repair — all without ever
leaving the sandbox it is confined to.

It uses **Gemini** for reasoning, **LangGraph** to orchestrate a six-phase state
machine (Diagnose → Locate → Propose → Fix → Validate → Done), and a hardened
path-level sandbox so the agent can read and write *only* inside the project
it was pointed at.

---

## ✨ Features

### LangGraph six-phase state machine

```mermaid
flowchart LR
    A[Diagnose<br/>analyze_error] --> B[Locate<br/>locate_code]
    B --> C[Propose<br/>propose_fix]
    C --> D[Fix<br/>apply_fix]
    D --> E[Validate<br/>validate]
    E -->|"STDERR clean"| F[Done]
    E -->|"still failing"| A
```

- Explicit phase prompts keep the LLM focused on one job at a time.
- Validation failure **automatically rewinds to Diagnose** instead of guessing.
- A hard iteration cap stops runaway loops and force-finishes cleanly.

### Perception-first tool-use discipline

Designed to mitigate tool-call hallucination:

| Rule | Behavior |
| --- | --- |
| **Read before modify** | Every phase instructs the model to observe files with `read_header` before touching them. |
| **≤ 50-line rewrite** | Small files are overwritten whole with `write_file` — no fragile regex matching. |
| **Literal patches** | Large files use `patch_file`, which escapes all regex metacharacters and requires a 1:1 literal match including indentation. |
| **Auto re-read on mismatch** | If a patch reports "pattern not found", the model is told to stop, re-read the file, and switch strategies instead of retrying blindly. |

### Stability & observability

- **Path-level sandbox escape prevention**: every file-system tool resolves and
  validates paths through a shared security module that blocks absolute paths,
  `..` traversal, sibling-directory prefix spoofing, and symlink escapes.
- **Iteration cap**: `MAX_ITERATIONS` guards the whole workflow.
- **Execution timeout**: every subprocess is bounded by `EXEC_TIMEOUT` (default
  30s) so a hung script cannot stall the loop.
- **Thought / Action / Observation logging**: every model thought, tool call,
  and tool result is streamed to the console and appended to a timestamped
  trace file in `logs/`, giving a complete audit trail of the repair.

### Docker-first runtime

The project ships with a `Dockerfile` and `docker-compose.yml`, so the agent can
run against an arbitrary buggy codebase in a clean, reproducible container and
re-verify fixes by re-running the target script.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11 or 3.12 (or Docker)
- A Google Gemini API key

### 2. Configuration

Copy `.env.example` to `.env` and fill in your key:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
PROJECT_ROOT=./sandbox/example_project
EXEC_TIMEOUT=30
```

### 3. Install

```bash
pip install -r requirements.txt
```

### 4. Run

Place a buggy Python project inside `sandbox/` (see
[`sandbox/buggy_project`](sandbox/buggy_project/README.md) for a ready-made
demo), point `PROJECT_ROOT` at it, then:

```bash
python main.py
```

The agent will explore the project, run its `main.py`, diagnose the failure,
apply a fix, and re-run until the program produces clean `STDOUT` (or the
iteration cap is reached).

### Running with Docker

```bash
cp .env.example .env   # fill in GOOGLE_API_KEY
docker compose up --build
```

The compose file mounts `./sandbox` and `./logs` into the container and targets
the `buggy_project` demo by default.

---

## 📂 Project Structure

```text
.
├── agent/
│   ├── workflow.py        # LangGraph state machine & phase routing
│   └── prompts.py         # Phase-specific system prompts
├── tools/
│   ├── explorer_tools.py  # list_files, find_file, grep_text, read_header
│   ├── editor_tools.py    # write_file, patch_file, insert_line
│   └── executor_tools.py  # run_python_script (bounded by EXEC_TIMEOUT)
├── utils/
│   ├── sandbox.py         # path-level containment checks (security core)
│   └── logger.py          # thought/action/observation console + file logging
├── sandbox/
│   ├── example_project/   # default healthy target
│   └── buggy_project/     # demo target with an injected import defect
├── tests/                 # sandbox & config security tests
├── docs/
│   └── ARCHITECTURE.md    # deep-dive design document
├── config.py              # env-driven configuration
├── state.py               # LangGraph state schema (AgentState)
├── main.py                # entry point
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## ⚙️ Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | — | Gemini API key (required) |
| `PROJECT_ROOT` | `./sandbox/example_project` | Sandbox root the agent may read/write |
| `EXEC_TIMEOUT` | `30` | Per-subprocess execution timeout (seconds) |
| `MODEL_NAME` | `gemini-2.5-flash` | LLM used for reasoning |
| `TEMPERATURE` | `0` | Sampling temperature |
| `MAX_ITERATIONS` | `10` | Hard cap on workflow iterations |

## 🔒 Security Design

All file-system access funnels through `utils/sandbox.py`, which resolves the
configured root once with `realpath` and rejects any path whose canonical form
falls outside it. This defends against:

- absolute paths (`/etc/passwd`)
- parent traversal (`../../`)
- sibling prefix spoofing (`sandbox_evil` when the root is `sandbox`)
- symlinks pointing outside the sandbox

The sandbox boundary is enforced at the *tool* layer, so even if the model is
prompted (or tricks itself) into requesting an out-of-scope path, the request is
rejected with a `PermissionError`.

## 🧪 Development

```bash
pip install -r requirements-dev.txt
make test        # or: python -m pytest
```

The test suite covers sandbox containment (traversal, absolute paths, sibling
spoofing, symlink escapes) and configuration sanity.

## 📖 Documentation

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a deep dive into the state
machine, tool discipline, security model, and extension points.

## 📄 License

TBD — MIT (pending).
