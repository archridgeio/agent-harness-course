"""Chapter 17 — a small eval suite for the repo assistant, with A/B harness variants.

Each task in evals/tasks.jsonl has a question and strings the answer must contain.
Change ONE thing in the harness (here: the tool set) and compare pass rate and tokens.

Run:  python ch17-evals-tracing/run_evals.py --variant full
      python ch17-evals-tracing/run_evals.py --variant no-search
      python ch17-evals-tracing/run_evals.py --compare --repeat 3   # both variants, 3 runs each, side by side
"""

from __future__ import annotations

import json
import re
import sys
import time
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


def tool_calls(messages: list) -> list[str]:
    calls = []
    for m in messages:
        if m["role"] == "assistant" and not isinstance(m["content"], str):
            for b in m["content"]:
                if getattr(b, "type", None) == "tool_use":
                    calls.append(f"{b.name}({', '.join(str(v)[:40] for v in (b.input or {}).values())})")
    return calls


def run(variant: str = "full", client=None, tasks=TASKS, repeat: int = 1) -> dict:
    client = client or get_client()
    results = []
    for task in tasks:
        for n in range(1, repeat + 1):
            suffix = f"-r{n}" if repeat > 1 else ""
            tracer = Tracer(HERE / "traces" / f"{variant}-{task['id']}{suffix}.jsonl")
            start = time.perf_counter()
            out = run_agent(client, task["question"], tracer.wrap(variant_tools(variant)),
                            hooks=Hooks(after_turn=tracer.after_turn), max_turns=12)
            results.append({"id": task["id"], "run": n, "passed": grade(out.text, task), "turns": out.turns,
                            "input_tokens": out.input_tokens, "output_tokens": out.output_tokens,
                            "seconds": time.perf_counter() - start, "tools": tool_calls(out.messages),
                            "answer": out.text.strip()})
    passed = sum(r["passed"] for r in results)
    return {"variant": variant, "passed": passed, "total": len(results), "repeat": repeat,
            "input_tokens": sum(r["input_tokens"] for r in results),
            "output_tokens": sum(r["output_tokens"] for r in results), "results": results}


def show(report: dict) -> None:
    print(f"\n=== variant: {report['variant']} ===")
    for r in report["results"]:
        run_label = f" run {r['run']}" if report["repeat"] > 1 else ""
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']:<10}{run_label:<6} {r['turns']:>2} turns  "
              f"{r['input_tokens']:>6,} in  {r['output_tokens']:>5,} out  {r['seconds']:5.1f}s  "
              f"{' · '.join(r['tools']) or '-'}")
        if not r["passed"]:
            print(f"      answer was: {r['answer'][:200]!r}")
    print(f"{report['variant']}: {report['passed']}/{report['total']} passed, {report['input_tokens']:,} input "
          f"and {report['output_tokens']:,} output tokens. Traces in ch17-evals-tracing/traces/")


def compare(reports: list[dict]) -> None:
    ids = list(dict.fromkeys(r["id"] for r in reports[0]["results"]))
    print("\n=== side by side ===")
    print(f"{'task':<12}" + "".join(f"{rep['variant']:>26}" for rep in reports))
    for tid in ids:
        cells = []
        for rep in reports:
            rs = [r for r in rep["results"] if r["id"] == tid]
            avg = sum(r["input_tokens"] + r["output_tokens"] for r in rs) / len(rs)
            cells.append(f"{sum(r['passed'] for r in rs)}/{len(rs)} pass · {avg:>6,.0f} tok")
        print(f"{tid:<12}" + "".join(f"{c:>26}" for c in cells))
    cells = [f"{rep['passed']}/{rep['total']} · {rep['input_tokens'] + rep['output_tokens']:>7,} tok" for rep in reports]
    print(f"{'total':<12}" + "".join(f"{c:>26}" for c in cells))


if __name__ == "__main__":
    repeat = int(sys.argv[sys.argv.index("--repeat") + 1]) if "--repeat" in sys.argv else 1
    if "--compare" in sys.argv:
        reports = [run(v, repeat=repeat) for v in ("full", "no-search")]
        for rep in reports:
            show(rep)
        compare(reports)
    else:
        variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "full"
        show(run(variant, repeat=repeat))
