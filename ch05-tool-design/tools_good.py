"""Chapter 5 — the same capabilities, redesigned for an agent.

Design rules shown here:
1. Descriptions written for a new colleague: what it does, when to use it, what comes back.
2. One smart tool (search_code) instead of many thin wrappers.
3. Token-efficient output: paging, truncation, a concise/detailed switch.
4. Errors that say how to recover.
"""

import difflib
import re
from pathlib import Path

from course.tools import Tool, Toolbox, safe_path

SKIP = {".git", "__pycache__", ".pytest_cache"}


def _files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_file() and not SKIP & set(p.parts)]


def search_code(root: Path, query: str, glob: str = "*.py", max_results: int = 10, offset: int = 0,
                response_format: str = "concise") -> str:
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as exc:
        return f"Error: '{query}' is not a valid regular expression ({exc}). Escape special characters or use plain words."
    hits = []
    for p in _files(root):
        if not p.match(glob):
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for n, line in enumerate(lines, 1):
            if pattern.search(line):
                rel = p.relative_to(root).as_posix()
                if response_format == "detailed":
                    lo, hi = max(0, n - 3), min(len(lines), n + 2)
                    context = "\n".join(f"    {i + 1:>4}  {lines[i]}" for i in range(lo, hi))
                    hits.append(f"{rel}:{n}\n{context}")
                else:
                    hits.append(f"{rel}:{n}: {line.strip()[:120]}")
    if not hits:
        return f"No matches for /{query}/ in {glob} files. Try a broader pattern or glob='*'."
    page = hits[offset:offset + max_results]
    footer = ""
    if offset + max_results < len(hits):
        footer = f"\n[{len(hits)} matches total; call again with offset={offset + max_results} for more]"
    return "\n".join(page) + footer


def read_file(root: Path, path: str, start_line: int = 1, max_lines: int = 120) -> str:
    try:
        target = safe_path(root, path)
    except ValueError:
        return f"Error: '{path}' is outside the repository. Paths are relative to the repository root."
    if not target.is_file():
        names = [p.relative_to(root).as_posix() for p in _files(root)]
        close = difflib.get_close_matches(path, names, n=3)
        hint = f" Did you mean: {', '.join(close)}?" if close else " Use search_code to find the file."
        return f"Error: file not found: {path}.{hint}"
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    end = min(len(lines), start_line - 1 + max_lines)
    body = "\n".join(f"{i + 1:>4}  {lines[i]}" for i in range(start_line - 1, end))
    if end < len(lines):
        body += f"\n[lines {start_line}-{end} of {len(lines)}; call again with start_line={end + 1}]"
    return body


def good_tools(root: Path) -> Toolbox:
    root = Path(root).resolve()
    return Toolbox([
        Tool(
            "search_code",
            "Find where something is defined or used. Searches file contents with a case-insensitive regex and "
            "returns path:line matches. Start here instead of opening files one by one. Use response_format="
            "'detailed' to get 2 lines of context around each match. Results are paged 10 at a time.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Regex or plain words, e.g. 'def mean'"},
                    "glob": {"type": "string", "default": "*.py", "description": "File name pattern"},
                    "max_results": {"type": "integer", "default": 10},
                    "offset": {"type": "integer", "default": 0},
                    "response_format": {"type": "string", "enum": ["concise", "detailed"], "default": "concise"},
                },
                "required": ["query"],
            },
            lambda **kw: search_code(root, **kw),
        ),
        Tool(
            "read_file",
            "Read part of a file with line numbers, 120 lines at a time. Use after search_code to read the code "
            "around a match: pass start_line a few lines above it.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path, e.g. inventory/stats.py"},
                    "start_line": {"type": "integer", "default": 1},
                    "max_lines": {"type": "integer", "default": 120},
                },
                "required": ["path"],
            },
            lambda **kw: read_file(root, **kw),
        ),
    ])
