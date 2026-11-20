# Chapter 5 — Designing tools agents can actually use

**Video:** [How to Design Tools for AI Agents: Descriptions, Schemas, Errors](https://youtu.be/6jl7OZ8jbI8) · **Length:** 5:04

Your agent is not dumb. Your tool description is.

| File | What it shows |
| --- | --- |
| [`tools_bad.py`](tools_bad.py) | Vague names, thin OS wrappers, whole files and raw tracebacks |
| [`tools_good.py`](tools_good.py) | One smart search tool, paging, concise/detailed output, recovery hints in errors |
| [`compare.py`](compare.py) | Same task, both tool sets: compare turns and tokens |

```bash
python ch05-tool-design/compare.py
```

Tool-count bloat (dozens of tools loaded every turn) is covered again in Chapters 8 and 18.

Reference: tool definitions in [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).
