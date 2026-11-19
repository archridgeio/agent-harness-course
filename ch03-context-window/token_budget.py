"""Chapter 3 — watch the context window fill up, turn by turn.

Runs the repo assistant on a task and prints how many input tokens each turn
used, split into tool definitions, system prompt and conversation (history +
tool results). The conversation share is the part that keeps growing.

Run:  python ch03-context-window/token_budget.py "Explain every module in this repo"
"""

import sys

from course import MODEL, SAMPLE_REPO, Hooks, get_client, repo_tools, run_agent

SYSTEM = "You are a repo assistant. Use the tools to read code before answering."
BAR_WIDTH = 40


def fixed_costs(client, toolbox, system: str) -> dict:
    """Tokens for tool definitions and system prompt, measured with count_tokens."""
    probe = [{"role": "user", "content": "x"}]
    base = client.messages.count_tokens(model=MODEL, messages=probe).input_tokens
    with_tools = client.messages.count_tokens(model=MODEL, messages=probe, tools=toolbox.specs()).input_tokens
    with_system = client.messages.count_tokens(model=MODEL, messages=probe, system=system).input_tokens
    return {"tools": max(with_tools - base, 0), "system": max(with_system - base, 0)}


def bar(n: int, scale: int) -> str:
    return "#" * max(1, round(n / scale * BAR_WIDTH)) if n else ""


def report(rows: list[dict]) -> str:
    scale = max(r["input"] for r in rows) or 1
    lines = [f"{'turn':>4}  {'input':>7}  {'tools':>6}  {'system':>6}  {'conversation':>12}  growth"]
    for r in rows:
        lines.append(
            f"{r['turn']:>4}  {r['input']:>7}  {r['tools']:>6}  {r['system']:>6}  {r['conversation']:>12}  "
            f"{bar(r['input'], scale)}"
        )
    total = sum(r["input"] for r in rows)
    lines.append(f"\nTotal input tokens billed across {len(rows)} turns: {total:,}")
    lines.append("Every turn re-sends the whole conversation, so cost grows faster than the transcript.")
    return "\n".join(lines)


def run(task: str, client=None) -> list[dict]:
    client = client or get_client()
    toolbox = repo_tools(SAMPLE_REPO)
    fixed = fixed_costs(client, toolbox, SYSTEM)
    rows: list[dict] = []

    def record(turn, response, messages):
        used = response.usage.input_tokens
        rows.append({
            "turn": turn,
            "input": used,
            "tools": fixed["tools"],
            "system": fixed["system"],
            "conversation": max(used - fixed["tools"] - fixed["system"], 0),
        })

    run_agent(client, task, toolbox, system=SYSTEM, hooks=Hooks(after_turn=record))
    return rows


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "Read every Python file and explain what each module does."
    print(report(run(task)))
