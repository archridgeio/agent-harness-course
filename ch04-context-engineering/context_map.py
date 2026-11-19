"""Chapter 4 — map everything that enters the context window.

Builds one realistic request for the repo assistant out of the six inputs of
context engineering and prints how much each one costs. Works offline with a
~4 characters per token estimate; pass --exact to measure with the API.

Run:  python ch04-context-engineering/context_map.py [--exact]
"""

import json
import sys

from course import MODEL, SAMPLE_REPO, repo_tools
from course.tools import read_file

BAR_WIDTH = 40


def build_inputs() -> dict[str, str]:
    toolbox = repo_tools(SAMPLE_REPO, writable=True)
    return {
        "1. System prompt": "You are a careful repo assistant. Read code before answering. Keep answers short.",
        "2. Tool definitions": json.dumps(toolbox.specs()),
        "3. Instruction file (AGENTS.md)": (SAMPLE_REPO / "AGENTS.md").read_text(),
        "4. Conversation history": json.dumps([
            {"role": "user", "content": "Why does test_mean fail?"},
            {"role": "assistant", "content": "Let me look at inventory/stats.py."},
        ]),
        "5. Retrieved data (tool output)": read_file(SAMPLE_REPO, "inventory/stats.py"),
        "6. Memory": "- Team prefers small, reviewed fixes.\n- Last session: pricing tiers were confirmed correct.",
    }


def estimate(text: str) -> int:
    return max(1, len(text) // 4)


def exact_counts(inputs: dict[str, str]) -> dict[str, int]:
    from course import get_client

    client = get_client()
    probe = [{"role": "user", "content": "x"}]
    base = client.messages.count_tokens(model=MODEL, messages=probe).input_tokens
    counts = {}
    for name, text in inputs.items():
        msgs = [{"role": "user", "content": text}]
        counts[name] = client.messages.count_tokens(model=MODEL, messages=msgs).input_tokens - base + 1
    return counts


def render(counts: dict[str, int]) -> str:
    total = sum(counts.values())
    width = max(len(k) for k in counts)
    lines = []
    for name, n in counts.items():
        share = n / total
        lines.append(f"{name:<{width}}  {n:>6}  {share:>5.1%}  {'#' * max(1, round(share * BAR_WIDTH))}")
    lines.append(f"{'Total':<{width}}  {total:>6}")
    lines.append("\nStatic every turn: 1-3.  Rebuilt every turn: 4-6.  Every token here should earn its place.")
    return "\n".join(lines)


if __name__ == "__main__":
    inputs = build_inputs()
    counts = exact_counts(inputs) if "--exact" in sys.argv else {k: estimate(v) for k, v in inputs.items()}
    print(render(counts))
