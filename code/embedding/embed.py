"""
Phase 3 — Embedding.

Reads data/chunks/chunks.json. Embeds chunk.text only with MiniLM.
Writes { chunk_id, embedding, text, source_url, fund_name, fetched_at }.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TypedDict

from loading.corpus import ALLOWED_URLS, CORPUS

from .model import EMBEDDING_DIM, MODEL_NAME, embed_texts

REPO_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = REPO_ROOT / "data" / "chunks" / "chunks.json"
EMBEDDINGS_DIR = REPO_ROOT / "data" / "embeddings"

REQUIRED_CHUNK_KEYS = ("chunk_id", "text", "source_url", "fund_name", "fetched_at")


class EmbeddedChunk(TypedDict):
    chunk_id: str
    embedding: list[float]
    text: str
    source_url: str
    fund_name: str
    fetched_at: str


def _read_chunks(chunks_path: Path) -> list[dict]:
    if not chunks_path.is_file():
        raise RuntimeError(f"Chunking output missing: {chunks_path}")
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    if not chunks:
        raise RuntimeError("Chunking output is empty.")

    urls = set()
    ids = set()
    for chunk in chunks:
        missing = [key for key in REQUIRED_CHUNK_KEYS if key not in chunk]
        if missing:
            raise RuntimeError(f"Chunk missing {missing}: {chunk.get('chunk_id')}")
        if chunk["source_url"] not in ALLOWED_URLS:
            raise RuntimeError(
                f"Chunk URL is not in the locked corpus: {chunk['source_url']}"
            )
        if chunk["chunk_id"] in ids:
            raise RuntimeError(f"Duplicate chunk_id: {chunk['chunk_id']}")
        ids.add(chunk["chunk_id"])
        urls.add(chunk["source_url"])

    expected = {page["source_url"] for page in CORPUS}
    if urls != expected:
        raise RuntimeError(
            "Embedding failed; chunks must cover all five corpus URLs. "
            f"missing={sorted(expected - urls)} extra={sorted(urls - expected)}"
        )
    return chunks


def embed_corpus(
    chunks_path: Path | None = None,
    embeddings_dir: Path | None = None,
) -> list[EmbeddedChunk]:
    """Embed every chunk. Write nothing unless all vectors succeed."""
    source = chunks_path or CHUNKS_PATH
    out_dir = embeddings_dir or EMBEDDINGS_DIR
    chunks = _read_chunks(source)

    print(f"Embedding {len(chunks)} chunks with {MODEL_NAME}")
    vectors = embed_texts([chunk["text"] for chunk in chunks], show_progress=True)
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count.")

    records: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors):
        if len(vector) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Bad vector dim {len(vector)} for {chunk['chunk_id']}"
            )
        records.append(
            {
                "chunk_id": chunk["chunk_id"],
                "embedding": vector,
                "text": chunk["text"],
                "source_url": chunk["source_url"],
                "fund_name": chunk["fund_name"],
                "fetched_at": chunk["fetched_at"],
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "embeddings.json"
    out_path.write_text(
        json.dumps(records, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} embeddings ({EMBEDDING_DIM}-d) to {out_path}")
    return records


def main() -> int:
    try:
        embed_corpus()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
