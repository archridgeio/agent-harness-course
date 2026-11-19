# Chapter 7 — System prompts and project instruction files

**Video:** _link added on release_ · **Length:** ~12 min

The most valuable file in an AI-assisted repo might be a Markdown file. It is also loaded into every single turn, so keep it short.

| File | What it shows |
| --- | --- |
| [`../sample-repo/AGENTS.md`](../sample-repo/AGENTS.md) | A project instruction file: commands, conventions, gotchas |
| [`instructions.py`](instructions.py) | How a harness layers base → user → project → nested instructions |
| [`examples/CLAUDE.md`](examples/CLAUDE.md) | Pointing Claude Code at the shared AGENTS.md |
| [`examples/kiro-steering-product.md`](examples/kiro-steering-product.md) | The same idea as a Kiro steering file |

```bash
python ch07-instruction-files/instructions.py            # see the assembled system prompt
python ch07-instruction-files/instructions.py --compare  # behaviour with and without AGENTS.md
```

What belongs in the file: build/test commands, conventions, gotchas. What does not: essays, style guides you could link to, anything the agent can find with one search.

References: [agentsmd/agents.md](https://github.com/agentsmd/agents.md), real AGENTS.md files in [openai/codex](https://github.com/openai/codex).
