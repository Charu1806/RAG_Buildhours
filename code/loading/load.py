"""
Phase 1 — Data loading.

Fetches the five architecture URLs, extracts visible text, writes
{fund_name, source_url, page_text, fetched_at} to data/raw/.
Fails the ingest if any URL cannot be loaded (live or same-URL snapshot).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from .corpus import CORPUS, FundPage
from .extract import extract_visible_text, is_thin_text
from .fetch import fetch_html

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
HTML_DIR = RAW_DIR / "html"


class RawDocument(TypedDict):
    fund_name: str
    source_url: str
    page_text: str
    fetched_at: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mtime_iso(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _snapshot_path(slug: str) -> Path:
    return HTML_DIR / f"{slug}.html"


def _load_snapshot(page: FundPage) -> tuple[str, str] | None:
    path = _snapshot_path(page["slug"])
    if not path.is_file():
        return None
    html = path.read_text(encoding="utf-8")
    text = extract_visible_text(html)
    if is_thin_text(text):
        return None
    return text, _mtime_iso(path)


def _load_one(page: FundPage) -> RawDocument:
    html: str | None = None
    live_error: Exception | None = None

    try:
        html = fetch_html(page["source_url"])
    except Exception as exc:  # noqa: BLE001 — surface any fetch failure
        live_error = exc

    if html is not None:
        page_text = extract_visible_text(html)
        if not is_thin_text(page_text):
            HTML_DIR.mkdir(parents=True, exist_ok=True)
            _snapshot_path(page["slug"]).write_text(html, encoding="utf-8")
            return {
                "fund_name": page["fund_name"],
                "source_url": page["source_url"],
                "page_text": page_text,
                "fetched_at": _utc_now(),
            }
        snapshot = _load_snapshot(page)
        if snapshot:
            text, fetched_at = snapshot
            return {
                "fund_name": page["fund_name"],
                "source_url": page["source_url"],
                "page_text": text,
                "fetched_at": fetched_at,
            }
        raise RuntimeError(
            f"JS-thin page and no usable snapshot for {page['source_url']}"
        )

    snapshot = _load_snapshot(page)
    if snapshot:
        text, fetched_at = snapshot
        return {
            "fund_name": page["fund_name"],
            "source_url": page["source_url"],
            "page_text": text,
            "fetched_at": fetched_at,
        }
    raise RuntimeError(f"Could not load {page['source_url']}: {live_error}")


def load_corpus(raw_dir: Path | None = None) -> list[RawDocument]:
    """Load all five pages. Write nothing unless every page succeeds."""
    out_dir = raw_dir or RAW_DIR
    documents: list[RawDocument] = []
    errors: list[str] = []

    for page in CORPUS:
        try:
            documents.append(_load_one(page))
            print(f"OK  {page['fund_name']}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{page['source_url']}: {exc}")
            print(f"FAIL  {page['fund_name']}: {exc}", file=sys.stderr)

    if errors or len(documents) != len(CORPUS):
        raise RuntimeError(
            "Ingest failed; all five URLs must load. "
            + " | ".join(errors)
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    if len(documents) != len(CORPUS):
        raise RuntimeError("Ingest failed; document count does not match corpus.")
    for page, doc in zip(CORPUS, documents):
        path = out_dir / f"{page['slug']}.json"
        path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"Wrote {len(documents)} documents to {out_dir}")
    return documents


def main() -> int:
    try:
        load_corpus()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
