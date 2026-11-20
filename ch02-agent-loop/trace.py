"""Chapter 2 — the same loop as loop.py, printing every turn.

For each turn: the stop reason, input/output tokens, and each tool_use / tool_result
pair with its matching ID. Watch input_tokens grow: every turn re-sends the whole
conversation.

Run:  python ch02-agent-loop/trace.py "Is there a bug in this repository? Find it and explain the fix."
"""

import sys
import time
from pathlib import Path

from anthropic import Anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loop import MODEL, TOOLS, run_tool  # noqa: E402


def trace(task: str, client=None, max_turns: int = 10) -> str:
    client = client or Anthropic()
    messages = [{"role": "user", "content": task}]
    start = time.time()
    for turn in range(1, max_turns + 1):
        response = client.messages.create(model=MODEL, max_tokens=2048, tools=TOOLS, messages=messages)
        usage = response.usage
        print(f"[turn {turn}] stop_reason={response.stop_reason} "
              f"input_tokens={usage.input_tokens} output_tokens={usage.output_tokens}")
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            answer = "".join(b.text for b in response.content if b.type == "text")
            print(answer)
            print(f"[time] {time.time() - start:.1f}s")
            return answer
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_tool(block.name, block.input)
                print(f"  tool_use    id={block.id} name={block.name} input={block.input}")
                print(f"  tool_result id={block.id} ({len(output)} chars)")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})
    print(f"[time] {time.time() - start:.1f}s")
    return "Stopped: reached max_turns."


if __name__ == "__main__":
    trace(sys.argv[1] if len(sys.argv) > 1 else "Is there a bug in this repository? Find it and explain the fix.")
