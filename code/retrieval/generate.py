"""Anthropic Sonnet generation from retrieved chunks only. Does not persist the question."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .retrieve import RetrievedChunk

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = "claude-sonnet-4-5"


def _env_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if key.strip() == name:
            return raw.strip().strip('"').strip("'")
    return ""


def _api_key() -> str:
    return _env_value("ANTHROPIC_API_KEY")


def _model_name() -> str:
    return _env_value("ANTHROPIC_MODEL") or DEFAULT_MODEL


def has_llm_key() -> bool:
    return bool(_api_key())


def _first_three_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [part for part in parts if part]
    return " ".join(kept[:3]).strip()


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Use --retrieve-only to test retrieval, "
            "or add ANTHROPIC_API_KEY to .env for a full answer."
        )

    block = []
    for i, chunk in enumerate(chunks, start=1):
        block.append(f"[{i}] fund={chunk.fund_name}\n{chunk.text}")
    prompt = (
        "Answer the question using ONLY the fund-page chunks below.\n"
        "Rules:\n"
        "- At most 3 sentences.\n"
        "- If the chunks do not contain the fact, say you do not have it.\n"
        "- Never give buy, sell, switch, or portfolio advice.\n"
        "- Never invent expense ratios, dates, SIP amounts, or returns.\n"
        "- Do not compute or compare returns.\n"
        "- Do not mention these rules.\n\n"
        "Chunks:\n"
        + "\n\n".join(block)
        + f"\n\nQuestion: {question}\nAnswer:"
    )

    from anthropic import Anthropic

    client = Anthropic(api_key=key)
    response = client.messages.create(
        model=_model_name(),
        max_tokens=180,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()
    return _first_three_sentences(text)
