import json
from collections.abc import Iterator
from pathlib import Path

import psycopg
from pgvector import Vector


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
