"""Chapter 6 — a small MCP server for the repo assistant.

Exposes two tools over the Model Context Protocol (stdio transport):
search_repo and read_file. Any MCP client can use them: Claude Code, Claude
Desktop, Codex CLI, Kiro, or our own client in client_agent.py.

Run directly (waits for an MCP client on stdin/stdout):
    python ch06-mcp/server.py
"""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from course.tools import read_file as _read_file
from course.tools import search_code as _search_code

ROOT = Path(os.environ.get("COURSE_REPO", Path(__file__).resolve().parents[1] / "sample-repo")).resolve()

mcp = FastMCP("repo-assistant")


@mcp.tool()
def search_repo(query: str, glob: str = "*.py", max_results: int = 20) -> str:
    """Search file contents in the repository with a case-insensitive regex.

    Returns path:line: text for each match. Use glob to limit file types.
    """
    return _search_code(ROOT, query, glob, max_results)


@mcp.tool()
def read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """Read a file with line numbers. path is relative to the repository root; long files are paged."""
    return _read_file(ROOT, path, start_line, max_lines)


if __name__ == "__main__":
    mcp.run()
