"""Locked embedding model. Same instance for chunks and queries."""

from __future__ import annotations

from typing import Sequence

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: Sequence[str], show_progress: bool = False) -> list[list[float]]:
    """Embed raw strings only. Do not pass metadata, PII, or chat logs."""
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(
        list(texts),
        convert_to_numpy=True,
        show_progress_bar=show_progress,
        normalize_embeddings=True,
    )
    if vectors.ndim != 2 or vectors.shape[1] != EMBEDDING_DIM:
        raise RuntimeError(
            f"Unexpected embedding shape {getattr(vectors, 'shape', None)}; "
            f"expected (*, {EMBEDDING_DIM}) from {MODEL_NAME}"
        )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Query-time path — same model as corpus chunks."""
    return embed_texts([text])[0]
