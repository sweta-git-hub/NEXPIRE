# NEXPIRE — AI-Powered Surplus Food Redistribution & Expiration Platform

NEXPIRE is an intelligent surplus food management and redistribution ecosystem: FastAPI + Postgres/PostGIS + Redis + Celery, running under Docker Compose.

## 🚀 Quick Start

```bash
# 1. Environment setup
cp .env.example .env

# 2. Build and start containers
docker compose up --build -d

# 3. Verify health check
curl http://localhost:8000/health
# -> {"database":"ok","redis":"ok","healthy":true}

# 4. Run automated test suite (pytest + coverage)
docker compose exec api pytest -v --cov=app
```

## 📦 Services Overview

| Service | Container | Internal Port | Host Port |
|---|---|---|---|
| FastAPI API | nexpire-api | 8000 | 8000 |
| Celery Worker | nexpire-worker | - | - |
| Postgres + PostGIS | nexpire-db | 5432 | 5432 |
| Redis | nexpire-redis | 6379 | 6379 |

## 🛠️ API Reference (Phase 1 — Inventory Core)

### Stores
- `POST /api/v1/stores` — Create store location
- `GET /api/v1/stores` — List stores (paginated)
- `GET /api/v1/stores/{store_id}` — Get store details
- `PUT /api/v1/stores/{store_id}` — Update store
- `DELETE /api/v1/stores/{store_id}` — Delete store

### Inventory Batches
- `POST /api/v1/inventory/batches` — Add inventory batch (auto-calculates current price from discount)
- `GET /api/v1/inventory/batches` — List batches (filters: `store_id`, `category`, `status`, `expiring_before`, `expiring_after`)
- `GET /api/v1/inventory/batches/{batch_id}` — Get batch details
- `PUT /api/v1/inventory/batches/{batch_id}` — Update batch details
- `DELETE /api/v1/inventory/batches/{batch_id}` — Delete batch
- `POST /api/v1/inventory/upload-csv` — Bulk CSV inventory import with error diagnostics

## 🧪 Testing

```bash
# Run pytest in container
docker compose exec api pytest -v --cov=app
```

## 📋 Documentation
- [STATUS.md](file:///Users/sweta/Desktop/sweta/HACKATHONS/AAROH/NEXPIRE/STATUS.md) — Implementation roadmap & phase completion checklist
- [DECISIONS.md](file:///Users/sweta/Desktop/sweta/HACKATHONS/AAROH/NEXPIRE/DECISIONS.md) — Architecture decision records
