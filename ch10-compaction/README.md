# Chapter 10 — Compaction and summarisation

**Video:** _link added on release_ · **Length:** ~14 min

Compaction is controlled forgetting: decide what the agent must never forget.

[`compaction.py`](compaction.py) plugs into the loop's `before_model` hook:

1. **Tool-result clearing** — all but the newest 3 tool outputs become a one-line placeholder.
2. **Compaction** — past 70% of the budget, older turns are summarised (task, decisions, files, errors, what's left) and replaced by the summary. The cut always lands on an assistant message, so tool calls and their results stay paired.

```bash
python ch10-compaction/compaction.py --budget 6000 "Read every file, then list three risks per module."
python ch10-compaction/compaction.py --off          "Read every file, then list three risks per module."
```

The Claude API can also do this server-side (context editing and compaction): see the memory and context management notebooks in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks).
