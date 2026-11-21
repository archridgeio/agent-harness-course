# Chapter 15 — Long-horizon tasks: state, checkpoints, progress files

**Video:** _link added on release_ · **Length:** ~14 min

When a task needs more context than any window holds, keep the state outside the window.

[`long_task.py`](long_task.py) works on a copy of the sample repo in `ch15-long-horizon/workspace/` (git-ignored):

- **Initializer session** turns a 4-item spec into `features.json` and `progress.md`.
- **Worker sessions** each start with a fresh window, read the files and `git log`, finish one feature, run the tests and update the files.
- **The harness commits after every session**, so git is the checkpoint log.

```bash
python ch15-long-horizon/long_task.py --reset --stop-after 2   # start clean, stop after 2 worker sessions
python ch15-long-horizon/long_task.py --show                   # features.json, progress.md, git log
python ch15-long-horizon/long_task.py                          # resumes from progress.md / features.json / git
```

Each session prints its tool calls, turns, tokens and its largest single window, so you can see every
worker start fresh. Ctrl+C at any point stops cleanly and lists uncommitted changes; the next run
resumes from the last commit, and session numbers carry on from the git log.

Reference: the `autonomous-coding` quickstart in [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts), which uses the same initializer + worker pattern.
