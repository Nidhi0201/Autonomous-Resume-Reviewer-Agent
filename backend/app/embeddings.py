"""
Semantic matching of resume bullets to a job description.

Uses sentence-transformers embeddings (all-MiniLM-L6-v2) with cosine similarity.
Falls back to keyword-overlap scoring if sentence-transformers is unavailable.
JD embeddings can be cached in Postgres/pgvector (see app.embedding_cache) so
they are not recomputed across runs.
"""
import re
from typing import List, Optional, Tuple

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model():
    """Lazy-load the sentence-transformers model; None if the lib is missing."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(MODEL_NAME)
        except Exception:
            _model = False  # sentinel: unavailable
    return _model or None


def embeddings_available() -> bool:
    return _get_model() is not None


def embed(texts: List[str]) -> np.ndarray:
    """Embed a list of texts into a (n, dim) float32 matrix."""
    model = _get_model()
    if model is None:
        raise RuntimeError("sentence-transformers is not installed")
    return np.asarray(model.encode(texts, normalize_embeddings=True), dtype=np.float32)


def embed_job_description(jd_text: str, conn=None) -> np.ndarray:
    """
    Embed a job description, using the pgvector cache when a DB connection is
    provided (recompute only on a cache miss).
    """
    if conn is not None:
        from app.embedding_cache import get_cached_embedding, store_embedding

        cached = get_cached_embedding(conn, jd_text)
        if cached is not None:
            return cached
        vec = embed([jd_text])[0]
        store_embedding(conn, jd_text, vec)
        return vec
    return embed([jd_text])[0]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    # inputs are normalized, so a dot product is the cosine similarity
    return float(np.clip(np.dot(a, b), 0.0, 1.0))


def map_bullets_to_jd(
    resume_bullets: List[str],
    job_description: str,
    top_k: Optional[int] = 3,
) -> List[Tuple[str, float, str]]:
    """
    Map resume bullets to the most relevant JD chunk.

    Returns (bullet, relevance_score, matched_jd_snippet), sorted by score.
    Uses embeddings when available, otherwise keyword overlap.
    """
    if not resume_bullets:
        return []

    jd_chunks = _extract_jd_chunks(job_description) or [job_description[:200]]

    if embeddings_available():
        chunk_vecs = embed(jd_chunks)
        bullet_vecs = embed(resume_bullets)
        mappings = []
        for bullet, bvec in zip(resume_bullets, bullet_vecs):
            sims = chunk_vecs @ bvec  # cosine (all normalized)
            best = int(np.argmax(sims))
            mappings.append((bullet, float(np.clip(sims[best], 0.0, 1.0)), jd_chunks[best]))
    else:
        mappings = []
        for bullet in resume_bullets:
            best_score, best_chunk = 0.0, jd_chunks[0]
            for chunk in jd_chunks:
                score = _calculate_simple_relevance(bullet, chunk)
                if score > best_score:
                    best_score, best_chunk = score, chunk
            mappings.append((bullet, best_score, best_chunk))

    mappings.sort(key=lambda x: x[1], reverse=True)
    return mappings[:top_k] if top_k else mappings


# --------------------------------------------------------------------------- #
# Keyword fallback (used when sentence-transformers is unavailable)
# --------------------------------------------------------------------------- #
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "should", "could", "may",
    "might", "must", "can",
}


def _calculate_simple_relevance(bullet: str, jd_text: str) -> float:
    bullet_words = set(re.findall(r"\b\w+\b", bullet.lower())) - _STOP_WORDS
    jd_words = set(re.findall(r"\b\w+\b", jd_text.lower())) - _STOP_WORDS
    if not bullet_words or not jd_words:
        return 0.5
    union = len(bullet_words | jd_words)
    if union == 0:
        return 0.5
    return min(len(bullet_words & jd_words) / union * 2, 1.0)


def _extract_jd_chunks(job_description: str) -> List[str]:
    chunks = []
    for sentence in job_description.replace("\n", " ").split("."):
        sentence = sentence.strip()
        if len(sentence) > 20:
            chunks.append(sentence)
    for section in job_description.split("\n\n"):
        section = section.strip()
        if len(section) > 30:
            chunks.append(section)
    return chunks[:50]
