# Architecture Decision Records (ADR)

## ADR 001: Project Rebranding to NEXPIRE
- **Context**: Project named ResQ-Chain renamed to NEXPIRE across codebase, configuration, and documentation.
- **Decision**: Update all docker service names, environment variables, documentation, and API metadata to `NEXPIRE`.
- **Status**: Implemented & Verified.

## ADR 002: Inventory Core Architecture (Phase 1)
- **Context**: Need high-throughput CRUD for retail store inventory management and bulk CSV imports.
- **Decision**: 
  - Use SQLAlchemy ORM with PostgreSQL backend for persistent storage.
  - Implement Pydantic v2 schemas for strict request/response data validation.
  - Automatic `current_price` calculation based on `discount_percentage` when `current_price` is omitted.
  - Streamed CSV parsing using standard library `csv.DictReader` and row-level rollback handling to return clear import error diagnostics without failing valid rows.
- **Status**: Implemented & Verified.
