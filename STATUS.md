# NEXPIRE Project Status

## Current Phase: Phase 2 — ML Expiration Risk Model & Dynamic Discounting (Completed)

### Phase 2 Summary
Phase 2 implements the machine learning engine for food batch expiration risk scoring and dynamic price markdown calculation.

- **Synthetic Dataset Generator**: Realistic training data simulation in `app/ml/synthetic_data.py` (perishability decay, stock levels, margins, and ambient temperature factor).
- **Scikit-Learn Regression Pipeline**: Multi-output Random Forest regressor (`app/ml/trainer.py`) trained to predict `risk_score` (0.0 to 1.0) and `suggested_discount_percentage` (0% to 90%), serialized to `pricing_model.joblib`.
- **Inference & Weather Integration**: `PricingPredictor` engine with OpenWeather API integration (`app/services/weather.py`) for temperature-driven risk scaling.
- **REST Endpoints**:
  - `POST /api/v1/ml/predict-discount`: Direct risk score & discount inference for item attributes.
  - `POST /api/v1/ml/reprice-batch/{batch_id}`: Evaluates database batch risk, applies ML discount & current price to PostgreSQL DB.
  - `POST /api/v1/ml/train`: On-demand model retraining.
- **Testing & Coverage**: 9 total test suites passing with 92% code coverage.

---

## Phase Roadmap Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Docker & Postgres/Redis Infrastructure | ✅ Completed |
| Phase 1 | Inventory Core (Stores, Batches, CSV Upload) | ✅ Completed |
| Phase 2 | ML Expiration Risk Model & Dynamic Discounting | ✅ Completed |
| Phase 3 | Notification Engine (SMS, WhatsApp, Twilio) | ⏳ Pending |
| Phase 4 | Standing Order Engine (NGO & Shelter priority) | ⏳ Pending |
| Phase 5 | Consumer Marketplace & Geo-routing | ⏳ Pending |
| Phase 6 | Multi-rail Payments (Stripe & Razorpay) | ⏳ Pending |
| Phase 7 | Analytics Dashboard & Final Hardening | ⏳ Pending |
