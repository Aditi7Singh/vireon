#!/usr/bin/env python3
"""
setup_merge_integration.py

Automated setup script for Merge.dev integration.
Checks environment, validates credentials, runs health checks.

Usage:
    python setup_merge_integration.py
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{BLUE}ℹ {text}{RESET}")


def check_environment_variables() -> Tuple[bool, dict]:
    """Check if required environment variables are set."""
    print_header("1. Checking Environment Variables")
    
    required_vars = {
        "MERGE_API_KEY": "Merge.dev API key",
        "MERGE_ACCOUNT_TOKEN": "Merge.dev account token",
        "DATA_SOURCE": "Data source (merge|erpnext)",
        "DATABASE_URL": "Database connection string",
    }
    
    env_vars = {}
    all_set = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            env_vars[var] = value
            # Mask sensitive values
            display_value = value[:10] + "..." if len(value) > 13 else value
            print_success(f"{var} is set ({description})")
        else:
            print_error(f"{var} not set ({description})")
            all_set = False
    
    return all_set, env_vars


def check_python_imports() -> bool:
    """Check if required Python packages are available."""
    print_header("2. Checking Python Dependencies")
    
    required_packages = {
        "fastapi": "FastAPI",
        "sqlalchemy": "SQLAlchemy",
        "celery": "Celery",
        "redis": "Redis",
        "requests": "Requests",
        "pydantic": "Pydantic",
    }
    
    all_available = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print_success(f"{name} is installed")
        except ImportError:
            print_error(f"{name} is NOT installed")
            all_available = False
    
    return all_available


def check_merge_client() -> bool:
    """Check if Merge client can be imported."""
    print_header("3. Checking Merge Client")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from integrations.merge_client import get_merge_client
        print_success("Merge client imported successfully")
        return True
    except ImportError as e:
        print_error(f"Cannot import Merge client: {e}")
        return False


def test_merge_connectivity() -> bool:
    """Test connection to Merge.dev API."""
    print_header("4. Testing Merge.dev API Connection")
    
    merge_api_key = os.getenv("MERGE_API_KEY")
    merge_account_token = os.getenv("MERGE_ACCOUNT_TOKEN")
    
    if not merge_api_key or not merge_account_token:
        print_warning("Skipping API test: credentials not set")
        return False
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from integrations.merge_client import get_merge_client
        
        client = get_merge_client(merge_api_key, merge_account_token)
        
        print_info("Testing health check...")
        if client.health_check():
            print_success("Merge.dev API is reachable and responding")
            return True
        else:
            print_error("Merge.dev API health check failed")
            return False
            
    except Exception as e:
        print_error(f"API connection test failed: {e}")
        return False


def check_database() -> bool:
    """Check database connection."""
    print_header("5. Checking Database Connection")
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print_warning("DATABASE_URL not configured")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(database_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print_success("Database connection successful")
            
            # Check for required tables
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
                table_count = result.scalar()
                print_info(f"Found {table_count} tables in database")
            except:
                pass
            
            return True
            
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


def check_redis() -> bool:
    """Check Redis connection (optional, for Celery)."""
    print_header("6. Checking Redis (Optional)")
    
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    
    try:
        import redis
        conn = redis.from_url(redis_url)
        conn.ping()
        print_success("Redis is running and accessible")
        return True
    except Exception as e:
        print_warning(f"Redis not available: {e}")
        print_info("This is optional; Celery tasks will be queued in database if Redis unavailable")
        return False


def check_backend_files() -> bool:
    """Check if critical backend files exist."""
    print_header("7. Checking Backend Files")
    
    backend_path = Path(__file__).parent / "backend"
    required_files = {
        "main.py": "FastAPI application",
        "integrations/merge_client.py": "Merge.dev client",
        "tasks.py": "Celery tasks",
        "models.py": "Database models",
        "schemas.py": "Pydantic schemas",
    }
    
    all_exist = True
    for file, description in required_files.items():
        file_path = backend_path / file
        if file_path.exists():
            print_success(f"{file} exists ({description})")
        else:
            print_error(f"{file} NOT found ({description})")
            all_exist = False
    
    return all_exist


def generate_env_file() -> bool:
    """Generate .env file from template if it doesn't exist."""
    print_header("8. Environment Configuration")
    
    env_file = Path(__file__).parent / ".env"
    env_template = Path(__file__).parent / ".env.merge.example"
    
    if env_file.exists():
        print_success(".env file already exists")
        return True
    
    if env_template.exists():
        print_info("Creating .env from .env.merge.example template...")
        try:
            env_file.write_text(env_template.read_text())
            print_success(".env file created from template")
            print_warning("⚠ Please edit .env and add your Merge.dev credentials:")
            print(f"   - MERGE_API_KEY: Get from https://app.merge.dev/settings/api")
            print(f"   - MERGE_ACCOUNT_TOKEN: Generated when linking accounting system")
            return True
        except Exception as e:
            print_error(f"Failed to create .env file: {e}")
            return False
    else:
        print_warning(".env.merge.example template not found")
        return False


