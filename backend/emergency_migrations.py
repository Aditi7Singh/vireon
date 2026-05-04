#!/usr/bin/env python
"""
Emergency migration: runs on every app startup to ensure critical columns exist.
This is a safety net in case alembic migrations fail or haven't been run.
"""
import sys
import os

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text


def run_emergency_migrations():
    """Add any missing critical columns that may have been skipped by alembic."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  Emergency migration skipped: DATABASE_URL not set")
        return

    # SQLite doesn't need this (uses SQLAlchemy create_all)
    if database_url.startswith("sqlite"):
        return

    print("🔧 Running emergency migrations...")
    engine = create_engine(database_url)

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
    except Exception as e:
        print(f"⚠️  Could not inspect database: {e}")
        return

    with engine.connect() as conn:
        if "companies" in tables:
            columns = [col["name"] for col in inspector.get_columns("companies")]
            critical_additions = []

            if "settings" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN settings JSONB NULL DEFAULT '{}'"
                )
            if "last_sync_erpnext" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN last_sync_erpnext TIMESTAMP"
                )
            if "last_sync_merge" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN last_sync_merge TIMESTAMP"
                )
            if "notification_contacts" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN notification_contacts JSONB NULL"
                )
            if "alert_thresholds" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN alert_thresholds JSONB NOT NULL DEFAULT '{\"critical_months\": 3, \"warning_months\": 6}'"
                )
            if "effective_tax_rate" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN effective_tax_rate NUMERIC(5, 4) DEFAULT 0.2500"
                )
            if "stage" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN stage VARCHAR(50)"
                )
            if "initial_cash" not in columns:
                critical_additions.append(
                    "ALTER TABLE companies ADD COLUMN initial_cash NUMERIC(15, 2)"
                )

            for sql in critical_additions:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    col_name = sql.split("ADD COLUMN ")[1].split(" ")[0]
                    print(f"  ✅ Added missing column: {col_name}")
                except Exception as e:
                    # Column might already exist from a concurrent run
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        pass
                    else:
                        print(f"  ⚠️  Failed: {sql[:60]}... -> {e}")

        if "financial_ledger_entries" in tables:
            columns = [col["name"] for col in inspector.get_columns("financial_ledger_entries")]
            additions = []
            if "department" not in columns:
                additions.append(
                    "ALTER TABLE financial_ledger_entries ADD COLUMN department VARCHAR(50)"
                )
            for sql in additions:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception:
                    pass

    print("✅ Emergency migrations complete")


if __name__ == "__main__":
    run_emergency_migrations()
