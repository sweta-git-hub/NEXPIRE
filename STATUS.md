# NEXPIRE Project Status

## Current Phase: ALL PHASES COMPLETED (Phase 0 - Phase 7)

### Phase 7 Summary
Phase 7 delivers the Analytics & Waste Reduction Dashboard, quantifying environmental impact (food waste prevented in kg, CO2 emissions offset in kg), financial recovery metrics, NGO standing order allocations, and claim conversion rates across individual stores and platform-wide.

- **Analytics Service** (`app/services/analytics.py`): Platform-wide and store-specific metrics aggregation for waste reduction (0.5 kg waste / item rescued), CO2e savings (2.5 kg CO2e / kg food waste), revenue recovered, and NGO subsidized allocations.
- **REST Endpoints**:
  - `GET /api/v1/analytics/summary`: Platform-wide waste impact, financial recovery, CO2 savings, and NGO metrics.
  - `GET /api/v1/analytics/store/{store_id}`: Store-level breakdown of active, expired, and rescued batches with total revenue recovered.
- **Testing**: 36 total test suites passing across all 7 phases.

### Phase 6 Summary
Phase 6 implements the Multi-rail Payment engine supporting both Razorpay (INR/paise) and Stripe (USD/cents) checkout flows, signature-verified webhooks, and an automatic payment bypass for subsidized NGO/shelter allocations.

- **Payment Service** (`app/services/payment.py`): Multi-provider checkout order creation (Razorpay Orders API & Stripe Checkout Sessions) with automatic mock fallback when live credentials are not supplied. Webhook HMAC signature verification for both rails.
- **Subsidized NGO Bypass**: NGO standing order allocations marked `is_subsidized=True` skip payment processing completely, immediately resolving to status `PAID` with payment reference `SUBSIDIZED_BYPASS`.
- **REST Endpoints**:
  - `POST /api/v1/payments/checkout-session`: Initiate Razorpay or Stripe payment for a reserved claim.
  - `POST /api/v1/payments/webhooks/razorpay`: Handle Razorpay `payment.captured` webhooks & transition claim to `PAID`.
  - `POST /api/v1/payments/webhooks/stripe`: Handle Stripe `checkout.session.completed` webhooks & transition claim to `PAID`.
- **Testing**: 32 total test suites passing across all phases.

### Phase 5 Summary
Phase 5 implements the Consumer Marketplace with geo-fenced batch discovery and high-concurrency Redis TTL reservation locking for atomic claim management.

- **Claim Model** (`app/models/claim.py`): Tokenized claim records with `claim_token`, `reserved_until` TTL timestamp, `fulfillment_type` (pickup/delivery), `status` (RESERVED/PAID/FULFILLED/CANCELLED), and `is_subsidized` flag for NGO bypass.
- **Redis Reservation Lock** (`app/services/reservation.py`): Atomic `SET NX EX` Redis key per batch — single source of truth for concurrency safety, auto-released on payment confirmation or expiry.
- **PostGIS Geo-fenced Search** (`app/services/geo_routing.py`): `ST_DWithin` geography query returning nearby active/discounted batches within a configurable radius (km) with Python haversine fallback.
- **REST Endpoints**:
  - `POST /api/v1/claims/geo-search`: Geo-fenced marketplace search by lat/lng + radius.
  - `POST /api/v1/claims`: Create tokenized reservation with Redis TTL lock.
  - `GET /api/v1/claims/{token}`: Resolve a tokenized claim link.
  - `GET /api/v1/claims/batch/{batch_id}`: Fetch active reservation for a batch.
  - `PATCH /api/v1/claims/{token}`: Update claim status (e.g., PAID, FULFILLED).
  - `GET /api/v1/claims/lock-status/{batch_id}`: Inspect Redis reservation lock.
- **Testing**: 27 total test suites passing across all phases.

### Phase 3 Summary
Phase 3 implements the Notification Engine using Twilio (SMS & WhatsApp Business API), enabling hyper-local flash sale alerts, background broadcast dispatch, and single-tap "reply YES" SMS claiming.

- **Notification Service**: `TwilioNotificationService` in `app/services/notification.py` handling SMS dispatch, WhatsApp messaging, and batch flash-sale broadcasts (with automatic mock fallback when live credentials are not set).
- **Asynchronous Worker Tasks**: Celery background task `dispatch_batch_notifications_task` in `app/tasks/dispatch.py`.
- **REST Endpoints**:
  - `POST /api/v1/notifications/send`: Outbound SMS or WhatsApp dispatch to a recipient.
  - `POST /api/v1/notifications/broadcast/{batch_id}`: Trigger hyper-local flash sale broadcast.
  - `POST /api/v1/notifications/twilio-inbound`: Handle inbound Twilio webhooks for single-tap "reply YES" claiming.
- **Testing**: 17 total test suites passing across inventory, ML pricing, standing orders, and notifications.

---

## Phase Roadmap Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Docker & Postgres/Redis Infrastructure | ✅ Completed |
| Phase 1 | Inventory Core (Stores, Batches, CSV Upload) | ✅ Completed |
| Phase 2 | ML Expiration Risk Model & Dynamic Discounting | ✅ Completed |
| Phase 3 | Notification Engine (SMS, WhatsApp, Twilio) | ✅ Completed |
| Phase 4 | Standing Order Engine (NGO & Shelter priority) | ✅ Completed |
| Phase 5 | Consumer Marketplace & Geo-routing | ✅ Completed |
| Phase 6 | Multi-rail Payments (Stripe & Razorpay) | ✅ Completed |
| Phase 7 | Analytics Dashboard & Final Hardening | ✅ Completed |


