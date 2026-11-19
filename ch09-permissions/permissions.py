"""Chapter 9 — sandboxes, permissions and human-in-the-loop.

A permission policy plugs into the loop's before_tool hook. Every tool call
goes through:
  1. pre-tool hooks (hard rules: block writes outside the repo, secrets, dangerous commands)
  2. the permission mode: "ask" (approve every risky call), "allowlist", or "auto"

Run:  python ch09-permissions/permissions.py --mode ask "Fix the failing test and run the tests"
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from course import SAMPLE_REPO, Tool, get_client, repo_tools, run_agent

READ_ONLY = {"list_files", "read_file", "search_code"}
SECRET_PATTERNS = [r"sk-ant-[A-Za-z0-9_-]{10,}", r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]
DANGEROUS_COMMANDS = [r"\brm\s+-rf\b", r"\bsudo\b", r"curl[^|]*\|\s*(sh|bash)", r"\bgit\s+push\b", r">\s*/dev/sd"]

Check = Callable[[str, dict], "str | None"]


def block_outside_repo(root: Path) -> Check:
    def check(name: str, args: dict) -> str | None:
        if name == "write_file":
            target = (root / args.get("path", "")).resolve()
            if root.resolve() not in target.parents:
                return f"Blocked: {args.get('path')} is outside the repository. Write only inside {root.name}/."
        return None
    return check


def block_secrets(name: str, args: dict) -> str | None:
    blob = " ".join(str(v) for v in args.values())
    if any(re.search(p, blob) for p in SECRET_PATTERNS):
        return "Blocked: the input looks like it contains a secret (API key or private key). Remove it."
    return None


def block_dangerous_commands(name: str, args: dict) -> str | None:
    if name == "run_command":
        cmd = args.get("command", "")
        for pattern in DANGEROUS_COMMANDS:
            if re.search(pattern, cmd):
                return f"Blocked: '{cmd}' matches a forbidden pattern ({pattern}). Find a safer way."
    return None


@dataclass
class PermissionPolicy:
    mode: str = "ask"                                   # ask | allowlist | auto
    allowlist: set[str] = field(default_factory=lambda: set(READ_ONLY))
    hooks: list[Check] = field(default_factory=list)
    approve: Callable[[str, dict], bool] = None         # how to ask a human; defaults to input()
    log: list[str] = field(default_factory=list)

    def __call__(self, name: str, args: dict) -> str | None:
        for hook in self.hooks:                         # hard rules apply in every mode
            verdict = hook(name, args)
            if verdict:
                self.log.append(f"HOOK  {name}: {verdict}")
                return verdict
        if self.mode == "auto" or name in READ_ONLY:
            return None
        if self.mode == "allowlist":
            if name in self.allowlist:
                return None
            self.log.append(f"DENY  {name}: not on the allowlist")
            return f"Denied: {name} is not on the allowlist for this session."
        approve = self.approve or _ask_human
        if approve(name, args):
            self.log.append(f"ALLOW {name}")
            return None
        self.log.append(f"DENY  {name}: user said no")
        return f"Denied by the user: {name}. Ask what they would like instead."


def _ask_human(name: str, args: dict) -> bool:
    preview = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in args.items())
    return input(f"\nAllow {name}({preview})? [y/N] ").strip().lower() == "y"


def run_command_tool(root: Path) -> Tool:
    def run_command(command: str) -> str:
        proc = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=60)
        return f"exit code {proc.returncode}\n{proc.stdout[-4000:]}{proc.stderr[-2000:]}"
    return Tool("run_command", "Run a shell command in the repository folder (60 s timeout). Use for tests.",
                {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
                run_command)


def build(root: Path = SAMPLE_REPO, mode: str = "ask", approve=None):
    toolbox = repo_tools(root, writable=True)
    toolbox.add(run_command_tool(root))
    policy = PermissionPolicy(mode=mode, approve=approve,
                              hooks=[block_outside_repo(root), block_secrets, block_dangerous_commands])
    return toolbox, policy


if __name__ == "__main__":
    from course import Hooks

    args = sys.argv[1:]
    mode = "ask"
    if "--mode" in args:
        i = args.index("--mode")
        mode = args[i + 1]
        del args[i:i + 2]
    task = args[0] if args else "Fix the failing test in this repo and run the tests to confirm."
    toolbox, policy = build(mode=mode)
    result = run_agent(get_client(), task, toolbox, hooks=Hooks(before_tool=policy))
    print("\n" + result.text)
    print("\nPermission log:", *policy.log, sep="\n  ")
