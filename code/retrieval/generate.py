"""Mistral generation from retrieved chunks only. Does not persist the question."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .retrieve import RetrievedChunk

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL = "mistral-small-latest"


def _api_key() -> str:
    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "MISTRAL_API_KEY":
                return value.strip().strip('"').strip("'")
    return ""


def has_mistral_key() -> bool:
    return bool(_api_key())


def _first_three_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [part for part in parts if part]
    return " ".join(kept[:3]).strip()


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError(
            "MISTRAL_API_KEY is not set. Use --retrieve-only to test retrieval, "
            "or export MISTRAL_API_KEY for a full answer."
        )

    block = []
    for i, chunk in enumerate(chunks, start=1):
        block.append(
            f"[{i}] fund={chunk.fund_name}\n{chunk.text}"
        )
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

    from mistralai import Mistral

    client = Mistral(api_key=key)
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=180,
    )
    text = (response.choices[0].message.content or "").strip()
    return _first_three_sentences(text)
