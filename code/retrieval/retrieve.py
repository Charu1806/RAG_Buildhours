"""Embed the question with MiniLM and fetch top-k chunks from ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass

from embedding.model import embed_query
from loading.corpus import ALLOWED_URLS
from vector_store.store import query_by_embedding

TOP_K = 5
# Cosine distance (1 - similarity). Named-fund hits can be looser
# because short queries like "ELSS lock-in?" sit farther from a long chunk.
WEAK_DISTANCE = 0.50
WEAK_DISTANCE_NAMED = 0.72


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    source_url: str
    fund_name: str
    fetched_at: str
    distance: float


def retrieve(question: str, k: int = TOP_K) -> list[RetrievedChunk]:
    vector = embed_query(question)
    raw = query_by_embedding(vector, n_results=k)
    ids = raw["ids"][0]
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    distances = raw["distances"][0]

    chunks: list[RetrievedChunk] = []
    for chunk_id, text, meta, distance in zip(ids, docs, metas, distances):
        url = meta.get("source_url", "")
        if url not in ALLOWED_URLS:
            continue
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=text,
                source_url=url,
                fund_name=meta.get("fund_name", ""),
                fetched_at=meta.get("fetched_at", ""),
                distance=float(distance),
            )
        )
    return chunks


def filter_to_fund(chunks: list[RetrievedChunk], source_url: str) -> list[RetrievedChunk]:
    return [chunk for chunk in chunks if chunk.source_url == source_url]


def is_weak(chunks: list[RetrievedChunk], named_fund: bool = False) -> bool:
    if not chunks:
        return True
    limit = WEAK_DISTANCE_NAMED if named_fund else WEAK_DISTANCE
    return chunks[0].distance > limit
