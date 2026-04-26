import os
import sys
import random
from sqlalchemy.orm import Session
from database import SessionLocal
from sqlalchemy import func
import models
from datetime import datetime, date, timedelta
from decimal import Decimal
from anomaly_detection import detect_expense_anomalies

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_metrics_and_anomalies():
    print("📈 Processing financial data for metrics and anomalies...")
    db = SessionLocal()
    try:
        # 0. Multi-Company Seeding
        other_companies = ["Acme Corp", "CloudMetrics Inc"]
        for c_name in other_companies:
            if not db.query(models.Company).filter(models.Company.name == c_name).first():
                new_c = models.Company(name=c_name, stage="seed")
                db.add(new_c)
        db.commit()

        company = db.query(models.Company).filter(models.Company.name == "Seedlinglabs").first()
        if not company:
            print("❌ Company 'Seedlinglabs' not found. Run sync first.")
            return

        # 1. User Seeding (Requested)
        print("👤 Seeding system users...")
        mock_users = [
            {"username": "admin", "email": "admin@seedlinglabs.com"},
            {"username": "asingh", "email": "asingh@seedlinglabs.com"},
            {"username": "finance_lead", "email": "finance@seedlinglabs.com"}
        ]
        for u in mock_users:
            if not db.query(models.User).filter(models.User.username == u["username"]).first():
                user = models.User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password="hashed_placeholder", 
                    is_active=True
                )
                db.add(user)
        db.commit()

        # 2. Map Purchase Invoices to Expenses
        print("💸 Mapping Purchase Invoices to Expenses...")
        purchase_invoices = db.query(models.Invoice).filter(
            models.Invoice.company_id == company.id,
            models.Invoice.type == "ACCOUNTS_PAYABLE"
        ).all()
        
        for inv in purchase_invoices:
            existing = db.query(models.Expense).filter(models.Expense.remote_id == inv.remote_id).first()
            if not existing:
                expense = models.Expense(
                    remote_id=inv.remote_id,
                    company_id=inv.company_id,
                    transaction_date=inv.issue_date,
                    contact_id=inv.contact_id,
                    total_amount=inv.total_amount,
                    sub_total=inv.sub_total,
                    tax_amount=inv.tax_amount,
                    currency=inv.currency,
                    category=random.choice(["Infrastructure", "Software", "SaaS", "Consulting", "Rent", "Travel"]),
                    memo=inv.memo
                )
                db.add(expense)
        db.commit()

        # 3. Detect Anomalies
        print("🚨 Running deep anomaly detection...")
        detect_expense_anomalies(db, company.id)
        
        # Add a few manual high-value anomalies for demo
        today_date = date.today()
        for i in range(3):
            manual_anomaly = models.Anomaly(
                company_id=company.id,
                anomaly_date=today_date,
                type="fraud_alert" if i==0 else "budget_overrun",
                severity="critical" if i==0 else "high",
                description=f"Unusual pattern detected in {random.choice(['AWS', 'Hardware Depot'])} payments.",
                actual_value=Decimal(str(random.randint(50000, 100000))),
                expected_value=Decimal("5000"),
                status="open"
            )
            db.add(manual_anomaly)

        # 4. Generate Monthly Metrics (Historical)
        print("📊 Generating 6-month metrics history...")
        for month_offset in range(6, -1, -1):
            target_date = date.today() - timedelta(days=30 * month_offset)
            first_of_month = date(target_date.year, target_date.month, 1)
            
            revenue = db.query(func.sum(models.Invoice.total_amount)).filter(
                models.Invoice.company_id == company.id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.issue_date >= first_of_month,
                models.Invoice.issue_date < first_of_month + timedelta(days=31)
            ).scalar() or Decimal(random.randint(20000, 40000))

            expenses = db.query(func.sum(models.Invoice.total_amount)).filter(
                models.Invoice.company_id == company.id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.issue_date >= first_of_month,
                models.Invoice.issue_date < first_of_month + timedelta(days=31)
            ).scalar() or Decimal(random.randint(10000, 25000))

            metric = db.query(models.MonthlyMetric).filter(
                models.MonthlyMetric.company_id == company.id,
                models.MonthlyMetric.metric_month == first_of_month
            ).first()

            if not metric:
                metric = models.MonthlyMetric(company_id=company.id, metric_month=first_of_month)
                db.add(metric)
            
            metric.total_revenue = revenue
            metric.total_expenses = expenses
            metric.net_cash_flow = revenue - expenses
            metric.burn_rate = expenses
            metric.ending_cash = Decimal("200000") + (revenue * (6-month_offset)) - (expenses * (6-month_offset))
        
        db.commit()
        print("✅ SUCCESS! All tables now densely populated.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_metrics_and_anomalies()
