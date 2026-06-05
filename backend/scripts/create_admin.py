"""
create_admin.py — CLI script to create an admin user directly in the DB.
Use this for bootstrapping the first admin account before any UI exists.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email admin@example.com --username admin --password secret

Change Tracker:
v1.0 — initial
"""

import sys
import argparse
from pathlib import Path

# ── Allow imports from backend root ───────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.database import fn_create_all_tables
from config.security import fn_hash_password
from config.logging_config import fn_setup_logging, logger
from database.session import fn_get_standalone_db
from database.crud_users import fn_get_user_by_email, fn_create_user


def fn_create_admin(email: str, username: str, password: str) -> None:
    fn_setup_logging()
    fn_create_all_tables()

    db = fn_get_standalone_db()
    try:
        var_existing = fn_get_user_by_email(db, email)
        if var_existing:
            print(f"[ERROR] User with email '{email}' already exists.")
            print(f"        Current role: {var_existing.user_role}")
            if var_existing.user_role != "admin":
                print("        Promoting to admin...")
                from database.crud_users import fn_update_user
                fn_update_user(db, var_existing.user_id, user_role="admin")
                print("        Done — user promoted to admin.")
            return

        var_hashed = fn_hash_password(password)
        var_user = fn_create_user(
            db=db,
            user_name=username,
            user_email=email,
            hashed_password=var_hashed,
            user_role="admin",
        )
        # Auto-verify admin accounts
        from database.crud_users import fn_update_user
        fn_update_user(db, var_user.user_id, is_verified=True)

        print(f"[OK] Admin user created:")
        print(f"     user_id  : {var_user.user_id}")
        print(f"     email    : {email}")
        print(f"     username : {username}")
        print(f"     role     : admin")
        logger.info(f"Admin user created: id={var_user.user_id} email={email}")

    except Exception as e:
        print(f"[ERROR] Failed to create admin: {e}")
        logger.error(f"create_admin failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email",    default="admin@securedoc.local")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="Admin@1234")
    args = parser.parse_args()

    print(f"Creating admin user: {args.email}")
    fn_create_admin(
        email=args.email,
        username=args.username,
        password=args.password,
    )


if __name__ == "__main__":
    main()