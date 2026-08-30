"""Extract visible page text from public HTML. Does not follow links."""

from __future__ import annotations

from bs4 import BeautifulSoup

# Below this, treat the fetch as JS-thin and try a same-URL snapshot.
MIN_VISIBLE_CHARS = 800

_STRIP_TAGS = ("script", "style", "noscript", "svg", "iframe")


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines()]
    return "\n".join(line for line in lines if line)


def is_thin_text(page_text: str) -> bool:
    return len(page_text) < MIN_VISIBLE_CHARS
