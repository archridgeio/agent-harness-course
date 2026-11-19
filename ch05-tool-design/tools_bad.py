"""Chapter 5 — a badly designed tool set (on purpose).

What is wrong:
- vague names and descriptions ("fs_op", "get")
- thin wrappers over OS calls, so the model needs many calls for one question
- whole files and raw tracebacks dumped into the context
- no way to search, so the model must open files one by one
"""

import os
import traceback
from pathlib import Path

from course.tools import Tool, Toolbox


def bad_tools(root: Path) -> Toolbox:
    root = Path(root).resolve()

    def fs_op(op: str, path: str = ".") -> str:
        try:
            target = root / path
            if op == "ls":
                return str(os.listdir(target))          # one folder at a time, Python repr
            if op == "stat":
                return str(os.stat(target))
            return "bad op"
        except Exception:
            return traceback.format_exc()               # raw traceback into the context

    def get(p: str) -> str:
        try:
            return (root / p).read_text()               # whole file, no paging, no line numbers
        except Exception:
            return traceback.format_exc()

    return Toolbox([
        Tool("fs_op", "Filesystem operation.", {
            "type": "object", "properties": {"op": {"type": "string"}, "path": {"type": "string"}}, "required": ["op"]},
            fs_op),
        Tool("get", "Get a file.", {"type": "object", "properties": {"p": {"type": "string"}}, "required": ["p"]}, get),
    ])
