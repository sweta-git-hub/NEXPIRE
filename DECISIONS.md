# DECISIONS.md — Technical Decision Log

Append-only. One entry per non-trivial technical decision, added **at the time the decision is made**
— not reconstructed later from memory. See `RULES.md` Rule D. Newest entries at the bottom.

Format:
```markdown
## [Phase <n>] <short decision title>
**Date:** <date>
**Decision:** <what was decided>
**Rationale:** <why, including alternatives considered and rejected>
**Reversible?** <yes/no — and what it would take to reverse it>
```

---

## [Phase 0] Use synthetic data for initial ML training
**Date:** repo initialization
**Decision:** Train Model A/B on a generated synthetic dataset (per-category price-elasticity curves
plus noise, seeded for reproducibility) rather than waiting for or fabricating real retailer history.
**Rationale:** No real retailer POS history is available at project start. Synthetic data lets the ML
pipeline be built and demoed honestly, labeled as such, rather than presenting placeholder numbers as
real. The model interface is designed so real data can be swapped in later without changing the
scoring API.
**Reversible?** Yes — swapping in real data requires no interface change, only a new training dataset
and a retrain.

## [Phase 0] PostgreSQL + PostGIS as the single source of truth
**Date:** repo initialization
**Decision:** Use one PostgreSQL instance (with the PostGIS extension) for both relational/transactional
data (stores, batches, claims) and geospatial radius queries (geofencing, delivery-fee distance calc),
rather than a separate geospatial datastore.
**Rationale:** Avoids operating two databases under a short timeline; PostGIS is mature enough for the
radius-query volume this project needs; keeps transactional integrity (claims/reservations) and
geospatial queries in the same consistency boundary.
**Reversible?** Yes, but costly later — would require a data-layer split if geospatial query volume
ever outgrows a single Postgres instance. Not a near-term concern at hackathon/early-product scale.

## [Phase 0] Redis TTL keys as the reservation-locking mechanism
**Date:** repo initialization
**Decision:** Use a Redis key with a TTL (`reserved_until`) per batch as the single mechanism preventing
double-claims, rather than a database-row lock or a separate distributed-lock service.
**Rationale:** Redis is already in the stack as the Celery broker, so this adds no new infrastructure.
TTL expiry naturally implements "reservation times out after N minutes" without extra cleanup logic.
**Reversible?** Yes, but any future locking mechanism must be a full replacement, not a second
competing lock — see `ARCHITECTURE.md` §6.

---

_Add new entries below this line as decisions are made._
