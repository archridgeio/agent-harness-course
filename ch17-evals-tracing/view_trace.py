"""Chapter 17 — summarise a trace and point at the wasteful turn.

Run:  python ch17-evals-tracing/view_trace.py ch17-evals-tracing/traces/<file>.jsonl
      python ch17-evals-tracing/view_trace.py --all ch17-evals-tracing/traces   # one line per trace
"""

import sys
from pathlib import Path

from tracing import load


def summarize(events: list[dict]) -> str:
    turns = [e for e in events if e["event"] == "model_turn"]
    tools = [e for e in events if e["event"] == "tool_call"]
    lines = [f"{len(turns)} model turns, {len(tools)} tool calls, "
             f"{sum(t['input_tokens'] for t in turns):,} input tokens, "
             f"{sum(t['seconds'] for t in turns):.1f}s in model calls"]
    lines.append(f"\n{'turn':>4}  {'input':>7}  {'output':>6}  {'secs':>5}  tools")
    for t in turns:
        lines.append(f"{t['turn']:>4}  {t['input_tokens']:>7}  {t['output_tokens']:>6}  {t['seconds']:>5}  "
                     f"{', '.join(t['tool_calls']) or '-'}")
    if turns:
        big = max(turns, key=lambda t: t["input_tokens"])
        lines.append(f"\nMost expensive turn: turn {big['turn']}, {big['input_tokens']:,} input tokens"
                     f" (turn 1 was {turns[0]['input_tokens']:,}).")
    if tools:
        worst = max(tools, key=lambda e: e["approx_tokens"])
        lines.append(f"\nBiggest tool output: {worst['tool']}({worst['args']}) ≈ {worst['approx_tokens']:,} tokens"
                     " — it is re-sent on every later turn. Page it, truncate it or clear it.")
        errors = [e for e in tools if e["error"]]
        if errors:
            lines.append(f"Tool errors: {len(errors)} ({', '.join(e['tool'] for e in errors)})")
    return "\n".join(lines)


def overview(folder: str | Path) -> str:
    lines = [f"{'trace':<28} {'turns':>5} {'tools':>5} {'input':>7} {'biggest tool output':>22}"]
    for path in sorted(Path(folder).glob("*.jsonl")):
        events = load(path)
        turns = [e for e in events if e["event"] == "model_turn"]
        tools = [e for e in events if e["event"] == "tool_call"]
        worst = max(tools, key=lambda e: e["approx_tokens"]) if tools else None
        big = f"{worst['tool']} ≈{worst['approx_tokens']:,}" if worst else "-"
        lines.append(f"{path.stem:<28} {len(turns):>5} {len(tools):>5} "
                     f"{sum(t['input_tokens'] for t in turns):>7,} {big:>22}")
    return "\n".join(lines)


if __name__ == "__main__":
    if sys.argv[1] == "--all":
        print(overview(sys.argv[2]))
    else:
        print(summarize(load(sys.argv[1])))
