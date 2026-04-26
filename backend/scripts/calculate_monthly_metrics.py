#!/usr/bin/env python3
"""
Calculate MonthlyMetric records from FinancialLedgerEntry data.
This aggregates ledger entries by month to produce revenue, expenses, and derived metrics.
"""

import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Company, FinancialLedgerEntry, MonthlyMetric, LedgerEntryType, LedgerCategory
from analytics import metrics

def calculate_monthly_metrics():
    """Generate MonthlyMetric records from FinancialLedgerEntry data."""
    db = SessionLocal()
    
    print("\n📊 Calculating Monthly Metrics from Ledger Entries...")
    
    try:
        # Get all companies
        companies = db.query(Company).all()
        if not companies:
            print("❌ No companies found")
            return
        
        for company in companies:
            print(f"\n📈 Processing company: {company.name}")
            
            # Get all ledger entries for this company
            entries = db.query(FinancialLedgerEntry).filter(
                FinancialLedgerEntry.company_id == company.id
            ).all()
            
            if not entries:
                print("   ⚠ No ledger entries found")
                continue
            
            # Group entries by month
            months_data = {}
            for entry in entries:
                month_key = entry.transaction_date.strftime("%Y-%m-01")
                if month_key not in months_data:
                    months_data[month_key] = {
                        "revenue": Decimal(0),
                        "expenses": Decimal(0),
                        "cash": Decimal(0),
                    }
                
                amount = entry.amount_inr
                if entry.entry_type == LedgerEntryType.CREDIT:
                    months_data[month_key]["revenue"] += amount
                else:
                    months_data[month_key]["expenses"] += amount
            
            # Create or update MonthlyMetric records
            for month_str, data in sorted(months_data.items()):
                month_date = datetime.strptime(month_str, "%Y-%m-%d").date()
                
                # Check if metric exists
                metric = db.query(MonthlyMetric).filter(
                    MonthlyMetric.company_id == company.id,
                    MonthlyMetric.metric_month == month_date
                ).first()
                
                if metric:
                    # Update existing
                    metric.total_revenue = data["revenue"]
                    metric.total_expenses = data["expenses"]
                    metric.net_cash_flow = data["revenue"] - data["expenses"]
                    metric.burn_rate = data["expenses"]
                else:
                    # Create new
                    metric = MonthlyMetric(
                        company_id=company.id,
                        metric_month=month_date,
                        total_revenue=data["revenue"],
                        total_expenses=data["expenses"],
                        net_cash_flow=data["revenue"] - data["expenses"],
                        burn_rate=data["expenses"],
                        ending_cash=Decimal("1000000"),  # Placeholder
                        runway_months=Decimal("12"),  # Placeholder
                    )
                    db.add(metric)
                
                db.flush()
                print(f"   ✓ {month_str}: Revenue=₹{data['revenue']:,.0f}, Expenses=₹{data['expenses']:,.0f}")
            
            db.commit()
        
        print("\n✅ Monthly metrics calculation complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def seed_revenue_metrics():
    """Seed sample revenue data (MRR, ARR, churn, NRR) for demo."""
    db = SessionLocal()
    
    print("\n💰 Seeding Revenue Metrics...")
    
    try:
        # Get default company
        company = db.query(Company).first()
        if not company:
            print("❌ No companies found")
            return
        
        print(f"✓ Company: {company.name}")
        
        # Create sample revenue entries if they don't exist
        today = datetime.now()
        for month_offset in range(6, 0, -1):
            month_date = today - timedelta(days=30 * month_offset)
            trans_date = month_date.date()
            
            # Check if revenue entries exist for this month
            existing = db.query(FinancialLedgerEntry).filter(
                FinancialLedgerEntry.company_id == company.id,
                FinancialLedgerEntry.transaction_date == trans_date,
                FinancialLedgerEntry.category == LedgerCategory.REVENUE
            ).first()
            
            if existing:
                continue
            
            # Sample revenue values (in INR)
            mrr = 500000  # ₹5L monthly recurring revenue
            arr = mrr * 12
            
            # Create revenue entry
            entry = FinancialLedgerEntry(
                company_id=company.id,
                transaction_date=trans_date,
                amount=mrr,
                currency="INR",
                amount_inr=mrr,
                entry_type=LedgerEntryType.CREDIT,
                category=LedgerCategory.REVENUE,
                source="sandbox",
                description=f"Product License Sales ({trans_date.strftime('%B %Y')})",
                entered_by_role="system",
                tags={"mrr": mrr, "arr": arr, "auto_seeded": True},
            )
            db.add(entry)
            print(f"   ✓ {trans_date.strftime('%Y-%m')}: MRR=₹{mrr:,.0f}")
        
        db.commit()
        print("\n✅ Revenue metrics seeded!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Initialize database
    Base.metadata.create_all(bind=engine)
    
    print("=" * 60)
    print("Monthly Metrics & Revenue Calculation")
    print("=" * 60)
    
    # Seed revenue if needed
    seed_revenue_metrics()
    
    # Calculate metrics from ledger
    calculate_monthly_metrics()
    
    print("\n" + "=" * 60)
    print("✨ Complete!")
    print("=" * 60)
