"""
Postgres + pgvector cache for job-description embeddings.

JD text is embedded once (sentence-transformers) and the resulting vector is
persisted keyed by a content hash, so repeated analyses of the same JD reuse
the stored embedding instead of recomputing it.
"""
import hashlib
import os

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


def get_connection():
    url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    conn = psycopg2.connect(url)
    return conn


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS jd_embeddings (
                jd_hash    TEXT PRIMARY KEY,
                embedding  vector({EMBEDDING_DIM}),
                created_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )
    conn.commit()
    register_vector(conn)


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def get_cached_embedding(conn, jd_text: str):
    """Return the stored embedding for this JD, or None on a cache miss."""
    with conn.cursor() as cur:
        # Cast to text so parsing is independent of the pgvector type adapter.
        cur.execute(
            "SELECT embedding::text FROM jd_embeddings WHERE jd_hash = %s",
            (_hash(jd_text),),
        )
        row = cur.fetchone()
    if not row:
        return None
    return np.array(row[0].strip("[]").split(","), dtype=np.float32)


def store_embedding(conn, jd_text: str, embedding: np.ndarray) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO jd_embeddings (jd_hash, embedding) VALUES (%s, %s)
            ON CONFLICT (jd_hash) DO NOTHING
            """,
            (_hash(jd_text), np.asarray(embedding, dtype=np.float32)),
        )
    conn.commit()
