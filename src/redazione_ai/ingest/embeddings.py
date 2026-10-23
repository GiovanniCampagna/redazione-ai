import hashlib                       # libreria standard: hash
from itertools import batched        # libreria standard: divide in gruppi
from typing import Literal           # libreria standard: tipo "solo questi valori"

import httpx                         # libreria esterna: chiamate HTTP

from redazione_ai.config import settings   # il nostro package: la configurazione

BATCH_SIZE = 32                      # costante: quanti testi per richiesta
PREFIXES = {                         # dizionario: tipo di testo -> prefisso
    "document": "search_document: ",
    "query": "search_query: ",
}


def content_hash(text: str) -> str:
    """Impronta SHA-256 del testo: 64 caratteri esadecimali."""
    # testo -> byte -> hash -> stringa esadecimale di 64 caratteri
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _embed_batch(
    texts: list[str], kind: Literal["document", "query"]
) -> list[list[float]]:
    """Una sola richiesta a Ollama per un gruppo di testi."""
    prefix = PREFIXES[kind]                      # "search_document: " o "search_query: "
    inputs = [prefix + t for t in texts]         # aggiunge il prefisso a ogni testo
    r = httpx.post(                              # la richiesta HTTP POST
        f"{settings.ollama_url}/api/embed",      # URL preso dalla configurazione
        json={"model": settings.embed_model, "input": inputs},   # corpo della richiesta
        timeout=120,                             # aspetta al massimo 120 secondi
    )
    r.raise_for_status()                         # errore 4xx/5xx -> eccezione subito
    return r.json()["embeddings"]                # dalla risposta prendo la lista di vettori


def embed(
    texts: list[str], kind: Literal["document", "query"] = "document"
) -> list[list[float]]:
    """Calcola gli embedding di tutti i testi, BATCH_SIZE alla volta."""
    vectors: list[list[float]] = []              # lista vuota che riempiremo

    for batch in batched(texts, BATCH_SIZE):     # gruppi da 32 (l'ultimo può essere più corto)
        embedded = _embed_batch(list(batch), kind)   # una richiesta per gruppo
        vectors.extend(embedded)                 # aggiungo TUTTI i vettori del gruppo
    return vectors                               # un vettore per ogni testo, nello stesso ordine