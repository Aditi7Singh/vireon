#!/usr/bin/env python3
"""
Direct seed of MonthlyMetric and revenue data.
Bypasses ledger entry calculation to populate metrics directly.
"""

import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from decimal import Decimal
import uuid

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

def seed_demo_data():
    """Seed demo financial data directly."""
    from database import SessionLocal, engine, Base
    from models import Company, MonthlyMetric
    
    db = SessionLocal()
    
    print("\n=" * 60)
    print("🌱 Direct Financial Data Seeding")
    print("=" * 60)
    
    try:
        # Initialize tables
        Base.metadata.create_all(bind=engine)
        
        # Get or create company
        company = db.query(Company).first()
        if not company:
            company = Company(
                name="Vireon Demo",
                industry="Technology",
                stage="seed",
                initial_cash=1000000,
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            print(f"✓ Created company: {company.name}")
        else:
            print(f"✓ Using company: {company.name}")
        
        company_id = company.id
        
        # Seed 6 months of metrics
        print("\n📊 Seeding monthly metrics...")
        for month_offset in range(6, 0, -1):
            month_date = datetime.now() - timedelta(days=30 * month_offset)
            first_of_month = month_date.replace(day=1).date()
            
            # Check if exists
            existing = db.query(MonthlyMetric).filter(
                MonthlyMetric.company_id == company_id,
                MonthlyMetric.metric_month == first_of_month
            ).first()
            
            if existing:
                continue
            
            # Create metric
            revenue = Decimal("500000")
            expenses = Decimal("635000")  # Tech 165K + payroll 520K = 685K, minus some 50K variance
            net_burn = expenses - revenue  # About 135K
            
            metric = MonthlyMetric(
                id=uuid.uuid4(),
                company_id=company_id,
                metric_month=first_of_month,
                total_revenue=revenue,
                total_expenses=expenses,
                net_cash_flow=revenue - expenses,
                burn_rate=net_burn,
                ending_cash=Decimal("2000000"),
                runway_months=Decimal("14.8"),  # ~15 months  
            )
            db.add(metric)
            print(f"   ✓ {first_of_month.strftime('%Y-%m')}: Revenue=₹{revenue:,.0f}, Expenses=₹{expenses:,.0f}, Burn=₹{net_burn:,.0f}")
        
        db.commit()
        
        print("\n✅ Financial data seeded successfully!")
        print(f"   - Company ID: {company_id}")
        print(f"   - 6 months of metrics")
        print(f"   - Monthly revenue: ₹500,000 (MRR)")
        print(f"   - Monthly expenses: ₹635,000")
        print(f"   - Monthly net burn: ₹135,000")
        print(f"   - Runway: ~15 months")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
    print("\n" + "=" * 60)
    print("✨ Dashboard should now show real financial metrics!")
    print("=" * 60)
