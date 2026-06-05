"""
reset_database.py — Drop and recreate ALL database tables.
⚠️  DESTRUCTIVE — use only in development.

Usage:
    python scripts/reset_database.py
    python scripts/reset_database.py --yes   # Skip confirmation prompt

Change Tracker:
v1.0 — initial
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.logging_config import fn_setup_logging, logger
from config.database import engine, Base


def fn_reset_database(skip_confirm: bool = False) -> None:
    fn_setup_logging()

    if not skip_confirm:
        var_confirm = input(
            "\n⚠️  WARNING: This will DROP all tables and recreate them.\n"
            "   All data will be permanently lost.\n"
            "   Type 'yes' to continue: "
        ).strip()
        if var_confirm.lower() != "yes":
            print("Aborted.")
            return

    print("Dropping all tables...")
    logger.warning("Database reset initiated — dropping all tables")

    try:
        # Import all models so Base knows about them
        import models  # noqa: F401
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped.")

        print("Recreating tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables recreated.")

        logger.info("Database reset complete")
        print("\nDatabase reset complete. Run seed_data.py to populate test data.")

    except Exception as e:
        print(f"[ERROR] Reset failed: {e}")
        logger.error(f"fn_reset_database error: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Reset database (DESTRUCTIVE)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    fn_reset_database(skip_confirm=args.yes)


if __name__ == "__main__":
    main()