"""Chapter 5 — run the same task with the bad and the good tool set.

Run:  python ch05-tool-design/compare.py
"""

from tools_bad import bad_tools
from tools_good import good_tools

from course import SAMPLE_REPO, get_client, run_agent

TASK = "Where is the bulk discount calculated, and what discount does an order of 60 units get?"


def compare(client=None, task: str = TASK) -> list[dict]:
    client = client or get_client()
    rows = []
    for label, toolbox in [("bad tools", bad_tools(SAMPLE_REPO)), ("good tools", good_tools(SAMPLE_REPO))]:
        result = run_agent(client, task, toolbox, max_turns=15)
        rows.append({"tools": label, "turns": result.turns, "input_tokens": result.input_tokens,
                     "answer": result.text.strip()})
    return rows


if __name__ == "__main__":
    for row in compare():
        print(f"\n=== {row['tools']}: {row['turns']} turns, {row['input_tokens']:,} input tokens ===")
        print(row["answer"])