def run_diagnostics() -> None:
    """Run all diagnostic checks."""
    print_header("MERGE.DEV INTEGRATION SETUP DIAGNOSTICS")
    
    results = {}
    
    # Check files first
    results["files"] = check_backend_files()
    
    # Check Python
    results["python"] = check_python_imports()
    results["merge_client"] = check_merge_client()
    
    # Check environment
    env_ok, env_vars = check_environment_variables()
    results["environment"] = env_ok
    
    # Generate .env if needed
    results["env_file"] = generate_env_file()
    
    # Conditional checks (only if env is set)
    if env_ok:
        results["database"] = check_database()
        results["redis"] = check_redis()
        results["merge_api"] = test_merge_connectivity()
    else:
        print_info("Skipping optional connectivity tests (environment not fully configured)")
        results["database"] = False
        results["redis"] = False
        results["merge_api"] = False
    
    # Summary
    print_header("SUMMARY")
    
    critical_checks = {
        "Backend files": results["files"],
        "Python dependencies": results["python"],
        "Merge client": results["merge_client"],
        "Environment variables": results["environment"],
    }
    
    optional_checks = {
        "Database connection": results["database"],
        "Redis connection": results["redis"],
        "Merge.dev API": results["merge_api"],
    }
    
    critical_pass = all(critical_checks.values())
    total_pass = all(results.values())
    
    print(f"\n{BOLD}Critical Checks:{RESET}")
    for check, passed in critical_checks.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {status} - {check}")
    
    print(f"\n{BOLD}Optional Checks:{RESET}")
    for check, passed in optional_checks.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}SKIP{RESET}"
        print(f"  {status} - {check}")
    
    print()
    if critical_pass:
        print_success("Critical checks PASSED - Ready for development!")
        if total_pass:
            print_success("All checks PASSED - Ready for production!")
        else:
            print_warning("Some optional checks failed - development mode ready")
    else:
        print_error("Critical checks FAILED - Please fix issues before proceeding")
        sys.exit(1)
    
    print_header("Next Steps")
    if not env_ok:
        print(f"1. Edit .env and add Merge.dev credentials")
        print(f"2. Set DATA_SOURCE=merge")
        print(f"3. Run this script again")
    else:
        print(f"1. Start Redis: redis-server")
        print(f"2. Start FastAPI: python -m uvicorn backend.main:app --reload")
        print(f"3. Start Celery worker: celery -A tasks worker --loglevel=info")
        print(f"4. Start Celery beat: celery -A tasks beat --loglevel=info")
        print(f"5. Open http://localhost:3000/dashboard")


if __name__ == "__main__":
    try:
        run_diagnostics()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup cancelled by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{RED}Setup error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
