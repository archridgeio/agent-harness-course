"""Chapter 15 — long-horizon tasks: state outside the window.

Pattern (initializer + worker sessions):
- Session 0 (initializer) turns a spec into features.json and progress.md.
- Every later session starts with a FRESH context window, reads progress.md,
  features.json and git log, finishes ONE feature, runs the tests, updates the
  files. The harness commits after every session, so git is the checkpoint log.
- Kill it at any point and run it again: it resumes from the files.

Run:  python ch15-long-horizon/long_task.py            # run until done (max 8 sessions)
      python ch15-long-horizon/long_task.py --reset    # start over from a clean copy
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from course import SAMPLE_REPO, Tool, get_client, repo_tools, run_agent

WORKSPACE = Path(__file__).with_name("workspace")

SPEC = """Improve the inventory project:
1. Fix the bug in stats.mean.
2. Add pricing.clearance_price(price, percent) that applies a discount capped at 50%.
3. Add Stock.restock_report() returning {sku: units_needed_to_reach_reorder_level + 5} for low-stock SKUs.
4. Add tests for features 2 and 3 in tests/test_inventory.py."""

INITIALIZER_SYSTEM = """You are the initializer. Do not write any product code.
Read the spec and the repo, then create:
- features.json: a JSON list of {"id": "F1", "description": "...", "passes": false}, one per spec item.
- progress.md: a heading, the spec, and a "## Log" section.
Then stop."""

WORKER_SYSTEM = """You are one session in a long-running task. Your memory of earlier sessions is in files.
1. Read progress.md and features.json, and call git_log.
2. Pick the FIRST feature with "passes": false. Work on that one only.
3. Implement it, then call run_tests.
4. Only if the tests pass, set its "passes" to true in features.json.
5. Append one line to the Log in progress.md: feature id, what you did, test result.
Then stop. Leave the repo in a working state."""


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=WORKSPACE, capture_output=True, text=True)
    return (proc.stdout + proc.stderr).strip()


def setup_workspace(reset: bool = False) -> None:
    if reset and WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    if WORKSPACE.exists():
        return
    shutil.copytree(SAMPLE_REPO, WORKSPACE, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    git("init", "-q")
    git("add", "-A")
    git("-c", "user.name=harness", "-c", "user.email=harness@example.com", "commit", "-qm", "start")


def commit(message: str) -> None:
    git("add", "-A")
    git("-c", "user.name=harness", "-c", "user.email=harness@example.com", "commit", "-qm", message)


def features() -> list[dict]:
    path = WORKSPACE / "features.json"
    return json.loads(path.read_text()) if path.exists() else []


def toolbox():
    tb = repo_tools(WORKSPACE, writable=True)

    def run_tests() -> str:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=WORKSPACE, capture_output=True,
                              text=True, timeout=120)
        return proc.stdout[-3000:] + proc.stderr[-1000:]

    tb.add(Tool("run_tests", "Run the test suite with pytest and return the summary.",
                {"type": "object", "properties": {}}, run_tests))
    tb.add(Tool("git_log", "Show the last 10 commits (one per session).",
                {"type": "object", "properties": {}}, lambda: git("log", "--oneline", "-10")))
    return tb


def run(client=None, max_sessions: int = 8, reset: bool = False) -> list[dict]:
    client = client or get_client()
    setup_workspace(reset)
    log = []
    if not features():
        run_agent(client, f"Spec:\n{SPEC}", toolbox(), system=INITIALIZER_SYSTEM, max_turns=10)
        commit("session 0: initializer")
        log.append({"session": 0, "remaining": sum(not f["passes"] for f in features())})
    for n in range(1, max_sessions + 1):
        remaining = [f for f in features() if not f["passes"]]
        if not remaining:
            break
        result = run_agent(client, "Continue the long-running task.", toolbox(), system=WORKER_SYSTEM, max_turns=25)
        commit(f"session {n}: {remaining[0]['id']}")
        log.append({"session": n, "target": remaining[0]["id"], "turns": result.turns,
                    "remaining": sum(not f["passes"] for f in features())})
        print(f"session {n}: worked on {remaining[0]['id']} in {result.turns} turns; "
              f"{log[-1]['remaining']} features left")
    return log


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
    print("\n" + git("log", "--oneline"))
    print(json.dumps(features(), indent=2))
