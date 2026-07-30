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

## ADR 003: ML Expiration Risk & Dynamic Discount Architecture (Phase 2)
- **Context**: Need automated, objective price markdown recommendations based on perishable food timelines, stock volumes, margin constraints, and environmental factors.
- **Decision**:
  - Scikit-Learn Multi-Output `RandomForestRegressor` pipeline preprocessed with `ColumnTransformer` (StandardScaler + OneHotEncoder).
  - Synthetic food batch training data generator (`app/ml/synthetic_data.py`) to ensure deterministic offline training capability.
  - Model serialization using `joblib` stored at `app/ml/artifacts/pricing_model.joblib`.
  - Automatic initial training on app startup if artifact is missing.
  - Ambient temperature integration via `app/services/weather.py` (OpenWeather API with 25.0°C default fallback).
- **Status**: Implemented & Verified.

## ADR 004: Standing Order Engine & NGO Priority Allocation (Phase 4)
- **Context**: Shelters and NGOs require reliable, priority access to expiring food batches without competing in consumer payment loops.
- **Decision**:
  - Implement rule-based `StandingOrder` subscription model (`category_filter`, `min_quantity`, `priority_window_hours`).
  - Create dedicated `StandingOrderMatch` priority allocation entities (`is_subsidized=True`, `status="RESERVED"`), bypassing payment processing entirely for shelter claims.
  - Provide automated evaluation trigger endpoint (`POST /api/v1/standing-orders/evaluate`) to scan candidate active/discounted batches against standing order rules.
- **Status**: Implemented & Verified.

## ADR 005: Notification Engine Architecture & Inbound SMS Claiming (Phase 3)
- **Context**: Need hyper-local outbound flash-sale notification dispatch (SMS & WhatsApp via Twilio) and frictionless inbound SMS reply claiming ("reply YES").
- **Decision**:
  - Implement `TwilioNotificationService` (`app/services/notification.py`) supporting both SMS and WhatsApp channels.
  - Automatic fallback to mock message IDs when Twilio API credentials are unset or invalid in local testing.
  - Inbound Twilio webhook handler (`POST /api/v1/notifications/twilio-inbound`) parsing "YES" or "CLAIM <batch_id>" to automatically reserve food rescue items.
  - Asynchronous background dispatch task `dispatch_batch_notifications_task` in `app/tasks/dispatch.py` for Celery worker execution off the HTTP request path.
- **Status**: Implemented & Verified.


