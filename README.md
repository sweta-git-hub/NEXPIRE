# NEXPIRE — Phase 0 Starter

Minimal, working scaffold: FastAPI + Postgres/PostGIS + Redis + Celery,
all wired together and running under Docker Compose, with a seed script.
This is the "definition of done" for Phase 0 — everything past this point
(Phases 1-7) builds inside this skeleton.

## Prerequisites
- Docker + Docker Compose installed
- Git

## First-time setup

```bash
# 1. Copy the env template and fill in real values as you get to
#    Twilio/Stripe/weather API keys in later phases. Phase 0 works
#    fine with the defaults as-is.
cp .env.example .env

# 2. Build and start everything
docker compose up --build

# 3. In a second terminal, confirm the API can reach both Postgres
#    and Redis
curl http://localhost:8000/health
# -> {"database":"ok","redis":"ok","healthy":true}

# 4. Seed demo data
docker compose exec api python scripts/seed.py
```

## What's running

| Service | Container | Port |
|---|---|---|
| FastAPI app | nexpire-api | 8000 |
| Celery worker | nexpire-worker | - |
| Postgres + PostGIS | nexpire-db | 5432 |
| Redis | nexpire-redis | 6379 |

## Common commands

```bash
# Tail logs
docker compose logs -f api

# Open a psql shell
docker compose exec db psql -U nexpire -d nexpire

# Open a Redis CLI
docker compose exec redis redis-cli

# Rebuild after changing requirements.txt
docker compose up --build

# Wipe the DB completely (re-runs init.sql on next up)
docker compose down -v
```

## Repo/branch conventions (per RULE.md)

- One branch per phase: `phase-0-setup`, `phase-1-inventory`, etc.
- Frequent small commits within a phase branch.
- Request explicit go-ahead before merging a phase branch or starting the next one.
- Update `STATUS.md` and `DECISIONS.md` at every commit/phase boundary.
