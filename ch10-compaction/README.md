# Chapter 10 — Compaction and summarisation

**Video:** _link added on release_ · **Length:** ~14 min

Compaction is controlled forgetting: decide what the agent must never forget.

[`compaction.py`](compaction.py) plugs into the loop's `before_model` hook:

1. **Tool-result clearing** — tool output older than the last 2 tool turns becomes a one-line placeholder. It counts turns, not results: a model often reads 8 files in one turn, and every result must reach it at least once.
2. **Compaction** — past 70% of the budget, older turns are summarised (task, decisions, files, errors, what's left) and replaced by the summary. The cut always lands on an assistant message, so tool calls and their results stay paired.

```bash
python ch10-compaction/compaction.py --budget 3000   # module-by-module review, compaction on
python ch10-compaction/compaction.py --off           # same task, no clearing or compaction
```

The sample repo is tiny, so a 3,000-token budget stands in for a large codebase filling a real window. Each turn's tool calls are printed, so you can see where compaction kicks in.

## Two traps we hit while building this chapter

1. **Clearing results the model has not seen yet.** Models often read many files in one turn. Our first version kept "the newest 3 results", so 5 of 8 files read in parallel were cleared before the model saw them, and it re-read files until it hit the 30-turn limit. Clear by *turn*, and never the newest one.
2. **Clearing without telling the agent.** If old output silently disappears, the agent goes back for it. The system prompt tells it results get cleared, so it notes each fact as it goes. Compare:

```bash
python ch10-compaction/compaction.py --budget 3000 --no-notes
```

The Claude API can also do this server-side (context editing and compaction): see the memory and context management notebooks in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks).
