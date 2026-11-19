"""Shared helpers for the course chapters.

Chapter 2 writes the agent loop by hand. From Chapter 3 on, chapters import
`run_agent` and `Toolbox` from here so each video can focus on one idea.
"""

from course.client import MODEL, get_client
from course.loop import AgentResult, Hooks, run_agent
from course.paths import REPO_ROOT, SAMPLE_REPO
from course.tools import Tool, Toolbox, repo_tools

__all__ = [
    "MODEL",
    "get_client",
    "AgentResult",
    "Hooks",
    "run_agent",
    "REPO_ROOT",
    "SAMPLE_REPO",
    "Tool",
    "Toolbox",
    "repo_tools",
]
