"""Chapter 7 — layered instruction files.

Most harnesses build the system prompt from layers, most general first:
  1. the harness's own base prompt
  2. user-level instructions   (~/.repo-assistant/instructions.md)
  3. project instructions      (AGENTS.md at the repo root)
  4. nested instructions       (AGENTS.md in the folder you are working in; closest wins)

Run:  python ch07-instruction-files/instructions.py            # print the assembled prompt
      python ch07-instruction-files/instructions.py --compare  # run a task with and without it
"""

import sys
from pathlib import Path

from course import SAMPLE_REPO, get_client, repo_tools, run_agent

BASE_PROMPT = "You are a repo assistant. Read code before answering. Be brief and specific."
USER_FILE = Path.home() / ".repo-assistant" / "instructions.md"
NAMES = ("AGENTS.md", "CLAUDE.md")


def find_project_files(repo: Path, workdir: Path | None = None) -> list[Path]:
    """Instruction files from the repo root down to workdir (root first, closest last)."""
    repo = repo.resolve()
    workdir = (workdir or repo).resolve()
    chain = [repo] + [p for p in reversed(workdir.parents) if repo in p.parents] + ([workdir] if workdir != repo else [])
    found = []
    for folder in chain:
        for name in NAMES:
            if (folder / name).is_file():
                found.append(folder / name)
    return found


def build_system_prompt(repo: Path, workdir: Path | None = None, user_file: Path = USER_FILE) -> tuple[str, list[str]]:
    layers = [("harness base prompt", BASE_PROMPT)]
    if user_file.is_file():
        layers.append((f"user: {user_file}", user_file.read_text()))
    for f in find_project_files(repo, workdir):
        layers.append((f"project: {f.relative_to(repo.parent)}", f.read_text()))
    parts = [f"<instructions source=\"{src}\">\n{body.strip()}\n</instructions>" for src, body in layers]
    prompt = "\n\n".join(parts)
    prompt += "\n\nWhen instructions conflict, the later (more specific) source wins."
    return prompt, [src for src, _ in layers]


TASK = "Fix the failing test in this repo, then tell me how you verified it."


def compare(client=None) -> dict:
    client = client or get_client()
    with_files, _ = build_system_prompt(SAMPLE_REPO)
    out = {}
    for label, system in [("base prompt only", BASE_PROMPT), ("with AGENTS.md", with_files)]:
        # read-only tools: we only want to see whether the plan follows the project's conventions
        result = run_agent(client, TASK + " Describe the change; do not write files.", repo_tools(SAMPLE_REPO),
                           system=system, max_turns=10)
        out[label] = result.text
    return out


if __name__ == "__main__":
    if "--compare" in sys.argv:
        for label, answer in compare().items():
            print(f"\n=== {label} ===\n{answer}")
    else:
        prompt, sources = build_system_prompt(SAMPLE_REPO)
        print("Layers loaded:", *sources, sep="\n  - ")
        print(f"\nAbout {len(prompt) // 4} tokens, sent on every single turn:\n")
        print(prompt)
