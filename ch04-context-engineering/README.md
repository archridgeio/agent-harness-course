# Chapter 4 — Context engineering vs prompt engineering

**Video:** _link added on release_ · **Length:** ~12 min

Prompt engineering writes one message. Context engineering designs everything the model sees, every turn:

1. System prompt
2. Tool definitions
3. Instruction files (AGENTS.md, CLAUDE.md, steering files)
4. Conversation history
5. Retrieved data (tool output)
6. Memory

```bash
python ch04-context-engineering/context_map.py           # offline estimate
python ch04-context-engineering/context_map.py --exact   # measured with the API's count_tokens
```

Modules 2 and 3 of the course give you a tool for each of these six inputs.

Further reading: the context engineering notebook in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) (`tool_use/context_engineering`).
