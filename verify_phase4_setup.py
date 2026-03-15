"""
Phase 4 Setup Verification Script

Verifies:
1. All required packages installed
2. Environment variables configured
3. Redis is running
4. PostgreSQL connection works
5. Database tables exist
6. Celery configuration is valid
7. All Phase 4 modules are importable
"""

import sys
import os
from pathlib import Path

# Add vireon to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_packages():
    """Verify all required packages are installed."""
    print_section("1. CHECKING REQUIRED PACKAGES")
    
    required_packages = [
        ("celery", "Celery 5.5+"),
        ("redis", "Redis Python client"),
        ("psycopg2", "PostgreSQL adapter"),
        ("sqlalchemy", "SQLAlchemy ORM"),
        ("pydantic", "Pydantic validation"),
        ("httpx", "HTTP client"),
        ("flower", "Celery monitoring UI"),
    ]
    
    all_installed = True
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package:20} ({description})")
        except ImportError:
            print(f"  ✗ {package:20} NOT INSTALLED")
            all_installed = False
    
    return all_installed


def check_environment():
    """Verify environment variables are set."""
    print_section("2. CHECKING ENVIRONMENT VARIABLES")
    
    required_vars = {
        "DATABASE_URL": "PostgreSQL connection string",
        "REDIS_URL": "Redis connection string",
        "BACKEND_URL": "FastAPI backend URL (default: http://localhost:8000)",
        "COMPANY_NAME": "Company name for alerts",
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show masked value for sensitive vars
            if "PASSWORD" in var or "KEY" in var:
                display = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                display = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✓ {var:20} = {display}")
        else:
            print(f"  ✗ {var:20} NOT SET (required: {description})")
            all_set = False
    
    return all_set


def check_redis():
    """Verify Redis is running and accessible."""
    print_section("3. CHECKING REDIS CONNECTION")
    
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        ping_result = r.ping()
        print(f"  ✓ Connected to Redis at {redis_url}")
        print(f"  ✓ Ping response: {ping_result}")
        return True
    except Exception as e:
        print(f"  ✗ Redis connection failed: {e}")
        print(f"    Start Redis: redis-server")
        print(f"    Or Docker: docker run -d -p 6379:6379 redis:7-alpine")
        return False


def check_postgresql():
    """Verify PostgreSQL is running and accessible."""
    print_section("4. CHECKING POSTGRESQL CONNECTION")
    
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print(f"  ✗ DATABASE_URL not set")
            return False
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"  ✓ Connected to PostgreSQL")
        print(f"  ✓ Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"  ✗ PostgreSQL connection failed: {e}")
        print(f"    Verify DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
        return False


def check_database_schema():
    """Verify required tables exist in PostgreSQL."""
    print_section("5. CHECKING DATABASE SCHEMA")
    
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('alerts', 'alert_thresholds', 'anomaly_runs')
        """)
        tables = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        required_tables = {"alerts", "alert_thresholds", "anomaly_runs"}
        
        for table in sorted(required_tables):
            if table in tables:
                print(f"  ✓ {table} table exists")
            else:
                print(f"  ✗ {table} table NOT FOUND")
        
        if required_tables.issubset(tables):
            return True
        else:
            print(f"\n  Run migrations: python backend/anomaly/migrations/run_migrations.py")
            return False
    
    except Exception as e:
        print(f"  ✗ Schema check failed: {e}")
        return False


def check_celery_config():
    """Verify Celery configuration is valid."""
    print_section("6. CHECKING CELERY CONFIGURATION")
    
    try:
        from backend.anomaly.celery_app import app as celery_app
        
        print(f"  ✓ Celery app imported successfully")
        print(f"  ✓ Broker: {celery_app.conf.broker_url}")
        print(f"  ✓ Backend: {celery_app.conf.result_backend}")
        print(f"  ✓ Timezone: {celery_app.conf.timezone}")
        print(f"  ✓ Task time limit: {celery_app.conf.task_time_limit}s")
        
        beat_schedule = celery_app.conf.beat_schedule
        print(f"  ✓ Beat schedule tasks: {len(beat_schedule)}")
        for task_name in sorted(beat_schedule.keys()):
            print(f"    - {task_name}")
        
        return True
    except Exception as e:
        print(f"  ✗ Celery configuration failed: {e}")
        return False


def check_modules():
    """Verify all Phase 4 modules are importable."""
    print_section("7. CHECKING PHASE 4 MODULES")
    
    modules = [
        ("backend.anomaly.celery_app", "Celery configuration"),
        ("backend.anomaly.scanner", "Anomaly scanner"),
        ("backend.anomaly.tasks", "Celery tasks"),
    ]
    
    all_modules_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:35} ({description})")
        except Exception as e:
            print(f"  ✗ {module_name:35} ERROR: {e}")
            all_modules_ok = False
    
    return all_modules_ok


def check_file_structure():
    """Verify Phase 4 directory structure."""
    print_section("8. CHECKING FILE STRUCTURE")
    
    required_files = [
        "backend/anomaly/__init__.py",
        "backend/anomaly/celery_app.py",
        "backend/anomaly/scanner.py",
        "backend/anomaly/tasks.py",
        "backend/anomaly/test_anomaly.py",
        "backend/anomaly/migrations/__init__.py",
        "backend/anomaly/migrations/001_create_alerts.sql",
        "backend/anomaly/migrations/run_migrations.py",
        "PHASE_4_README.md",
    ]
    
    base_path = Path(__file__).parent.parent.parent
    all_exist = True
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✓ {file_path:50} ({size:,} bytes)")
        else:
            print(f"  ✗ {file_path:50} NOT FOUND")
            all_exist = False
    
    return all_exist


def print_summary(results):
    """Print verification summary."""
    print("\n" + "=" * 70)
    print("  VERIFICATION SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {check}")
    
    print("\n" + "=" * 70)
    print(f"  Result: {passed}/{total} checks passed")
    print("=" * 70)
    
    return failed == 0


def print_next_steps(results):
    """Print next steps based on verification results."""
    print("\nNEXT STEPS:")
    print("-" * 70)
    
    if results.get("packages"):
        print("✓ Packages installed")
    else:
        print("✗ Install packages:")
        print("  pip install -r backend/requirements.txt")
    
    if results.get("environment"):
        print("✓ Environment variables set")
    else:
        print("✗ Set environment variables (see .env.example):")
        print("  DATABASE_URL=postgresql://...")
        print("  REDIS_URL=redis://...")
    
    if results.get("redis"):
        print("✓ Redis is running")
    else:
        print("✗ Start Redis:")
        print("  redis-server")
        print("  or: docker run -d -p 6379:6379 redis:7-alpine")
    
    if results.get("postgresql"):
        print("✓ PostgreSQL is running")
    else:
        print("✗ Verify PostgreSQL connection:")
        print("  psql $DATABASE_URL")
    
    if results.get("schema"):
        print("✓ Database schema is ready")
    else:
        print("✗ Run migrations:")
        print("  python backend/anomaly/migrations/run_migrations.py")
    
    if all(results.values()):
        print("\n" + "=" * 70)
        print("ALL CHECKS PASSED! Ready to start Phase 4:")
        print("=" * 70)
        print("\nStart Celery components (in separate terminals):")
        print("  Terminal 1: celery -A backend.anomaly.celery_app worker --loglevel=info")
        print("  Terminal 2: celery -A backend.anomaly.celery_app beat --loglevel=info")
        print("  Terminal 3: celery -A backend.anomaly.celery_app flower --port=5555")
        print("  Terminal 4: uvicorn backend.main:app --reload --port 8000")
        print("\nThen:")
        print("  • Flower dashboard: http://localhost:5555")
        print("  • FastAPI docs: http://localhost:8000/docs")
        print("  • Test scan: python backend/anomaly/scanner.py")


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 4: ANOMALY DETECTION - SETUP VERIFICATION" + " " * 6 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        "packages": check_packages(),
        "environment": check_environment(),
        "redis": check_redis(),
        "postgresql": check_postgresql(),
        "schema": check_database_schema(),
        "celery": check_celery_config(),
        "modules": check_modules(),
        "files": check_file_structure(),
    }
    
    all_ok = print_summary(results)
    print_next_steps(results)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
