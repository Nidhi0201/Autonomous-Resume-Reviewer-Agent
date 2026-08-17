"""
Measure the JD-embedding latency win from the pgvector cache.

Cold pass  : compute the embedding (sentence-transformers) and store it.
Warm pass  : fetch the same embedding from pgvector (cache hit).

Usage (needs Postgres with the vector extension available):
    DATABASE_URL=postgresql://user:pass@localhost:5432/db \
    python -m scripts.bench_embeddings
"""
import statistics
import time

from app.embedding_cache import ensure_schema, get_connection
from app.embeddings import _get_model, embed_job_description

JOB_DESCRIPTIONS = [
    "Backend Software Engineer. Build scalable REST APIs in Python and Go, "
    "work with PostgreSQL and Redis, design event-driven systems, and own "
    "reliability. Experience with Kubernetes and observability is a plus.",
    "Frontend Engineer. Build accessible React/TypeScript interfaces, work "
    "closely with design, optimize performance, and ship a component library.",
    "Data Engineer. Design batch and streaming pipelines with Spark and Kafka, "
    "model warehouses in dbt/Snowflake, and maintain data quality checks.",
    "Machine Learning Engineer. Train and serve models, build feature pipelines, "
    "run offline evaluation, and deploy inference services with low latency.",
    "Site Reliability Engineer. Own SLOs, build monitoring and alerting, automate "
    "incident response, and improve CI/CD and infrastructure as code.",
]


def _timed(jd, conn):
    t0 = time.perf_counter()
    embed_job_description(jd, conn)
    return (time.perf_counter() - t0) * 1000  # ms


def main():
    conn = get_connection()
    ensure_schema(conn)
    # start from a clean cache so the cold pass really computes
    with conn.cursor() as cur:
        cur.execute("TRUNCATE jd_embeddings")
    conn.commit()

    t0 = time.perf_counter()
    _get_model()  # one-time model load
    load_ms = (time.perf_counter() - t0) * 1000

    cold = [_timed(jd, conn) for jd in JOB_DESCRIPTIONS]   # compute + store
    warm = [_timed(jd, conn) for jd in JOB_DESCRIPTIONS]   # cache hit

    print("\n" + "=" * 54)
    print("JD EMBEDDING CACHE  (pgvector)")
    print("=" * 54)
    print(f"  model load (one-time)      {load_ms:8.1f} ms")
    print(f"  cold  (compute + store)    {statistics.mean(cold):8.1f} ms  avg")
    print(f"  warm  (pgvector cache hit) {statistics.mean(warm):8.1f} ms  avg")
    speedup = statistics.mean(cold) / statistics.mean(warm) if statistics.mean(warm) else 0
    print(f"  cached lookup is {speedup:.0f}x faster than recomputing")
    print("=" * 54)


if __name__ == "__main__":
    main()
