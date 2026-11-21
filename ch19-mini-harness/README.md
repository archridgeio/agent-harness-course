# Chapter 19 — Build a mini harness from scratch

**Video:** _link added on release_ · **Length:** ~15 min

Everything from 18 chapters in one file, [`mini_harness.py`](mini_harness.py), with no imports from the course package:

| Piece | Chapter |
| --- | --- |
| The loop with stop conditions | 2 |
| Paged, searchable repo tools | 5 |
| AGENTS.md / CLAUDE.md loading | 7 |
| Skills listed by name, loaded on demand | 8 |
| Permission check before writes and commands | 9 |
| Tool-result clearing and compaction at 70% of budget | 10 |
| Long-term memory notes | 12 |
| `delegate` to a read-only sub-agent | 13 |
| Cache breakpoints on system prompt and tools | 14 |
| `progress.md` log of every run | 15 |
| JSONL trace of turns, tools, sub-agents and compactions | 17 |
| Tool output wrapped and marked as data | 18 |

```bash
python ch19-mini-harness/mini_harness.py "Fix the failing test and run the tests"
python ch19-mini-harness/mini_harness.py --auto --repo /path/to/your/repo "Explain this codebase"
git checkout sample-repo    # undo the agent's fix
```

While it runs, the harness prints one line per turn (tokens, cache reads and writes, tools) and per tool call, plus
any clearing, compaction or sub-agent. It ends with a summary: turns, tokens, tools used, context events and
permissions asked. `--quiet` prints only the answer and the summary; `--reset-state` forgets memory, progress and
traces before the run.

State (memory, progress log, traces) lives in `ch19-mini-harness/.harness/` (git-ignored).

Compare the design with [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent), which makes the opposite choice: bash as the only tool.
