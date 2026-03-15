# Phase 4 Deployment Checklist

Use this checklist to deploy Phase 4 anomaly detection engine to production or staging.

## Pre-Deployment Setup (Do Once)

### 1. Database Setup
- [ ] PostgreSQL instance running (Neon.tech or local)
- [ ] Create alerts database or schema:
  ```bash
  createdb alerts  # if using local postgres
  ```
- [ ] Run migrations:
  ```bash
  python backend/anomaly/migrations/run_migrations.py
  ```
- [ ] Verify tables created:
  ```bash
  psql -d alerts -c "\dt"
  # Should show: anomaly_runs, alert_thresholds, alerts
  ```
- [ ] Verify default thresholds loaded:
  ```bash
  psql -d alerts -c "SELECT * FROM alert_thresholds LIMIT 5;"
  ```

### 2. Redis Setup
- [ ] Redis server installed (`brew install redis` or `apt-get install redis`)
- [ ] Redis running on localhost:6379 or configured in .env
- [ ] Test Redis connection:
  ```bash
  redis-cli ping  # Should return PONG
  ```

### 3. ERPNext Integration
- [ ] ERPNext instance running (locally or cloud)
- [ ] API access verified:
  ```bash
  curl -H "Authorization: Bearer {token}" \
    http://localhost:8001/api/resource/GL%20Entry?fields=["date","account","debit","credit"]&limit_page_length=5
  # Should return GL entries JSON
  ```
- [ ] Create API token if needed:
  - In ERPNext: Awesome Bar → "User" → Your User → API Token
  - Copy token to .env as `ERPNEXT_API_TOKEN`
- [ ] Set ERPNEXT_URL in .env

### 4. Environment Configuration
- [ ] Create/update `.env`:
  ```bash
  # Database
  DATABASE_URL=postgresql://user:pass@host:5432/alerts
  
  # ERPNext
  ERPNEXT_URL=http://localhost:8001
  ERPNEXT_API_TOKEN=your_token_here
  
  # Redis
  REDIS_URL=redis://localhost:6379/0
  REDIS_RESULTS_DB=1
  
  # Celery
  CELERY_BROKER_URL=redis://localhost:6379/0
  CELERY_RESULT_BACKEND=redis://localhost:6379/1
  
  # Backend API (for runway calls)
  BACKEND_URL=http://localhost:8000
  ```
- [ ] Load environment: `source .env` or `set -a && source .env`

### 5. Python Dependencies
- [ ] Install packages:
  ```bash
  pip install -r backend/requirements.txt
  ```
- [ ] Verify key packages:
  ```bash
  python -c "import pandas, numpy, scipy, celery, redis; print('OK')"
  ```

## Deployment Steps (Per Release)

### 6. Code Deployment
- [ ] Pull latest code:
  ```bash
  git pull origin main
  ```
- [ ] Review changes:
  ```bash
  git diff HEAD~1 backend/anomaly/
  ```
- [ ] Data migrations (if added):
  ```bash
  python backend/anomaly/migrations/run_migrations.py
  ```

### 7. Service Startup (Development)

**Terminal 1 - Redis:**
```bash
redis-server
# Should show: "Ready to accept connections"
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
celery -A anomaly.celery_app worker --loglevel=info --concurrency=2
# Should show: "ready to accept tasks"
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
cd backend
celery -A anomaly.celery_app beat --loglevel=info
# Should show: "Scheduler started"
# Should show: "[2024-...] Scheduler: Sending due task scan_for_anomalies"
```

**Terminal 4 - Monitoring (Optional):**
```bash
celery -A backend.anomaly.celery_app flower --port=5555
# Open browser: http://localhost:5555
```

