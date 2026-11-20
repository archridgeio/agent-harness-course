# Chapter 2 — Anatomy of the agent loop

**Video:** _link added on release_ · **Length:** ~13 min

Every agent is a while-loop. [`loop.py`](loop.py) is the whole thing in about 40 lines:

1. Send the conversation and the tool definitions to the model.
2. If the model asks for tools (`stop_reason == "tool_use"`), run them.
3. Append the results as a `tool_result` message and go round again.
4. Stop when the model answers without tools, or when `max_turns` runs out.

```bash
python ch02-agent-loop/loop.py "Find and explain the bug in inventory/stats.py"
```

To watch every turn, run [`trace.py`](trace.py): the same loop, printing each turn's stop reason, token counts and every `tool_use` / `tool_result` pair with its matching ID.

```bash
python ch02-agent-loop/trace.py "Is there a bug in this repository? Find it and explain the fix."
```

Compare it with [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)'s agent class: the same loop, with bash as the only tool.

From Chapter 3 on, the course reuses this loop from [`course/loop.py`](../course/loop.py), which adds hooks for context management, permissions and tracing.
