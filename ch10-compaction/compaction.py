"""Chapter 10 — compaction and summarisation.

Two techniques, both plugged into the loop's before_model hook:
1. Tool-result clearing: old tool output is replaced with a short placeholder.
   Cheap, lossless for anything the agent can fetch again.
2. Compaction: once the window passes a threshold (70% of a budget), older
   turns are summarised by the model and replaced with that summary.

Run:  python ch10-compaction/compaction.py --budget 6000 "Review every module and list risks"
      python ch10-compaction/compaction.py --budget 6000 --no-notes "..."   # watch it re-read files
      python ch10-compaction/compaction.py --off "Review every module and list risks"
"""

from __future__ import annotations

import json
import sys

from course import MODEL, SAMPLE_REPO, Hooks, get_client, repo_tools, run_agent

CLEARED = "[cleared to save context: call the tool again if you need this output]"

SUMMARY_PROMPT = """You compress an agent's working history so it can continue in a fresh context window.
Keep, in this order:
1. The user's original task, word for word.
2. Decisions made and why.
3. Files read or changed, with the key facts learned from each (function names, line numbers).
4. Errors seen and how they were handled.
5. What is still left to do.
Drop raw tool output, repeated reasoning and pleasantries. Use short bullet points."""


def _plain(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if v is not None}
    return str(obj)


def estimate_tokens(messages: list) -> int:
    return len(json.dumps(messages, default=_plain)) // 4


def clear_old_tool_results(messages: list, keep_last: int = 2) -> list:
    """Clear tool output from all but the newest `keep_last` tool-result TURNS.

    Counting turns, not individual results, matters: a model often reads 8 files in one
    turn, and those results must reach it intact at least once. The newest turn's results
    are never cleared, because the model has not seen them yet.
    """
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], list)
             and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"])]
    to_clear = set(turns[:-max(keep_last, 1)])
    out = []
    for i, m in enumerate(messages):
        if i in to_clear:
            content = [dict(b, content=CLEARED) if isinstance(b, dict) and b.get("type") == "tool_result" else b
                       for b in m["content"]]
            out.append({"role": m["role"], "content": content})
        else:
            out.append(m)
    return out


def transcript(messages: list, max_tool_chars: int = 400) -> str:
    lines = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            lines.append(f"{m['role'].upper()}: {content}")
            continue
        for b in content:
            b = b if isinstance(b, dict) else _plain(b)
            kind = b.get("type")
            if kind == "text":
                lines.append(f"{m['role'].upper()}: {b['text']}")
            elif kind == "tool_use":
                lines.append(f"TOOL CALL {b['name']}({json.dumps(b.get('input'))})")
            elif kind == "tool_result":
                lines.append(f"TOOL RESULT: {str(b.get('content'))[:max_tool_chars]}")
    return "\n".join(lines)


class Compactor:
    """before_model hook: clear old tool results, and summarise when over the threshold."""

    def __init__(self, client, budget: int = 20_000, threshold: float = 0.7, keep_recent: int = 4,
                 keep_tool_results: int = 2, model: str = MODEL):
        self.client, self.budget, self.threshold = client, budget, threshold
        self.keep_recent, self.keep_tool_results, self.model = keep_recent, keep_tool_results, model
        self.compactions = 0
        self.history: list[tuple[int, int]] = []  # (tokens before, tokens after)

    def cut_index(self, messages: list) -> int | None:
        """Start of the kept tail: an assistant message, so tool_use/tool_result pairs stay together."""
        for i in range(len(messages) - self.keep_recent, 0, -1):
            if messages[i]["role"] == "assistant":
                return i
        return None

    def __call__(self, messages: list) -> list:
        messages = clear_old_tool_results(messages, self.keep_tool_results)
        before = estimate_tokens(messages)
        if before < self.threshold * self.budget:
            return messages
        cut = self.cut_index(messages)
        if cut is None:
            return messages
        summary = self.client.messages.create(
            model=self.model, max_tokens=1500, system=SUMMARY_PROMPT,
            messages=[{"role": "user", "content": transcript(messages[:cut])}],
        )
        text = "".join(b.text for b in summary.content if b.type == "text")
        compacted = [{"role": "user", "content": f"<summary_of_earlier_work>\n{text}\n</summary_of_earlier_work>\n"
                                                 "Continue the task from where this summary leaves off."}]
        compacted += messages[cut:]
        self.compactions += 1
        self.history.append((before, estimate_tokens(compacted)))
        return compacted


NOTE_TAKING_SYSTEM = """You are a repo assistant. Respond in English.
Old tool results are cleared from your context to save space, and older turns may be summarised.
So after each tool result, write one short line with the facts you will need later
(for example: "stats.py - risk: mean() divides by len - 1"). Never re-read a file you have
already read: use your notes."""


def trace_turn(turn, response, messages):
    calls = [f"{b.name}({', '.join(f'{v}' for v in (b.input or {}).values())})"
             for b in response.content if b.type == "tool_use"]
    print(f"  turn {turn:>2}: {', '.join(calls) or 'final answer'}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    budget = 20_000
    if "--budget" in args:
        i = args.index("--budget")
        budget = int(args[i + 1])
        del args[i:i + 2]
    off = "--off" in args
    no_notes = "--no-notes" in args  # show the thrash: clearing without telling the agent to take notes
    args = [a for a in args if a not in ("--off", "--no-notes")]
    task = args[0] if args else "Read every file in the repo, then list three risks per module."
    client = get_client()
    compactor = None if off else Compactor(client, budget=budget)
    hooks = Hooks(before_model=compactor, after_turn=trace_turn) if compactor else Hooks(after_turn=trace_turn)
    system = "" if no_notes else NOTE_TAKING_SYSTEM
    result = run_agent(client, task, repo_tools(SAMPLE_REPO), system=system, hooks=hooks, max_turns=30)
    print("\n" + result.text)
    print(f"\nTurns: {result.turns}   input tokens billed: {result.input_tokens:,}")
    if compactor:
        print(f"Compactions: {compactor.compactions}  (estimated tokens before -> after: {compactor.history})")
