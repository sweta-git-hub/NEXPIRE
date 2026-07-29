import os
import redis
from fastapi import FastAPI
from app.db import check_db_connection

app = FastAPI(title="NEXPIRE API", version="0.1.0")

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)


@app.get("/")
def root():
    return {"service": "nexpire-api", "status": "running"}


@app.get("/health")
def health():
    """Phase 0 proof-of-life check: confirms Postgres+PostGIS and Redis
    are both reachable from the API container."""
    db_ok = check_db_connection()
    try:
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False

    return {
        "database": "ok" if db_ok else "unreachable",
        "redis": "ok" if redis_ok else "unreachable",
        "healthy": db_ok and redis_ok,
    }
