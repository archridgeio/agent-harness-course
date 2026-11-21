"""Chapter 12 — file-based long-term memory.

The context window resets every session; a memory folder does not. The agent
gets one `memory` tool with file commands (view, create, str_replace, insert,
delete, rename) scoped to a /memories folder. The same command set as the
Claude API's memory tool, implemented client-side so you can see every step.

Run:  python ch12-memory/memory_tool.py reset      # empty the memory folder
      python ch12-memory/memory_tool.py session1   # agent learns a decision and saves it
      python ch12-memory/memory_tool.py session2   # fresh conversation recalls it
      python ch12-memory/memory_tool.py session2 --no-memory   # same question, empty memory
      python ch12-memory/memory_tool.py show        # print the memory folder and its files
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from course import SAMPLE_REPO, Tool, get_client, repo_tools, run_agent

MEMORY_DIR = Path(__file__).with_name(".memories")

SYSTEM = """You are a repo assistant with long-term memory.
At the start of every task, view /memories and read anything relevant.
Save durable facts (decisions, conventions, open issues) as short Markdown files in /memories.
Keep memory current: update or delete facts that are no longer true. Never store secrets."""


class MemoryStore:
    def __init__(self, root: Path = MEMORY_DIR):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, virtual: str) -> Path:
        if not virtual.startswith("/memories"):
            raise ValueError("paths must start with /memories")
        target = (self.root / virtual.removeprefix("/memories").lstrip("/")).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError("path escapes /memories")
        return target

    def view(self, path: str = "/memories") -> str:
        target = self._path(path)
        if target.is_dir():
            files = sorted(p.relative_to(self.root).as_posix() for p in target.rglob("*") if p.is_file())
            return "Directory /memories:\n" + ("\n".join(f"- /memories/{f}" for f in files) or "(empty)")
        if not target.is_file():
            return f"Error: {path} does not exist."
        return "\n".join(f"{i:>4}  {line}" for i, line in enumerate(target.read_text().splitlines(), 1))

    def create(self, path: str, file_text: str) -> str:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_text)
        return f"Created {path}."

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        target = self._path(path)
        text = target.read_text()
        count = text.count(old_str)
        if count != 1:
            return f"Error: old_str found {count} times in {path}; it must match exactly once."
        target.write_text(text.replace(old_str, new_str))
        return f"Updated {path}."

    def insert(self, path: str, insert_line: int, insert_text: str) -> str:
        target = self._path(path)
        lines = target.read_text().splitlines()
        lines.insert(insert_line, insert_text.rstrip("\n"))
        target.write_text("\n".join(lines) + "\n")
        return f"Inserted at line {insert_line} of {path}."

    def delete(self, path: str) -> str:
        target = self._path(path)
        if target == self.root:
            return "Error: cannot delete /memories itself."
        target.unlink()
        return f"Deleted {path}."

    def rename(self, old_path: str, new_path: str) -> str:
        self._path(old_path).rename(self._path(new_path))
        return f"Renamed {old_path} to {new_path}."

    def run(self, command: str, **kwargs) -> str:
        handler = getattr(self, command, None)
        if command.startswith("_") or command == "run" or handler is None:
            return f"Error: unknown command '{command}'. Use view, create, str_replace, insert, delete or rename."
        return handler(**kwargs)


def memory_tool(store: MemoryStore) -> Tool:
    return Tool(
        "memory",
        "Read and write long-term memory files under /memories. Commands: view(path), create(path, file_text), "
        "str_replace(path, old_str, new_str), insert(path, insert_line, insert_text), delete(path), "
        "rename(old_path, new_path).",
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "enum": ["view", "create", "str_replace", "insert", "delete", "rename"]},
                "path": {"type": "string"}, "file_text": {"type": "string"}, "old_str": {"type": "string"},
                "new_str": {"type": "string"}, "insert_line": {"type": "integer"}, "insert_text": {"type": "string"},
                "old_path": {"type": "string"}, "new_path": {"type": "string"},
            },
            "required": ["command"],
        },
        lambda command, **kw: store.run(command, **kw),
    )


SESSIONS = {
    "session1": "Our team decided: all discount percentages are capped at 50%, and we never change pricing.py "
                "without a test. Remember this for future sessions. Then tell me where discounts are applied.",
    "session2": "I want to add a 60% clearance discount to pricing.py. What should I watch out for?",
}


def run_session(task: str, client=None, store: MemoryStore | None = None):
    store = store or MemoryStore()
    toolbox = repo_tools(SAMPLE_REPO)
    toolbox.add(memory_tool(store))
    return run_agent(client or get_client(), task, toolbox, system=SYSTEM)


def trace(result) -> list[str]:
    """One line per tool call: the turn and the call, with memory paths and short arguments."""
    lines, turn = [], 0
    for m in result.messages:
        if m["role"] != "assistant" or isinstance(m["content"], str):
            continue
        turn += 1
        for b in m["content"]:
            if getattr(b, "type", None) == "tool_use":
                args = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in (b.input or {}).items())
                lines.append(f"[turn {turn}] {b.name}({args})")
    return lines


def show(store: MemoryStore) -> str:
    out = [store.view()]
    for p in sorted(store.root.rglob("*")):
        if p.is_file():
            out.append(f"\n--- /memories/{p.relative_to(store.root).as_posix()} ---\n{p.read_text().rstrip()}")
    return "\n".join(out)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "session1"
    if which == "show":
        print(show(MemoryStore()))
    elif which == "reset":
        shutil.rmtree(MEMORY_DIR, ignore_errors=True)
        print("Memory folder emptied.")
    else:
        empty = "--no-memory" in sys.argv
        store = MemoryStore(Path(tempfile.mkdtemp())) if empty else MemoryStore()
        result = run_session(SESSIONS[which], store=store)
        print("Trace:", *trace(result), sep="\n  ")
        print(f"\n{result.turns} turns · {result.input_tokens:,} input tokens" + ("  (empty memory)" if empty else ""))
        print("\n" + result.text)
