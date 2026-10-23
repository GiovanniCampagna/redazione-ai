import json
from collections.abc import Iterator
from pathlib import Path

import psycopg


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
