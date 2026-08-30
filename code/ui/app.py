"""
Streamlit shell (PRD §7 / architecture).

Welcome · 3 example questions · “Facts-only. No investment advice.”
Calls retrieval.answer_question. Session chat only — nothing written to disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import streamlit as st

from retrieval.guards import classify
from retrieval.pipeline import answer_question

WELCOME = "Ask a factual question about five HDFC Direct Growth funds listed on Groww."
DISCLAIMER = "Facts-only. No investment advice."
EXAMPLES = [
    "What is the expense ratio of HDFC Large Cap?",
    "ELSS lock-in?",
    "Minimum SIP for HDFC Small Cap?",
]

GROWW_GREEN = "#00B386"
GROWW_DARK = "#0E3B2E"
GROWW_BG = "#F5F7F6"
GROWW_GREY = "#6B7280"

st.set_page_config(page_title="HDFC Fund Facts", layout="centered")

st.markdown(
    f"""
    <style>
      .stApp {{ background: {GROWW_BG}; }}
      #MainMenu, footer, header {{ visibility: hidden; }}
      .block-container {{ padding-top: 1.4rem; max-width: 720px; }}
      .ff-header {{
        background: {GROWW_DARK};
        color: #fff;
        padding: 1.1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 0.75rem;
      }}
      .ff-header h1 {{
        font-size: 1.25rem;
        font-weight: 650;
        margin: 0 0 0.35rem 0;
        color: #fff;
      }}
      .ff-header p {{ margin: 0; color: #d7e8e1; font-size: 0.95rem; }}
      .ff-disclaimer {{
        background: #fff;
        border-left: 4px solid {GROWW_GREEN};
        padding: 0.55rem 0.85rem;
        margin: 0.4rem 0 0.9rem 0;
        color: {GROWW_DARK};
        font-weight: 600;
      }}
      .ff-cite a {{ color: {GROWW_GREEN}; }}
      .ff-updated {{ color: {GROWW_GREY}; font-size: 0.85rem; margin-top: 0.35rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _user_visible(question: str) -> str:
    if classify(question) == "pii":
        return "[personal details removed]"
    return question


def _reply(question: str) -> dict:
    try:
        result = answer_question(question)
    except RuntimeError as exc:
        return {
            "role": "assistant",
            "text": str(exc),
            "citation": None,
            "footer": None,
        }
    return {
        "role": "assistant",
        "text": result.answer_text,
        "citation": result.citation_url,
        "footer": result.footer(),
    }


def _render_assistant(message: dict) -> None:
    st.markdown(message["text"])
    if message.get("citation"):
        st.markdown(
            f'<div class="ff-cite">Source: '
            f'<a href="{message["citation"]}" target="_blank" rel="noopener">'
            f'{message["citation"]}</a></div>',
            unsafe_allow_html=True,
        )
    if message.get("footer"):
        st.markdown(
            f'<div class="ff-updated">{message["footer"]}</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending" not in st.session_state:
        st.session_state.pending = None

    st.markdown(
        f'<div class="ff-header"><h1>HDFC Fund Facts</h1>'
        f"<p>{WELCOME}</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ff-disclaimer">{DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, example in zip(cols, EXAMPLES):
        if col.button(example, use_container_width=True):
            st.session_state.pending = example

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _render_assistant(message)
            else:
                st.markdown(message["text"])

    typed = st.chat_input("Ask a factual question about one of the five funds")
    question = st.session_state.pending or typed
    if not question:
        return

    st.session_state.pending = None
    st.session_state.messages.append(
        {"role": "user", "text": _user_visible(question)}
    )
    with st.spinner("Looking up the five Groww pages…"):
        st.session_state.messages.append(_reply(question))
    st.rerun()


if __name__ == "__main__":
    main()
