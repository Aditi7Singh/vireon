"""
Migration runner for Phase 4 anomaly detection schema.
Usage: python backend/anomaly/migrations/run_migrations.py
"""

import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_database_url():
    """Get DATABASE_URL from environment or use fallback."""
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set in environment")
        print("Set it in .env or export DATABASE_URL=postgresql://user:pass@host/dbname")
        sys.exit(1)
    return url


def run_migration(conn, migration_file):
    """Execute a single migration SQL file."""
    try:
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        
        print(f"✓ Executed: {Path(migration_file).name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"✗ Error executing {Path(migration_file).name}: {e}")
        return False


def main():
    """Run all migrations in order."""
    print("=" * 70)
    print("PHASE 4: ANOMALY DETECTION - DATABASE MIGRATIONS")
    print("=" * 70)
    
    db_url = get_database_url()
    
    try:
        conn = psycopg2.connect(db_url)
        print(f"✓ Connected to PostgreSQL via Neon.tech")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("Verify DATABASE_URL is correct: postgresql://user:pass@host/dbname")
        sys.exit(1)
    
    migration_dir = Path(__file__).parent
    migrations = sorted(migration_dir.glob("*.sql"))
    
    if not migrations:
        print("✗ No migration files found in migrations/")
        sys.exit(1)
    
    print(f"\nFound {len(migrations)} migration(s):\n")
    
    success_count = 0
    for migration_file in migrations:
        if run_migration(conn, migration_file):
            success_count += 1
    
    # Verify tables exist
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('alerts', 'alert_thresholds', 'anomaly_runs')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        print(f"\n✓ Created tables: {', '.join(sorted(tables))}")
        
        # Show alert_thresholds preview
        cursor = conn.cursor()
        cursor.execute("SELECT category, warn_pct, critical_pct FROM alert_thresholds ORDER BY category")
        thresholds = cursor.fetchall()
        cursor.close()
        
        if thresholds:
            print(f"\n✓ Alert thresholds loaded ({len(thresholds)} categories):")
            for cat, warn, crit in thresholds:
                print(f"  {cat:15} → Warning: {warn}%, Critical: {crit}%")
    
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False
    finally:
        conn.close()
    
    print("\n" + "=" * 70)
    if success_count == len(migrations):
        print(f"SUCCESS: All {success_count} migration(s) completed")
        print("=" * 70)
        return True
    else:
        print(f"PARTIAL: {success_count}/{len(migrations)} migrations completed")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
