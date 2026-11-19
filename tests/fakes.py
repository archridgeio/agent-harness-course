"""A scripted stand-in for the Anthropic client so every chapter can be tested offline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


@dataclass
class Block:
    type: str
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict | None = None


@dataclass
class Usage:
    input_tokens: int = 100
    output_tokens: int = 20
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class Response:
    content: list
    stop_reason: str
    usage: Usage = field(default_factory=Usage)


def text(t: str, **usage) -> Response:
    return Response([Block("text", text=t)], "end_turn", Usage(**usage))


_counter = 0


def tool(name: str, args: dict | None = None, **usage) -> Response:
    global _counter
    _counter += 1
    return Response([Block("tool_use", id=f"toolu_{_counter}", name=name, input=args or {})], "tool_use", Usage(**usage))


class FakeMessages:
    def __init__(self, script: list[Response]):
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.script:
            raise AssertionError("FakeClient ran out of scripted responses")
        return self.script.pop(0)

    def count_tokens(self, **kwargs):
        return SimpleNamespace(input_tokens=len(json.dumps(kwargs, default=str)) // 4)


class FakeClient:
    def __init__(self, script: list[Response]):
        self.messages = FakeMessages(script)
