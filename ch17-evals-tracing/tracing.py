"""Chapter 17 — traces: every turn, tool call, token count and latency, as JSON lines.

Usage in code:
    tracer = Tracer("traces/run.jsonl")
    run_agent(client, task, tracer.wrap(toolbox), hooks=Hooks(after_turn=tracer.after_turn))
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from course.tools import Toolbox


class Tracer:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("")
        self._turn_started = time.perf_counter()

    def _write(self, event: dict) -> None:
        with self.path.open("a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def after_turn(self, turn: int, response, messages) -> None:
        now = time.perf_counter()
        u = response.usage
        self._write({
            "event": "model_turn", "turn": turn, "stop_reason": response.stop_reason,
            "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
            "tool_calls": [b.name for b in response.content if b.type == "tool_use"],
            "seconds": round(now - self._turn_started, 3),
        })
        self._turn_started = now

    def wrap(self, toolbox: Toolbox) -> Toolbox:
        tracer = self

        class TracedToolbox(Toolbox):
            def call(self, name, args):
                start = time.perf_counter()
                out = super().call(name, args)
                tracer._write({"event": "tool_call", "tool": name, "args": args, "output_chars": len(out),
                               "approx_tokens": len(out) // 4, "error": out.startswith("Error"),
                               "seconds": round(time.perf_counter() - start, 4)})
                return out

        traced = TracedToolbox()
        traced.tools = toolbox.tools
        return traced


def load(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
