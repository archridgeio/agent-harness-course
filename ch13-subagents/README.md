# Chapter 13 — Sub-agents and context isolation

**Video:** _link added on release_ · **Length:** ~14 min

Spawn a helper, let it read 50 files, get back one paragraph.

[`subagents.py`](subagents.py) gives the orchestrator a `delegate` tool. Each sub-agent runs its own loop in a clean context window with read-only tools; only a condensed report (≤ 150 words, capped at 1,500 characters) returns.

```bash
python ch13-subagents/subagents.py "Find every caller of bulk_discount and explain each one"
python ch13-subagents/subagents.py --no-subagents "Find every caller of bulk_discount and explain each one"
```

Watch two numbers: main-window tokens (lower with sub-agents) and total tokens (often higher). Sub-agents are a context-isolation tool first, a speed tool second.

Reference: sub-agent support in [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python).
