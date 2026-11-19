"""Chapter 1 — the same model with no harness.

We ask the model to fix the bug in our sample repo with a single API call:
no tools, no files, no loop. Compare the answer with the Ch 2 agent
(`python ch02-agent-loop/loop.py "Find and explain the bug in inventory/stats.py"`).

Run:  python ch01-what-is-a-harness/bare_call.py
"""

from course import MODEL, get_client

TASK = "There is a bug in inventory/stats.py in my repository. Find it and tell me the fix."


def bare_call(client=None) -> str:
    client = client or get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": TASK}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    print("=== Bare model call (no harness) ===\n")
    print(bare_call())
    print("\nThe model never saw the file, so at best it guesses. Next: give it a loop and tools (Chapter 2).")
