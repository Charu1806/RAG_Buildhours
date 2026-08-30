"""Fetch public HTML for allowlisted Groww URLs only."""

from __future__ import annotations

import time

import requests

from .corpus import allowed_url

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

TIMEOUT_SECONDS = 30
RETRIES = 2


def fetch_html(url: str) -> str:
    if not allowed_url(url):
        raise ValueError(f"URL is not in the locked corpus: {url}")

    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            response = requests.get(url, headers=_HEADERS, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to load {url}: {last_error}") from last_error
