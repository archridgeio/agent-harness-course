# Chapter 9 — Sandboxes, permissions and human-in-the-loop

**Video:** _link added on release_ · **Length:** ~13 min

The agent wants to run `rm -rf`. What happens next is a harness decision.

[`permissions.py`](permissions.py) adds a policy to the loop's `before_tool` hook:

- **Hooks (always on):** block writes outside the repo, inputs that look like secrets, and dangerous shell commands.
- **Modes:** `ask` (you approve each write or command), `allowlist` (only named tools), `auto` (everything the hooks allow).

```bash
python ch09-permissions/permissions.py --mode ask "Fix the failing test and run the tests"
git checkout sample-repo   # undo the agent's fix afterwards
```

Pattern-matching hooks are a seatbelt, not a sandbox. For real isolation run the agent in a container or an OS-level sandbox such as [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime).
