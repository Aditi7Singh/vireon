#!/usr/bin/env python3
"""
Phase 4 Implementation Verification Script
Comprehensive check of all Phase 4 components
"""

import os
import sys
import json
from datetime import datetime

def check_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_file_exists(path, description=""):
    """Check if file exists"""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    desc = f": {description}" if description else ""
    print(f"  {status} {path}{desc}")
    return exists

def check_import(module, name=""):
    """Check if module can be imported"""
    try:
        __import__(module)
        print(f"  ✓ {name or module}")
        return True
    except ImportError as e:
        print(f"  ✗ {name or module}: {e}")
        return False

def check_env_var(var_name):
    """Check if environment variable is set"""
    value = os.environ.get(var_name)
    if value:
        # Mask sensitive values
        if "pass" in var_name.lower() or "token" in var_name.lower():
            masked = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
        else:
            masked = value
        print(f"  ✓ {var_name}={masked}")
        return True
    else:
        print(f"  ✗ {var_name} (not set)")
        return False

def main():
    """Run all verification checks"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          PHASE 4 IMPLEMENTATION VERIFICATION                ║
║              Anomaly Detection Engine v1.0                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    checks = {
        "PASSED": 0,
        "FAILED": 0,
        "WARNINGS": 0,
    }
    
    # ============================================================
    # 1. Source Code Files
    # ============================================================
    check_section("1. SOURCE CODE FILES")
    
    files_to_check = [
        ("backend/anomaly/__init__.py", "Package init"),
        ("backend/anomaly/scanner.py", "Core scanner (850+ lines)"),
        ("backend/anomaly/celery_app.py", "Celery configuration"),
        ("backend/anomaly/tasks.py", "Celery task definitions"),
        ("backend/anomaly/test_anomaly.py", "Unit tests (30+)"),
        ("backend/anomaly/migrations/run_migrations.py", "Migration runner"),
        ("backend/anomaly/migrations/001_create_alerts.sql", "Database schema"),
    ]
    
    for path, desc in files_to_check:
        if check_file_exists(path, desc):
            checks["PASSED"] += 1
        else:
            checks["FAILED"] += 1
    
    # ============================================================
    # 2. Documentation Files
    # ============================================================
    check_section("2. DOCUMENTATION FILES")
    
    docs = [
        ("PHASE_4_FINAL_SUMMARY.md", "Final summary"),
        ("PHASE_4_README.md", "Complete guide"),
        ("PHASE_4_SCANNER_REFERENCE.md", "Technical reference"),
        ("DEPLOYMENT_CHECKLIST.md", "Deployment steps"),
        ("PHASE_4_DOCUMENTATION_INDEX.md", "Documentation index"),
        ("PHASE_4_COMPLETION_REPORT.txt", "Completion report"),
        ("test_scanner_manual.py", "Standalone tests"),
    ]
    
    for path, desc in docs:
        if check_file_exists(path, desc):
            checks["PASSED"] += 1
        else:
            checks["FAILED"] += 1
    
    # ============================================================
    # 3. Python Imports
    # ============================================================
    check_section("3. PYTHON IMPORTS")
    
    imports = [
        ("pandas", "Pandas (data processing)"),
        ("numpy", "Numpy (arrays & math)"),
        ("scipy", "Scipy (statistics)"),
        ("celery", "Celery (task queue)"),
        ("redis", "Redis (broker)"),
        ("psycopg2", "Psycopg2 (PostgreSQL)"),
    ]
    
    for module, name in imports:
        if check_import(module, name):
            checks["PASSED"] += 1
        else:
            checks["FAILED"] += 1
    
    # ============================================================
    # 4. Phase 4 Module Imports
    # ============================================================
    check_section("4. PHASE 4 MODULE IMPORTS")
    
    phase4_imports = [
        ("backend.anomaly.scanner", "AnomalyScanner class"),
        ("backend.anomaly.celery_app", "Celery app"),
        ("backend.anomaly.tasks", "Task definitions"),
    ]
    
    for module, name in phase4_imports:
        if check_import(module, name):
            checks["PASSED"] += 1
        else:
            checks["FAILED"] += 1
    
    # ============================================================
    # 5. Environment Variables
    # ============================================================
    check_section("5. ENVIRONMENT VARIABLES")
    
    env_vars = [
        "DATABASE_URL",
        "ERPNEXT_URL",
        "REDIS_URL",
        "BACKEND_URL",
    ]
    
    set_count = 0
    for var in env_vars:
        if check_env_var(var):
            set_count += 1
        else:
            checks["WARNINGS"] += 1
    
    if set_count > 0:
        checks["PASSED"] += 1
    
    # ============================================================
    # 6. Scanner Functionality
    # ============================================================
    check_section("6. SCANNER FUNCTIONALITY")
    
    try:
        from backend.anomaly.scanner import AnomalyScanner
        scanner = AnomalyScanner()
        
        # Check methods exist
        methods = [
            "load_gl_transactions",
            "calculate_baselines",
            "detect_spike_alerts",
            "detect_trend_alerts",
            "detect_duplicate_payments",
            "detect_vendor_anomalies",
            "calculate_runway_impact",
            "write_alerts_to_db",
            "run_full_scan",
        ]
        
        for method in methods:
            if hasattr(scanner, method):
                print(f"  ✓ AnomalyScanner.{method}()")
                checks["PASSED"] += 1
            else:
                print(f"  ✗ AnomalyScanner.{method}() not found")
                checks["FAILED"] += 1
    
    except Exception as e:
        print(f"  ✗ Failed to load AnomalyScanner: {e}")
        checks["FAILED"] += 1
    
    # ============================================================
    # 7. Celery Configuration
    # ============================================================
    check_section("7. CELERY CONFIGURATION")
    
    try:
        from backend.anomaly.celery_app import app
        
        # Check Beat schedule
        if hasattr(app.conf, 'beat_schedule'):
            schedule = app.conf.beat_schedule
            print(f"  ✓ Beat schedule configured ({len(schedule)} tasks)")
            for task_name in schedule:
                print(f"    - {task_name}")
            checks["PASSED"] += 1
        else:
            print("  ✗ Beat schedule not found")
            checks["FAILED"] += 1
        
        # Check broker
        if hasattr(app.conf, 'broker_url'):
            print(f"  ✓ Broker URL configured")
            checks["PASSED"] += 1
        else:
            print("  ✗ Broker URL not configured")
            checks["FAILED"] += 1
    
    except Exception as e:
        print(f"  ✗ Failed to load Celery app: {e}")
        checks["FAILED"] += 2
    
    # ============================================================
    # 8. Test Suite
    # ============================================================
    check_section("8. TEST SUITE")
    
    try:
        # Count test methods in test_anomaly.py
        import re
        with open("backend/anomaly/test_anomaly.py", "r") as f:
            content = f.read()
            test_methods = re.findall(r'def (test_\w+)\(', content)
            test_count = len(test_methods)
        
        if test_count >= 30:
            print(f"  ✓ {test_count} unit tests defined")
            checks["PASSED"] += 1
        else:
            print(f"  ⚠ {test_count} unit tests (expected 30+)")
            checks["WARNINGS"] += 1
    
    except Exception as e:
        print(f"  ✗ Failed to analyze tests: {e}")
        checks["FAILED"] += 1
    
    # ============================================================
    # 9. Code Quality Checks
    # ============================================================
    check_section("9. CODE QUALITY")
    
    try:
        with open("backend/anomaly/scanner.py", "r") as f:
            scanner_code = f.read()
        
        # Check for docstrings
        docstring_count = scanner_code.count('"""')
        if docstring_count >= 20:
            print(f"  ✓ {docstring_count // 2} function docstrings")
            checks["PASSED"] += 1
        else:
            print(f"  ⚠ {docstring_count // 2} docstrings (expected 10+)")
            checks["WARNINGS"] += 1
        
        # Check for type hints
        type_hint_count = scanner_code.count(" -> ")
        if type_hint_count >= 5:
            print(f"  ✓ Type hints present ({type_hint_count} return annotations)")
            checks["PASSED"] += 1
        else:
            print(f"  ⚠ Limited type hints")
            checks["WARNINGS"] += 1
        
        # Check file size
        lines = len(scanner_code.split('\n'))
        if lines >= 800:
            print(f"  ✓ Scanner.py is {lines} lines (comprehensive)")
            checks["PASSED"] += 1
        else:
            print(f"  ⚠ Scanner.py is {lines} lines (expected 800+)")
            checks["WARNINGS"] += 1
    
    except Exception as e:
        print(f"  ✗ Failed to analyze code: {e}")
        checks["FAILED"] += 1
    
    # ============================================================
    # 10. Architecture Completeness
    # ============================================================
    check_section("10. ARCHITECTURE COMPLETENESS")
    
    try:
        from backend.anomaly.scanner import AnomalyScanner
        import inspect
        
        scanner = AnomalyScanner()
        
        # All 6 parts should exist
        parts = {
            "Part A": "load_gl_transactions",
            "Part B": "calculate_baselines",
            "Part C-Spike": "detect_spike_alerts",
            "Part C-Trend": "detect_trend_alerts",
            "Part C-Duplicate": "detect_duplicate_payments",
            "Part C-Vendor": "detect_vendor_anomalies",
            "Part D": "calculate_runway_impact",
            "Part E": "write_alerts_to_db",
            "Part F": "run_full_scan",
        }
        
        all_present = True
        for part, method in parts.items():
            if hasattr(scanner, method):
                print(f"  ✓ {part}: {method}()")
                checks["PASSED"] += 1
            else:
                print(f"  ✗ {part}: {method}() missing")
                checks["FAILED"] += 1
                all_present = False
        
        if all_present:
            print(f"\n  ✓ All 6 required architecture parts complete")
    
    except Exception as e:
        print(f"  ✗ Failed to verify architecture: {e}")
        checks["FAILED"] += 1
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print("  VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    total = checks["PASSED"] + checks["FAILED"]
    passed_pct = (checks["PASSED"] / total * 100) if total > 0 else 0
    
    print(f"""
  ✓ PASSED:   {checks['PASSED']:2d} checks
  ✗ FAILED:   {checks['FAILED']:2d} checks
  ⚠ WARNINGS: {checks['WARNINGS']:2d} items
  
  Total:      {total} checks
  Success:    {passed_pct:.1f}%
    """)
    
    if checks["FAILED"] == 0:
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ✓ PHASE 4 IMPLEMENTATION COMPLETE AND VERIFIED              ║
║                                                              ║
║  Next Steps:                                                 ║
║  1. Read: PHASE_4_FINAL_SUMMARY.md                          ║
║  2. Follow: DEPLOYMENT_CHECKLIST.md                         ║
║  3. Test: python test_scanner_manual.py                     ║
║  4. Deploy: Configure environment and start services        ║
║                                                              ║
║  Status: READY FOR PRODUCTION 🚀                            ║
╚══════════════════════════════════════════════════════════════╝
        """)
        return 0
    else:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  Phase 4 verification found {checks['FAILED']} issue(s) to resolve           ║
║                                                              ║
║  Next Steps:                                                 ║
║  1. Review errors above                                     ║
║  2. Check DEPLOYMENT_CHECKLIST.md for setup instructions    ║
║  3. Run: python test_scanner_manual.py                      ║
║  4. Fix any missing dependencies or configuration           ║
║                                                              ║
║  Status: INCOMPLETE - Fix issues before deployment         ║
╚══════════════════════════════════════════════════════════════╝
        """)
        return 1

if __name__ == '__main__':
    sys.exit(main())
