"""Chapter 2 — the whole agent loop in about 40 lines.

gather context -> call model -> run tool calls -> append results -> repeat

Run:  python ch02-agent-loop/loop.py "What does this repository do? Is there a bug?"
"""

import os
import sys
from pathlib import Path

from anthropic import Anthropic

MODEL = os.environ.get("COURSE_MODEL", "claude-sonnet-5-5")
ROOT = Path(os.environ.get("COURSE_REPO", Path(__file__).resolve().parents[1] / "sample-repo")).resolve()

TOOLS = [
    {"name": "list_files", "description": "List every file in the repository, one relative path per line.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "read_file", "description": "Read a UTF-8 text file. `path` is relative to the repository root.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
]


def run_tool(name: str, args: dict) -> str:
    if name == "list_files":
        return "\n".join(p.relative_to(ROOT).as_posix() for p in sorted(ROOT.rglob("*")) if p.is_file())
    if name == "read_file":
        path = (ROOT / args["path"]).resolve()
        if ROOT not in path.parents:
            return "Error: path is outside the repository."
        return path.read_text() if path.is_file() else f"Error: {args['path']} not found."
    return f"Error: unknown tool {name}"


def agent(task: str, client=None, max_turns: int = 10) -> str:
    client = client or Anthropic()
    messages = [{"role": "user", "content": task}]
    for _ in range(max_turns):                                     # stop condition 1: turn budget
        response = client.messages.create(model=MODEL, max_tokens=2048, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":                     # stop condition 2: model is done
            return "".join(b.text for b in response.content if b.type == "text")
        results = [{"type": "tool_result", "tool_use_id": b.id, "content": run_tool(b.name, b.input)}
                   for b in response.content if b.type == "tool_use"]
        messages.append({"role": "user", "content": results})      # tool output becomes new context
    return "Stopped: reached max_turns."


if __name__ == "__main__":
    print(agent(sys.argv[1] if len(sys.argv) > 1 else "What does this repository do? Is there a bug?"))
