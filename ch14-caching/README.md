# Chapter 14 — Prompt caching and the economics of context

**Video:** _link added on release_ · **Length:** ~12 min

Put stable content first and mark the end of it with `cache_control`. Every later turn reads that prefix from cache.

```bash
python ch14-caching/caching.py
```

The script runs the same multi-turn review twice and prints, per turn, uncached input tokens, cache writes and cache reads, plus a relative cost (cache writes ≈ 1.25×, reads ≈ 0.1× the base input price for the 5-minute cache; check current pricing in the Claude docs before quoting numbers on screen).

Ordering rule: tools → system prompt → conversation. Anything that changes every request (a timestamp, a shuffled tool list) breaks the cache for everything after it.

Reference: the prompt caching notebook in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks).
