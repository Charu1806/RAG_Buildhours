"""
Phase 4 — Vector store.

Loads precomputed MiniLM vectors into one local ChromaDB collection.
Upserts by chunk_id. Metadata is source_url, fetched_at, fund_name only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from loading.corpus import ALLOWED_URLS, CORPUS

REPO_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_PATH = REPO_ROOT / "data" / "embeddings" / "embeddings.json"
VECTORDB_DIR = REPO_ROOT / "data" / "vectordb"
COLLECTION_NAME = "hdfc_fund_facts"
REQUIRED_KEYS = (
    "chunk_id",
    "embedding",
    "text",
    "source_url",
    "fund_name",
    "fetched_at",
)


def _client(persist_dir: Path):
    import chromadb

    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def get_collection(persist_dir: Path | None = None):
    """Open the single corpus collection. Does not create a second store."""
    client = _client(persist_dir or VECTORDB_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _read_embeddings(path: Path) -> list[dict]:
    if not path.is_file():
        raise RuntimeError(f"Embedding output missing: {path}")
    records = json.loads(path.read_text(encoding="utf-8"))
    if not records:
        raise RuntimeError("Embedding output is empty.")

    urls: set[str] = set()
    ids: set[str] = set()
    for record in records:
        missing = [key for key in REQUIRED_KEYS if key not in record]
        if missing:
            raise RuntimeError(f"Embedded chunk missing {missing}")
        url = record["source_url"]
        if url not in ALLOWED_URLS:
            raise RuntimeError(f"Refusing to index URL outside the corpus: {url}")
        if record["chunk_id"] in ids:
            raise RuntimeError(f"Duplicate chunk_id: {record['chunk_id']}")
        ids.add(record["chunk_id"])
        urls.add(url)

    expected = {page["source_url"] for page in CORPUS}
    if urls != expected:
        raise RuntimeError(
            "Vector store failed; embeddings must cover all five corpus URLs. "
            f"missing={sorted(expected - urls)} extra={sorted(urls - expected)}"
        )
    return records


def _assert_five_urls_queryable(collection) -> None:
    """Acceptance: every corpus URL is present and retrievable from ChromaDB."""
    for page in CORPUS:
        hits = collection.get(where={"source_url": page["source_url"]}, limit=1)
        if not hits["ids"]:
            raise RuntimeError(
                f"Not queryable in ChromaDB: {page['source_url']}"
            )


def upsert_corpus(
    embeddings_path: Path | None = None,
    persist_dir: Path | None = None,
) -> int:
    """Replace the collection contents for the five URLs. No chat/PII storage."""
    records = _read_embeddings(embeddings_path or EMBEDDINGS_PATH)
    collection = get_collection(persist_dir)

    ids = [record["chunk_id"] for record in records]
    existing = collection.get(include=[])
    stale = set(existing["ids"]) - set(ids)
    if stale:
        collection.delete(ids=list(stale))

    collection.upsert(
        ids=ids,
        embeddings=[record["embedding"] for record in records],
        documents=[record["text"] for record in records],
        metadatas=[
            {
                "source_url": record["source_url"],
                "fund_name": record["fund_name"],
                "fetched_at": record["fetched_at"],
            }
            for record in records
        ],
    )

    _assert_five_urls_queryable(collection)
    count = collection.count()
    if count != len(records):
        raise RuntimeError(
            f"Chroma count {count} does not match upserted {len(records)}"
        )
    print(f"OK  {count} vectors in '{COLLECTION_NAME}'")
    print(f"OK  all five source URLs queryable")
    print(f"Wrote ChromaDB to {persist_dir or VECTORDB_DIR}")
    return count


def query_by_embedding(
    embedding: list[float],
    n_results: int = 5,
    persist_dir: Path | None = None,
) -> dict[str, Any]:
    """Lookup by a precomputed MiniLM vector. Used by retrieval; stores nothing."""
    collection = get_collection(persist_dir)
    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def main() -> int:
    try:
        upsert_corpus()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
