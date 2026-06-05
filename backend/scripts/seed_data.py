"""
seed_data.py — Seed the database with sample users and documents for development.
Do NOT run this in production.

Usage:
    python scripts/seed_data.py

Change Tracker:
v1.0 — initial
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.logging_config import fn_setup_logging, logger
from config.database import fn_create_all_tables
from config.security import fn_hash_password
from database.session import fn_get_standalone_db
from database.crud_users import fn_get_user_by_email, fn_create_user, fn_update_user


SEED_USERS = [
    {
        "user_name": "admin",
        "user_email": "admin@securedoc.local",
        "password": "Admin@1234",
        "user_role": "admin",
        "is_verified": True,
    },
    {
        "user_name": "alice",
        "user_email": "alice@securedoc.local",
        "password": "User@1234",
        "user_role": "user",
        "is_verified": True,
    },
    {
        "user_name": "bob",
        "user_email": "bob@securedoc.local",
        "password": "User@1234",
        "user_role": "user",
        "is_verified": False,  # Unverified user for testing
    },
]


def fn_seed_users(db) -> None:
    print("\n── Seeding users ────────────────────────────────────")
    for var_data in SEED_USERS:
        var_existing = fn_get_user_by_email(db, var_data["user_email"])
        if var_existing:
            print(f"  [SKIP] {var_data['user_email']} already exists")
            continue

        var_user = fn_create_user(
            db=db,
            user_name=var_data["user_name"],
            user_email=var_data["user_email"],
            hashed_password=fn_hash_password(var_data["password"]),
            user_role=var_data["user_role"],
        )
        fn_update_user(db, var_user.user_id, is_verified=var_data["is_verified"])
        print(
            f"  [OK]   {var_data['user_email']} "
            f"(role={var_data['user_role']}, "
            f"verified={var_data['is_verified']})"
        )
        logger.info(f"Seed user created: {var_data['user_email']}")


def main():
    fn_setup_logging()
    fn_create_all_tables()

    db = fn_get_standalone_db()
    try:
        fn_seed_users(db)
        print("\nSeed complete.")
    except Exception as e:
        print(f"\n[ERROR] Seed failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()