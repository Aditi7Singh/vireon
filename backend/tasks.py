"""
Celery tasks for data synchronization and processing.

Tasks:
  - sync_from_merge_dev: Pull accounting data from Merge.dev (15min for critical, daily for full)
  - scan_for_anomalies: Detect financial anomalies post-sync
  - calculate_runway: Recalculate cash runway
"""

import os
import logging
from celery import Celery, Task
from celery.schedules import crontab
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery(__name__)

# Load config from environment
app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

# Define periodic tasks
app.conf.beat_schedule = {
    # Sync critical data every 15 minutes
    "sync-merge-critical": {
        "task": "backend.tasks.sync_from_merge_dev",
        "schedule": crontab(minute="*/15"),
        "kwargs": {"full_sync": False},
    },
    # Full sync daily at 2 AM UTC
    "sync-merge-full": {
        "task": "backend.tasks.sync_from_merge_dev",
        "schedule": crontab(hour=2, minute=0),
        "kwargs": {"full_sync": True},
    },
    # Recalculate runway every hour
    "calculate-runway": {
        "task": "backend.tasks.calculate_runway",
        "schedule": crontab(minute=0),
    },
}


class CallbackTask(Task):
    """Task with error callbacks"""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@app.task(base=CallbackTask, bind=True)
def sync_from_merge_dev(self, full_sync: bool = False):
    """
    Sync accounting data from Merge.dev to PostgreSQL.

    This task:
    1. Fetches data from Merge.dev Accounting API
    2. Validates data completeness
    3. Upserts to PostgreSQL
    4. Triggers anomaly detection
    5. Updates runway calculations

    Args:
        full_sync: If True, perform full sync. If False, critical data only.

    Returns:
        Sync result metadata
    """
    try:
        from backend.integrations.merge_client import get_merge_client

        logger.info(f"Starting Merge.dev sync (full_sync={full_sync})")

        client = get_merge_client()

        # Verify API connectivity
        if not client.health_check():
            logger.warning("Merge.dev health check failed, retrying...")
            raise Exception("Merge.dev API unreachable")

        # Perform sync
        result = client.sync_to_postgres()

        logger.info(f"Merge.dev sync completed: {result}")

        # Trigger anomaly detection post-sync
        scan_for_anomalies.delay()

        # Recalculate runway
        calculate_runway.delay()

        return {
            "task_id": self.request.id,
            "status": "success",
            **result,
        }

    except Exception as exc:
        logger.error(f"Merge.dev sync failed: {exc}")
        # Retry will be handled by CallbackTask
        raise


@app.task(base=CallbackTask, bind=True)
def scan_for_anomalies(self):
    """
    Detect financial anomalies in synced data.

    Looks for:
    - Unusual spending patterns
    - Revenue spikes/drops
    - Cash flow anomalies
    - MRR/ARR changes

    Returns:
        List of detected anomalies
    """
    try:
        from backend.anomaly_detection import detect_anomalies

        logger.info("Starting anomaly detection scan")

        anomalies = detect_anomalies()

        logger.info(f"Detected {len(anomalies)} anomalies")

        return {
            "task_id": self.request.id,
            "anomalies_found": len(anomalies),
            "anomalies": anomalies,
        }

    except Exception as exc:
        logger.error(f"Anomaly detection failed: {exc}")
        raise


@app.task(base=CallbackTask, bind=True)
def calculate_runway(self):
    """
    Recalculate cash runway based on latest financial data.

    Updates:
    - Cash balance
    - Monthly burn rate
    - Projected runway
    - Zero date

    Returns:
        Updated runway metrics
    """
    try:
        from backend.database import SessionLocal
        from backend.models import Runway
        from datetime import datetime, timedelta
        from decimal import Decimal

        logger.info("Recalculating runway")

        session = SessionLocal()

        try:
            # Fetch latest cash and burn data
            from sqlalchemy import desc

            cash_record = session.query(CashBalance).order_by(desc(CashBalance.synced_at)).first()
            expense_record = session.query(ExpenseBreakdown).order_by(desc(ExpenseBreakdown.synced_at)).first()

            if not cash_record or not expense_record:
                logger.warning("Insufficient data for runway calculation")
                return {"status": "skipped", "reason": "missing_data"}

            cash = float(cash_record.net_cash)
            monthly_burn = float(expense_record.total)

            if monthly_burn <= 0:
                logger.warning("Invalid burn rate for runway calculation")
                return {"status": "skipped", "reason": "invalid_burn"}

            # Calculate runway
            runway_months = cash / monthly_burn
            zero_date = datetime.utcnow() + timedelta(days=runway_months * 30)

            # Calculate confidence interval (±2 weeks)
            confidence_interval = {
                "low": runway_months - 0.33,
                "high": runway_months + 0.33,
            }

            # Upsert runway record
            runway_record = Runway(
                runway_months=runway_months,
                zero_date=zero_date,
                confidence_interval=confidence_interval,
                cash_available=Decimal(str(cash)),
                monthly_burn=Decimal(str(monthly_burn)),
                source="merge",
                calculated_at=datetime.utcnow(),
            )

            session.merge(runway_record)
            session.commit()

            logger.info(f"Runway updated: {runway_months:.1f} months, zero date: {zero_date.date()}")

            return {
                "task_id": self.request.id,
                "status": "success",
                "runway_months": runway_months,
                "zero_date": zero_date.isoformat(),
                "monthly_burn": monthly_burn,
                "cash_available": cash,
            }

        finally:
            session.close()

    except Exception as exc:
        logger.error(f"Runway calculation failed: {exc}")
        raise


@app.task
def health_check():
    """
    Periodic health check for Merge.dev integration.

    Logs status and alerts if API is unreachable.
    """
    try:
        from backend.integrations.merge_client import get_merge_client

        client = get_merge_client()

        if client.health_check():
            logger.info("Merge.dev health check: OK")
            return {"status": "ok"}
        else:
            logger.warning("Merge.dev health check: FAILED")
            return {"status": "warning"}

    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {"status": "error", "error": str(exc)}
