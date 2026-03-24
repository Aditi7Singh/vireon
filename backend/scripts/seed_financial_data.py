#!/usr/bin/env python3
"""
Seed realistic financial data for dashboard demonstration.
This populates the database with representative expense and revenue entries.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    FinancialLedgerEntry, Company,
    LedgerCategory, LedgerEntryType, LedgerProductTag,
    LedgerEnteredByRole, LedgerSource
)
import random

# Initialize database tables
Base.metadata.create_all(bind=engine)

def get_or_create_company(db: Session, company_name: str = "Vireon Demo"):
    """Get or create default company"""
    company = db.query(Company).filter_by(name=company_name).first()
    if not company:
        company = Company(
            name=company_name,
            industry="Technology",
            stage="seed",
            initial_cash=1000000,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✓ Created company: {company.name} (ID: {company.id})")
    else:
        print(f"✓ Using existing company: {company.name} (ID: {company.id})")
    return company

def add_ledger_entry(
    db: Session,
    company_id: str,
    category: str,
    description: str,
    amount_inr: float,
    entry_type: str = "debit",
    transaction_date: datetime = None,
):
    """Add a ledger entry"""
    if not transaction_date:
        transaction_date = datetime.now()
    
    # Map string category to enum
    category_enum = LedgerCategory[category.upper()]
    entry_type_enum = LedgerEntryType(entry_type)
    
    ledger = FinancialLedgerEntry(
        company_id=company_id,
        transaction_date=transaction_date.date(),
        amount=amount_inr,
        currency="INR",
        amount_inr=amount_inr,
        entry_type=entry_type_enum,
        category=category_enum,
        product_tag=LedgerProductTag.UNALLOCATED,
        source=LedgerSource.SANDBOX,
        description=description,
        entered_by_role=LedgerEnteredByRole.SYSTEM,
        is_recurring=True if category in ["payroll", "office_expense"] else False,
        tags={"auto_seeded": True},
    )
    db.add(ledger)
    return ledger

def seed_financial_data(company_id: str):
    """Seed 6 months of realistic financial data"""
    db = SessionLocal()
    
    print("\n🌱 Seeding Financial Data...")
    print(f"Company ID: {company_id}")
    
    # Define realistic expense patterns
    TECH_COSTS = [
        {"name": "AWS", "monthly_base": 80000, "variance": 15000},
        {"name": "SaaS Tools", "monthly_base": 45000, "variance": 5000},
        {"name": "Software Licenses", "monthly_base": 25000, "variance": 0},
        {"name": "Development Tools", "monthly_base": 15000, "variance": 2000},
    ]
    
    PAYROLL = [
        {"name": "Engineer Salaries", "monthly": 250000},
        {"name": "Product Manager", "monthly": 120000},
        {"name": "Operations", "monthly": 100000},
        {"name": "Contingency Staff", "monthly": 50000},
    ]
    
    MARKETING = [
        {"name": "Digital Marketing", "monthly_base": 60000, "variance": 20000},
        {"name": "Events & Conferences", "monthly_base": 30000, "variance": 15000},
        {"name": "Content Marketing", "monthly_base": 20000, "variance": 5000},
    ]
    
    OTHER_EXPENSES = [
        {"name": "Office Rent", "monthly": 80000},
        {"name": "Utilities & Internet", "monthly": 15000},
        {"name": "Office Furniture", "monthly_base": 5000, "variance": 10000},
        {"name": "Travel & Transport", "monthly_base": 25000, "variance": 10000},
        {"name": "Legal & Compliance", "monthly_base": 10000, "variance": 5000},
        {"name": "Insurance", "monthly": 20000},
        {"name": "Miscellaneous", "monthly_base": 15000, "variance": 8000},
    ]
    
    REVENUE = [
        {"name": "Product License Sales", "monthly_base": 400000, "variance": 50000},
        {"name": "Consulting Services", "monthly_base": 200000, "variance": 80000},
        {"name": "Enterprise Support", "monthly_base": 150000, "variance": 30000},
    ]
    
    # Generate data for last 6 months
    entries = []
    today = datetime.now()
    
    for month_offset in range(6, 0, -1):
        month_date = today - timedelta(days=30 * month_offset)
        month_str = month_date.strftime("%Y-%m")
        
        print(f"\n📅 {month_str}:")
        
        # Add tech costs
        for tech in TECH_COSTS:
            amount = tech["monthly_base"] + random.randint(-tech.get("variance", 0), tech.get("variance", 0))
            date = month_date + timedelta(days=random.randint(1, 28))
            add_ledger_entry(
                db, company_id, "tech_cost",
                f"{tech['name']} - Monthly {month_str}",
                amount, "debit", date
            )
            print(f"  ✓ {tech['name']}: ₹{amount:,.0f}")
        
        # Add payroll
        payroll_total = 0
        for staff in PAYROLL:
            amount = staff["monthly"]
            date = month_date + timedelta(days=random.randint(24, 28))  # Around month-end
            add_ledger_entry(
                db, company_id, "payroll",
                f"{staff['name']} - {month_str}",
                amount, "debit", date
            )
            payroll_total += amount
        print(f"  ✓ Payroll Total: ₹{payroll_total:,.0f}")
        
        # Add marketing
        for mkt in MARKETING:
            amount = mkt["monthly_base"] + random.randint(-mkt.get("variance", 0), mkt.get("variance", 0))
            date = month_date + timedelta(days=random.randint(1, 28))
            add_ledger_entry(
                db, company_id, "marketing",
                f"{mkt['name']} - {month_str}",
                amount, "debit", date
            )
        print(f"  ✓ Marketing expenses added")
        
        # Add other expenses
        for expense in OTHER_EXPENSES:
            amount = expense.get("monthly") or (expense["monthly_base"] + random.randint(-expense.get("variance", 0), expense.get("variance", 0)))
            date = month_date + timedelta(days=random.randint(1, 28))
            add_ledger_entry(
                db, company_id, "office_expense",
                f"{expense['name']} - {month_str}",
                amount, "debit", date
            )
        print(f"  ✓ Other expenses added")
        
        # Add hiring costs
        if month_offset > 2:  # Add hiring costs for recent months
            hiring_amount = random.randint(0, 100000)
            if hiring_amount > 0:
                add_ledger_entry(
                    db, company_id, "hiring",
                    f"Hiring & Recruitment - {month_str}",
                    hiring_amount, "debit",
                    month_date + timedelta(days=random.randint(1, 15))
                )
                print(f"  ✓ Hiring: ₹{hiring_amount:,.0f}")
        
        # Add revenue
        revenue_total = 0
        for rev in REVENUE:
            amount = rev["monthly_base"] + random.randint(-rev.get("variance", 0), rev.get("variance", 0))
            date = month_date + timedelta(days=random.randint(1, 28))
            add_ledger_entry(
                db, company_id, "revenue",
                f"{rev['name']} - {month_str}",
                amount, "credit", date
            )
            revenue_total += amount
        print(f"  ✓ Revenue Total: ₹{revenue_total:,.0f}")
    
    db.commit()
    
    print(f"\n✅ Successfully seeded financial entries!")
    print(f"   Data available for analysis and dashboard display")
    
    db.close()

def main():
    """Main entry point"""
    print("=" * 60)
    print("Vireon Financial Data Seeding Script")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get or create company
        company = get_or_create_company(db)
        company_id = str(company.id)
        
        # Seed financial data
        seed_financial_data(company_id)
        
        print("\n" + "=" * 60)
        print("✨ Data seeding complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Refresh your browser to see updated dashboards")
        print("  2. Navigate to CEO Dashboard to view financial metrics")
        print("  3. Go to CTO Dashboard to see tech cost breakdown")
        print("  4. Check Anomalies page for financial health insights")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
