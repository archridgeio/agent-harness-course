# Chapter 1 — What is an agent harness?

**Video:** [What Is an Agent Harness? Same AI Model, Two Results!](https://youtu.be/e4OmXyfkSK0) · **Length:** 5:41

The model is the engine; the harness is the car: the loop, tools, instructions, memory and permissions around the model.

## Demo

```bash
python ch01-what-is-a-harness/bare_call.py          # same model, no harness: it can only guess
python ch02-agent-loop/loop.py "Find and explain the bug in inventory/stats.py"   # same model, minimal harness
```

The bare call never sees the code. The agent in Chapter 2 lists files, reads `stats.py` and finds the real bug.

## Harnesses mentioned

See [REFERENCES.md](../REFERENCES.md#chapter-1) for links to Claude Code, Codex CLI and Kiro.
