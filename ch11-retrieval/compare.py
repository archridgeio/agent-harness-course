"""Chapter 11 — the same questions answered with RAG and with agentic search.

RAG: retrieve top-k chunks up front, one model call.
Agentic search: give the model grep/list/read tools and let it fetch just in time.

Run:  python ch11-retrieval/compare.py
"""

from pathlib import Path

from vector_search import build_prompt, chunk_repo

from course import MODEL, SAMPLE_REPO, get_client, repo_tools, run_agent

QUESTIONS = [q.strip() for q in Path(__file__).with_name("questions.txt").read_text().splitlines() if q.strip()]


def rag_answer(client, chunks, question: str):
    response = client.messages.create(model=MODEL, max_tokens=600,
                                      messages=[{"role": "user", "content": build_prompt(chunks, question)}])
    return "".join(b.text for b in response.content if b.type == "text"), response.usage.input_tokens, 1


def agentic_answer(client, question: str):
    result = run_agent(client, question + " Answer in two sentences.", repo_tools(SAMPLE_REPO), max_turns=10)
    return result.text, result.input_tokens, result.turns


def compare(client=None, questions=QUESTIONS) -> list[dict]:
    client = client or get_client()
    chunks = chunk_repo(SAMPLE_REPO)
    rows = []
    for q in questions:
        rag, rag_tokens, _ = rag_answer(client, chunks, q)
        agent, agent_tokens, turns = agentic_answer(client, q)
        rows.append({"question": q, "rag": rag, "rag_tokens": rag_tokens,
                     "agentic": agent, "agentic_tokens": agent_tokens, "agentic_turns": turns})
    return rows


if __name__ == "__main__":
    for row in compare():
        print(f"\nQ: {row['question']}")
        print(f"  RAG      ({row['rag_tokens']:>6} tokens, 1 call): {row['rag'].strip()[:300]}")
        print(f"  Agentic  ({row['agentic_tokens']:>6} tokens, {row['agentic_turns']} turns): {row['agentic'].strip()[:300]}")
