"""Chapter 11 — classic RAG: chunk, embed, retrieve top-k up front.

To stay dependency-free this uses a hashed bag-of-words "embedding" and cosine
similarity. A real system would use an embedding model and a vector database
(for example Chroma), but the shape of the pipeline is the same.
"""

from __future__ import annotations

import math
import re
import zlib
from collections import Counter
from pathlib import Path

DIM = 512
CHUNK_LINES = 15
TOKEN = re.compile(r"[a-zA-Z_]+")


def embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for word, count in Counter(w.lower() for w in TOKEN.findall(text)).items():
        vec[zlib.crc32(word.encode()) % DIM] += count  # stable across runs, unlike hash()
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def chunk_repo(root: Path, glob: str = "*.py") -> list[dict]:
    chunks = []
    for path in sorted(root.rglob(glob)):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for start in range(0, len(lines), CHUNK_LINES):
            body = "\n".join(lines[start:start + CHUNK_LINES])
            if body.strip():
                rel = path.relative_to(root).as_posix()
                chunks.append({"source": f"{rel}:{start + 1}", "text": body, "vec": embed(rel + "\n" + body)})
    return chunks


def search(chunks: list[dict], query: str, k: int = 3) -> list[dict]:
    q = embed(query)
    scored = sorted(chunks, key=lambda c: -sum(a * b for a, b in zip(q, c["vec"])))
    return scored[:k]


def build_prompt(chunks: list[dict], question: str, k: int = 3) -> str:
    hits = search(chunks, question, k)
    context = "\n\n".join(f"<chunk source=\"{h['source']}\">\n{h['text']}\n</chunk>" for h in hits)
    return f"Answer using only these code excerpts.\n\n{context}\n\nQuestion: {question}"