**Terminal 5 - FastAPI Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
# Should show: "Uvicorn running on http://0.0.0.0:8000"
```

### 8. Verification Checklist

#### 8a. Module Imports
- [ ] Test imports:
  ```bash
  python -c "from backend.anomaly.scanner import run_full_scan; print('✓ Scanner imports')"
  python -c "from backend.anomaly.tasks import scan_for_anomalies; print('✓ Tasks import')"
  python -c "from backend.anomaly.celery_app import app; print('✓ Celery app imports')"
  ```

#### 8b. Database Connectivity
- [ ] Test PostgreSQL:
  ```bash
  python -c "
  import psycopg2
  conn = psycopg2.connect(os.environ['DATABASE_URL'])
  cursor = conn.cursor()
  cursor.execute('SELECT COUNT(*) FROM alerts;')
  print(f'✓ PostgreSQL: {cursor.fetchone()[0]} alerts in DB')
  conn.close()
  "
  ```

#### 8c. Redis Connectivity
- [ ] Test Redis:
  ```bash
  python -c "
  import redis
  r = redis.from_url(os.environ['REDIS_URL'])
  print(f'✓ Redis: {r.ping()} (latency OK)')
  "
  ```

#### 8d. Run Manual Scan
- [ ] Execute full scan:
  ```bash
  python -c "
  from backend.anomaly.scanner import run_full_scan
  import json
  result = run_full_scan()
  print(json.dumps(result, indent=2, default=str))
  "
  ```
- [ ] Check output:
  - Status should be: "success" or "partial"
  - Should show alerts_found: N
  - Should show scan_duration_seconds: T

#### 8e. Test Celery Task
- [ ] Trigger task manually:
  ```bash
  python -c "
  from backend.anomaly.tasks import scan_for_anomalies
  task = scan_for_anomalies.delay()
  print(f'Task ID: {task.id}')
  result = task.get(timeout=300)
  print(result)
  "
  ```
- [ ] Monitor in Flower: http://localhost:5555/tasks

#### 8f. Test Beat Scheduler
- [ ] Wait for automatic execution (watch Celery Beat log):
  ```
  [2024-...] Scheduler: Sending due task scan_for_anomalies (...)
  [2024-...] Created task execution.celery.scan_for_anomalies (...)
  ```
- [ ] Verify in PostgreSQL:
  ```bash
  psql -d alerts -c "SELECT * FROM anomaly_runs ORDER BY run_at DESC LIMIT 1;"
  # Should show recent run
  ```

#### 8g. Test API Endpoint
- [ ] Check REST API (if integrated in FastAPI):
  ```bash
  curl http://localhost:8000/alerts | jq .
  ```
- [ ] Response format:
  ```json
  [
    {
      "id": 123,
      "severity": "CRITICAL",
      "alert_type": "spike",
      "category": "aws",
      "amount": 18200,
      "baseline": 8000,
      "delta_pct": 127.5,
      "description": "AWS spending spiked...",
      "runway_impact": -2.3,
      "created_at": "2024-..."
    }
  ]
  ```

#### 8h. Test Dashboard Integration
- [ ] If frontend exists, verify alerts display:
  ```
  Dashboard → Alerts section → Should show scanner alerts
  Filter by severity, category, date range
  ```

### 9. Load Test (Optional)

- [ ] Trigger 5 scans in parallel:
  ```bash
  python -c "
  from backend.anomaly.tasks import scan_for_anomalies
  import time
  
  tasks = [scan_for_anomalies.delay() for _ in range(5)]
  print(f'Sent {len(tasks)} tasks')
  
  for i, task in enumerate(tasks):
      print(f'Task {i+1}: {task.get(timeout=300)}')
  "
  ```
- [ ] Monitor Resource Usage:
  ```bash
  # In separate terminal
  watch -n 1 "redis-cli INFO stats | grep total_commands_processed"
  ```
- [ ] Verify Redis not overloaded (should handle 5 tasks easily)

### 10. Monitoring & Alerting (Production)

- [ ] Set up log aggregation (e.g., ELK, CloudWatch)
- [ ] Monitor key metrics:
  - Scan duration (should be < 5s)
  - Redis memory usage (should be < 500MB)
  - PostgreSQL connections (should be < 10)
  - Alert volume (should be < 10 per scan typically)
- [ ] Create alerts for:
  - Scan failures (status = "error")
  - Scan timeout (> 60s)
  - Redis connection errors
  - Database connection errors

### 11. Threshold Configuration (Tuning)

- [ ] Review default thresholds:
  ```bash
  psql -d alerts -c "SELECT * FROM alert_thresholds;"
  ```
- [ ] Adjust sensitivity based on first 1-2 weeks:
  - Too many false positives? → Increase thresholds
  - Missing real anomalies? → Decrease thresholds
  - Example:
    ```sql
    -- Make AWS more sensitive (lower thresholds)
    UPDATE alert_thresholds 
    SET warn_pct = 15.0, critical_pct = 30.0,
        stddev_warn = 1.5, stddev_crit = 2.5
    WHERE category = 'aws';
    ```

### 12. Team Training

- [ ] Share PHASE_4_SCANNER_REFERENCE.md with team
- [ ] Demo how to:
  - Review active alerts: `curl http://localhost:8000/alerts`
  - Dismiss alert: `curl -X PUT http://localhost:8000/alerts/{id} -d '{"status":"dismissed"}'`
  - Check scan history: `psql -d alerts -c "SELECT * FROM anomaly_runs;"`
