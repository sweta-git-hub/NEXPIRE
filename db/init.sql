-- Runs automatically on first container start (mounted into
-- /docker-entrypoint-initdb.d/ by docker-compose). If you change this
-- file after the volume already exists, you must `docker compose down -v`
-- and re-up for it to re-run.

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------- Stores ----------
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    address TEXT,
    location GEOGRAPHY(POINT, 4326),  -- PostGIS: lat/long for radius queries
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Batches (inventory) ----------
-- Columns match Playbook Ch. 12.1 - refined further in Phase 1
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    sku TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    unit_cost NUMERIC,
    retail_price NUMERIC NOT NULL,
    current_price NUMERIC NOT NULL,
    expiry_date TIMESTAMPTZ NOT NULL,
    received_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'active',  -- active | claimed | sold | expired | donated
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Users (consumers) ----------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    coarse_location GEOGRAPHY(POINT, 4326),  -- opt-in, coarse only
    reliability_score NUMERIC DEFAULT 1.0,
    category_opt_ins TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Claims ----------
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES batches(id),
    user_id UUID REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'reserved',  -- reserved | paid | fulfilled | expired | cancelled
    fulfillment_type TEXT,  -- pickup | delivery
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at TIMESTAMPTZ,
    fulfilled_at TIMESTAMPTZ
);

-- ---------- Standing orders (NGO/shelter) ----------
CREATE TABLE IF NOT EXISTS standing_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_name TEXT NOT NULL,
    category TEXT,
    min_quantity NUMERIC,
    priority_window_hours INTEGER,
    verified BOOLEAN DEFAULT false,
    delivery_capable BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_batches_store_id ON batches(store_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);
CREATE INDEX IF NOT EXISTS idx_claims_batch_id ON claims(batch_id);
CREATE INDEX IF NOT EXISTS idx_stores_location ON stores USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_users_location ON users USING GIST(coarse_location);
