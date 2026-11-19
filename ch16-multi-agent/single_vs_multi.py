"""Chapter 16 — single agent vs multi-agent on the same task.

Task: a short review of every module in the repo.
- Single agent: one loop reads everything and writes the report.
- Multi-agent: an orchestrator fans out one worker per module in parallel,
  then a synthesizer merges their reports.

Run:  python ch16-multi-agent/single_vs_multi.py
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from course import MODEL, SAMPLE_REPO, get_client, repo_tools, run_agent

TASK = "Write a short review of the repo: for each module, its purpose, its riskiest function, and one improvement."
WORKER_SYSTEM = "Review exactly one module. Reply in at most 80 words: purpose, riskiest function, one improvement."


def modules() -> list[str]:
    return sorted(p.relative_to(SAMPLE_REPO).as_posix() for p in (SAMPLE_REPO / "inventory").glob("*.py")
                  if p.name != "__init__.py")


def single(client) -> dict:
    start = time.perf_counter()
    result = run_agent(client, TASK, repo_tools(SAMPLE_REPO))
    return {"report": result.text, "input_tokens": result.input_tokens, "seconds": time.perf_counter() - start,
            "agents": 1}


def multi(client, parallel: bool = True) -> dict:
    start = time.perf_counter()

    def worker(module: str):
        return module, run_agent(client, f"Review {module}.", repo_tools(SAMPLE_REPO), system=WORKER_SYSTEM)

    mods = modules()
    if parallel:
        with ThreadPoolExecutor(max_workers=len(mods)) as pool:
            results = list(pool.map(worker, mods))
    else:
        results = [worker(m) for m in mods]
    notes = "\n\n".join(f"## {m}\n{r.text}" for m, r in results)
    synth = client.messages.create(model=MODEL, max_tokens=1200, messages=[{
        "role": "user", "content": f"{TASK}\n\nCombine these per-module reviews into one report:\n\n{notes}"}])
    tokens = sum(r.input_tokens for _, r in results) + synth.usage.input_tokens
    return {"report": "".join(b.text for b in synth.content if b.type == "text"), "input_tokens": tokens,
            "seconds": time.perf_counter() - start, "agents": len(results) + 1}


if __name__ == "__main__":
    client = get_client()
    for label, out in [("single agent", single(client)), ("multi-agent", multi(client))]:
        print(f"\n=== {label}: {out['agents']} agent(s), {out['input_tokens']:,} input tokens, {out['seconds']:.1f}s ===")
        print(out["report"])
    print("\nMulti-agent wins on breadth (independent, parallel work). Single agent wins on coherence.")
