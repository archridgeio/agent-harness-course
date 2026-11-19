"""Chapter 8 — skills and progressive disclosure.

Only each skill's one-line description sits in the system prompt. The full
instructions load when the model calls load_skill, and extra files in the
skill folder load only through load_skill_file.

Run:  python ch08-skills/skill_loader.py                 # show the window before/after loading
      python ch08-skills/skill_loader.py --run "Write release notes for the fix to stats.mean"
"""

import sys
from pathlib import Path

from course import SAMPLE_REPO, Tool, get_client, repo_tools, run_agent

SKILLS_DIR = Path(__file__).with_name("skills")


def parse_skill(path: Path) -> dict:
    text = path.read_text()
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return {"name": meta.get("name", path.parent.name), "description": meta.get("description", ""),
            "body": body.strip(), "folder": path.parent}


def discover(skills_dir: Path = SKILLS_DIR) -> dict[str, dict]:
    return {s["name"]: s for s in map(parse_skill, sorted(skills_dir.glob("*/SKILL.md")))}


def skills_prompt(skills: dict[str, dict]) -> str:
    lines = ["You have skills. Each line is a name and when to use it. Call load_skill(name) before using one."]
    lines += [f"- {s['name']}: {s['description']}" for s in skills.values()]
    return "\n".join(lines)


def skill_tools(skills: dict[str, dict]) -> list[Tool]:
    def load_skill(name: str) -> str:
        if name not in skills:
            return f"Error: no skill named '{name}'. Available: {', '.join(skills)}."
        return skills[name]["body"]

    def load_skill_file(name: str, file: str) -> str:
        if name not in skills:
            return f"Error: no skill named '{name}'."
        target = (skills[name]["folder"] / file).resolve()
        if skills[name]["folder"].resolve() not in target.parents or not target.is_file():
            files = [p.name for p in skills[name]["folder"].iterdir() if p.name != "SKILL.md"]
            return f"Error: '{file}' not found in skill {name}. Files: {', '.join(files)}."
        return target.read_text()

    return [
        Tool("load_skill", "Load a skill's full instructions by name.",
             {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, load_skill),
        Tool("load_skill_file", "Read a supporting file (template, reference) from a loaded skill's folder.",
             {"type": "object", "properties": {"name": {"type": "string"}, "file": {"type": "string"}},
              "required": ["name", "file"]}, load_skill_file),
    ]


def window_report(skills: dict[str, dict]) -> str:
    before = skills_prompt(skills)
    after = before + "\n\n" + "\n\n".join(s["body"] for s in skills.values())
    return (f"Always in context (descriptions only): ~{len(before) // 4} tokens\n"
            f"If every skill were pre-loaded:        ~{len(after) // 4} tokens\n"
            f"Skills available: {len(skills)}. Each extra skill costs one line until it is used.")


def run(task: str, client=None):
    skills = discover()
    toolbox = repo_tools(SAMPLE_REPO)
    for tool in skill_tools(skills):
        toolbox.add(tool)
    return run_agent(client or get_client(), task, toolbox, system=skills_prompt(skills))


if __name__ == "__main__":
    if "--run" in sys.argv:
        task = sys.argv[sys.argv.index("--run") + 1]
        print(run(task).text)
    else:
        print(window_report(discover()))
