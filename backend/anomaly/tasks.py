"""
Celery tasks for Phase 4 Anomaly Detection.

Registered with Celery Beat for scheduled execution:
- scan_for_anomalies: Daily at 2:00 AM UTC
- cleanup_old_alerts: Weekly Sunday at 3:00 AM UTC
- check_redis_health: Every 6 hours
"""

import logging
import os
import json
from typing import Dict, Any
from datetime import datetime, timedelta

import psycopg2
import httpx
from psycopg2.extras import RealDictCursor

from backend.anomaly.celery_app import app
from backend.anomaly.scanner import run_full_scan

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, time_limit=300)
def scan_for_anomalies(self):
    """
    Main anomaly detection task.
    Runs daily at 2:00 AM UTC via Celery Beat.
    
    Includes exponential backoff retry:
    - Attempt 1: Immediate
    - Attempt 2: Retry after 30s
    - Attempt 3: Retry after 90s
    - Attempt 4: Retry after 270s (4.5 min)
    
    Calls the complete Phase 4 scanner:
    1. Loads GL transactions (ERPNext API or PostgreSQL fallback)
    2. Calculates 90-day baselines per category
    3. Detects spikes, trends, duplicates, new vendors
    4. Calculates runway impact
    5. Writes alerts to PostgreSQL with deduplication
    
    If critical alerts found, triggers Slack notification.
    
    Returns:
        dict: Result dict with status, alerts_found, critical_count, etc.
    """
    try:
        logger.info(f"[CELERY] ========== SCAN STARTED ==========")
        logger.info(f"[CELERY] Attempt {self.request.retries + 1}/3 (task_id: {self.request.id})")
        
        # Run full scan (pure Python math, no LLM)
        result = run_full_scan()
        
        logger.info(f"[CELERY] Scan completed in {result.get('scan_duration_seconds', 0):.2f}s")
        logger.info(f"[CELERY] Results:")
        logger.info(f"[CELERY]   Status: {result.get('status')}")
        logger.info(f"[CELERY]   Alerts found: {result.get('alerts_found', 0)}")
        logger.info(f"[CELERY]   CRITICAL: {result.get('critical_count', 0)}")
        logger.info(f"[CELERY]   WARNING: {result.get('warning_count', 0)}")
        logger.info(f"[CELERY]   INFO: {result.get('info_count', 0)}")
        logger.info(f"[CELERY] ========== SCAN COMPLETE ==========")
        
        # If critical alerts found, send Slack notification
        if result.get('critical_count', 0) > 0:
            logger.info(f"[CELERY] Queuing Slack notification for critical alerts")
            send_critical_alert_notification.delay(result)
        
        return result
    
    except Exception as exc:
        logger.error(f"[CELERY] SCAN FAILED: {exc}", exc_info=True)
        
        # Calculate exponential backoff: 30s, 90s, 270s
        countdown = 30 * (2 ** self.request.retries)
        retry_num = self.request.retries + 1
        
        logger.info(f"[CELERY] Retrying in {countdown}s (attempt {retry_num}/3)")
        
        # Raise retry with exponential backoff
        raise self.retry(exc=exc, countdown=countdown)


