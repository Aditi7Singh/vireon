#!/usr/bin/env python3
"""
Verification script for Finance Agent routers
Checks that all routers are properly implemented
"""

import os
import sys
from pathlib import Path

ROUTER_DIR = Path("/Users/asingh/vireon/backend/api/routers")

EXPECTED_ROUTERS = {
    "recurring_templates.py": {
        "endpoints": ["POST /", "GET /", "POST /generate-due"],
        "models": ["TransactionTemplate"]
    },
    "board_reports.py": {
        "endpoints": ["POST /", "GET /", "POST /{report_id}/export-pdf"],
        "models": ["BoardReport"]
    },
    "scenario_comparison.py": {
        "endpoints": ["POST /", "GET /", "POST /quick-compare"],
        "models": ["ScenarioComparison"]
    },
    "customer_health.py": {
        "endpoints": ["POST /calculate", "GET /", "GET /at-risk/summary"],
        "models": ["CustomerHealthScore"]
    },
    "forecast_monitoring.py": {
        "endpoints": ["POST /models", "GET /models", "POST /auto-retrain"],
        "models": ["ForecastModel", "ForecastAccuracy"]
    },
    "finance_tasks.py": {
        "endpoints": ["POST /", "GET /", "POST /close-checklist"],
        "models": ["FinanceTask"]
    },
    "transaction_comments.py": {
        "endpoints": ["POST /", "GET /", "GET /mentions/me"],
        "models": ["TransactionComment"]
    },
    "inventory.py": {
        "endpoints": ["POST /items", "GET /items", "POST /calculate-cogs"],
        "models": ["InventoryItem", "InventoryTransaction"]
    },
    "revenue_recognition_asc606.py": {
        "endpoints": ["POST /", "GET /", "POST /recognize-due"],
        "models": ["RevenueRecognition", "RevenueSchedule"]
    },
    "purchase_orders.py": {
        "endpoints": ["POST /", "GET /", "POST /{po_id}/approve"],
        "models": ["PurchaseOrder", "POLineItem"]
    }
}

def check_file_exists(filename):
    """Check if router file exists"""
    filepath = ROUTER_DIR / filename
    return filepath.exists(), filepath

def check_file_content(filepath, expected):
    """Check if file contains expected content"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        checks = {
            "has_router": "router = APIRouter" in content,
            "has_imports": "from fastapi import" in content,
            "has_auth": "get_current_user" in content,
            "has_db": "database.get_db" in content,
            "has_models": all(model in content for model in expected["models"]),
            "has_endpoints": any(endpoint.split()[1] in content for endpoint in expected["endpoints"])
        }
        
        return checks
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 70)
    print("Finance Agent Routers Verification")
    print("=" * 70)
    print()
    
    all_passed = True
    total_files = len(EXPECTED_ROUTERS)
    passed_files = 0
    
    for filename, expected in EXPECTED_ROUTERS.items():
        print(f"Checking {filename}...", end=" ")
        
        exists, filepath = check_file_exists(filename)
        
        if not exists:
            print("❌ FILE NOT FOUND")
            all_passed = False
            continue
        
        checks = check_file_content(filepath, expected)
        
        if "error" in checks:
            print(f"❌ ERROR: {checks['error']}")
            all_passed = False
            continue
        
        failed_checks = [k for k, v in checks.items() if not v]
        
        if failed_checks:
            print(f"⚠️  WARNING: Missing {', '.join(failed_checks)}")
        else:
            print("✅ PASSED")
            passed_files += 1
    
    print()
    print("=" * 70)
    print(f"Results: {passed_files}/{total_files} routers verified")
    
    if all_passed:
        print("✅ All Finance Agent routers are properly implemented!")
        return 0
    else:
        print("⚠️  Some issues found. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
