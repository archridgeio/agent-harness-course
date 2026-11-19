# Chapter 18 — Context failure modes and prompt injection

**Video:** _link added on release_ · **Length:** ~14 min

Most "model mistakes" are context mistakes, and context is an attack surface.

[`failures.py`](failures.py) reproduces five failures on a throwaway copy of the sample repo, each run broken and then fixed:

| Scenario | Broken | Fix (from earlier chapters) |
| --- | --- | --- |
| `poisoning` | A wrong claim in the history is trusted | Treat earlier conclusions as hypotheses; verify (Ch 7) |
| `distraction` | 25 irrelevant notes bury the task | Compaction (Ch 10) |
| `confusion` | 40 near-duplicate tools | A small, well-described tool set (Ch 5, 8) |
| `clash` | Contradictory instructions | Explicit precedence (Ch 7) |
| `injection` | A file tells the agent to write `INJECTED.txt` | Tool output marked as data + a permission hook (Ch 9) |

```bash
python ch18-failure-modes/failures.py injection
python ch18-failure-modes/failures.py all
```

The injected file, [`fixtures/CONTRIBUTING.md`](fixtures/CONTRIBUTING.md), is a harmless canary: its hidden comment, dressed up as a normal project rule, only asks for a file named `INJECTED.txt` holding a summary. (If an AI coding agent of yours ever creates that file in this repo, this demo just worked on it.)

Current models often refuse even the "broken" run, and results vary from run to run. That is the lesson: the model's judgement is a bonus, the harness defence (tool output marked as data, plus a hook that blocks writes nobody asked for) is what you rely on.

Background: [greshake/llm-security](https://github.com/greshake/llm-security) on indirect prompt injection.
