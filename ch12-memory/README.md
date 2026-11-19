# Chapter 12 — Memory: scratchpads, notes and long-term memory

**Video:** _link added on release_ · **Length:** ~14 min

The context window resets. The agent's notebook does not.

[`memory_tool.py`](memory_tool.py) gives the agent one `memory` tool with file commands (view, create, str_replace, insert, delete, rename) under `/memories`, stored in `ch12-memory/.memories/` (git-ignored).

```bash
python ch12-memory/memory_tool.py session1   # learns "discounts are capped at 50%" and saves it
python ch12-memory/memory_tool.py session2   # brand-new conversation: recalls the cap
python ch12-memory/memory_tool.py show
```

Risks to cover: stale memories, privacy (never store secrets), and memories that start acting like instructions.

References: the memory tool in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) (`tool_use/memory_tool.py`), and [letta-ai/letta](https://github.com/letta-ai/letta) for self-managed agent memory.
