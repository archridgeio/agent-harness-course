"""Chapter 14 — prompt caching and the economics of context.

Stable content first (tools, system prompt), volatile content last (the
conversation). A cache_control breakpoint on the last stable block lets every
later turn re-read that prefix from cache instead of paying full price.

Run:  python ch14-caching/caching.py           # uncached, cached, and a cache broken by a timestamp
"""

from __future__ import annotations

import copy
from datetime import datetime

from course import MODEL, SAMPLE_REPO, Hooks, get_client, repo_tools, run_agent
from course.tools import read_file

TASK = "Review each module in the repo one at a time and list one improvement per module."

# A long, stable system prompt (project handbook) is the classic thing to cache.
# Caching only kicks in above a minimum prefix length, so the demo pads it with real reference text.
HANDBOOK = "\n\n".join(
    [(SAMPLE_REPO / "AGENTS.md").read_text()]
    + [read_file(SAMPLE_REPO, f"inventory/{m}.py") for m in ("stats", "pricing", "stock")] * 3
)
SYSTEM_TEXT = "You are a code reviewer for this project. Project handbook and reference code:\n\n" + HANDBOOK


def cached_request_parts(toolbox):
    """System and tools with a cache breakpoint at the end of the stable prefix."""
    system = [{"type": "text", "text": SYSTEM_TEXT, "cache_control": {"type": "ephemeral"}}]
    tools = copy.deepcopy(toolbox.specs())
    tools[-1]["cache_control"] = {"type": "ephemeral"}
    return system, tools


def run(client=None, cached: bool = True, timestamp: bool = False) -> list[dict]:
    """cached=False: no breakpoints. timestamp=True: cached, but the system prompt starts with the
    current time, updated before every request, which is the classic way to break the cache."""
    client = client or get_client()
    toolbox = repo_tools(SAMPLE_REPO)
    rows: list[dict] = []

    def record(turn, response, messages):
        u = response.usage
        rows.append({"turn": turn, "uncached_input": u.input_tokens,
                     "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
                     "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0})

    if cached:
        system, tools = cached_request_parts(toolbox)
        before = None
        if timestamp:
            def before(messages):
                system[0]["text"] = f"Current time: {datetime.now().isoformat()}\n\n" + SYSTEM_TEXT
                return messages
        run_agent(client, TASK, toolbox, system=system, tools=tools,
                  hooks=Hooks(before_model=before, after_turn=record), max_turns=12)
    else:
        run_agent(client, TASK, toolbox, system=SYSTEM_TEXT, hooks=Hooks(after_turn=record), max_turns=12)
    return rows


# 5-minute cache writes cost 1.25x the base input price. Cache reads cost 0.1x on most models and
# 0.05x on Claude Sonnet 5.5 and Opus 5.5 (Claude pricing docs, Nov 2026). Check before quoting.
WRITE_MULT = 1.25
READ_MULT = 0.05 if any(m in MODEL for m in ("sonnet-5-5", "opus-5-5")) else 0.1


def relative_cost(rows: list[dict]) -> float:
    """Input cost in 'uncached token' units."""
    return sum(r["uncached_input"] + WRITE_MULT * r["cache_write"] + READ_MULT * r["cache_read"] for r in rows)


def show(label: str, rows: list[dict]) -> None:
    print(f"\n=== {label} ===")
    print(f"{'turn':>4}  {'uncached':>8}  {'cache write':>11}  {'cache read':>10}")
    for r in rows:
        print(f"{r['turn']:>4}  {r['uncached_input']:>8}  {r['cache_write']:>11}  {r['cache_read']:>10}")
    print(f"Relative input cost: {relative_cost(rows):,.0f}")


if __name__ == "__main__":
    client = get_client()
    print(f"Model: {MODEL} · cache write {WRITE_MULT}x · cache read {READ_MULT}x base input price")
    runs = {"without caching": run(client, cached=False),
            "with caching": run(client, cached=True),
            "with caching, but a timestamp in the system prompt": run(client, cached=True, timestamp=True)}
    for label, rows in runs.items():
        show(label, rows)
    base = relative_cost(runs["without caching"])
    print("\nSummary (relative input cost, uncached run = 100%):")
    for label, rows in runs.items():
        print(f"  {label:<52} {relative_cost(rows):>8,.0f}  ({relative_cost(rows) / base:.0%})")
    print("\nThings that silently break the cache: timestamps in the system prompt, reordered tools, edited history.")
