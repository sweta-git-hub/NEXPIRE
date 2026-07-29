"""
Populates demo stores + batches so the app is demo-ready from a clean
clone. Run from inside the api container:

    docker compose exec api python scripts/seed.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine

DEMO_STORES = [
    # (name, lon, lat)  -- Note PostGIS point order is (lon, lat)
    ("GreenMart - Sector 12", 77.0810, 28.6100),
    ("FreshCo Express", 77.0920, 28.6250),
]

DEMO_BATCHES = [
    # (sku, product_name, category, qty, unit_cost, retail_price, hours_to_expiry)
    ("MILK-1L-001", "Whole Milk 1L", "dairy", 24, 30, 55, 20),
    ("YOG-500G-002", "Greek Yogurt 500g", "dairy", 15, 40, 85, 30),
    ("BRD-WHT-003", "Whole Wheat Bread", "bakery", 18, 20, 45, 12),
    ("BAN-BUNCH-004", "Banana Bunch", "produce", 40, 15, 35, 48),
]


def run():
    with engine.begin() as conn:
        store_ids = []
        for name, lon, lat in DEMO_STORES:
            result = conn.execute(
                text(
                    """
                    INSERT INTO stores (name, location)
                    VALUES (:name, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    RETURNING id
                    """
                ),
                {"name": name, "lon": lon, "lat": lat},
            )
            store_ids.append(result.scalar())
            print(f"Created store: {name}")

        now = datetime.now(timezone.utc)
        for store_id in store_ids:
            for sku, product_name, category, qty, cost, price, hrs in DEMO_BATCHES:
                expiry = now + timedelta(hours=hrs)
                conn.execute(
                    text(
                        """
                        INSERT INTO batches
                            (store_id, sku, product_name, category, quantity,
                             unit_cost, retail_price, current_price, expiry_date)
                        VALUES
                            (:store_id, :sku, :product_name, :category, :qty,
                             :cost, :price, :price, :expiry)
                        """
                    ),
                    {
                        "store_id": store_id,
                        "sku": sku,
                        "product_name": product_name,
                        "category": category,
                        "qty": qty,
                        "cost": cost,
                        "price": price,
                        "expiry": expiry,
                    },
                )
        print(f"Seeded {len(store_ids) * len(DEMO_BATCHES)} batches.")


if __name__ == "__main__":
    run()
