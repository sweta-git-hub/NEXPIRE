import os
import sys

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.user import User
from app.models.store import Store
from app.core.security import hash_password


def seed_users():
    db: Session = SessionLocal()
    try:
        # Check existing stores
        stores = db.query(Store).order_by(Store.id).limit(2).all()
        store_1_id = stores[0].id if len(stores) > 0 else None
        store_2_id = stores[1].id if len(stores) > 1 else None

        users_to_seed = [
            {
                "email": "admin@nexpire.org",
                "phone_number": "+18005550199",
                "password": "AdminPassword123!",
                "full_name": "NEXPIRE Platform Admin",
                "role": "admin",
                "store_id": None,
            },
            {
                "email": "metro.manager@nexpire.org",
                "phone_number": "+18005550101",
                "password": "VendorPassword123!",
                "full_name": "Downtown Market Manager",
                "role": "vendor",
                "store_id": store_1_id,
            },
            {
                "email": "green.grocer@nexpire.org",
                "phone_number": "+18005550102",
                "password": "VendorPassword123!",
                "full_name": "Green Grocer Store Owner",
                "role": "vendor",
                "store_id": store_2_id,
            },
            {
                "email": "customer@nexpire.org",
                "phone_number": "+919876543210",
                "password": None,
                "full_name": "Priya Sharma (Community Rescuer)",
                "role": "customer",
                "store_id": None,
            },
        ]

        print("--- Seeding Sample Users ---")
        for u in users_to_seed:
            existing = db.query(User).filter(
                (User.email == u["email"]) | (User.phone_number == u["phone_number"])
            ).first()

            hashed = hash_password(u["password"]) if u["password"] else None

            if existing:
                existing.hashed_password = hashed or existing.hashed_password
                existing.role = u["role"]
                existing.store_id = u["store_id"]
                existing.full_name = u["full_name"]
                existing.is_active = True
                print(f"Updated user: {u['email'] or u['phone_number']} (Role: {u['role']})")
            else:
                new_user = User(
                    email=u["email"],
                    phone_number=u["phone_number"],
                    hashed_password=hashed,
                    full_name=u["full_name"],
                    role=u["role"],
                    store_id=u["store_id"],
                    is_active=True,
                )
                db.add(new_user)
                print(f"Created user: {u['email'] or u['phone_number']} (Role: {u['role']})")

        db.commit()
        print("Successfully seeded all sample users!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
