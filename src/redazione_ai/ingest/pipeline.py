import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import psycopg
from pgvector import Vector

from redazione_ai.db import get_connection
from redazione_ai.ingest.chunking import split_into_chunks
from redazione_ai.ingest.embeddings import content_hash, embed


def read_articles(path: Path) -> Iterator[dict]:
    """Legge il file JSONL e restituisce un articolo alla volta."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            yield d


def get_stored_hash(conn: psycopg.Connection, source_id: str) -> str | None:
    """Restituisce l'hash salvato per l'articolo, o None se non è nel database."""
    row = conn.execute(
        "SELECT content_hash FROM article WHERE source_id = %s", (source_id,)
    ).fetchone()
    if row:
        return row[0]
    return None


UPSERT_ARTICLE = """
    INSERT INTO article (source_id, title, url, content, content_hash)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (source_id) DO UPDATE SET
        title = EXCLUDED.title,
        url = EXCLUDED.url,
        content = EXCLUDED.content,
        content_hash = EXCLUDED.content_hash,
        ingested_at = now()
    RETURNING id
"""

INSERT_CHUNK = """
    INSERT INTO chunk (article_id, position, content, embedding)
    VALUES (%s, %s, %s, %s)
"""


def upsert_article(conn: psycopg.Connection, art: dict, content_hash: str) -> int:
    """Inserisce l'articolo o, se esiste già, lo aggiorna. Restituisce il suo id."""
    params = (
        art["source_id"],
        art["title"],
        art.get("url"),
        art["content"],
        content_hash,
    )
    row = conn.execute(UPSERT_ARTICLE, params).fetchone()
    assert row is not None
    return row[0]


def insert_chunks(
    conn: psycopg.Connection,
    article_id: int,
    chunks: list[str],
    vectors: list[list[float]],
) -> None:
    """Salva i chunk dell'articolo, ciascuno con la sua posizione e il suo vettore."""
    for position, (content, vector) in enumerate(zip(chunks, vectors)):
        conn.execute(INSERT_CHUNK, (article_id, position, content, Vector(vector)))


def ingest_article(conn: psycopg.Connection, art: dict) -> str:
    """Indicizza un articolo. Restituisce "new", "updated" o "skipped"."""
    # 1. hash del contenuto attuale e hash salvato nel database
    new_hash = content_hash(art["content"])
    stored_hash = get_stored_hash(conn, art["source_id"])

    # 2. se sono uguali l'articolo non è cambiato: restituisci "skipped"
    if new_hash == stored_hash:
        return "skipped"

    # 3. "new" se non c'era nessun hash salvato, altrimenti "updated"
    if stored_hash:
        status = "updated"
    else:
        status = "new"

    # 4. chunking ed embedding, FUORI dalla transazione perché sono la parte lenta
    chunks = split_into_chunks(art["content"])
    vectors = embed(chunks)

    # 5. tutto o niente: upsert, cancellazione dei vecchi chunk, inserimento dei nuovi
    with conn.transaction():
        article_id = upsert_article(conn, art, new_hash)
        conn.execute("DELETE FROM chunk WHERE article_id = %s", (article_id,))
        insert_chunks(conn, article_id, chunks, vectors)

    return status


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python -m redazione_ai.ingest.pipeline <file.jsonl>")
        sys.exit(1)
    path = Path(sys.argv[1])

    counts = {"new": 0, "updated": 0, "skipped": 0}
    start = time.perf_counter()

    with get_connection() as conn:
        for i, art in enumerate(read_articles(path), start=1):
            status = ingest_article(conn, art)
            counts[status] += 1
            if i % 100 == 0:
                print(f"{i} articoli elaborati... {counts}")

    elapsed = time.perf_counter() - start
    print(
        f"Fatto in {elapsed:.1f} s: {counts['new']} nuovi, "
        f"{counts['updated']} aggiornati, {counts['skipped']} saltati"
    )


if __name__ == "__main__":
    main()
