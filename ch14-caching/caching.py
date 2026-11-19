"""Chapter 14 — prompt caching and the economics of context.

Stable content first (tools, system prompt), volatile content last (the
conversation). A cache_control breakpoint on the last stable block lets every
later turn re-read that prefix from cache instead of paying full price.

Run:  python ch14-caching/caching.py           # cached vs uncached, same task
"""

from __future__ import annotations

import copy

from course import SAMPLE_REPO, Hooks, get_client, repo_tools, run_agent
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


def run(client=None, cached: bool = True) -> list[dict]:
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
        run_agent(client, TASK, toolbox, system=system, tools=tools, hooks=Hooks(after_turn=record), max_turns=12)
    else:
        run_agent(client, TASK, toolbox, system=SYSTEM_TEXT, hooks=Hooks(after_turn=record), max_turns=12)
    return rows


def relative_cost(rows: list[dict]) -> float:
    """Input cost in 'uncached token' units: cache writes cost ~1.25x, cache reads ~0.1x (5-minute cache)."""
    return sum(r["uncached_input"] + 1.25 * r["cache_write"] + 0.1 * r["cache_read"] for r in rows)


def show(label: str, rows: list[dict]) -> None:
    print(f"\n=== {label} ===")
    print(f"{'turn':>4}  {'uncached':>8}  {'cache write':>11}  {'cache read':>10}")
    for r in rows:
        print(f"{r['turn']:>4}  {r['uncached_input']:>8}  {r['cache_write']:>11}  {r['cache_read']:>10}")
    print(f"Relative input cost: {relative_cost(rows):,.0f}")


if __name__ == "__main__":
    client = get_client()
    show("without caching", run(client, cached=False))
    show("with caching", run(client, cached=True))
    print("\nThings that silently break the cache: timestamps in the system prompt, reordered tools, edited history.")
