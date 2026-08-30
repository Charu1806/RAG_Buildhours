"""Pre-retrieve guards. PII is never embedded, retrieved, logged, or stored."""

from __future__ import annotations

import re
from typing import Literal

from loading.corpus import CORPUS

GuardKind = Literal["ok", "pii", "advice", "compare", "empty"]

_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I)
_AADHAAR = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(\+91[\s-]?)?[6-9]\d{9}\b")
_OTP = re.compile(r"\b(otp|one[-\s]?time\s+password)\b", re.I)
_ACCOUNT = re.compile(r"\b(account\s*(no|number|#)|a/?c\s*(no|number)|ifsc)\b", re.I)

_ADVICE = re.compile(
    r"\b(should\s+i|buy|sell|switch|recommend|recommended|advice|"
    r"worth\s+investing|allocate|allocation|portfolio)\b",
    re.I,
)
_COMPARE = re.compile(
    r"("
    r"\bcompare\b|\bcomparison\b|\bversus\b|\bvs\.?\b|"
    r"which\s+(fund\s+)?is\s+better|"
    r"\bbetter\s+than\b|\boutperform\b|"
    r"what\s+will\s+.+\s+become|"
    r"1\s*l(akh)?\s+become|"
    r"calculate\s+(return|returns)|"
    r"projected\s+return|future\s+value"
    r")",
    re.I,
)
_OUT_OF_CORPUS = re.compile(
    r"\b(sbi|bluechip|nippon|parag\s+parikh|mirae|"
    r"icici\s+prudential|quant\s+(small|mid|flexi|large))\b",
    re.I,
)

FUND_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        CORPUS[0]["source_url"],
        ("large cap", "large-cap", "hdfc large"),
    ),
    (
        CORPUS[1]["source_url"],
        ("flexi cap", "flexi-cap", "flexicap", "hdfc flexi", "hdfc equity fund"),
    ),
    (
        CORPUS[2]["source_url"],
        ("elss", "tax saver", "tax-saver", "lock-in", "lock in", "3y lock"),
    ),
    (
        CORPUS[3]["source_url"],
        ("small cap", "small-cap", "hdfc small"),
    ),
    (
        CORPUS[4]["source_url"],
        (
            "balanced advantage",
            "baf",
            "dynamic asset",
            "hdfc hybrid",
            "hdfc balanced",
        ),
    ),
)

REFUSE_PII = (
    "I can't accept personal details such as PAN, Aadhaar, account numbers, "
    "OTPs, emails, or phone numbers. Ask a factual question about one of the "
    "five HDFC funds, without personal data."
)
REFUSE_ADVICE = (
    "I only share facts from the five Groww fund pages. I can't advise "
    "whether to buy, sell, switch, or how to allocate a portfolio. "
    "Facts-only. No investment advice."
)
REFUSE_COMPARE = (
    "I don't compute or compare returns. Check the official numbers on the "
    "fund page (and its factsheet / on-page returns)."
)
ASK_FACTUAL = (
    "Please ask a factual question about one of these five funds: "
    "HDFC Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, or Balanced Advantage."
)
ABSTAIN = (
    "I don't have that on the five Groww pages in this prototype. "
    "I can only answer facts from those sources."
)
CLARIFY = (
    "Which of the five funds do you mean — HDFC Large Cap, Flexi Cap, "
    "ELSS Tax Saver, Small Cap, or Balanced Advantage?"
)


def named_fund_urls(question: str) -> list[str]:
    q = question.lower()
    found: list[str] = []
    for url, aliases in FUND_ALIASES:
        if any(alias in q for alias in aliases):
            found.append(url)
    return found


def is_out_of_corpus_fund(question: str) -> bool:
    return bool(_OUT_OF_CORPUS.search(question))


def is_ambiguous_fund(question: str) -> bool:
    """Unnamed SIP / 'this fund' / a fact with no usable fund name."""
    q = question.lower()
    if re.search(r"\bthis fund\b", q):
        return True
    named = named_fund_urls(question)
    if named:
        return False
    factish = re.search(
        r"\b(expense\s*ratio|sip|exit\s*load|min(imum)?\s+(sip|invest)|"
        r"riskometer|benchmark|nav|aum|capital[-\s]?gains?)\b",
        q,
    )
    return bool(factish) or bool(re.search(r"\b(sip|expense|exit load)\b", q))


def _is_gibberish(text: str) -> bool:
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return True
    return all(not re.search(r"[aeiouAEIOU]", word) for word in words)


def classify(question: str) -> GuardKind:
    text = question.strip()
    if len(text) < 3 or _is_gibberish(text):
        return "empty"
    tokens = text.split()
    if (
        len(tokens) == 1
        and len(text) <= 16
        and not named_fund_urls(text)
        and not re.search(
            r"expense|sip|elss|nav|aum|lock|load|risk|benchmark", text, re.I
        )
    ):
        return "empty"
    if (
        _PAN.search(text)
        or _AADHAAR.search(text)
        or _EMAIL.search(text)
        or _PHONE.search(text)
        or _OTP.search(text)
        or _ACCOUNT.search(text)
    ):
        return "pii"
    if _COMPARE.search(text):
        return "compare"
    if _ADVICE.search(text):
        return "advice"
    return "ok"


def educational_link(question: str) -> str | None:
    named = named_fund_urls(question)
    if len(named) == 1:
        return named[0]
    return None
