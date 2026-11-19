# Chapter 11 — Retrieval: RAG vs agentic search

**Video:** _link added on release_ · **Length:** ~15 min

Many coding agents skip the vector database and let the model grep. This chapter answers the same five questions both ways.

| File | What it shows |
| --- | --- |
| [`vector_search.py`](vector_search.py) | Chunk → embed → top-k, with a dependency-free toy embedding |
| [`compare.py`](compare.py) | RAG (one call) vs agentic search (tools, several turns): answers, tokens, turns |
| [`questions.txt`](questions.txt) | The five test questions |

```bash
python ch11-retrieval/compare.py
```

Trade-offs to discuss: freshness (the index goes stale; grep never does), precision, latency, setup cost. Hybrid often wins on large codebases.

References: [chroma-core/chroma](https://github.com/chroma-core/chroma) for vector search, [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) for the fast grep most coding agents use.
