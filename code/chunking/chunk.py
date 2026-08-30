"""
Phase 2 — Chunking.

Reads data/raw documents. Writes chunks that keep one source_url each:
{ chunk_id, text, source_url, fund_name, fetched_at }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TypedDict

from loading.corpus import ALLOWED_URLS, CORPUS

from .split import chunk_page_text

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
CHUNKS_DIR = REPO_ROOT / "data" / "chunks"


class RawDocument(TypedDict):
    fund_name: str
    source_url: str
    page_text: str
    fetched_at: str


class Chunk(TypedDict):
    chunk_id: str
    text: str
    source_url: str
    fund_name: str
    fetched_at: str


def _read_raw(raw_dir: Path) -> list[tuple[str, RawDocument]]:
    documents: list[tuple[str, RawDocument]] = []
    missing: list[str] = []
    for page in CORPUS:
        path = raw_dir / f"{page['slug']}.json"
        if not path.is_file():
            missing.append(str(path))
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("source_url") not in ALLOWED_URLS:
            raise RuntimeError(f"Raw document URL is not in the locked corpus: {path}")
        documents.append((page["slug"], doc))
    if missing:
        raise RuntimeError(
            "Chunking failed; all five raw documents must exist. Missing: "
            + ", ".join(missing)
        )
    return documents


def chunk_document(slug: str, doc: RawDocument) -> list[Chunk]:
    parts = chunk_page_text(doc["page_text"], doc["fund_name"])
    chunks: list[Chunk] = []
    for index, text in enumerate(parts):
        chunks.append(
            {
                "chunk_id": f"{slug}-{index:03d}",
                "text": text,
                "source_url": doc["source_url"],
                "fund_name": doc["fund_name"],
                "fetched_at": doc["fetched_at"],
            }
        )
    if not chunks:
        raise RuntimeError(f"No chunks produced for {doc['source_url']}")
    urls = {chunk["source_url"] for chunk in chunks}
    if urls != {doc["source_url"]}:
        raise RuntimeError(f"Chunk URLs mixed or dropped for {slug}")
    return chunks


def chunk_corpus(
    raw_dir: Path | None = None,
    chunks_dir: Path | None = None,
) -> list[Chunk]:
    """Chunk all five raw pages. Write nothing unless every page yields chunks."""
    source_dir = raw_dir or RAW_DIR
    out_dir = chunks_dir or CHUNKS_DIR
    per_fund: list[tuple[str, list[Chunk]]] = []

    for slug, doc in _read_raw(source_dir):
        chunks = chunk_document(slug, doc)
        per_fund.append((slug, chunks))
        print(f"OK  {doc['fund_name']}: {len(chunks)} chunks")

    if len(per_fund) != len(CORPUS):
        raise RuntimeError("Chunking failed; expected one chunk list per corpus URL.")

    all_chunks = [chunk for _, chunks in per_fund for chunk in chunks]
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug, chunks in per_fund:
        (out_dir / f"{slug}.json").write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (out_dir / "chunks.json").write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(all_chunks)} chunks to {out_dir}")
    return all_chunks


def main() -> int:
    try:
        chunk_corpus()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
