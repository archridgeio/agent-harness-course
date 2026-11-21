"""Chapter 16 — single agent vs multi-agent on the same task.

Task: a short review of every module in the repo.
- Single agent: one loop reads everything and writes the report.
- Multi-agent: an orchestrator fans out one worker per module in parallel,
  then a synthesizer merges their reports.

Run:  python ch16-multi-agent/single_vs_multi.py                # single vs parallel multi-agent
      python ch16-multi-agent/single_vs_multi.py --sequential   # also run the workers one after another
Prints each agent's model calls, tool calls, tokens, largest window and time, then a summary.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor

from course import MODEL, SAMPLE_REPO, get_client, repo_tools, run_agent

TASK = "Write a short review of the repo: for each module, its purpose, its riskiest function, and one improvement."
WORKER_SYSTEM = "Review exactly one module. Reply in at most 80 words: purpose, riskiest function, one improvement."


def modules() -> list[str]:
    return sorted(p.relative_to(SAMPLE_REPO).as_posix() for p in (SAMPLE_REPO / "inventory").glob("*.py")
                  if p.name != "__init__.py")


def tool_calls(messages: list) -> list[str]:
    calls = []
    for m in messages:
        if m["role"] == "assistant" and not isinstance(m["content"], str):
            for b in m["content"]:
                if getattr(b, "type", None) == "tool_use":
                    calls.append(f"{b.name}({', '.join(str(v)[:40] for v in (b.input or {}).values())})")
    return calls


def agent_row(name: str, result, seconds: float) -> dict:
    return {"name": name, "calls": result.turns, "tools": tool_calls(result.messages),
            "input": result.input_tokens, "output": result.output_tokens,
            "peak": max((getattr(u, "input_tokens", 0) or 0 for u in result.usage), default=0),
            "seconds": seconds}


def totals(rows: list[dict], seconds: float, report: str) -> dict:
    return {"report": report, "agents": len(rows), "rows": rows, "seconds": seconds,
            "model_calls": sum(r["calls"] for r in rows),
            "input_tokens": sum(r["input"] for r in rows), "output_tokens": sum(r["output"] for r in rows),
            "peak": max(r["peak"] for r in rows)}


def single(client) -> dict:
    start = time.perf_counter()
    result = run_agent(client, TASK, repo_tools(SAMPLE_REPO))
    seconds = time.perf_counter() - start
    return totals([agent_row("single agent", result, seconds)], seconds, result.text)


def multi(client, parallel: bool = True) -> dict:
    start = time.perf_counter()

    def worker(module: str):
        t0 = time.perf_counter()
        result = run_agent(client, f"Review {module}.", repo_tools(SAMPLE_REPO), system=WORKER_SYSTEM)
        return agent_row(f"worker {module}", result, time.perf_counter() - t0), result.text

    mods = modules()
    if parallel:
        with ThreadPoolExecutor(max_workers=len(mods)) as pool:
            results = list(pool.map(worker, mods))
    else:
        results = [worker(m) for m in mods]
    notes = "\n\n".join(f"## {m}\n{text}" for m, (_, text) in zip(mods, results))
    t0 = time.perf_counter()
    synth = client.messages.create(model=MODEL, max_tokens=1200, messages=[{
        "role": "user", "content": f"{TASK}\n\nCombine these per-module reviews into one report:\n\n{notes}"}])
    rows = [row for row, _ in results]
    rows.append({"name": "synthesizer", "calls": 1, "tools": [], "input": synth.usage.input_tokens,
                 "output": synth.usage.output_tokens, "peak": synth.usage.input_tokens,
                 "seconds": time.perf_counter() - t0})
    report = "".join(b.text for b in synth.content if b.type == "text")
    return totals(rows, time.perf_counter() - start, report)


def show(label: str, out: dict) -> None:
    print(f"\n=== {label}: {out['agents']} agent(s) ===")
    for r in out["rows"]:
        print(f"  {r['name']}: {r['calls']} model calls · {r['input']:,} in / {r['output']:,} out · "
              f"largest window {r['peak']:,} · {r['seconds']:.1f}s")
        for call in r["tools"]:
            print(f"      {call}")
    print(f"  total: {out['model_calls']} model calls · {out['input_tokens']:,} input · "
          f"{out['output_tokens']:,} output tokens · {out['seconds']:.1f}s wall clock")
    print(f"\n--- report ({len(out['report'])} chars) ---\n{out['report']}")


if __name__ == "__main__":
    client = get_client()
    runs = [("single agent", single(client)), ("multi-agent, parallel", multi(client))]
    if "--sequential" in sys.argv:
        runs.append(("multi-agent, sequential", multi(client, parallel=False)))
    for label, out in runs:
        show(label, out)
    base = runs[0][1]
    print("\n=== summary ===")
    for label, out in runs:
        tokens = out["input_tokens"] + out["output_tokens"]
        base_tokens = base["input_tokens"] + base["output_tokens"]
        print(f"  {label:<24} {out['agents']} agents · {out['model_calls']:>2} calls · {tokens:>7,} tokens "
              f"({tokens / base_tokens:.2f}×) · largest window {out['peak']:>6,} · {out['seconds']:5.1f}s "
              f"({out['seconds'] / base['seconds']:.2f}×)")
