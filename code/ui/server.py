"""Serve the Stitch UI and POST /api/ask → retrieval.answer_question."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from retrieval.guards import classify
from retrieval.pipeline import answer_question

UI_DIR = Path(__file__).resolve().parent
INDEX = UI_DIR / "index.html"
DEFAULT_PORT = 8501


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        path = urlparse(self.path).path
        if path == "/api/ask":
            return
        super().log_message(fmt, *args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/ask":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send(
                400,
                json.dumps({"error": "invalid json"}).encode("utf-8"),
                "application/json",
            )
            return
        question = str(payload.get("question") or "")
        kind = classify(question)
        user_text = "[personal details removed]" if kind == "pii" else question
        try:
            result = answer_question(question)
            body = {
                "status": result.status,
                "answer_text": result.answer_text,
                "citation_url": result.citation_url,
                "last_updated_line": result.footer(),
                "user_text": user_text,
            }
        except Exception as exc:  # noqa: BLE001 — keep the chat from dying
            body = {
                "status": "error",
                "answer_text": (
                    "Could not generate an answer. Check MISTRAL_API_KEY in .env."
                    if "401" in str(exc) or "API Key" in str(exc)
                    else str(exc)
                ),
                "citation_url": None,
                "last_updated_line": None,
                "user_text": user_text,
            }
        self._send(200, json.dumps(body).encode("utf-8"), "application/json")


def main(port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"GrowChatBot UI  http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    chosen = DEFAULT_PORT
    if len(sys.argv) > 1:
        chosen = int(sys.argv[1])
    main(chosen)
