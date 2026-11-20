# Chapter 3 — The context window is working memory

**Video:** [Why Bigger Context Windows Don't Fix Your AI Agent](https://youtu.be/J2ec-GBcL6g) · **Length:** 5:43

A big window is not the same as a big attention span. Every turn re-sends the whole conversation, and tool output is usually the largest part of it.

```bash
python ch03-context-window/token_budget.py "Read every Python file and explain what each module does."
```

Example output shape:

```text
turn    input   tools  system  conversation  growth
   1      912     610      25           277  ######
   2     1734     610      25          1099  ############
   ...
```

Treat context as a budget, not a bucket. Background reading: Chroma's [Context Rot](https://github.com/chroma-core/context-rot) study.
