
import sys
import os
from pathlib import Path
from datetime import date

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from analytics import metrics
from database import SessionLocal
import models

def verify():
    db = SessionLocal()
    try:
        company_name = "SeedlingLabs India Private Limited"
        company = db.query(models.Company).filter(models.Company.name == company_name).first()
        if not company:
            print("❌ Company not found.")
            return
        
        cid = company.id
        
        print(f"--- Verifying DB Metrics for {company_name} ---")
        
        # 1. Payroll Cost
        payroll_cost = metrics.calculate_monthly_payroll_cost(db, cid, date(2025, 4, 1))
        print(f"Monthly Payroll Outflow (Estimated from Employees): ₹{payroll_cost['total_employer_outflow']:,}")
        
        # We have 1 employee at 28L (₹2,35,466.67 outflow)
        # 1 at 18L (₹1,51,371.43 outflow) - wait, I only added Aditi in the direct script for simplicity
        # Let's check how many employees were actually added
        emp_count = db.query(models.Employee).filter(models.Employee.company_id == company.id).count()
        print(f"Active Employees: {emp_count}")
        
        # 2. Loan Metrics
        loan_metrics = metrics.calculate_loan_metrics(db, cid)
        print(f"Total Debt: ₹{loan_metrics['total_debt']:,}")
        print(f"Monthly Interest: ₹{loan_metrics['monthly_interest_expense']:,}")
        
        # Principal 50L, Interest 10.5%. Monthly interest on 42L remaining:
        # 4,200,000 * 0.105 / 12 = 36,750
        if abs(loan_metrics['monthly_interest_expense'] - 36750) < 10:
            print("✅ Loan interest matches.")
        else:
            print(f"❌ Loan interest mismatch. Got {loan_metrics['monthly_interest_expense']}")

        # 3. Depreciation
        dep_expense = metrics.calculate_monthly_depreciation_expense(db, cid, date(2025, 4, 1))
        print(f"Monthly Depreciation: ₹{dep_expense:,}")
        # Mac Studio 4.5L, Salvage 0 (default), 3 years = 1.25L/year = 12,500/month
        # Wait, purchase_cost 450,000 / 36 months = 12,500.
        if abs(dep_expense - 12500) < 10:
            print("✅ Depreciation matches.")
        else:
            print(f"❌ Depreciation mismatch. Got {dep_expense}")

    finally:
        db.close()

if __name__ == "__main__":
    verify()
