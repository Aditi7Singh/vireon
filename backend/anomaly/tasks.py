"""
Celery Tasks
============
Background tasks for anomaly detection and alerting.
"""

import os
import httpx
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from anomaly.celery_app import app
from anomaly.scanner import run_full_scan
from config.settings import BACKEND_URL, DATABASE_URL, REDIS_URL


# Get Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


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
    Send Slack notification for critical alerts.
    
    Args:
        scan_result: Result from scan_for_anomalies
    """
    if not SLACK_WEBHOOK_URL:
        print("[TASKS] Slack not configured, skipping notification")
        return
    
    try:
        message = {
            "text": f"🚨 *Agentic CFO Alert*: {scan_result.get('critical_count', 0)} critical "
                    f"financial anomalies detected. Check your dashboard."
        }
        
        response = httpx.post(SLACK_WEBHOOK_URL, json=message, timeout=5)
        response.raise_for_status()
        
        print("[TASKS] Slack notification sent successfully")
        
    except Exception as e:
        print(f"[TASKS] Failed to send Slack notification: {e}")


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
def sync_from_merge_dev():
    """
    Sync data from Merge.dev for production.
    
    This task pulls accounting data from Merge.dev unified API
    and syncs it to the local database.
    """
    print("[TASKS] Merge.dev sync not yet implemented")
    # Would call MergeAccountingClient().sync_to_postgres()
    return {"status": "not_implemented"}
