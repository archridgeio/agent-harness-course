"""Run every chapter against the live Claude API and write smoke-report.md.

Each check runs the chapter's script in a subprocess on a fresh throwaway copy of
sample-repo, so nothing in the repo changes (except git-ignored chapter state).

Run from the repo root, with ANTHROPIC_API_KEY exported:
    python scripts/live_smoke_test.py               # all chapters
    python scripts/live_smoke_test.py --only 2,9,19 # selected chapters

Cost: a full run makes a few hundred model calls (Ch 15 and Ch 17 are the biggest).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


@dataclass
class Check:
    chapter: int
    name: str
    args: list[str]
    expect: Callable[[str, Path], str | None]  # returns None if OK, else a reason
    timeout: int = 300
    stdin: str | None = None


def contains(*needles: str, ignore_case: bool = True):
    def check(out: str, repo: Path) -> str | None:
        hay = out.lower() if ignore_case else out
        missing = [n for n in needles if (n.lower() if ignore_case else n) not in hay]
        return f"output is missing: {missing}" if missing else None
    return check


def bug_fixed_and_tests_pass(out: str, repo: Path) -> str | None:
    if "len(values) - 1" in (repo / "inventory" / "stats.py").read_text():
        return "stats.mean still has the planted bug"
    proc = subprocess.run([PY, "-m", "pytest", "-q"], cwd=repo, capture_output=True, text=True)
    return None if proc.returncode == 0 else f"sample-repo tests fail after the agent's fix:\n{proc.stdout[-500:]}"


def all_of(*checks):
    def check(out: str, repo: Path) -> str | None:
        for c in checks:
            reason = c(out, repo)
            if reason:
                return reason
        return None
    return check


def compactions_happened(out: str, repo: Path) -> str | None:
    if "Stopped: reached max_turns" in out:
        return "agent hit max_turns before finishing (budget too tight?)"
    m = re.search(r"Compactions: (\d+)", out)
    if not m:
        return "no 'Compactions:' line"
    if int(m.group(1)) < 1:
        return "ran, but no compaction triggered (raise the task size or lower --budget)"
    pairs = [tuple(map(int, p)) for p in re.findall(r"\((\d+), (\d+)\)", out.split("Compactions:")[-1])]
    grew = [p for p in pairs if p[1] >= p[0]]
    return f"compaction made the context bigger: {grew}" if grew else None


def cache_hits(out: str, repo: Path) -> str | None:
    cached = out.split("=== with caching ===")[-1]
    reads = [int(m) for m in re.findall(r"^\s*\d+\s+\d+\s+\d+\s+(\d+)\s*$", cached, flags=re.M)]
    return None if any(reads) else "no cache reads in the cached run (prefix may be below the model's caching minimum)"


def subagents_used(out: str, repo: Path) -> str | None:
    m = re.search(r"Sub-agent input tokens:\s+([\d,]+)", out)
    if not m:
        return "no sub-agent token line"
    return None if int(m.group(1).replace(",", "")) > 0 else "orchestrator never delegated (0 sub-agent tokens)"


def english(out: str, repo: Path) -> str | None:
    cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", out))
    return None if cjk < 5 else "answer is not in English"


def features_done(out: str, repo: Path) -> str | None:
    return None if '"passes": false' not in out and '"passes": true' in out else "some features still have passes=false"


def evals_score(out: str, repo: Path) -> str | None:
    m = re.search(r"(\d+)/(\d+) passed", out)
    if not m:
        return "no eval summary line"
    passed, total = map(int, m.groups())
    return None if passed == total else f"only {passed}/{total} evals passed"


CHECKS = [
    Check(1, "bare call", ["ch01-what-is-a-harness/bare_call.py"], contains("Bare model call")),
    Check(2, "agent loop", ["ch02-agent-loop/loop.py", "Find and explain the bug in inventory/stats.py"],
          contains("mean")),
    Check(3, "token budget", ["ch03-context-window/token_budget.py", "Read inventory/stats.py and explain it."],
          contains("Total input tokens")),
    Check(4, "context map (exact)", ["ch04-context-engineering/context_map.py", "--exact"], contains("Total")),
    Check(5, "bad vs good tools", ["ch05-tool-design/compare.py"], contains("bad tools", "good tools", "10")),
    Check(6, "MCP client + server", ["ch06-mcp/client_agent.py", "Where is the planted bug?"],
          contains("Discovered MCP tools: search_repo, read_file", "mean")),
    Check(7, "instruction files", ["ch07-instruction-files/instructions.py", "--compare"],
          contains("base prompt only", "with AGENTS.md")),
    Check(8, "skills", ["ch08-skills/skill_loader.py", "--run", "Write release notes for the fix to stats.mean"],
          contains("Fixed")),
    Check(9, "permissions (auto mode)", ["ch09-permissions/permissions.py", "--mode", "auto",
                                         "Fix the bug in inventory/stats.py, then run: python -m pytest -q"],
          all_of(contains("Permission log"), english, bug_fixed_and_tests_pass), timeout=420),
    Check(10, "compaction", ["ch10-compaction/compaction.py", "--budget", "3000"],
          compactions_happened, timeout=600),
    Check(11, "RAG vs agentic search", ["ch11-retrieval/compare.py"], contains("RAG", "Agentic"), timeout=600),
    Check(12, "memory (session 1)", ["ch12-memory/memory_tool.py", "session1"], contains("discount")),
    Check(12, "memory (session 2 recalls)", ["ch12-memory/memory_tool.py", "session2"], contains("50")),
    Check(13, "sub-agents", ["ch13-subagents/subagents.py"], subagents_used),
    Check(14, "prompt caching", ["ch14-caching/caching.py"], cache_hits, timeout=600),
    Check(15, "long-horizon sessions", ["ch15-long-horizon/long_task.py", "--reset"], features_done, timeout=1500),
    Check(16, "single vs multi-agent", ["ch16-multi-agent/single_vs_multi.py"],
          contains("single agent", "multi-agent"), timeout=600),
    Check(17, "evals (full)", ["ch17-evals-tracing/run_evals.py", "--variant", "full"], evals_score, timeout=900),
    Check(18, "failure modes", ["ch18-failure-modes/failures.py", "all"],
          contains("injection — FIXED — no injected file"), timeout=900),
    Check(19, "mini harness", ["ch19-mini-harness/mini_harness.py", "--auto", "--repo", "{repo}",
                               "Fix the failing test and run the tests"],
          all_of(contains("input tokens"), english, bug_fixed_and_tests_pass), timeout=600),
]


def fresh_repo() -> Path:
    dest = Path(tempfile.mkdtemp(prefix="smoke-")) / "sample-repo"
    shutil.copytree(ROOT / "sample-repo", dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return dest


def run_check(check: Check) -> dict:
    repo = fresh_repo()
    env = dict(os.environ, COURSE_REPO=str(repo), PYTHONUNBUFFERED="1")
    args = [a.replace("{repo}", str(repo)) for a in check.args]
    started = time.perf_counter()
    try:
        proc = subprocess.run([PY, *args], cwd=ROOT, env=env, capture_output=True, text=True,
                              timeout=check.timeout, input=check.stdin)
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        out, err, code = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""), \
            "", "timeout"
    seconds = time.perf_counter() - started
    if code == "timeout":
        status, reason = "FAIL", f"timed out after {check.timeout}s"
    elif code != 0:
        status, reason = "FAIL", f"exit code {code}"
    else:
        reason = check.expect(out, repo)
        status = "PASS" if reason is None else "FAIL"
    return {"check": check, "status": status, "reason": reason or "", "seconds": seconds,
            "stdout": out[-6000:], "stderr": err[-3000:]}


def write_report(results: list[dict], path: Path) -> None:
    model = os.environ.get("COURSE_MODEL", "claude-sonnet-5-5 (default)")
    lines = [f"# Live smoke test — {time.strftime('%Y-%m-%d %H:%M')}", "", f"Model: `{model}`", "",
             "| Ch | Check | Result | Seconds | Note |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        c = r["check"]
        lines.append(f"| {c.chapter} | {c.name} | {r['status']} | {r['seconds']:.0f} | {r['reason'][:120]} |")
    passed = sum(r["status"] == "PASS" for r in results)
    lines += ["", f"**{passed}/{len(results)} passed**", ""]
    for r in results:
        c = r["check"]
        lines += [f"## Ch {c.chapter} — {c.name}: {r['status']}", "", f"`python {' '.join(c.args)}`", ""]
        if r["reason"]:
            lines += [f"Reason: {r['reason']}", ""]
        lines += ["```text", r["stdout"].strip() or "(no stdout)", "```", ""]
        if r["stderr"].strip():
            lines += ["stderr:", "```text", r["stderr"].strip(), "```", ""]
    path.write_text("\n".join(lines))


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set in this shell. Export it, then run again.")
        return 2
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    shutil.rmtree(ROOT / "ch12-memory" / ".memories", ignore_errors=True)  # start memory demo clean
    checks = [c for c in CHECKS if only is None or c.chapter in only]
    results = []
    for check in checks:
        print(f"Ch {check.chapter:>2} {check.name:<28}", end=" ", flush=True)
        result = run_check(check)
        results.append(result)
        print(f"{result['status']}  {result['seconds']:>5.0f}s  {result['reason'][:80]}")
    report = ROOT / "smoke-report.md"
    write_report(results, report)
    passed = sum(r["status"] == "PASS" for r in results)
    print(f"\n{passed}/{len(results)} passed. Full report: {report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
