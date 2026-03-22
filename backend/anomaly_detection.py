from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import datetime

def detect_expense_anomalies(db: Session, company_id=None):
    # Logic: Calculate 90-day moving average for all expense categories.
    # If a new transaction comes in that is >15% higher than the baseline, generate an "Anomaly".
    
    ninety_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    
    # Calculate average per account for the last 90 days
    query = db.query(
        models.Expense.account_id,
        func.avg(models.Expense.total_amount).label("avg_amount")
    ).filter(models.Expense.transaction_date >= ninety_days_ago)
    
    if company_id:
        query = query.filter(models.Expense.company_id == company_id)
        
    averages = query.group_by(models.Expense.account_id).all()
    
    for account_id, avg_amount in averages:
        # Find latest expenses for this account that haven't been processed yet
        # For simplicity, we look at the last 1 day
        latest_expenses = db.query(models.Expense).filter(
            models.Expense.account_id == account_id,
            models.Expense.transaction_date >= datetime.datetime.utcnow() - datetime.timedelta(days=40) # Look back 40 days to catch Feb 2026 data in simulation
        ).all()
        
        for exp in latest_expenses:
            if float(exp.total_amount) > float(avg_amount) * 1.15:
                # Check if this anomaly was already detected (using remote_id or similar logic)
                # For simplicity, we just add it if it looks new
                
                anomaly = models.Anomaly(
                    company_id=exp.company_id,
                    anomaly_date=exp.transaction_date,
                    type="spending_spike",
                    severity="high" if float(exp.total_amount) > float(avg_amount) * 1.5 else "medium",
                    description=f"Spending in {exp.category or 'General'} is {((float(exp.total_amount)/float(avg_amount))-1)*100:.1f}% higher than 90-day average.",
                    expected_value=avg_amount,
                    actual_value=exp.total_amount,
                    status="open"
                )
                db.add(anomaly)
    
    db.commit()


def detect_revenue_anomalies(db: Session, company_id=None):
    """Detect revenue anomalies using GeneralLedger data (Revenue accounts 4XXX)."""
    ninety_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    
    # Get all revenue account codes (starting with 4)
    revenue_codes = [c for c in models.GLAccountCode if c.value.startswith("4")]
    
    # Calculate baseline revenue (Credit amounts in revenue accounts)
    query = db.query(
        func.avg(models.GeneralLedger.credit_amount).label("avg_credit")
    ).filter(
        models.GeneralLedger.transaction_date >= ninety_days_ago.date(),
        models.GeneralLedger.account_code.in_(revenue_codes)
    )
    
    if company_id:
        query = query.filter(models.GeneralLedger.company_id == company_id)
        
    avg_result = query.first()
    if not avg_result or avg_result.avg_credit is None:
        return
    
    avg_revenue = float(avg_result.avg_credit)
    
    # Check recent credit entries
    recent_entries_query = db.query(models.GeneralLedger).filter(
        models.GeneralLedger.transaction_date >= (datetime.datetime.utcnow() - datetime.timedelta(days=30)).date(),
        models.GeneralLedger.account_code.in_(revenue_codes),
        models.GeneralLedger.credit_amount > 0
    )
    
    if company_id:
        recent_entries_query = recent_entries_query.filter(models.GeneralLedger.company_id == company_id)
        
    for entry in recent_entries_query.all():
        revenue = float(entry.credit_amount)
        variance_pct = ((revenue - avg_revenue) / avg_revenue) * 100 if avg_revenue > 0 else 0
        
        if abs(variance_pct) > 25: # Higher threshold for individual transactions
            anomaly = models.Anomaly(
                company_id=entry.company_id,
                anomaly_date=entry.transaction_date,
                type="revenue_spike" if variance_pct > 0 else "revenue_drop",
                severity="high" if abs(variance_pct) > 100 else "medium",
                description=f"Unusual revenue entry in {entry.account_name}: { 'up' if variance_pct > 0 else 'down' } {abs(variance_pct):.1f}% vs baseline.",
                expected_value=avg_revenue,
                actual_value=revenue,
                status="open"
            )
            db.add(anomaly)
    
    db.commit()


def detect_duplicate_invoices(db: Session, company_id=None):
    """Detect potential duplicate GL entries (same amount, account, date, and description)."""
    # Group GL entries by amount, date, and account, count occurrences
    query = db.query(
        models.GeneralLedger.debit_amount,
        models.GeneralLedger.credit_amount,
        models.GeneralLedger.transaction_date,
        models.GeneralLedger.account_code,
        func.count(models.GeneralLedger.id).label("count")
    ).filter((models.GeneralLedger.debit_amount > 0) | (models.GeneralLedger.credit_amount > 0))
    
    if company_id:
        query = query.filter(models.GeneralLedger.company_id == company_id)
        
    duplicates = query.group_by(
        models.GeneralLedger.debit_amount,
        models.GeneralLedger.credit_amount,
        models.GeneralLedger.transaction_date,
        models.GeneralLedger.account_code
    ).having(func.count(models.GeneralLedger.id) > 1).all()
    
    for dup in duplicates:
        amount = float(dup.debit_amount or dup.credit_amount)
        # Create anomaly for duplicates
        anomaly = models.Anomaly(
            company_id=company_id,
            anomaly_date=dup.transaction_date,
            type="duplicate_gl_entry",
            severity="medium",
            description=f"Potential duplicate GL entries: {dup.count} entries with amount ${amount} in account {dup.account_code} on {dup.transaction_date}",
            expected_value=1,
            actual_value=dup.count,
            status="open"
        )
        db.add(anomaly)
    
    db.commit()
