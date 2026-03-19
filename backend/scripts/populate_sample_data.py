import sys
import os
from datetime import date, timedelta, datetime
import uuid
import random

# Add the parent directory to sys.path to import models and database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
import models

def populate():
    # Create all tables (ensure schema is up to date)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Get or Create Company
        company = db.query(models.Company).filter(models.Company.name == "SeedlingLabs").first()
        if not company:
            company = models.Company(
                name="SeedlingLabs",
                industry="Software",
                stage="Series A",
                initial_cash=5000000,
                founding_date=date(2024, 1, 1)
            )
            db.add(company)
            db.flush()
        
        company_id = company.id
        print(f"Using Company: {company.name} ({company_id})")

        # 2. Add Employees
        employees = [
            {"first_name": "Aditi", "last_name": "Singh", "email": "aditi@seedlinglabs.com", "role": "CEO", "salary": 250000},
            {"first_name": "Priya", "last_name": "Sharma", "email": "priya@seedlinglabs.com", "role": "CTO", "salary": 240000},
            {"first_name": "Rahul", "last_name": "Verma", "email": "rahul@seedlinglabs.com", "role": "Lead Engineer", "salary": 180000},
            {"first_name": "Sanya", "last_name": "Malhotra", "email": "sanya@seedlinglabs.com", "role": "Product Manager", "salary": 160000},
            {"first_name": "Vikram", "last_name": "Rao", "email": "vikram@seedlinglabs.com", "role": "Frontend Developer", "salary": 140000},
        ]

        db_employees = []
        for emp in employees:
            existing = db.query(models.Employee).filter(models.Employee.email == emp["email"]).first()
            if not existing:
                db_emp = models.Employee(
                    company_id=company_id,
                    employee_id=f"EMP-{emp['first_name'][:3].upper()}-{random.randint(100, 999)}",
                    first_name=emp["first_name"],
                    last_name=emp["last_name"],
                    email=emp["email"],
                    hire_date=date(2024, 6, 1),
                    salary=emp["salary"],
                    job_title=emp["role"],
                    department="Engineering" if "Developer" in emp["role"] or "Engineer" in emp["role"] or "CTO" in emp["role"] else "Management",
                    status="active"
                )
                db.add(db_emp)
                db_employees.append(db_emp)
            else:
                db_employees.append(existing)
        
        db.flush()
        print(f"Added/Verified {len(db_employees)} employees")

        # 3. Add Payroll Entries (Last 6 months)
        for emp in db_employees:
            for i in range(6):
                # Calculate last day of month correctly
                year = date.today().year
                month = date.today().month - i
                while month <= 0:
                    month += 12
                    year -= 1
                
                # Simple month-end log
                pay_date = date(year, month, 28)
                
                existing = db.query(models.PayrollEntry).filter(
                    models.PayrollEntry.employee_id == emp.id,
                    models.PayrollEntry.pay_date == pay_date
                ).first()
                if not existing:
                    gross = float(emp.salary or 0) / 12
                    tax = gross * 0.2
                    net = gross - tax
                    db_pr = models.PayrollEntry(
                        employee_id=emp.id,
                        pay_period_start=pay_date.replace(day=1),
                        pay_period_end=pay_date,
                        gross_pay=gross,
                        federal_tax=tax * 0.7,
                        state_tax=tax * 0.3,
                        net_pay=net,
                        pay_date=pay_date,
                        status="processed"
                    )
                    db.add(db_pr)
        
        print("Added payroll entries")

        # 4. Add Cloud Account & Costs
        cloud_acc = db.query(models.CloudAccount).filter(models.CloudAccount.account_id == "AWS-7788-9900").first()
        if not cloud_acc:
            cloud_acc = models.CloudAccount(
                company_id=company_id,
                provider="AWS",
                account_id="AWS-7788-9900",
                account_name="Production-Main",
                status="active"
            )
            db.add(cloud_acc)
            db.flush()
        
        # Add Cloud Costs
        services = ["EC2", "RDS", "S3", "Lambda", "CloudFront"]
        for i in range(30):
            usage_date = date.today() - timedelta(days=i)
            for service in services:
                existing = db.query(models.CloudCostDetail).filter(
                    models.CloudCostDetail.account_id == cloud_acc.id,
                    models.CloudCostDetail.service_name == service,
                    models.CloudCostDetail.usage_date == usage_date
                ).first()
                if not existing:
                    cost = models.CloudCostDetail(
                        account_id=cloud_acc.id,
                        service_name=service,
                        amount=random.uniform(10, 100),
                        usage_date=usage_date,
                        region="us-east-1"
                    )
                    db.add(cost)
        
        print("Added cloud accounts and costs")

        # 5. Add Bank Feed & Transactions
        bank_feed = db.query(models.BankFeed).filter(models.BankFeed.account_name == "HDFC-Primary").first()
        if not bank_feed:
            bank_feed = models.BankFeed(
                company_id=company_id,
                bank_name="HDFC Bank",
                account_name="HDFC-Primary",
                account_type="checking",
                account_number_last4="4455",
                currency="INR",
                status="active",
                last_synced_at=datetime.utcnow()
            )
            db.add(bank_feed)
            db.flush()

        # Add Banking Transactions
        merchants = ["Amazon Web Services", "Slack Technologies", "Google Workspace", "GitHub", "Vercel", "Uber", "Swiggy"]
        for i in range(50):
            t_date = date.today() - timedelta(days=i)
            merchant = random.choice(merchants)
            existing = db.query(models.BankingTransaction).filter(
                models.BankingTransaction.feed_id == bank_feed.id,
                models.BankingTransaction.transaction_date == t_date,
                models.BankingTransaction.merchant_name == merchant
            ).first()
            if not existing:
                is_saas = merchant in ["Slack Technologies", "Google Workspace", "GitHub", "Vercel"]
                amount = random.uniform(500, 5000)
                db_t = models.BankingTransaction(
                    feed_id=bank_feed.id,
                    transaction_date=t_date,
                    amount=amount,
                    description=f"Payment to {merchant}",
                    merchant_name=merchant,
                    category="Software" if is_saas else "Travel/Food",
                    is_saas=is_saas
                )
                db.add(db_t)
        
        print("Added bank feeds and transactions")

        db.commit()
        print("Successfully populated sample data!")
        
    except Exception as e:
        db.rollback()
        print(f"Error populating data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate()
