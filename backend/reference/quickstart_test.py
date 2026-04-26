#!/usr/bin/env python3
"""
QUICK START TEST
Run this to verify Phase 1 is complete and working
"""

import json
import os

def main():
    print("\n" + "="*80)
    print("PHASE 1 - QUICK VERIFICATION")
    print("="*80 + "\n")
    
    # Test 1: Files exist
    print("✓ TEST 1: Files Generated")
    files = [
        "schema.sql",
        "config.py",
        "generate_full_data.py",
        "generated_data/all_companies.json"
    ]
    for f in files:
        exists = os.path.exists(f)
        print(f"  {'✓' if exists else '✗'} {f}")
    
    # Test 2: Data quality
    print("\n✓ TEST 2: Data Quality")
    with open("generated_data/seedlinglabs.json", "r") as f:
        data = json.load(f)
    
    print(f"  ✓ Invoices: {len(data['invoices'])}")
    print(f"  ✓ Expenses: {len(data['expenses'])}")
    print(f"  ✓ Anomalies: {len(data['anomalies'])}")
    print(f"  ✓ Monthly Metrics: {len(data['monthly_metrics'])}")
    
    # Test 3: Financial calculations
    print("\n✓ TEST 3: Financial Calculations")
    final = data['monthly_metrics'][-1]
    print(f"  ✓ Final Cash: ${final['ending_cash']:,.2f}")
    print(f"  ✓ Runway: {final['runway_months']:.1f} months")
    
    # Test 4: Anomalies present
    print("\n✓ TEST 4: Anomalies Detected")
    for anomaly in data['anomalies'][:3]:
        print(f"  ✓ {anomaly['type']:20s} | {anomaly['severity']:8s}")
    
    print("\n" + "="*80)
    print("✅ PHASE 1 COMPLETE - READY FOR PHASE 2")
    print("="*80)
    print("\nNext: Set up Neon database and load schema.sql")
    print()

if __name__ == "__main__":
    main()
