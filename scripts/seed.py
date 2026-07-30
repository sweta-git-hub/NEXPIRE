"""
Populates demo stores, batches, and standing orders from the generated
seed_demo_subset synthetic files. Run from inside the api container:

    docker compose exec api python scripts/seed.py
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.db import engine

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run():
    # Detect the correct path to the output directory
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "seed_demo_subset")
    if not os.path.exists(base_path):
        base_path = "/app/output/seed_demo_subset"

    print(f"Loading seed data from: {base_path}")

    stores_df = pd.read_csv(os.path.join(base_path, "stores.csv"))
    products_df = pd.read_csv(os.path.join(base_path, "products.csv"))
    batches_df = pd.read_csv(os.path.join(base_path, "batches.csv"))
    batches_df = batches_df.merge(products_df, on="sku_id", how="inner")
    ngo_df = pd.read_csv(os.path.join(base_path, "ngo_standing_orders.csv"))

    with engine.begin() as conn:
        # Clear existing data to avoid conflicts
        print("Clearing existing batches, standing orders, and stores...")
        conn.execute(text("TRUNCATE TABLE batches CASCADE"))
        conn.execute(text("TRUNCATE TABLE standing_orders CASCADE"))
        conn.execute(text("TRUNCATE TABLE stores CASCADE"))

        # 1. Insert Stores
        store_map = {}  # store_id (CSV) -> database id (PK)
        for _, row in stores_df.iterrows():
            result = conn.execute(
                text(
                    """
                    INSERT INTO stores (name, address, location_lat, location_lng, created_at, updated_at)
                    VALUES (:name, :address, :lat, :lng, NOW(), NOW())
                    RETURNING id
                    """
                ),
                {
                    "name": row["store_name"],
                    "address": f"{row['city']}, {row['state']}, India",
                    "lat": float(row["latitude"]),
                    "lng": float(row["longitude"]),
                },
            )
            db_id = result.scalar()
            store_map[row["store_id"]] = db_id
            print(f"Created store: {row['store_name']} in {row['city']} (ID: {db_id})")

        # 2. Insert NGO Standing Orders (Rescue Squads)
        for _, row in ngo_df.iterrows():
            # Get first category from category_priority (split by | if needed)
            cats = str(row["category_priority"]).split("|")
            cat_filter = cats[0] if cats else "ALL"

            conn.execute(
                text(
                    """
                    INSERT INTO standing_orders 
                        (ngo_name, contact_email, contact_phone, category_filter, 
                         min_quantity, priority_window_hours, is_active, created_at, updated_at)
                    VALUES 
                        (:ngo_name, :contact_email, :contact_phone, :category_filter, 
                         :min_quantity, :priority_window_hours, :is_active, NOW(), NOW())
                    """
                ),
                {
                    "ngo_name": row["ngo_name"],
                    "contact_email": f"contact@{row['ngo_name'].lower().replace(' ', '')}.org",
                    "contact_phone": "+919876543210",
                    "category_filter": cat_filter,
                    "min_quantity": int(row["min_quantity_kg"]),
                    "priority_window_hours": int(row["priority_time_window_hours"]),
                    "is_active": True if row["verified_status"] == "verified" else False,
                },
            )
            print(f"Created standing order for NGO: {row['ngo_name']} ({cat_filter})")

        # 3. Insert Batches
        now = datetime.now(timezone.utc)
        batch_count = 0
        for _, row in batches_df.iterrows():
            csv_store_id = row["store_id"]
            if csv_store_id not in store_map:
                continue
            db_store_id = store_map[csv_store_id]

            # Adjust dates relative to now to make them fresh for live demo
            # received_date and expiry_date are relative
            expiry_dt = datetime.fromisoformat(row["expiry_date"]).replace(tzinfo=timezone.utc)
            received_dt = datetime.fromisoformat(row["received_date"]).replace(tzinfo=timezone.utc)
            delta_days = (expiry_dt - received_dt).days
            
            # Make expiry fresh: 1 to 5 days from now
            new_expiry = now + timedelta(days=float(row["batch_id"].split("-")[-1]) % 4 + 1)
            new_received = new_expiry - timedelta(days=max(1, delta_days))

            category = row["category"]

            conn.execute(
                text(
                    """
                    INSERT INTO batches
                        (store_id, sku, product_name, category, quantity,
                         cost_price, original_selling_price, current_price, expiration_date, created_at, updated_at)
                    VALUES
                        (:store_id, :sku, :product_name, :category, :qty,
                         :cost, :orig_price, :curr_price, :expiry, NOW(), NOW())
                    """
                ),
                {
                    "store_id": db_store_id,
                    "sku": row["sku_id"],
                    "product_name": row["product_name"],
                    "category": category,
                    "qty": int(row["quantity_received"]),
                    "cost": float(row["unit_cost_inr"]) if "unit_cost_inr" in row else 10.0,
                    "orig_price": float(row["current_price_inr"]),
                    "curr_price": float(row["current_price_inr"]),
                    "expiry": new_expiry.date(),
                },
            )
            batch_count += 1

        print(f"Seeded {batch_count} batches successfully.")


if __name__ == "__main__":
    run()
