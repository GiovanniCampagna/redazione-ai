import psycopg
from pgvector.psycopg import register_vector

from redazione_ai.config import settings


def get_connection() -> psycopg.Connection:
    """Apre una connessione al database, pronta per i vettori."""
    conn = psycopg.connect(settings.database_url, autocommit=True)
    register_vector(conn)
    return conn
