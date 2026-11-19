# Chapter 16 — Multi-agent architectures: when they help and hurt

**Video:** _link added on release_ · **Length:** ~13 min

More agents is not always better. Sometimes it is just more tokens.

[`single_vs_multi.py`](single_vs_multi.py) runs one review task two ways and prints tokens, wall-clock time and the reports:

- **Single agent** — one loop, one window.
- **Orchestrator–worker** — one worker per module in parallel, then a synthesizer.

```bash
python ch16-multi-agent/single_vs_multi.py
```

Rule of thumb: multi-agent for breadth (independent research, parallel reviews); single agent for tightly coupled work like a multi-file code change, where workers make conflicting decisions.

References: multi-agent patterns in [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk) and handoffs in [openai/openai-agents-python](https://github.com/openai/openai-agents-python).
