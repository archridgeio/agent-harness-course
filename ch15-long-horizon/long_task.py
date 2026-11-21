"""Chapter 15 — long-horizon tasks: state outside the window.

Pattern (initializer + worker sessions):
- Session 0 (initializer) turns a spec into features.json and progress.md.
- Every later session starts with a FRESH context window, reads progress.md,
  features.json and git log, finishes ONE feature, runs the tests, updates the
  files. The harness commits after every session, so git is the checkpoint log.
- Kill it at any point and run it again: it resumes from the files.

Run:  python ch15-long-horizon/long_task.py                          # run until done (max 8 sessions)
      python ch15-long-horizon/long_task.py --reset                  # start over from a clean copy
      python ch15-long-horizon/long_task.py --reset --stop-after 2   # stop after 2 worker sessions
      python ch15-long-horizon/long_task.py --show                   # print the state files and git log
Ctrl+C at any point stops the run; the next run resumes from the last commit.
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
    git("-c", "user.name=harness", "-c", "user.email=harness@example.com", "commit", "--allow-empty", "-qm", message)


def features() -> list[dict]:
    path = WORKSPACE / "features.json"
    return json.loads(path.read_text()) if path.exists() else []


def toolbox(last_tests: dict | None = None):
    tb = repo_tools(WORKSPACE, writable=True)

    def run_tests() -> str:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=WORKSPACE, capture_output=True,
                              text=True, timeout=120)
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if last_tests is not None and lines:
            last_tests["line"] = lines[-1]
        return proc.stdout[-3000:] + proc.stderr[-1000:]

    tb.add(Tool("run_tests", "Run the test suite with pytest and return the summary.",
                {"type": "object", "properties": {}}, run_tests))
    tb.add(Tool("git_log", "Show the last 10 commits (one per session).",
                {"type": "object", "properties": {}}, lambda: git("log", "--oneline", "-10")))
    return tb


def tool_calls(messages: list) -> list[str]:
    calls = []
    for m in messages:
        if m["role"] == "assistant" and not isinstance(m["content"], str):
            for b in m["content"]:
                if getattr(b, "type", None) == "tool_use":
                    calls.append(f"{b.name}({', '.join(str(v)[:40] for v in (b.input or {}).values())})")
    return calls


def tokens(result) -> int:
    return sum((u.input_tokens or 0) + (u.output_tokens or 0) for u in result.usage)


def peak_window(result) -> int:
    """Largest single request in the session: how full its context window got."""
    return max((u.input_tokens or 0 for u in result.usage), default=0)


def next_session_number() -> int:
    log = git("log", "--format=%s")
    done = [int(line.split()[1].rstrip(":")) for line in log.splitlines()
            if line.startswith("session ") and line.split()[1].rstrip(":").isdigit()]
    return max(done, default=0) + 1


def report(result, last_tests: dict) -> None:
    for call in tool_calls(result.messages):
        print(f"    {call}")
    print(f"  turns {result.turns} · tokens {tokens(result):,} · largest window {peak_window(result):,}")
    if last_tests.get("line"):
        print(f"  tests: {last_tests['line']}")


def run(client=None, max_sessions: int = 8, reset: bool = False, stop_after: int | None = None) -> list[dict]:
    client = client or get_client()
    setup_workspace(reset)
    log = []
    fs = features()
    if fs:
        done = sum(f["passes"] for f in fs)
        print(f"Resuming: {done} of {len(fs)} features pass. Last checkpoint: {git('log', '-1', '--oneline')}")
    else:
        print(f"Fresh start. Last checkpoint: {git('log', '-1', '--oneline')}")
    session = None
    try:
        if not features():
            session = 0
            print("\nsession 0 · initializer · fresh window")
            last_tests: dict = {}
            result = run_agent(client, f"Spec:\n{SPEC}", toolbox(last_tests), system=INITIALIZER_SYSTEM, max_turns=10)
            report(result, last_tests)
            commit("session 0: initializer")
            print(f"  wrote {len(features())} features · commit {git('log', '-1', '--oneline')}")
            log.append({"session": 0, "tokens": tokens(result), "peak": peak_window(result),
                        "remaining": sum(not f["passes"] for f in features())})
        worked = 0
        while worked < max_sessions:
            remaining = [f for f in features() if not f["passes"]]
            if not remaining:
                break
            if stop_after is not None and worked >= stop_after:
                print(f"\nStopped after {worked} worker sessions (--stop-after {stop_after}). "
                      "Run again to resume from the files and git log.")
                break
            session = next_session_number()
            target = remaining[0]["id"]
            print(f"\nsession {session} · target {target} · fresh window")
            last_tests = {}
            result = run_agent(client, "Continue the long-running task.", toolbox(last_tests),
                               system=WORKER_SYSTEM, max_turns=25)
            report(result, last_tests)
            commit(f"session {session}: {target}")
            left = sum(not f["passes"] for f in features())
            print(f"  {left} features left · commit {git('log', '-1', '--oneline')}")
            log.append({"session": session, "target": target, "turns": result.turns, "tokens": tokens(result),
                        "peak": peak_window(result), "remaining": left})
            worked += 1
    except KeyboardInterrupt:
        print(f"\n\nInterrupted during session {session}. Nothing was committed for it.")
        changes = git("status", "--short")
        print("Uncommitted changes in the workspace:\n" + (changes or "  (none)"))
        print("Run again to resume from the last checkpoint.")
    if log:
        print(f"\nThis run: {len(log)} sessions · {sum(e['tokens'] for e in log):,} tokens · "
              f"largest single window {max(e['peak'] for e in log):,}")
    return log


def show() -> None:
    for name in ("features.json", "progress.md"):
        path = WORKSPACE / name
        print(f"===== {name} =====")
        print(path.read_text() if path.exists() else "(missing)")
    print("===== git log =====")
    print(git("log", "--oneline"))
    print("===== git status =====")
    print(git("status", "--short") or "(clean)")


if __name__ == "__main__":
    if "--show" in sys.argv:
        show()
        sys.exit(0)
    stop = int(sys.argv[sys.argv.index("--stop-after") + 1]) if "--stop-after" in sys.argv else None
    run(reset="--reset" in sys.argv, stop_after=stop)
    print("\n" + git("log", "--oneline"))
    print("\n".join(f"{f['id']}  {'pass' if f['passes'] else 'todo'}  {f['description'][:70]}" for f in features()))
