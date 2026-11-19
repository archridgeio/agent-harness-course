# Chapter 8 — Skills and progressive disclosure

**Video:** _link added on release_ · **Length:** ~12 min

Load knowledge just in time, not just in case.

- [`skills/release-notes/SKILL.md`](skills/release-notes/SKILL.md) — a skill: YAML front matter (name + description) and instructions
- [`skills/release-notes/template.md`](skills/release-notes/template.md) — a supporting file that loads only when needed
- [`skill_loader.py`](skill_loader.py) — discovers skills, lists one line per skill in the system prompt, and gives the model `load_skill` / `load_skill_file`

```bash
python ch08-skills/skill_loader.py
python ch08-skills/skill_loader.py --run "Write release notes for the fix to stats.mean"
```

The description is what the model matches against, so write it as "what it does + when to use it".

References: [anthropics/skills](https://github.com/anthropics/skills), [agentskills/agentskills](https://github.com/agentskills/agentskills).
