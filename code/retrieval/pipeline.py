"""
Phase 5 — Retrieval logic.

Guards → MiniLM retrieve → abstain/clarify → Mistral (chunks only).
Returns the PRD envelope. Stores nothing (no chat, no PII).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .generate import generate_answer, has_mistral_key
from .guards import (
    ABSTAIN,
    ASK_FACTUAL,
    CLARIFY,
    REFUSE_ADVICE,
    REFUSE_COMPARE,
    REFUSE_PII,
    classify,
    educational_link,
    is_ambiguous_fund,
    is_out_of_corpus_fund,
    named_fund_urls,
)
from .retrieve import RetrievedChunk, filter_to_fund, is_weak, retrieve

Status = Literal[
    "ok",
    "pii",
    "advice",
    "compare",
    "empty",
    "clarify",
    "abstain",
]


@dataclass
class Answer:
    status: Status
    answer_text: str
    citation_url: str | None = None
    last_updated: str | None = None
    retrieved: list[dict[str, Any]] = field(default_factory=list)

    def footer(self) -> str | None:
        if not self.last_updated:
            return None
        date = self.last_updated[:10]
        return f"Last updated from sources: {date}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["last_updated_line"] = self.footer()
        return payload


def _chunk_payload(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": chunk.chunk_id,
            "source_url": chunk.source_url,
            "fund_name": chunk.fund_name,
            "fetched_at": chunk.fetched_at,
            "distance": round(chunk.distance, 4),
            "text_preview": chunk.text[:180].replace("\n", " "),
        }
        for chunk in chunks
    ]


def _envelope(
    status: Status,
    text: str,
    chunks: list[RetrievedChunk] | None = None,
    citation_url: str | None = None,
    last_updated: str | None = None,
) -> Answer:
    return Answer(
        status=status,
        answer_text=text,
        citation_url=citation_url,
        last_updated=last_updated,
        retrieved=_chunk_payload(chunks or []),
    )


def _cite(chunks: list[RetrievedChunk]) -> tuple[str, str]:
    """Exactly one URL: the best-matching fund page."""
    top = chunks[0]
    return top.source_url, top.fetched_at


def answer_question(question: str, retrieve_only: bool = False) -> Answer:
    kind = classify(question)
    if kind == "empty":
        return _envelope("empty", ASK_FACTUAL)
    if kind == "pii":
        return _envelope("pii", REFUSE_PII)
    if kind == "advice":
        return _envelope(
            "advice",
            REFUSE_ADVICE,
            citation_url=educational_link(question),
        )
    if kind == "compare":
        return _envelope(
            "compare",
            REFUSE_COMPARE,
            citation_url=educational_link(question),
        )

    if is_out_of_corpus_fund(question):
        return _envelope("abstain", ABSTAIN)

    named = named_fund_urls(question)
    if len(named) > 1:
        return _envelope("clarify", CLARIFY)
    if is_ambiguous_fund(question) and not named:
        return _envelope("clarify", CLARIFY)

    chunks = retrieve(question)
    if named:
        chunks = filter_to_fund(chunks, named[0])

    if is_weak(chunks, named_fund=bool(named)):
        return _envelope("abstain", ABSTAIN, chunks)

    citation, fetched_at = _cite(chunks)
    if retrieve_only:
        return _envelope(
            "ok",
            f"Retrieved {len(chunks)} chunk(s). Top: {chunks[0].chunk_id}",
            chunks,
            citation_url=citation,
            last_updated=fetched_at,
        )

    if not has_mistral_key():
        raise RuntimeError(
            "MISTRAL_API_KEY is not set. Re-run with --retrieve-only to test "
            "chunk retrieval, or export MISTRAL_API_KEY for a generated answer."
        )

    text = generate_answer(question, chunks)
    return _envelope("ok", text, chunks, citation_url=citation, last_updated=fetched_at)
