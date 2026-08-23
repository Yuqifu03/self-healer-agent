"""Snapshot/diff logic and end-to-end runner behaviour with FakeLLM."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autofix.runner import diff_snapshots, run_repair, snapshot_dir  # noqa: E402
from agent.workflow import create_app  # noqa: E402
from tests.fake_llm import FakeLLM  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_snapshot_and_diff(tmp_path):
    root = tmp_path / "project"
    _write(root / "main.py", "print('hi')\n")
    _write(root / "keep.py", "x = 1\n")

    before = snapshot_dir(str(root))
    assert set(before) == {"main.py", "keep.py"}

    _write(root / "main.py", "print('hello')\n")
    _write(root / "new.py", "y = 2\n")
    os.remove(root / "keep.py")

    changes = diff_snapshots(before, snapshot_dir(str(root)))
    by_path = {c["path"]: c for c in changes}
    assert by_path["main.py"]["status"] == "modified"
    assert "-print('hi')" in by_path["main.py"]["diff"]
    assert by_path["new.py"]["status"] == "added"
    assert by_path["keep.py"]["status"] == "deleted"


def test_run_repair_completes_with_fake_llm(tmp_path):
    project = tmp_path / "project"
    _write(project / "main.py", "print('ok')\n")

    llm = FakeLLM()
    app = create_app(llm)
    result = run_repair(
        app,
        llm,
        project_root=str(project),
        task="run and fix errors",
        max_iterations=10,
    )

    assert result.is_success
    assert result.iterations >= 5
    assert result.diffs == []
    assert any(e["type"] == "phase_enter" for e in result.trace)
    assert any(e["type"] == "observation" for e in result.trace)
    assert result.llm_stats["calls"] > 0