- [ ] Establish alert response SLA:
  - CRITICAL: Review within 1 hour
  - WARNING: Review within 4 hours
  - INFO: Review within 24 hours

## Post-Deployment (Day 1)

- [ ] Check that Beat tasks executed on schedule
- [ ] Review any alerts generated
- [ ] Check for error logs in Celery worker
- [ ] Verify Redis memory usage is stable
- [ ] Verify PostgreSQL disk usage is acceptable

## Weekly Checks

- [ ] Database disk usage trending:
  ```bash
  # PostgreSQL size
  psql -d alerts -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"
  ```
- [ ] Alert volume statistics:
  ```bash
  psql -d alerts -c "
  SELECT 
    severity, 
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE status = 'active') as active
  FROM alerts
  GROUP BY severity
  ORDER BY severity DESC;
  "
  ```
- [ ] Scan performance:
  ```bash
  psql -d alerts -c "
  SELECT 
    DATE(run_at) as date,
    COUNT(*) as runs,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms
  FROM anomaly_runs
  WHERE run_at > CURRENT_DATE - INTERVAL '7 days'
  GROUP BY DATE(run_at);
  "
  ```
- [ ] Error frequency:
  ```bash
  psql -d alerts -c "
  SELECT COUNT(*) as error_count 
  FROM anomaly_runs 
  WHERE status = 'error' 
  AND run_at > CURRENT_DATE - INTERVAL '7 days';
  "
  ```

## Troubleshooting Quick Reference

| Issue | Cause | Fix |
|-------|-------|-----|
| `CRITICAL: Can't connect to broker` | Redis not running | `redis-server` in Terminal 1 |
| `Task timeout after 300s` | Scan taking too long | Optimize GL query or reduce data window |
| `ModuleNotFoundError: pandas` | Requirements not installed | `pip install -r requirements.txt` |
| `psycopg2.OperationalError` | PostgreSQL not running or wrong URL | Check DATABASE_URL, start postgres |
| `No alerts generated` | No GL data in ERPNext | Add test GL entries or check ERPNext API |
| `Too many duplicate alerts` | Deduplication window too large | Reduce from 7 days to 5 days in scanner.py |
| `Runway impact always None` | FastAPI /runway endpoint missing | Implement endpoint from Phase 3 agent |

## Rollback Plan

If critical issues discovered after deployment:

1. Stop Beat scheduler (Terminal 3):
   ```bash
   Ctrl+C
   ```

2. Stop Celery worker (Terminal 2):
   ```bash
   Ctrl+C
   ```

3. Revert code:
   ```bash
   git revert HEAD
   git push
   ```

4. Drop alerts tables (WARNING - data loss):
   ```bash
   python -c "
   from backend.anomaly.migrations.run_migrations import drop_tables
   drop_tables()  # DESTRUCTIVE - only if absolutely needed
   "
   ```

5. Redeploy previous version:
   ```bash
   git checkout main
   python backend/anomaly/migrations/run_migrations.py
   ```

---

## Success Criteria

Phase 4 deployment is successful when:

- [x] All 3 Celery Beat tasks execute on schedule
- [x] scan_for_anomalies completes in < 10 seconds
- [x] At least 1 alert generated per week (or configured threshold met)
- [x] PostgreSQL alerts table populated with new rows
- [x] No errors in Celery worker logs for 48 hours
- [x] Team can access and interpret alerts
- [x] Thresholds tuned for false positive rate < 10%

Once all criteria met, Phase 4 is production-ready! 🚀
