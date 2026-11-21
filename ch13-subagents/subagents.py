"""Chapter 13 — sub-agents and context isolation.

The orchestrator gets a `delegate` tool. Each delegation runs a fresh agent
loop with its own clean context window and read-only tools, and only its
final, condensed answer comes back to the orchestrator.

Run:  python ch13-subagents/subagents.py "Find every caller of bulk_discount and explain each one"
      python ch13-subagents/subagents.py --no-subagents "..."   # same task, single agent
"""

from __future__ import annotations

import sys

from course import SAMPLE_REPO, Tool, Toolbox, get_client, repo_tools, run_agent

ORCHESTRATOR_SYSTEM = """You coordinate work on a code repository. You cannot read files yourself:
call `delegate` with a focused, self-contained brief for each job (several briefs are fine), then
combine the sub-agents' reports into the final answer. Respond in English."""

SUBAGENT_SYSTEM = """You are a sub-agent with a single focused job. Use the tools, then reply with a
condensed report: at most 150 words, with file:line references. No preamble."""

MAX_REPORT_CHARS = 1500


def tool_calls(messages: list) -> list[str]:
    calls = []
    for m in messages:
        if m["role"] == "assistant" and not isinstance(m["content"], str):
            for b in m["content"]:
                if getattr(b, "type", None) == "tool_use":
                    calls.append(f"{b.name}({', '.join(str(v)[:50] for v in (b.input or {}).values())})")
    return calls


def peak_window(result) -> int:
    """Largest single request: how full the context window got."""
    return max((getattr(u, "input_tokens", 0) or 0 for u in result.usage), default=0)


class Delegator:
    def __init__(self, client, max_turns: int = 12):
        self.client, self.max_turns = client, max_turns
        self.runs: list[dict] = []

    def __call__(self, brief: str) -> str:
        result = run_agent(self.client, brief, repo_tools(SAMPLE_REPO), system=SUBAGENT_SYSTEM,
                           max_turns=self.max_turns)
        report = result.text.strip()
        self.runs.append({"brief": brief, "turns": result.turns, "input_tokens": result.input_tokens,
                          "peak_window": peak_window(result), "calls": tool_calls(result.messages),
                          "report_chars": len(report)})
        if len(report) > MAX_REPORT_CHARS:
            report = report[:MAX_REPORT_CHARS] + " [report truncated]"
        return report

    def tool(self) -> Tool:
        return Tool("delegate",
                    "Hand a focused job to a sub-agent with a fresh context window and read-only repo tools. "
                    "Write a self-contained brief: the goal, what to look at, and what to report back.",
                    {"type": "object", "properties": {"brief": {"type": "string"}}, "required": ["brief"]},
                    self)


def run(task: str, client=None, use_subagents: bool = True) -> dict:
    client = client or get_client()
    if not use_subagents:
        result = run_agent(client, task, repo_tools(SAMPLE_REPO))
        return {"answer": result.text, "main_window_tokens": result.input_tokens, "subagent_tokens": 0,
                "turns": result.turns, "peak_window": peak_window(result), "calls": tool_calls(result.messages)}
    delegator = Delegator(client)
    # The orchestrator gets ONLY the delegate tool: it cannot read files itself, so all
    # reading happens in sub-agents and only their reports enter the main window.
    toolbox = Toolbox([delegator.tool()])
    result = run_agent(client, task, toolbox, system=ORCHESTRATOR_SYSTEM)
    return {"answer": result.text, "main_window_tokens": result.input_tokens,
            "subagent_tokens": sum(r["input_tokens"] for r in delegator.runs), "subagents": delegator.runs,
            "turns": result.turns, "peak_window": peak_window(result), "calls": tool_calls(result.messages)}


if __name__ == "__main__":
    args = sys.argv[1:]
    single = "--no-subagents" in args
    args = [a for a in args if a != "--no-subagents"]
    task = args[0] if args else "Find every caller of bulk_discount and explain what each one does with it."
    out = run(task, use_subagents=not single)
    print(f"Main agent: {out['turns']} turns · calls: {'; '.join(out['calls'])}")
    for i, r in enumerate(out.get("subagents", []), 1):
        print(f"\nSub-agent {i}: {r['turns']} turns · {r['input_tokens']:,} input tokens · "
              f"largest window {r['peak_window']:,} · report {r['report_chars']} chars")
        print(f"  brief: {r['brief'][:160]}")
        print(f"  calls: {'; '.join(r['calls'])}")
    print("\n" + out["answer"])
    print(f"\nMain window input tokens: {out['main_window_tokens']:,}  (largest single window: {out['peak_window']:,})")
    print(f"Sub-agent input tokens:   {out['subagent_tokens']:,}  (isolated: never entered the main window)")
    print(f"Total input tokens:       {out['main_window_tokens'] + out['subagent_tokens']:,}")
