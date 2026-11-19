"""Chapter 13 — sub-agents and context isolation.

The orchestrator gets a `delegate` tool. Each delegation runs a fresh agent
loop with its own clean context window and read-only tools, and only its
final, condensed answer comes back to the orchestrator.

Run:  python ch13-subagents/subagents.py "Find every caller of bulk_discount and explain each one"
      python ch13-subagents/subagents.py --no-subagents "..."   # same task, single agent
"""

from __future__ import annotations

import sys

from course import SAMPLE_REPO, Tool, get_client, repo_tools, run_agent

ORCHESTRATOR_SYSTEM = """You coordinate work on a code repository.
For any job that needs reading several files, call `delegate` with a focused brief instead of reading
the files yourself. Combine the sub-agents' reports into the final answer."""

SUBAGENT_SYSTEM = """You are a sub-agent with a single focused job. Use the tools, then reply with a
condensed report: at most 150 words, with file:line references. No preamble."""

MAX_REPORT_CHARS = 1500


class Delegator:
    def __init__(self, client, max_turns: int = 12):
        self.client, self.max_turns = client, max_turns
        self.runs: list[dict] = []

    def __call__(self, brief: str) -> str:
        result = run_agent(self.client, brief, repo_tools(SAMPLE_REPO), system=SUBAGENT_SYSTEM,
                           max_turns=self.max_turns)
        self.runs.append({"brief": brief, "turns": result.turns, "input_tokens": result.input_tokens})
        report = result.text.strip()
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
        return {"answer": result.text, "main_window_tokens": result.input_tokens, "subagent_tokens": 0}
    delegator = Delegator(client)
    toolbox = repo_tools(SAMPLE_REPO)
    toolbox.add(delegator.tool())
    result = run_agent(client, task, toolbox, system=ORCHESTRATOR_SYSTEM)
    return {"answer": result.text, "main_window_tokens": result.input_tokens,
            "subagent_tokens": sum(r["input_tokens"] for r in delegator.runs), "subagents": delegator.runs}


if __name__ == "__main__":
    args = sys.argv[1:]
    single = "--no-subagents" in args
    args = [a for a in args if a != "--no-subagents"]
    task = args[0] if args else "Find every caller of bulk_discount and explain what each one does with it."
    out = run(task, use_subagents=not single)
    print(out["answer"])
    print(f"\nMain window input tokens: {out['main_window_tokens']:,}")
    print(f"Sub-agent input tokens:   {out['subagent_tokens']:,}  (isolated: never entered the main window)")
