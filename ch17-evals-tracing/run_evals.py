"""Chapter 17 — a small eval suite for the repo assistant, with A/B harness variants.

Each task in evals/tasks.jsonl has a question and strings the answer must contain.
Change ONE thing in the harness (here: the tool set) and compare pass rate and tokens.

Run:  python ch17-evals-tracing/run_evals.py --variant full
      python ch17-evals-tracing/run_evals.py --variant no-search
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from tracing import Tracer

from course import SAMPLE_REPO, Hooks, Toolbox, get_client, repo_tools, run_agent

HERE = Path(__file__).parent
TASKS = [json.loads(line) for line in (HERE / "evals" / "tasks.jsonl").read_text().splitlines() if line.strip()]


def variant_tools(variant: str) -> Toolbox:
    toolbox = repo_tools(SAMPLE_REPO)
    if variant == "no-search":
        toolbox.tools.pop("search_code")
    return toolbox


def grade(answer: str, task: dict) -> bool:
    """Each must_contain entry is a case-insensitive regex, so "(2|two) decimal" accepts either wording."""
    return all(re.search(pattern, answer, re.IGNORECASE) for pattern in task["must_contain"])


def run(variant: str = "full", client=None, tasks=TASKS) -> dict:
    client = client or get_client()
    results = []
    for task in tasks:
        tracer = Tracer(HERE / "traces" / f"{variant}-{task['id']}.jsonl")
        out = run_agent(client, task["question"], tracer.wrap(variant_tools(variant)),
                        hooks=Hooks(after_turn=tracer.after_turn), max_turns=12)
        results.append({"id": task["id"], "passed": grade(out.text, task), "turns": out.turns,
                        "input_tokens": out.input_tokens})
    passed = sum(r["passed"] for r in results)
    return {"variant": variant, "passed": passed, "total": len(results),
            "input_tokens": sum(r["input_tokens"] for r in results), "results": results}


if __name__ == "__main__":
    variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "full"
    report = run(variant)
    for r in report["results"]:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']:<12} {r['turns']:>2} turns  {r['input_tokens']:>7,} tokens")
    print(f"\n{report['variant']}: {report['passed']}/{report['total']} passed, "
          f"{report['input_tokens']:,} input tokens. Traces in ch17-evals-tracing/traces/")
