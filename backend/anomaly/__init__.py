"""
Phase 4: Anomaly Detection Engine

Background worker service that:
1. Scans GL transactions every 24 hours (Celery Beat)
2. Calculates 90-day moving averages per category
3. Detects spikes, trends, duplicates, and anomalies
4. Writes alerts to PostgreSQL
5. Exposes alerts via FastAPI /alerts endpoint
6. Integrates with LangGraph agent (get_active_alerts tool)

Components:
- celery_app: Celery configuration with Redis broker
- scanner: Core anomaly detection algorithm
- tasks: Celery task definitions for Beat scheduler
- migrations: Database schema setup

See PHASE_4_README.md for full documentation.
"""

__version__ = "1.0.0"
__all__ = ["scanner", "celery_app", "tasks"]
