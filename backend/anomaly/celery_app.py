"""
Celery Application Configuration
================================
Celery + Redis configuration with Beat scheduler.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "vireon_anomaly",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["anomaly.tasks", "tasks.alert_tasks", "tasks.document_tasks", "tasks.fx_tasks"]
)

# Configure Celery
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_time_limit=300,  # 5 minutes max per scan
    task_soft_time_limit=240,  # 4 minutes soft limit
    task_max_retries=3,
    
    # Retry settings with exponential backoff
    task_default_retry_delay=30,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Celery Beat schedule
app.conf.beat_schedule = {
    # Daily anomaly scan at 2am UTC
    "daily-anomaly-scan": {
        "task": "anomaly.tasks.scan_for_anomalies",
        "schedule": crontab(hour=2, minute=0),
    },
    # Weekly cleanup on Sunday at 3am UTC
    "weekly-cleanup": {
        "task": "anomaly.tasks.cleanup_old_alerts",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
    # Daily runway alert check at 9:00 AM IST (03:30 UTC)
    "daily-runway-alert-check": {
        "task": "tasks.alert_tasks.check_runway_alerts_all_companies",
        "schedule": crontab(hour=3, minute=30),
    },
    # Monthly FX revaluation snapshot on the 1st day of month at 01:00 UTC
    "monthly-fx-revaluation": {
        "task": "tasks.fx_tasks.run_monthly_fx_revaluation_all_companies",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
    },
}


if __name__ == "__main__":
    app.start()
