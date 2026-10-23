import hashlib
from itertools import batched
from typing import Literal

import httpx

from redazione_ai.config import settings

BATCH_SIZE = 32
PREFIXES = {
    "document": "search_document: ",
    "query": "search_query: ",
}


def content_hash(text: str) -> str:
    """Impronta SHA-256 del testo: 64 caratteri esadecimali."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _embed_batch(
    texts: list[str], kind: Literal["document", "query"]
) -> list[list[float]]:
    """Una sola richiesta a Ollama per un gruppo di testi."""
    prefix = PREFIXES[kind]
    inputs = [prefix + t for t in texts]
    r = httpx.post(
        f"{settings.ollama_url}/api/embed",
        json={"model": settings.embed_model, "input": inputs},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["embeddings"]


def embed(
    texts: list[str], kind: Literal["document", "query"] = "document"
) -> list[list[float]]:
    """Calcola gli embedding di tutti i testi, BATCH_SIZE alla volta."""
    vectors: list[list[float]] = []

    for batch in batched(texts, BATCH_SIZE):
        embedded = _embed_batch(list(batch), kind)
        vectors.extend(embedded)
    return vectors
