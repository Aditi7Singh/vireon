#!/usr/bin/env python3
"""
Seed demo data for Vireon - Realistic Seedling Labs financial scenario
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

from models import (
    Company, FinancialLedgerEntry, LedgerCategory, LedgerEntryType, 
    LedgerProductTag, LedgerOfficeTag, LedgerSource, LedgerEnteredByRole,
    Expense, GeneralLedger, CustomerCohort, RecommendationReport, RunwayAlert,
    GLAccountCode, Department
)

# Database setup
engine = create_engine('sqlite:///app.db')
Session = sessionmaker(bind=engine)
session = Session()

def create_company():
    """Create Seedling Labs company profile"""
    company = Company(
        id=uuid.uuid4(),
        name="Seedling Labs",
        industry="Agritech SaaS",
        stage="series_a",
        initial_cash=25000000.0,  # ₹2.5 Cr
        effective_tax_rate=0.25,  # 25%
        founding_date=datetime(2020, 1, 1).date(),
        notification_contacts={
            "email": ["founder@seedlinglabs.io", "cfo@seedlinglabs.io"],
            "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        },
        alert_thresholds={
            "critical_months": 3,
            "warning_months": 6
        }
    )
    session.add(company)
    session.commit()
    return company

def create_financial_ledger_entries(company):
    """Create 12 months of financial ledger entries"""
    base_date = datetime(2024, 1, 1)
    products = [LedgerProductTag.ORCHARD, LedgerProductTag.SPROUTS, LedgerProductTag.AI_LAB]
    offices = [LedgerOfficeTag.BENGALURU, LedgerOfficeTag.GANGAVATHI, LedgerOfficeTag.REMOTE]
    departments = ["engineering", "product", "marketing", "sales", "operations", "finance", "people"]
    
    entries_count = 0
    monthly_arr = 500000.0  # Starting ARR
    
    for month in range(12):
        current_date = base_date + timedelta(days=30 * month)
        
        # --- REVENUE ENTRIES ---
        mrr = monthly_arr / 12 * (1.05 ** month)
        prod = random.choice(products)
        office = random.choice(offices)
        revenue = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.REVENUE,
            amount_inr=mrr,
            amount=mrr,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=prod,
            office_tag=office,
            source=LedgerSource.ERPNEXT,
            entry_type=LedgerEntryType.CREDIT,
            description=f"MRR {current_date.strftime('%B %Y')} - {prod.value} subscription from {office.value}",
            entered_by_role=LedgerEnteredByRole.SYSTEM,
            department=random.choice(departments),
        )
        session.add(revenue)
        entries_count += 1
        
        # --- PAYROLL ---
        # Bengaluru HQ
        payroll_blr = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.PAYROLL,
            amount_inr=1200000.0,
            amount=1200000.0,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=LedgerProductTag.SHARED,
            office_tag=LedgerOfficeTag.BENGALURU,
            source=LedgerSource.ERPNEXT,
            entry_type=LedgerEntryType.DEBIT,
            description="Bengaluru HQ Payroll",
            entered_by_role=LedgerEnteredByRole.FINANCE,
            department="people",
        )
        session.add(payroll_blr)
        
        # Gangavathi Hub
        payroll_gv = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.PAYROLL,
            amount_inr=500000.0,
            amount=500000.0,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=LedgerProductTag.SPROUTS,
            office_tag=LedgerOfficeTag.GANGAVATHI,
            source=LedgerSource.ERPNEXT,
            entry_type=LedgerEntryType.DEBIT,
            description="Gangavathi Hub Operations Payroll",
            entered_by_role=LedgerEnteredByRole.FINANCE,
            department="operations",
        )
        session.add(payroll_gv)
        entries_count += 2
        
        # --- AWS COSTS ---
        aws_cost = 150000 * (1 + month * 0.08)
        aws = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.TECH_COST,
            amount_inr=aws_cost,
            amount=aws_cost,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=LedgerProductTag.SHARED,
            office_tag=LedgerOfficeTag.BENGALURU,
            source=LedgerSource.AWS_BILLING,
            entry_type=LedgerEntryType.DEBIT,
            description="AWS infrastructure - EC2, AI Lab model inference",
            entered_by_role=LedgerEnteredByRole.CTO,
            department="engineering",
        )
        session.add(aws)
        entries_count += 1
        
        # --- OFFICE EXPENSES ---
        # Bengaluru Rent
        rent_blr = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.OFFICE_EXPENSE,
            amount_inr=150000,
            amount=150000,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=LedgerProductTag.UNALLOCATED,
            office_tag=LedgerOfficeTag.BENGALURU,
            source=LedgerSource.MANUAL_FINANCE,
            entry_type=LedgerEntryType.DEBIT,
            description="Bengaluru Office Rent & Utilities",
            entered_by_role=LedgerEnteredByRole.FINANCE,
            department="operations",
        )
        session.add(rent_blr)
        
        # Gangavathi Rent (Much cheaper)
        rent_gv = FinancialLedgerEntry(
            id=uuid.uuid4(),
            company_id=company.id,
            category=LedgerCategory.OFFICE_EXPENSE,
            amount_inr=35000,
            amount=35000,
            currency="INR",
            transaction_date=current_date.date(),
            product_tag=LedgerProductTag.UNALLOCATED,
            office_tag=LedgerOfficeTag.GANGAVATHI,
            source=LedgerSource.MANUAL_FINANCE,
            entry_type=LedgerEntryType.DEBIT,
            description="Gangavathi Hub Rent",
            entered_by_role=LedgerEnteredByRole.FINANCE,
            department="operations",
        )
        session.add(rent_gv)
        entries_count += 2
    
    session.commit()
    print(f"✅ Created {entries_count} financial ledger entries (12 months)")

def create_general_ledger_entries(company):
    """Create GL entries for audit trail"""
    gl_accounts = [
        (GLAccountCode.CASH, "Cash", 25000000.0),
        (GLAccountCode.ACCOUNTS_RECEIVABLE, "Accounts Receivable", 500000.0),
        (GLAccountCode.ACCOUNTS_PAYABLE, "Accounts Payable", -200000.0),
        (GLAccountCode.PRODUCT_REVENUE, "Product Revenue", 6000000.0),
        (GLAccountCode.TECH_COST_AWS, "AWS Cloud Costs", -1500000.0),
        (GLAccountCode.PAYROLL_EXPENSE, "Employee Salaries", -16000000.0),
        (GLAccountCode.MARKETING_EXPENSE, "Marketing Expenses", -960000.0),
    ]
    
    for account_code, account_name, balance in gl_accounts:
        gl = GeneralLedger(
            id=uuid.uuid4(),
            company_id=company.id,
            account_code=account_code,
            account_name=account_name,
            transaction_date=datetime.now().date(),
            debit_amount=balance if balance > 0 else 0,
            credit_amount=abs(balance) if balance < 0 else 0,
            description=f"GL entry for {account_name}",
            department=Department.FINANCE,
            source_type="consolidated",
        )
        session.add(gl)
    
    session.commit()
    print(f"✅ Created {len(gl_accounts)} GL entries")

def create_customer_cohorts(company):
    """Create customer cohort analytics"""
    cohorts = [
        {
            "cohort_name": "Q1 2024 - Enterprise",
            "cohort_type": "acquisition_month",
            "cohort_value": "Q1-2024",
            "mrr_total": 250000,
            "arr_total": 3000000,
            "customer_count": 12,
            "churn_rate": 0.08,
            "ltv_estimate": 3600000,
            "cac_estimate": 180000,
            "nrr": 1.15,
            "gross_margin_pct": 78.0,
            "payback_months": 6,
            "health_score": 9
        },
        {
            "cohort_name": "Q2 2024 - Mid-Market",
            "cohort_type": "acquisition_month",
            "cohort_value": "Q2-2024",
            "mrr_total": 180000,
            "arr_total": 2160000,
            "customer_count": 28,
            "churn_rate": 0.15,
            "ltv_estimate": 1944000,
            "cac_estimate": 120000,
            "nrr": 1.08,
            "gross_margin_pct": 75.0,
            "payback_months": 8,
            "health_score": 7
        },
    ]
    
    for cohort_data in cohorts:
        cohort = CustomerCohort(
            id=uuid.uuid4(),
            company_id=company.id,
            cohort_name=cohort_data["cohort_name"],
            cohort_type=cohort_data["cohort_type"],
            cohort_value=cohort_data["cohort_value"],
            mrr_total=cohort_data["mrr_total"],
            arr_total=cohort_data["arr_total"],
            customer_count=cohort_data["customer_count"],
            customer_acquired_date=datetime.now(),
            churn_rate=cohort_data["churn_rate"],
            ltv_estimate=cohort_data["ltv_estimate"],
            cac_estimate=cohort_data["cac_estimate"],
            nrr=cohort_data["nrr"],
            gross_margin_pct=cohort_data["gross_margin_pct"],
            payback_months=cohort_data["payback_months"],
            health_score=cohort_data["health_score"],
        )
        session.add(cohort)
    
    session.commit()
    print(f"✅ Created {len(cohorts)} customer cohorts")

def create_recommendations(company):
    """Create AI CFO recommendations"""
    recommendations = [
        {
            "priority": "HIGH",
            "category": "Burn Rate",
            "finding": "Monthly net burn trending upward (₹28L → ₹31L)",
            "impact_inr": 300000,
            "action": "Review non-essential subscriptions (Datadog, Figma)",
            "confidence": 0.92
        },
        {
            "priority": "MEDIUM",
            "category": "Revenue Optimization",
            "finding": "Enterprise cohort showing 115% NRR. Expand sales team.",
            "impact_inr": 500000,
            "action": "Hire 1 more sales person (₹12L/year for ₹50L+ upside)",
            "confidence": 0.85
        },
    ]
    
    report = RecommendationReport(
        id=uuid.uuid4(),
        company_id=company.id,
        month=datetime.now().strftime("%Y-%m"),
        recommendations=recommendations,
        runway_at_generation=8.5,
    )
    session.add(report)
    session.commit()
    print(f"✅ Created AI CFO recommendation report")

def main():
    try:
        print("\n📊 Seeding Seedling Labs demo data...")
        company = create_company()
        print(f"✅ Company created: {company.name}")
        
        create_financial_ledger_entries(company)
        create_general_ledger_entries(company)
        create_customer_cohorts(company)
        create_recommendations(company)
        
        print("\n✅ All demo data seeded successfully!")
        print("\n📈 Seedling Labs Snapshot:")
        print(f"  💰 Initial Cash: ₹2.5 Cr")
        print(f"  📊 ARR Growth: ₹50l → ₹78l (12 months)")
        print(f"  🔥 Net Burn: ~₹30L/month")
        print(f"  ⏱️  Runway: ~8 months")
        print(f"  🎯 Enterprise NRR: 115%")
        print(f"  📈 Health Score: 8/10\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
