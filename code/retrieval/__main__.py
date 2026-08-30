"""CLI to test retrieval (and optional Mistral generation)."""

from __future__ import annotations

import argparse
import json
import sys

from .pipeline import answer_question

SAMPLE_QUERIES = [
    "What is the expense ratio of HDFC Large Cap?",
    "ELSS lock-in?",
    "Minimum SIP for HDFC Small Cap?",
    "What is the exit load of HDFC Flexi Cap?",
    "What is the benchmark of HDFC Balanced Advantage?",
    "Minimum SIP?",
    "Should I buy HDFC Small Cap?",
    "Which fund is better, Large Cap or Small Cap?",
    "Expense ratio of SBI Bluechip?",
    "asdfgh",
]


def _print_answer(question: str, retrieve_only: bool) -> int:
    result = answer_question(question, retrieve_only=retrieve_only)
    print(f"status:   {result.status}")
    print(f"answer:   {result.answer_text}")
    if result.citation_url:
        print(f"citation: {result.citation_url}")
    footer = result.footer()
    if footer:
        print(f"footer:   {footer}")
    if result.retrieved:
        print("retrieved:")
        print(json.dumps(result.retrieved, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HDFC fund facts retrieval backend (no UI)."
    )
    parser.add_argument("question", nargs="*", help="User question")
    parser.add_argument(
        "--retrieve-only",
        action="store_true",
        help="Skip Mistral; print top-k chunks, distances, and citation.",
    )
    parser.add_argument(
        "--samples",
        action="store_true",
        help="Run the built-in retrieval test questions (retrieve-only).",
    )
    args = parser.parse_args(argv)

    if args.samples:
        code = 0
        for query in SAMPLE_QUERIES:
            print("=" * 72)
            print(f"Q: {query}")
            try:
                _print_answer(query, retrieve_only=True)
            except RuntimeError as exc:
                print(exc, file=sys.stderr)
                code = 1
            print()
        return code

    question = " ".join(args.question).strip()
    if not question:
        print("Usage: PYTHONPATH=code python3 -m retrieval \"<question>\"")
        print("       PYTHONPATH=code python3 -m retrieval --retrieve-only \"<question>\"")
        print("       PYTHONPATH=code python3 -m retrieval --samples")
        print("\nTry:")
        for query in SAMPLE_QUERIES[:5]:
            print(f"  {query}")
        return 1

    try:
        return _print_answer(question, retrieve_only=args.retrieve_only)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