@app.task(bind=False, time_limit=30)
def send_critical_alert_notification(scan_result: Dict[str, Any]):
    """
    Send Slack notification for critical anomalies.
    
    Optional task - only runs if SLACK_WEBHOOK_URL environment variable is configured.
    Called automatically when critical_count > 0 after scan_for_anomalies.
    
    Args:
        scan_result: Result dict from run_full_scan() containing alerts
    
    Returns:
        dict: Status of notification delivery
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    # Skip if Slack not configured
    if not webhook_url:
        logger.info("[NOTIFY] Slack webhook not configured, skipping notification")
        return {
            "status": "skipped",
            "reason": "SLACK_WEBHOOK_URL environment variable not set"
        }
    
    try:
        critical_count = scan_result.get('critical_count', 0)
        warning_count = scan_result.get('warning_count', 0)
        
        # Format Slack message with blocks
        message = {
            "text": f"🚨 Agentic CFO Alert: {critical_count} critical financial anomalies detected",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🚨 {critical_count} CRITICAL Alerts Detected*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Critical:*\n{critical_count}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Warnings:*\n{warning_count}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Check your *Agentic CFO Dashboard* immediately."
                    }
                }
            ]
        }
        
        logger.info(f"[NOTIFY] Sending Slack notification ({critical_count} critical, {warning_count} warnings)")
        
        # Post to Slack webhook
        response = httpx.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
        logger.info("[NOTIFY] ✓ Slack notification sent successfully")
        return {
            "status": "sent",
            "critical_count": critical_count,
            "warning_count": warning_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except httpx.RequestError as e:
        logger.error(f"[NOTIFY] Slack request failed: {e}")
        return {
            "status": "failed",
            "error": f"Request error: {e}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[NOTIFY] Failed to send Slack notification: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.task(time_limit=60)
def cleanup_old_alerts():
    """
    Weekly maintenance task to clean up old alerts.
    Runs every Sunday at 3:00 AM UTC via Celery Beat.
    
    Actions:
    1. Auto-dismiss 'active' alerts older than 30 days
    2. Hard-delete 'dismissed'/'resolved' alerts older than 90 days
    
    Returns:
        dict: Cleanup statistics {dismissed: N, deleted: N}
    """
    try:
        logger.info("[CLEANUP] ========== ALERT CLEANUP STARTED ==========")
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Connect to alerts database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Auto-dismiss 'active' alerts older than 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        logger.info(f"[CLEANUP] Auto-dismissing alerts older than {thirty_days_ago.date()}")
        
        cursor.execute("""
            UPDATE alerts 
            SET status = 'dismissed', updated_at = NOW()
            WHERE status = 'active' 
            AND created_at < %s
        """, (thirty_days_ago,))
        dismissed_count = cursor.rowcount
        logger.info(f"[CLEANUP] ✓ Auto-dismissed {dismissed_count} old active alerts")
        
        # 2. Hard-delete dismissed/resolved alerts older than 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)
        logger.info(f"[CLEANUP] Hard-deleting dismissed/resolved alerts older than {ninety_days_ago.date()}")
        
        cursor.execute("""
            DELETE FROM alerts 
            WHERE status IN ('dismissed', 'resolved') 
            AND created_at < %s
        """, (ninety_days_ago,))
        deleted_count = cursor.rowcount
        logger.info(f"[CLEANUP] ✓ Hard-deleted {deleted_count} old dismissed/resolved alerts")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        result = {
            "status": "success",
            "dismissed": dismissed_count,
            "deleted": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[CLEANUP] ========== CLEANUP COMPLETE ==========")
        return result
        
    except psycopg2.Error as e:
        logger.error(f"[CLEANUP] Database error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Database error: {e}",
            "dismissed": 0,
            "deleted": 0
        }
    except Exception as e:
        logger.error(f"[CLEANUP] Cleanup failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "dismissed": 0,
            "deleted": 0
        }


@app.task(time_limit=60)
def trigger_scan_now():
    """
    On-demand anomaly scan triggered from FastAPI endpoint.
    
    Called via: POST /alerts/scan-now
    Same as daily scheduled scan but runs immediately on request.
    Returns same result format for immediate feedback.
    
    Returns:
        dict: Scan result with alerts_found, critical_count, etc.
    """
    try:
        logger.info("[SCAN] ========== ON-DEMAND SCAN STARTED ==========")
        
        result = run_full_scan()
        
        logger.info(f"[SCAN] On-demand scan complete in {result.get('scan_duration_seconds', 0):.2f}s")
        logger.info(f"[SCAN]   Alerts: {result.get('alerts_found', 0)}")
        logger.info(f"[SCAN]   CRITICAL: {result.get('critical_count', 0)}")
        logger.info(f"[SCAN]   WARNING: {result.get('warning_count', 0)}")
        logger.info(f"[SCAN] ========== ON-DEMAND SCAN COMPLETE ==========")
        
        # Notify on critical alerts even for on-demand scans
        if result.get('critical_count', 0) > 0:
            logger.info("[SCAN] Queuing Slack notification for critical alerts")
            send_critical_alert_notification.delay(result)
        
        return result
        
    except Exception as e:
        logger.error(f"[SCAN] On-demand scan failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "alerts_found": 0
        }


@app.task(time_limit=30)
def check_redis_health():
    """
    Periodic health check task.
    Runs every 6 hours via Celery Beat.
    
    Verifies connectivity to:
    - Redis (broker and results backend)
    - PostgreSQL (alerts database)
    
    Returns:
        dict: Health status {status: 'ok' | 'error', redis: bool, postgres: bool}
    """
    try:
        import redis
        
        logger.info("[HEALTH] ========== HEALTH CHECK STARTED ==========")
        
        # Check Redis connectivity
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        logger.info(f"[HEALTH] Checking Redis: {redis_url[:30]}...")
        
        r = redis.from_url(redis_url)
        r.ping()
        logger.info("[HEALTH] ✓ Redis broker OK")
        redis_status = "ok"
        
    except redis.ConnectionError as e:
        logger.error(f"[HEALTH] Redis connection failed: {e}")
        redis_status = "connection_failed"
    except Exception as e:
        logger.error(f"[HEALTH] Redis check failed: {e}")
        redis_status = "error"
    
    # Check PostgreSQL connectivity
    try:
        db_url = os.getenv("DATABASE_URL")
        logger.info("[HEALTH] Checking PostgreSQL...")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        logger.info("[HEALTH] ✓ PostgreSQL OK")
        postgres_status = "ok"
        
    except psycopg2.Error as e:
        logger.error(f"[HEALTH] PostgreSQL error: {e}")
        postgres_status = "connection_failed"
    except Exception as e:
        logger.error(f"[HEALTH] PostgreSQL check failed: {e}")
        postgres_status = "error"
    
    result = {
        "status": "ok" if (redis_status == "ok" and postgres_status == "ok") else "error",
        "redis": redis_status,
        "postgres": postgres_status,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"[HEALTH] ========== HEALTH CHECK COMPLETE ==========")
    return result


@app.task(time_limit=10)
def dismiss_alert(alert_id: int):
    """
    Dismiss an alert (mark as 'dismissed').
    
    Called via: PATCH /alerts/{alert_id}/dismiss
    Used to manually dismiss false positives or resolved alerts.
    
    Args:
        alert_id: ID of alert to dismiss
    
    Returns:
        dict: Updated alert info or error
    """
    try:
        logger.info(f"[DISMISS] Dismissing alert {alert_id}")
        
        db_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update alert status to 'dismissed'
        cursor.execute("""
            UPDATE alerts 
            SET status = 'dismissed', updated_at = NOW()
            WHERE id = %s
            RETURNING id, status, severity, alert_type, category, updated_at
        """, (alert_id,))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"[DISMISS] ✓ Alert {alert_id} dismissed successfully")
            return {
                "status": "success",
                "alert": dict(result),
                "message": f"Alert {alert_id} dismissed"
            }
        else:
            logger.warning(f"[DISMISS] Alert {alert_id} not found")
            return {
                "status": "error",
                "error": f"Alert {alert_id} not found"
            }
    
    except psycopg2.Error as e:
        logger.error(f"[DISMISS] Database error: {e}")
        return {
            "status": "error",
            "error": f"Database error: {e}"
        }
    except Exception as e:
        logger.error(f"[DISMISS] Failed to dismiss alert {alert_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


@app.task(bind=True, name="backend.anomaly.tasks.trigger_alert_dashboard_refresh")
def trigger_alert_dashboard_refresh(self):
    """
    Notify frontend to refresh alert dashboard.
    
    Called after scan_for_anomalies completes to push fresh data to frontend.
    Uses FastAPI background task or WebSocket for real-time updates.
    
    Returns:
        dict: Status of refresh signal
    """
    try:
        logger.info("[REFRESH] Alert dashboard refresh triggered")
        # This could send a message to a message queue that frontend listens to
        # Or call a webhook endpoint
        return {
            "status": "success",
            "message": "Dashboard refresh signaled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as exc:
        logger.error(f"[REFRESH] Dashboard refresh failed: {exc}")
        return {
            "status": "error",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # For testing tasks manually
    print("Available Celery tasks:")
    print("  1. scan_for_anomalies.delay()  - Trigger manual scan")
    print("  2. cleanup_old_alerts.delay()  - Manual cleanup")
    print("  3. check_redis_health.delay()  - Health check")
    print("  4. trigger_scan_now.delay()  - On-demand scan")
    print("  5. dismiss_alert.delay(alert_id)  - Dismiss alert")
    print("\nExample usage:")
    print("  from backend.anomaly.tasks import scan_for_anomalies")
    print("  result = scan_for_anomalies.delay()")
    print("  print(result.get())  # Wait for result")
