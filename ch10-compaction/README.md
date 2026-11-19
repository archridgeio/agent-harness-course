# Chapter 10 — Compaction and summarisation

**Video:** _link added on release_ · **Length:** ~14 min

Compaction is controlled forgetting: decide what the agent must never forget.

[`compaction.py`](compaction.py) plugs into the loop's `before_model` hook:

1. **Tool-result clearing** — all but the newest 3 tool outputs become a one-line placeholder.
2. **Compaction** — past 70% of the budget, older turns are summarised (task, decisions, files, errors, what's left) and replaced by the summary. The cut always lands on an assistant message, so tool calls and their results stay paired.

```bash
python ch10-compaction/compaction.py --budget 12000 "Read every file, then list three risks per module."
python ch10-compaction/compaction.py --off          "Read every file, then list three risks per module."
```

## The trap: clearing without notes

Clear tool output without telling the agent, and it re-reads the same files over and over to answer
(our first live run hit the 30-turn limit this way). Run it with `--no-notes` to watch it happen turn by turn.
The fix is in the system prompt: tell the agent old results get cleared, so it writes down each fact as it goes.

```bash
python ch10-compaction/compaction.py --budget 12000 --no-notes "Read every file, then list three risks per module."
```

The Claude API can also do this server-side (context editing and compaction): see the memory and context management notebooks in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks).
