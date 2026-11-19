# Harness design checklist

A one-page review for any agent harness: one you build, buy or inherit. From the Archridge course *Agent Harnesses & Context Management*.

## 1. Loop
- [ ] Clear stop conditions: task done, turn limit, token or cost budget, human interrupt
- [ ] Errors from tools go back to the model as text, not crashes

## 2. Tools
- [ ] Each description says what it does, when to use it and what comes back
- [ ] A few capable tools rather than many thin wrappers
- [ ] Output is paged or truncated, with a hint for getting more
- [ ] Error messages say how to recover
- [ ] Rarely used tools are loaded on demand, not on every turn

## 3. Instructions
- [ ] Project file (AGENTS.md / CLAUDE.md / steering) holds commands, conventions and gotchas, kept short
- [ ] Precedence between layers is stated
- [ ] Specialised know-how lives in skills, loaded only when needed

## 4. Context management
- [ ] Old tool output is cleared
- [ ] Compaction has a threshold and a rule for what must survive
- [ ] Retrieval fetches late and precisely (references first, content on demand)
- [ ] Long-term memory exists, is kept current and never holds secrets
- [ ] Sub-agents isolate noisy work and return condensed reports

## 5. Cost and latency
- [ ] Stable content first; cache breakpoints placed
- [ ] Nothing volatile (timestamps, shuffled tools) inside the cached prefix
- [ ] Token use per task is measured, not guessed

## 6. Long-running work
- [ ] State is written outside the window (progress file, feature list, git)
- [ ] A crashed or reset session can resume from files alone

## 7. Safety
- [ ] Writes and commands pass a permission check; dangerous patterns are blocked
- [ ] The agent runs in a sandbox with scoped filesystem and network access
- [ ] Tool output, files and web pages are treated as data, never as instructions

## 8. Observability
- [ ] Every turn and tool call is traced with tokens and latency
- [ ] An eval set of real tasks runs on every harness change
- [ ] Changes are A/B tested one variable at a time
