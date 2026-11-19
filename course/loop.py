"""The reusable agent loop, with hooks for the techniques taught in later chapters.

Hooks
-----
before_model(messages) -> messages
    Runs before every model call. Context management lives here
    (tool-result clearing in Ch 10, compaction in Ch 10, memory in Ch 12).
before_tool(name, args) -> str | None
    Runs before every tool call. Return a string to block the call; the string
    is sent back to the model as an error (permissions in Ch 9).
after_turn(turn, response, messages) -> None
    Runs after every model response (token accounting in Ch 3, tracing in Ch 17).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from course.client import MODEL
from course.tools import Toolbox


# Used when a chapter passes no system prompt, so answers stay in English on camera.
DEFAULT_SYSTEM = "You are a helpful repo assistant. Always respond in English."


@dataclass
class Hooks:
    before_model: Callable[[list], list] | None = None
    before_tool: Callable[[str, dict], str | None] | None = None
    after_turn: Callable[[int, Any, list], None] | None = None


@dataclass
class AgentResult:
    text: str
    messages: list
    turns: int
    stopped: str  # "end_turn", "max_turns", ...
    usage: list = field(default_factory=list)

    @property
    def input_tokens(self) -> int:
        return sum(getattr(u, "input_tokens", 0) or 0 for u in self.usage)

    @property
    def output_tokens(self) -> int:
        return sum(getattr(u, "output_tokens", 0) or 0 for u in self.usage)


def response_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def run_agent(
    client,
    task: str,
    toolbox: Toolbox | None = None,
    *,
    system: str | list = "",
    model: str = MODEL,
    max_turns: int = 20,
    max_tokens: int = 4096,
    hooks: Hooks | None = None,
    messages: list | None = None,
    tools: list[dict] | None = None,
) -> AgentResult:
    """Run the loop until the model stops asking for tools or max_turns is hit.

    `messages` lets a caller continue an earlier conversation. `tools` overrides
    the toolbox specs (Ch 14 uses it to add cache_control).
    """
    toolbox = toolbox or Toolbox()
    hooks = hooks or Hooks()
    messages = messages if messages is not None else []
    messages.append({"role": "user", "content": task})
    usage: list = []
    tool_specs = tools if tools is not None else toolbox.specs()

    for turn in range(1, max_turns + 1):
        if hooks.before_model:
            messages[:] = hooks.before_model(messages)

        kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
        kwargs["system"] = system or DEFAULT_SYSTEM
        if tool_specs:
            kwargs["tools"] = tool_specs
        response = client.messages.create(**kwargs)
        usage.append(response.usage)
        messages.append({"role": "assistant", "content": response.content})
        if hooks.after_turn:
            hooks.after_turn(turn, response, messages)

        if response.stop_reason != "tool_use":
            return AgentResult(response_text(response), messages, turn, response.stop_reason or "end_turn", usage)

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            blocked = hooks.before_tool(block.name, block.input) if hooks.before_tool else None
            if blocked is not None:
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": blocked, "is_error": True})
            else:
                output = toolbox.call(block.name, block.input or {})
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})

    return AgentResult("Stopped: reached max_turns before finishing.", messages, max_turns, "max_turns", usage)
