# Chapter 17 — Evals, traces and observability for harnesses

**Video:** _link added on release_ · **Length:** ~15 min

You cannot improve a harness you cannot see.

| File | What it shows |
| --- | --- |
| [`tracing.py`](tracing.py) | JSON-lines traces: every model turn (tokens, latency, tools called) and every tool call (output size, errors) |
| [`view_trace.py`](view_trace.py) | Summarise a trace and flag the biggest tool output |
| [`run_evals.py`](run_evals.py) | Five graded tasks; A/B the harness by changing one thing (`--variant full` vs `no-search`) |
| [`evals/tasks.jsonl`](evals/tasks.jsonl) | The eval tasks |

```bash
python ch17-evals-tracing/run_evals.py --variant full
python ch17-evals-tracing/run_evals.py --variant no-search
python ch17-evals-tracing/view_trace.py ch17-evals-tracing/traces/full-mean-bug.jsonl
```

For production, send the same events to an observability tool such as [langfuse/langfuse](https://github.com/langfuse/langfuse). [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) ships a trajectory inspector worth showing on screen.
