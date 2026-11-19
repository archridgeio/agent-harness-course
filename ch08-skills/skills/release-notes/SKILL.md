---
name: release-notes
description: Write release notes for the inventory project from a list of changes. Use when asked for release notes, a changelog entry or a "what's new" summary.
---

# Release notes

1. Collect the changes: read the files the user mentions, or ask for the list of changes.
2. Group them under these headings, in this order, skipping empty ones:
   - **Fixed** — bugs fixed, with the function name in backticks
   - **Added** — new behaviour
   - **Changed** — behaviour that works differently now
3. One line per change, written for a store manager, not a developer: say what they will notice.
4. End with the test command and its result, e.g. "Tests: `python -m pytest -q` — 5 passed".
5. Follow the layout in `template.md` in this skill folder (read it with load_skill_file).
