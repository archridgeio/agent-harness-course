# Chapter 20 — Harness design review and what comes next

**Video:** _link added on release_ · **Length:** ~15 min

How do the harnesses you use every day make the choices this course covered?

## Teardown dimensions

For each harness, the video fills in this table from **its public documentation only** (check each product's current docs in the week you record; these products change fast):

| Dimension | Claude Code | Codex CLI | Kiro | Strands Agents / AgentCore | Our mini harness (Ch 19) |
| --- | --- | --- | --- | --- | --- |
| Loop and stop conditions | | | | | turn limit + end_turn |
| Tool strategy | | | | | 9 tools, paged output |
| Instruction files | | | | | AGENTS.md, CLAUDE.md |
| Skills / on-demand knowledge | | | | | load_skill |
| Compaction | | | | | clear + summarise at 70% |
| Memory | | | | | memory notes |
| Sub-agents | | | | | delegate (read-only) |
| Permissions / sandbox | | | | | approval + secret check |
| Observability | | | | | JSONL traces |

Repos to show: [anthropics/claude-code](https://github.com/anthropics/claude-code), [openai/codex](https://github.com/openai/codex), [kirodotdev/Kiro](https://github.com/kirodotdev/Kiro), [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk), [awslabs/amazon-bedrock-agentcore-samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples).

## Download

[`harness-design-checklist.md`](harness-design-checklist.md) — the one-page checklist from the end of the video.
