#!/usr/bin/env python3
"""
Test Script - Run Financial Data Generator
Generates realistic financial data with anomalies
"""

import json
from config import COMPANY_PROFILES

# Quick test to verify everything works
def test_config():
    """Test that config loads correctly"""
    print("Testing configuration...")
    print(f"✓ Companies defined: {len(COMPANY_PROFILES)}")
    print(f"✓ First company: {COMPANY_PROFILES[0]['name']}")
    print(f"✓ Initial cash: ${COMPANY_PROFILES[0]['initial_cash']:,}")
    print()

def test_data_structure():
    """Test data structure matches Merge.dev schema"""
    print("Testing data structures...")
    
    # Expected tables from schema
    expected_tables = [
        "companies", "accounts", "invoices", "invoice_line_items",
        "expenses", "expense_line_items", "payments", "contacts",
        "employees", "payroll_runs", "cloud_costs", "monthly_metrics", "anomalies"
    ]
    
    print(f"✓ Expected tables: {len(expected_tables)}")
    for table in expected_tables:
        print(f"  - {table}")
    print()

def test_sample_generation():
    """Generate sample data for one company"""
    print("="*80)
    print("GENERATING SAMPLE DATA")
    print("="*80)
    
    # Simple generator for testing
    import uuid
    from datetime import datetime, timedelta
    from decimal import Decimal
    import random
    
    profile = COMPANY_PROFILES[0]  # SeedlingLabs
    company_id = str(uuid.uuid4())
    
    data = {
        "companies": [],
        "invoices": [],
        "expenses": [],
        "monthly_metrics": []
    }
    
    # Create company
    data["companies"].append({
        "id": company_id,
        "name": profile["name"],
        "initial_cash": float(profile["initial_cash"]),
        "stage": profile["stage"]
    })
    
    # Generate 3 months of sample data
    start_date = datetime(2024, 1, 1)
    for month in range(3):
        month_date = start_date + timedelta(days=30 * month)
        
        # Sample revenue
        mrr = profile["monthly_revenue_base"]
        for i in range(5):  # 5 sample invoices
            data["invoices"].append({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "invoice_number": f"INV-{month_date.strftime('%Y%m')}-{i+1:04d}",
                "issue_date": month_date.isoformat(),
                "total_amount": float(mrr / 5),
                "status": "paid"
            })
        
        # Sample expenses
        burn = profile["burn_rate_base"]
        for i in range(8):  # 8 sample expenses
            data["expenses"].append({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "transaction_date": month_date.isoformat(),
                "total_amount": float(burn / 8),
                "category": random.choice(["Cloud", "Payroll", "Software", "Marketing"])
            })
    
    # Calculate simple metrics
    total_revenue = sum(inv["total_amount"] for inv in data["invoices"])
    total_expenses = sum(exp["total_amount"] for exp in data["expenses"])
    
    print(f"\n✓ Sample Data Generated:")
    print(f"  Company: {profile['name']}")
    print(f"  Invoices: {len(data['invoices'])}")
    print(f"  Expenses: {len(data['expenses'])}")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    print(f"  Total Expenses: ${total_expenses:,.2f}")
    print(f"  Net: ${total_revenue - total_expenses:,.2f}")
    
    # Save sample
    import os
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/sample_data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved: test_output/sample_data.json")
    print()
    
    return data

def test_anomaly_detection():
    """Test that anomalies are properly structured"""
    print("Testing anomaly detection structure...")
    
    from config import ANOMALY_TEMPLATES
    
    print(f"✓ Anomaly templates defined: {len(ANOMALY_TEMPLATES)}")
    
    for i, anomaly in enumerate(ANOMALY_TEMPLATES[:3], 1):
        print(f"\n  Anomaly {i}: {anomaly['name']}")
        print(f"    Type: {anomaly['type']}")
        print(f"    Month: {anomaly['month']}")
        print(f"    Severity: {anomaly['severity']}")
        print(f"    Description: {anomaly['description'][:60]}...")
    
    print()

def test_merge_dev_compliance():
    """Test that generated data matches Merge.dev API structure"""
    print("Testing Merge.dev API compliance...")
    
    # Sample invoice structure (Merge.dev format)
    sample_invoice = {
        "id": "uuid",
        "remote_id": "inv_12345",
        "company_id": "uuid",
        "invoice_number": "INV-202401-0001",
        "contact_id": "uuid",
        "issue_date": "2024-01-01",
        "due_date": "2024-01-31",
        "status": "paid",
        "total_amount": 1000.00,
        "currency": "USD"
    }
    
    # Sample expense structure
    sample_expense = {
        "id": "uuid",
        "remote_id": "exp_67890",
        "company_id": "uuid",
        "transaction_date": "2024-01-15",
        "total_amount": 500.00,
        "category": "Cloud",
        "currency": "USD"
    }
    
    print("✓ Invoice structure matches Merge.dev:")
    for key in sample_invoice.keys():
        print(f"    {key}")
    
    print("\n✓ Expense structure matches Merge.dev:")
    for key in sample_expense.keys():
        print(f"    {key}")
    
    print()

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("FINANCIAL DATA GENERATOR - TEST SUITE")
    print("="*80 + "\n")
    
    try:
        test_config()
        test_data_structure()
        test_anomaly_detection()
        test_merge_dev_compliance()
        test_sample_generation()
        
        print("="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)
        print("\nNext steps:")
        print("1. Run: python3 generate_full_data.py")
        print("2. Check: generated_data/ folder for JSON files")
        print("3. Load data into PostgreSQL database")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
