# Chapter 14 — Prompt caching and the economics of context

**Video:** _link added on release_ · **Length:** ~12 min

Put stable content first and mark the end of it with `cache_control`. Every later turn reads that prefix from cache.

```bash
python ch14-caching/caching.py
```

The script runs the same multi-turn review three times (no caching, caching, and caching broken by a timestamp in the system prompt) and prints, per turn, uncached input tokens, cache writes and cache reads, plus a relative cost. A 5-minute cache write costs 1.25× the base input price; a cache read costs 0.1× on most models and 0.05× on Claude Sonnet 5.5 and Opus 5.5. Check current pricing in the Claude docs before quoting numbers on screen.

Ordering rule: tools → system prompt → conversation. Anything that changes every request (a timestamp, a shuffled tool list) breaks the cache for everything after it.

Reference: the prompt caching notebook in [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks).
