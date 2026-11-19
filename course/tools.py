"""A tiny tool registry plus the repo tools most chapters share."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MAX_OUTPUT_CHARS = 20_000


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., str]

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


class Toolbox:
    """Holds tools, exposes their specs to the model and runs calls safely."""

    def __init__(self, tools: list[Tool] | None = None):
        self.tools: dict[str, Tool] = {t.name: t for t in tools or []}

    def add(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [t.spec() for t in self.tools.values()]

    def call(self, name: str, args: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'. Available tools: {', '.join(self.tools)}."
        try:
            out = str(tool.fn(**args))
        except TypeError as exc:
            return f"Error: bad arguments for {name}: {exc}. Check the tool's input schema."
        except Exception as exc:  # tool errors go back to the model as text
            return f"Error running {name}: {exc}"
        if len(out) > MAX_OUTPUT_CHARS:
            out = out[:MAX_OUTPUT_CHARS] + f"\n[truncated: {len(out) - MAX_OUTPUT_CHARS} more characters]"
        return out


def safe_path(root: Path, rel: str) -> Path:
    """Resolve `rel` inside `root`, refusing anything that escapes it."""
    path = (root / rel).resolve()
    if path != root.resolve() and root.resolve() not in path.parents:
        raise ValueError(f"'{rel}' is outside the repository")
    return path


def list_files(root: Path) -> str:
    files = [p.relative_to(root).as_posix() for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts]
    return "\n".join(files) or "(no files)"


def read_file(root: Path, path: str, start_line: int = 1, max_lines: int = 200) -> str:
    target = safe_path(root, path)
    if not target.is_file():
        return f"Error: file not found: {path}. Use list_files or search_code to find the right path."
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    end = min(len(lines), start_line - 1 + max_lines)
    body = "\n".join(f"{i + 1:>4}  {lines[i]}" for i in range(start_line - 1, end))
    if end < len(lines):
        body += f"\n[showing lines {start_line}-{end} of {len(lines)}; call again with start_line={end + 1}]"
    return body


def search_code(root: Path, query: str, glob: str = "*", max_results: int = 20) -> str:
    pattern = re.compile(query, re.IGNORECASE)
    hits = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or ".git" in p.parts or not fnmatch.fnmatch(p.name, glob):
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    if not hits:
        return f"No matches for /{query}/ in files matching '{glob}'."
    shown = hits[:max_results]
    more = f"\n[{len(hits) - len(shown)} more matches; narrow the query or raise max_results]" if len(hits) > len(shown) else ""
    return "\n".join(shown) + more


def write_file(root: Path, path: str, content: str) -> str:
    target = safe_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}."


def repo_tools(root: Path, writable: bool = False) -> Toolbox:
    """The standard repo-assistant tool set used from Chapter 3 on."""
    root = Path(root).resolve()
    tools = [
        Tool(
            "list_files",
            "List every file in the repository as relative paths, one per line. Use this first to orient yourself.",
            {"type": "object", "properties": {}},
            lambda: list_files(root),
        ),
        Tool(
            "read_file",
            "Read a text file with line numbers. `path` is relative to the repository root. Long files are paged: "
            "use start_line to continue.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path, e.g. inventory/stats.py"},
                    "start_line": {"type": "integer", "minimum": 1, "default": 1},
                    "max_lines": {"type": "integer", "minimum": 1, "default": 200},
                },
                "required": ["path"],
            },
            lambda path, start_line=1, max_lines=200: read_file(root, path, start_line, max_lines),
        ),
        Tool(
            "search_code",
            "Search file contents with a case-insensitive regular expression. Returns path:line: text for each match. "
            "Use `glob` (e.g. '*.py') to limit which files are searched.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "glob": {"type": "string", "default": "*"},
                    "max_results": {"type": "integer", "default": 20},
                },
                "required": ["query"],
            },
            lambda query, glob="*", max_results=20: search_code(root, query, glob, max_results),
        ),
    ]
    if writable:
        tools.append(
            Tool(
                "write_file",
                "Create or overwrite a text file with the full new content. `path` is relative to the repository root.",
                {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
                lambda path, content: write_file(root, path, content),
            )
        )
    return Toolbox(tools)
