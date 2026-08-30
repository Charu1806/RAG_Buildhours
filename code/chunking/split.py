"""
Split one page's text into chunks.

Heading-first on Groww fund-page section titles. Oversized sections
(e.g. holdings) fall back to fixed size with overlap.
Never mixes text from two URLs — caller passes one page at a time.
"""

from __future__ import annotations

# Long enough for a fact + context; short enough for a ≤3-sentence answer.
MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 24
OVERLAP_CHARS = 150

# Exact line matches from the five Groww pages (visible text, not HTML tags).
_HEADING_EXACT = frozenset(
    {
        "return calculator",
        "minimum investments",
        "understand terms",
        "returns and rankings",
        "exit load",
        "exit load, stamp duty and tax",
        "compare similar funds",
        "fund management",
        "about",
        "investment objective",
        "fund benchmark",
        "fund house",
        "scheme information document(sid)",
    }
)


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    lower = stripped.lower()
    if lower in _HEADING_EXACT:
        return True
    return lower.startswith("holdings")


def main_content_bounds(lines: list[str]) -> tuple[int, int]:
    """Crop site nav / footer. Facts sit between the fund title and Fund house."""
    sip_idxs = [i for i, line in enumerate(lines) if line.strip() == "Min. for SIP"]
    if not sip_idxs:
        return 0, len(lines)

    first_sip = sip_idxs[0]
    start = 0
    for i in range(first_sip, -1, -1):
        text = lines[i]
        if "HDFC" in text and "Growth" in text:
            start = i
            break

    house = next(
        (i for i in range(start, len(lines)) if lines[i].strip() == "Fund house"),
        None,
    )
    if house is None:
        return start, len(lines)

    for i in range(house, len(lines)):
        if lines[i].strip() == "Home" or "Vaishnavi Tech Park" in lines[i]:
            return start, i
    return start, min(len(lines), house + 40)


def split_by_headings(lines: list[str]) -> list[str]:
    sections: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if is_heading(line) and current:
            sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)
    return ["\n".join(part).strip() for part in sections if "\n".join(part).strip()]


def split_fixed(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text] if len(text) >= MIN_CHUNK_CHARS else []

    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            cut = text.rfind("\n", start + max_chars // 2, end)
            if cut <= start:
                cut = end
        else:
            cut = end
        piece = text[start:cut].strip()
        if len(piece) >= MIN_CHUNK_CHARS:
            chunks.append(piece)
        if cut >= length:
            break
        next_start = cut - overlap
        if next_start <= start:
            next_start = cut
        start = next_start
    return chunks


def attach_fund_name(text: str, fund_name: str) -> str:
    if text.startswith(fund_name):
        return text
    return f"{fund_name}\n\n{text}"


def chunk_page_text(page_text: str, fund_name: str) -> list[str]:
    lines = page_text.splitlines()
    start, end = main_content_bounds(lines)
    body = lines[start:end]
    if not body:
        body = lines

    texts: list[str] = []
    for section in split_by_headings(body):
        for part in split_fixed(section):
            texts.append(attach_fund_name(part, fund_name))
    return texts
