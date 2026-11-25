# Chapter 20 — Harness design review and what comes next

**Video:** _link added on release_ · **Length:** ~15 min

How do the harnesses you use every day make the choices this course covered?

## Teardown

Filled in from each product's **public documentation only**, checked on 22 Nov 2026. These products change fast: check the current docs before you rely on a row. A dash means the docs we read didn't cover it, not that the feature is missing.

| Dimension | Claude Code | Codex CLI | Kiro | Strands harness / AgentCore | Our mini harness (Ch 19) |
| --- | --- | --- | --- | --- | --- |
| Loop and stop conditions | Runs until done; interrupt any time; checkpoints and rewind | Runs until done; approval policy (`on-request`, `never`, granular) decides when it pauses | Spec flow (requirements, design, tasks); checkpoints and rewind | Model-driven loop with hooks before and after each invocation and tool call | Turn limit + `end_turn` |
| Tool strategy | Built-in file, search and shell tools; MCP tool search defers schemas until needed | Shell and file edits; MCP servers and plugins | Built-in tools and MCP; Powers bundle tools and load on demand | Built-in file, `web_fetch`, `todo_write`, `subagent`; results over 1,500 tokens truncated, large results offloaded | 9 tools, paged output |
| Instruction files | `CLAUDE.md` every session (keep it short); path-scoped `.claude/rules` | `AGENTS.md` merged from global, repo root and down to the working folder | `.kiro/steering/` with always, fileMatch, manual and auto inclusion; `AGENTS.md` always included | System prompt set in code | `AGENTS.md`, `CLAUDE.md` |
| Skills / on-demand knowledge | Skills: description loaded up front, full content on use | Skills | Agent Skills and Powers | — | `load_skill` |
| Compaction | Auto-compact; `/compact` with a focus; compact instructions in `CLAUDE.md` | Manual and automatic, local or remote | Automatic (CLI default 80%); keeps goals, decisions, files, constraints and recent messages; `/compact` | Proactive compaction at 85% | Clear + summarise at 70% |
| Memory | Auto memory in `MEMORY.md`; first 200 lines / 25 KB loaded | Memories | Memory | AgentCore managed memory | Memory notes |
| Sub-agents | Own context window, return a summary | Only when asked or instructed; 6 threads and depth 1 by default; inherit the sandbox | Custom agents and subagents | Built-in `subagent` tool | `delegate` (read-only) |
| Permissions / sandbox | Permission modes and rules; hooks as guardrails; sandboxed Bash limits files and network | Sandbox modes `read-only`, `workspace-write`, `danger-full-access`; hooks (e.g. `PreToolUse`) | Capability rules, deny over ask over allow; command sandbox; hooks | Hooks can deny a tool call and fail closed by default; a microVM per session | Approval + secret check |
| Observability | OpenTelemetry metrics and events | OpenTelemetry export, off by default (`[otel]`) | — | OpenTelemetry; hook events in the response stream | JSONL traces |

Sources: [Claude Code docs](https://code.claude.com/docs), [Codex docs](https://developers.openai.com/codex), [Kiro docs](https://kiro.dev/docs), [Strands Agents docs](https://strandsagents.com), [AgentCore harness announcement (AWS blog, Nov 2026)](https://aws.amazon.com/blogs/).

Repos to show: [anthropics/claude-code](https://github.com/anthropics/claude-code), [openai/codex](https://github.com/openai/codex), [kirodotdev/Kiro](https://github.com/kirodotdev/Kiro), [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk), [awslabs/amazon-bedrock-agentcore-samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples).

## Download

[`harness-design-checklist.md`](harness-design-checklist.md) — the one-page checklist from the end of the video.
