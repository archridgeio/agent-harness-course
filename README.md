# Agent Harnesses & Context Management

Companion code for the **Archridge** video course: 20 chapters, 10–15 minutes each, from "what is an agent harness?" to building and debugging one.

> The model is the engine; the harness is the car. Learn to design the loop, tools and context that make an agent actually work.

Every chapter has a folder with runnable code and a README that links its video. One project runs through the whole course: a **repo assistant** agent that reads, searches and fixes the small Python project in [`sample-repo/`](sample-repo/).

## Setup

```bash
git clone https://github.com/archridgeio/agent-harness-course.git
cd agent-harness-course
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...        # https://console.anthropic.com
export COURSE_MODEL=claude-sonnet-5-5      # optional; any current Claude model id
```

Check everything works without an API key (the tests use a scripted fake model):

```bash
python -m pytest -q
```

Run any chapter from the repo root, e.g. `python ch02-agent-loop/loop.py "Find the bug"`. Agents that write files change `sample-repo/`; undo with `git checkout sample-repo`.

## Course map

| Ch | Module | Chapter | Code | Video |
| --- | --- | --- | --- | --- |
| 1 | Foundations | What is an agent harness? | [ch01](ch01-what-is-a-harness/) | _coming soon_ |
| 2 | Foundations | Anatomy of the agent loop | [ch02](ch02-agent-loop/) | _coming soon_ |
| 3 | Foundations | The context window is working memory | [ch03](ch03-context-window/) | _coming soon_ |
| 4 | Foundations | Context engineering vs prompt engineering | [ch04](ch04-context-engineering/) | _coming soon_ |
| 5 | Building the harness | Designing tools agents can actually use | [ch05](ch05-tool-design/) | _coming soon_ |
| 6 | Building the harness | MCP: the standard plug for tools and context | [ch06](ch06-mcp/) | _coming soon_ |
| 7 | Building the harness | System prompts and project instruction files | [ch07](ch07-instruction-files/) | _coming soon_ |
| 8 | Building the harness | Skills and progressive disclosure | [ch08](ch08-skills/) | _coming soon_ |
| 9 | Building the harness | Sandboxes, permissions and human-in-the-loop | [ch09](ch09-permissions/) | _coming soon_ |
| 10 | Context management | Compaction and summarisation | [ch10](ch10-compaction/) | _coming soon_ |
| 11 | Context management | Retrieval: RAG vs agentic search | [ch11](ch11-retrieval/) | _coming soon_ |
| 12 | Context management | Memory: scratchpads, notes and long-term memory | [ch12](ch12-memory/) | _coming soon_ |
| 13 | Context management | Sub-agents and context isolation | [ch13](ch13-subagents/) | _coming soon_ |
| 14 | Context management | Prompt caching and the economics of context | [ch14](ch14-caching/) | _coming soon_ |
| 15 | Long-running and multi-agent | Long-horizon tasks: state, checkpoints, progress files | [ch15](ch15-long-horizon/) | _coming soon_ |
| 16 | Long-running and multi-agent | Multi-agent architectures: when they help and hurt | [ch16](ch16-multi-agent/) | _coming soon_ |
| 17 | Long-running and multi-agent | Evals, traces and observability for harnesses | [ch17](ch17-evals-tracing/) | _coming soon_ |
| 18 | Long-running and multi-agent | Context failure modes and prompt injection | [ch18](ch18-failure-modes/) | _coming soon_ |
| 19 | Capstone | Build a mini harness from scratch | [ch19](ch19-mini-harness/) | _coming soon_ |
| 20 | Capstone | Harness design review and what comes next | [ch20](ch20-design-review/) | _coming soon_ |

Each chapter's code is also tagged (`ch01` … `ch20`), so you can check out exactly what a video showed: `git checkout ch05`.

## Repository layout

```text
course/            shared loop, tools and client used from Chapter 3 on
sample-repo/       the project the repo assistant works on (has a planted bug)
chNN-*/            one folder per chapter: code + README with the video link
tests/             offline tests for every chapter (scripted fake model)
assets/            diagram sources and screenshots used in the videos
templates/         video description template
REFERENCES.md      every external repo shown in the videos, by chapter
```

## External projects

The videos show screenshots of other people's open-source repos. They are linked, never copied, in [REFERENCES.md](REFERENCES.md). Their code stays under their own licences.

## Licence

Course code: [MIT](LICENSE).
