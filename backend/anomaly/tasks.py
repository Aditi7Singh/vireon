"""
Celery Tasks
============
Background tasks for anomaly detection and alerting.
"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from anomaly.celery_app import app
from anomaly.scanner import run_full_scan
from config.settings import BACKEND_URL, DATABASE_URL, REDIS_URL
from tasks.alert_tasks import _send_email


DEFAULT_ALERT_EMAIL = os.getenv("ALERT_FALLBACK_EMAIL", "sysswork@gmail.com")


@app.task(bind=True, max_retries=3, time_limit=300)
def scan_for_anomalies(self):
    """
    Main daily anomaly scanning task.
    
    Runs the full anomaly detection scan and sends notifications
    if critical alerts are found.
    """
    try:
        result = run_full_scan()
        
        # If critical alerts found, trigger notification
        if result.get("critical_count", 0) > 0:
            send_critical_alert_notification.delay(result)
        
        return result
        
    except Exception as exc:
        # Exponential backoff: 30s, 90s, 270s
        countdown = 30 * (2 ** self.request.retries)
        print(f"[TASKS] Scan failed, retrying in {countdown}s: {exc}")
        raise self.retry(exc=exc, countdown=countdown)


@app.task
def send_critical_alert_notification(scan_result: dict):
    """
    Send email notification for critical alerts.
    
    Args:
        scan_result: Result from scan_for_anomalies
    """
    try:
        subject = "[VIREON] Critical anomaly alert"
        body = (
            f"{scan_result.get('critical_count', 0)} critical financial anomalies were detected.\n"
            "Please review the dashboard for details."
        )
        _send_email([DEFAULT_ALERT_EMAIL], subject, body)
        print("[TASKS] Email notification sent successfully")
        
    except Exception as e:
        print(f"[TASKS] Failed to send email notification: {e}")


@app.task
def cleanup_old_alerts():
    """
    Weekly cleanup task for old alerts.
    
    - Auto-dismisses 'active' alerts older than 30 days
    - Hard-deletes 'dismissed'/'resolved' alerts older than 90 days
    
    Returns:
        Dictionary with counts of dismissed and deleted alerts
    """
    if not DATABASE_URL:
        print("[TASKS] No database configured, skipping cleanup")
        return {"dismissed": 0, "deleted": 0}
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Dismiss old active alerts (30 days)
            dismissed = conn.execute(text("""
                UPDATE alerts 
                SET status = 'dismissed', dismissed_at = NOW()
                WHERE status = 'active' 
                AND created_at < NOW() - INTERVAL '30 days'
            """))
            
            # Delete old resolved/dismissed alerts (90 days)
            deleted = conn.execute(text("""
                DELETE FROM alerts 
                WHERE status IN ('dismissed', 'resolved')
                AND created_at < NOW() - INTERVAL '90 days'
            """))
            
            conn.commit()
        
        result = {
            "dismissed": dismissed.rowcount,
            "deleted": deleted.rowcount
        }
        
        print(f"[TASKS] Cleanup complete: {result}")
        return result
        
    except Exception as e:
        print(f"[TASKS] Cleanup failed: {e}")
        return {"dismissed": 0, "deleted": 0, "error": str(e)}


@app.task
def trigger_scan_now():
    """
    On-demand scan trigger from FastAPI endpoint.
    
    Returns:
        Scan result dictionary
    """
    return run_full_scan()


@app.task
def sync_from_merge_dev(company_id_str: str):
    """
    Sync data from Merge.dev for production.
    """
    from database import SessionLocal
    from services.merge_service import MergeService
    from uuid import UUID
    
    db = SessionLocal()
    try:
        company_id = UUID(company_id_str)
        service = MergeService(db, company_id)
        result = service.sync_all()
        return result
    except Exception as e:
        print(f"[TASKS] Merge.dev sync failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@app.task
def quarterly_tax_reminder():
    """
    Quarterly check for tax liabilities.
    """
    if not DATABASE_URL:
        return {"status": "no_db"}
        
    try:
        from sqlalchemy.orm import sessionmaker
        from services.tax_service import calculate_quarterly_tax_summary
        import models
        from datetime import date
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # simplified check for all companies for current quarter
        today = date.today()
        current_quarter = (today.month - 1) // 3 + 1
        current_year = today.year
        
        companies = db.query(models.Company).all()
        alerts_sent = 0
        
        for comp in companies:
            summary = calculate_quarterly_tax_summary(db, comp.id, current_year, current_quarter)
            liability = summary.get("total_tax_liability", 0)
            
            if liability > 0:
                subject = f"[VIREON] Quarterly tax reminder: {comp.name}"
                body = (
                    f"Q{current_quarter} total estimated tax liability is ₹{liability:,.2f}.\n"
                    "Please review your dashboard."
                )
                _send_email([DEFAULT_ALERT_EMAIL], subject, body)
                alerts_sent += 1
                
        db.close()
        return {"status": "success", "alerts_sent": alerts_sent}
        
    except Exception as e:
        print(f"[TASKS] Quarterly tax reminder failed: {e}")
        return {"status": "error", "message": str(e)}


@app.task
def post_monthly_depreciation():
    """
    Monthly task to compute and post depreciation GL entries for all companies.
    Should be scheduled via Celery Beat to run on the last day of each month.
    """
    if not DATABASE_URL:
        return {"status": "no_db"}

    try:
        from sqlalchemy.orm import sessionmaker
        from services.depreciation_service import post_depreciation_to_gl
        import models
        from datetime import date

        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        today = date.today()
        companies = db.query(models.Company).all()
        results = []

        for comp in companies:
            result = post_depreciation_to_gl(db, comp.id, today)
            results.append({"company": comp.name, **result})

        db.close()
        print(f"[TASKS] Monthly depreciation posted for {len(results)} companies")
        return {"status": "success", "results": results}

    except Exception as e:
        print(f"[TASKS] Monthly depreciation posting failed: {e}")
        return {"status": "error", "message": str(e)}


@app.task
def auto_post_loan_payments():
    """
    Daily task to check for due loan payments and post them to the General Ledger.
    """
    if not DATABASE_URL:
        return {"status": "no_db"}

    try:
        from sqlalchemy.orm import sessionmaker
        from services.loan_service import auto_post_due_payments
        import models

        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        companies = db.query(models.Company).all()
        results = []

        for comp in companies:
            result = auto_post_due_payments(db, comp.id)
            results.append({"company": comp.name, **result})

        db.close()
        print(f"[TASKS] Daily loan payments processed for {len(results)} companies")
        return {"status": "success", "results": results}

    except Exception as e:
        print(f"[TASKS] Daily loan payment posting failed: {e}")
        return {"status": "error", "message": str(e)}

