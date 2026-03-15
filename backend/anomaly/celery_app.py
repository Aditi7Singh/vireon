"""
Celery application configuration for Phase 4 Anomaly Detection.

Stack: Celery 5.5 + Redis
Broker: Redis (message queue)
Backend: Redis (results storage)
Scheduler: Celery Beat (scheduled tasks)

Usage:
  # Start worker
  celery -A backend.anomaly.celery_app worker --loglevel=info

  # Start beat scheduler
  celery -A backend.anomaly.celery_app beat --loglevel=info

  # Start monitoring UI (Flower)
  celery -A backend.anomaly.celery_app flower --port=5555
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Initialize Celery app
app = Celery("anomaly_detection")

# Celery configuration
app.conf.update(
    # Broker and backend
    broker_url=REDIS_URL,
    result_backend=REDIS_URL.replace("/0", "/1"),  # Use DB 1 for results
    
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=250,  # 4.1 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time
    
    # Retry configuration
    task_max_retries=3,
    task_default_retry_delay=30,  # 30 seconds before first retry
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_disable_rate_limits=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    
    # Task routing
    task_routes={
        "backend.anomaly.tasks.scan_for_anomalies": {"queue": "anomaly"},
        "backend.anomaly.tasks.cleanup_old_alerts": {"queue": "maintenance"},
    },
    
    # Define queues
    task_queues=(
        Queue("anomaly", Exchange("anomaly"), routing_key="anomaly"),
        Queue("maintenance", Exchange("maintenance"), routing_key="maintenance"),
    ),
)

# Celery Beat Schedule (periodic tasks)
app.conf.beat_schedule = {
    # Main anomaly scanner: every day at 2:00 AM UTC
    "scan_for_anomalies": {
        "task": "backend.anomaly.tasks.scan_for_anomalies",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC
        "options": {
            "queue": "anomaly",
            "expires": 3600,  # 1 hour
        },
    },
    
    # Alert cleanup: every Sunday at 3:00 AM UTC
    "cleanup_old_alerts": {
        "task": "backend.anomaly.tasks.cleanup_old_alerts",
        "schedule": crontab(day_of_week=6, hour=3, minute=0),  # Sun 3:00 AM UTC
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
    
    # Health check: every 6 hours (verify Celery is running)
    "check_redis_health": {
        "task": "backend.anomaly.tasks.check_redis_health",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "options": {"expires": 600},
    },
}

# Task event settings for Flower monitoring
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

if __name__ == "__main__":
    app.start()
