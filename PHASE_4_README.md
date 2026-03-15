# PHASE 4: ANOMALY DETECTION ENGINE
# Complete Implementation Guide

## Overview

Phase 4 is the "always-on financial watchdog" for SeedlingLabs. While Phase 3 (LangGraph agent) answers questions reactively, Phase 4 runs proactively in the background — scanning GL transactions every 24 hours, learning spending patterns, and firing alerts BEFORE problems escalate.

**Architecture:**
```
PostgreSQL (Neon.tech)
    ↑
    ├─ alerts table (anomalies detected)
    ├─ alert_thresholds (per-category config)
    └─ anomaly_runs (job execution log)
    
Redis (Railway.app free tier)
    ↑
    └─ Celery message broker + results backend
    
Celery Workers (stateless, scalable)
    ├─ scan_for_anomalies (daily 2:00 AM UTC)
    ├─ cleanup_old_alerts (Sunday 3:00 AM UTC)
    └─ check_redis_health (every 6 hours)
    
Celery Beat (scheduler)
    └─ Triggers tasks on schedule
    
Flower (monitoring UI)
    └─ port 5555, live task monitoring
    
FastAPI Backend
    ├─ GET /alerts (returns PostgreSQL alerts)
    ├─ POST /alerts/{id}/dismiss (mark as resolved)
    └─ Integrates with Phase 3 agent
    
LangGraph Agent (Phase 3)
    └─ get_active_alerts() tool surfaces anomalies
```

---

## SETUP INSTRUCTIONS

### 1. Install Dependencies

```bash
cd vireon/

# Install Phase 4 packages
pip install celery[redis]==5.5.3 redis==5.0.8 flower==2.0.1 psycopg2-binary

# Or install everything from requirements.txt
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables

**Option A: Local Development (Recommended for testing)**

```bash
# In .env file (or export as environment variables)
DATABASE_URL=postgresql://localhost/vireon_alerts
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
BACKEND_URL=http://localhost:8000
COMPANY_NAME=SeedlingLabs
```

**Option B: Production (on Railway.app)**

```bash
# Redis on Railway (free tier 500MB)
REDIS_URL=redis://:password@rai.railway.internal:6379

# PostgreSQL on Neon.tech (free tier)
DATABASE_URL=postgresql://user:password@ep-silver.neon.tech/vireon_alerts
```

### 3. Create Database Tables

Run the migration:

```bash
# From vireon/ directory
python backend/anomaly/migrations/run_migrations.py
```

**Output:**
```
✓ Connected to PostgreSQL via Neon.tech
✓ Executed: 001_create_alerts.sql
✓ Created tables: alerts, alert_thresholds, anomaly_runs
✓ Alert thresholds loaded (8 categories):
  aws           → Warning: 15.0%, Critical: 50.0%
  payroll       → Warning: 15.0%, Critical: 50.0%
  saas          → Warning: 15.0%, Critical: 50.0%
  marketing     → Warning: 15.0%, Critical: 50.0%
  ...
SUCCESS: All 1 migration(s) completed
```

### 4. Start Local Redis

You can use:

**Option A: Docker (easiest)**
```bash
docker run --name redis-phase4 -d -p 6379:6379 redis:7-alpine
```

**Option B: Brew (macOS)**
```bash
brew install redis
redis-server
```

**Option C: Windows WSL2 (if using WSL)**
```bash
wsl
redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Response: PONG
```

### 5. Start Celery Components

Open 4 terminal windows (or use `tmux`/`screen`):

**Terminal 1: Celery Worker**
```bash
cd vireon/
celery -A backend.anomaly.celery_app worker --loglevel=info
```

Expected output:
```
 ---------- celery@yagna 4.0.3 (verdin)
 --- ***** ----- 
 -- ******* ---- Linux-5.15.0-1-generic-x64 2026-03-15 14:21:00
 - *** --- * --- 
 - ** ---------- [config]
 - ** ---------- .hostname: yagna@MacBook.local
 - ** ---------- .broker: redis://localhost:6379/0
 - ** ---------- | app.Include('backend.anomaly.celery_app')
 - ** ---------- 
 --- ******* ---- [queues]
 ---------- celery@... v5.5.3 (emerald-rush)

[*] Ready to accept tasks!
```

**Terminal 2: Celery Beat (scheduler)**
```bash
cd vireon/
celery -A backend.anomaly.celery_app beat --loglevel=info
```

Expected output:
```
celery beat v5.5.3 (emerald-rush) is starting.
LocalTime -> 2026-03-15 14:22:00.000000
Configuration ->
    . broker -> redis://localhost:6379/0
    . app -> backend.anomaly.celery_app:app
    . loader -> celery.loaders.app
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> -@%-(levelname)s
    . loglevel -> INFO
    . scheduler class -> celery.beat.PersistentScheduler
    Shutting down after 3600 seconds.

First run: Dispatching initial /celery.chord_unlock signals
Scheduler: Sending due task scan_for_anomalies (backend.anomaly.tasks.scan_for_anomalies)
Scheduler: Received tick signal from beat
Scheduler: Sending due task check_redis_health (backend.anomaly.tasks.check_redis_health)
```

**Terminal 3: Flower (Monitoring UI)**
```bash
cd vireon/
celery -A backend.anomaly.celery_app flower --port=5555
```

Expected output:
```
 ----------- Celery Flower 2.0.1 ----------
 
 Management Command-line interface for monitoring Celery clusters
 
 Visit me at http://localhost:5555
```

Then open **http://localhost:5555** in your browser. You'll see:
- Live task execution
- Worker status
- Success/failure rates
- Task details and logs

**Terminal 4: FastAPI Backend**
```bash
cd vireon/
uvicorn backend.main:app --reload --port 8000
```

### 6. Test a Manual Scan

In a 5th terminal:

```bash
cd vireon/

# Option A: Trigger task via Celery
python -c "
from backend.anomaly.tasks import scan_for_anomalies
result = scan_for_anomalies.delay()
print(f'Task ID: {result.id}')
print(f'Status: {result.status}')
print(f'Result: {result.get()}')
"

# Option B: Run scanner directly (bypassing Celery)
python backend/anomaly/scanner.py
```

**Expected output:**
```
======================================================================
PHASE 4: ANOMALY DETECTION SCAN STARTING
======================================================================
[2026-03-15 14:30:45] Fetched 523 GL transactions (last 90 days)
[2026-03-15 14:30:45] Scanning 12 transactions from last 24h
[2026-03-15 14:30:45] Categories: aws, marketing, payroll, saas
[2026-03-15 14:30:46] Alert created: spike (critical) for aws
[2026-03-15 14:30:46] Alert created: trend (info) for payroll
[2026-03-15 14:30:46] Alert created: duplicate (warning) for saas
[2026-03-15 14:30:46] Scan completed: 3 alerts in 1240ms
======================================================================
```

---

## ANOMALY DETECTION ALGORITHM

### Detection Types

**1. SPIKE Detection (Most Common)**
- Threshold: `amount > baseline + k*stddev`
- **WARNING:** `amount > (avg + 1.5σ)` AND `delta_pct > 15%`
- **CRITICAL:** `amount > (avg + 2.5σ)` AND `delta_pct > 50%`
- Example: AWS bill jumps from $8,000 to $18,000 → 125% spike → CRITICAL

**2. TREND Detection**
- Growth rate: category spending increasing each month
- Threshold: `>5%/month for 3 consecutive months`
- Severity: INFO (heads-up, not dangerous yet)
- Example: Payroll growing $10k/month due to hiring → Flag trend, ask agent for context

**3. DUPLICATE Detection**
- Same vendor, same amount, within 30-day window
- Severity: WARNING
- Suggests accidental double payment
- Example: Invoice paid twice to contractor

**4. TIMING Detection** (not yet implemented)
- Unusual payment timing for vendor
- E.g., usually paid 1st of month, but payment on 15th
- Severity: INFO

### Example: Spike Detection in Action

**Day 1 (Sample Data)**
- AWS transactions last 90 days: $8.5k, $8.2k, $8.8k, $7.9k, ... (avg: $8,000)
- stddev: $800

**Day 2 (New transaction)**
- AWS charge: $18,200
- delta_pct = (18,200 - 8,000) / 8,000 * 100 = **127.5%**
- stddev multiple = (18,200 - 8,000) / 800 = **12.75 σ** (way above threshold)

**Result:** CRITICAL alert created
- Baseline: $8,000
- Amount: $18,200
- Delta: +127.5%
- Description: "AWS spike: $18,200 vs expected $8,000"
- Suggested Owner: CTO
- Runway Impact: -2.3 months if sustained

---

## API INTEGRATION

### Existing Endpoints (Updated for Phase 4)

#### GET /alerts

Fetch all active alerts from PostgreSQL:

```bash
curl -X GET http://localhost:8000/alerts \
  -H "Authorization: Bearer your_token"
```

**Response:**
```json
{
  "status": "success",
  "alerts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "severity": "critical",
      "alert_type": "spike",
      "category": "aws",
      "amount": 18200.00,
      "baseline": 8000.00,
      "delta_pct": 127.50,
      "description": "AWS spike: $18,200 vs expected $8,000",
      "runway_impact": -2.3,
      "suggested_owner": "CTO",
      "status": "active",
      "created_at": "2026-03-15T02:00:15Z"
    },
    ...
  ],
  "total": 7,
  "active": 5,
  "resolved": 2
}
```

#### GET /alerts/history

Fetch dismissed/resolved alerts:

```bash
curl -X GET http://localhost:8000/alerts/history?days=7
```

#### POST /alerts/{id}/dismiss

Mark alert as dismissed:

```bash
curl -X POST http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000/dismiss \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive - expected cost"}'
```

### LangGraph Agent Integration

The **get_active_alerts()** tool (from Phase 3) now returns real data:

```python
# In agent conversation
User: "What financial alerts do we have?"

Agent internally calls:
get_active_alerts() → fetches from GET /alerts → returns active PostgreSQL alerts

Agent response:
"You have 3 active financial alerts:

(1) CRITICAL: AWS spike - $18,200 vs expected $8,000 (+127%)
    Runway impact: -2.3 months if sustained
    Suggested owner: CTO
    → Likely cause: new data pipeline or increased usage
    
(2) WARNING: Payroll duplicate - paid $45,000 twice to contractor Bob
    Suggested owner: Operations
    → Action: Contact Bob to reverse payment
    
(3) INFO: Marketing spend trending +8%/month for 3 months
    Current: $25,000, up from $23,000
    → Is this intentional? Should we adjust budget?"
```

---

## MONITORING & TROUBLESHOOTING

### Flower Dashboard (http://localhost:5555)

**Sections:**
- **Tasks:** Live view of all running/completed tasks
- **Workers:** Health of connected workers
- **Pools:** Thread pool status
- **Stats:** Task success rates, latency
- **Logs:** Detailed logs per task

### Common Issues

#### Issue: "Redis connection refused"
```
Error: ConnectionError: Error -2 connecting to localhost:6379
```

**Fix:**
```bash
# Check if Redis is running
redis-cli ping
# If not running, start it:
redis-server  # macOS/Linux
# or
docker run -d -p 6379:6379 redis:7-alpine
```

#### Issue: "PostgreSQL connection failed"
```
Error: psycopg2.OperationalError: could not connect to server
```

**Fix:**
```bash
# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
print('✓ Connected')
"
```

#### Issue: Celery tasks not running (stuck in PENDING)

**Check:**
1. Is worker running? `celery -A backend.anomaly.celery_app worker`
2. Is Beat running? `celery -A backend.anomaly.celery_app beat`
3. Check Flower: http://localhost:5555

**Fix:**
```bash
# Clear old tasks from Redis
redis-cli FLUSHDB

# Restart worker
celery -A backend.anomaly.celery_app worker --loglevel=debug
```

#### Issue: "Table 'alerts' does not exist"

**Fix:**
```bash
python backend/anomaly/migrations/run_migrations.py
```

---

## PRODUCTION DEPLOYMENT

### Railway.app (Recommended for Phase 4)

1. **Create Railway project:** https://railway.app

2. **Add services:**
   - PostgreSQL (Neon.tech addon)
   - Redis (Railway Redis service)

3. **Deploy FastAPI backend as web service**

4. **Deploy Celery as background jobs**
   - Worker: `celery -A backend.anomaly.celery_app worker`
   - Beat: `celery -A backend.anomaly.celery_app beat`
   - Flower: `celery -A backend.anomaly.celery_app flower`

5. **Set environment variables via Railway UI:**
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   GROQ_API_KEY=...
   ```

### Scaling Celery Workers

For high volume:

```bash
# Worker 1 (anomaly tasks)
celery -A backend.anomaly.celery_app worker -Q anomaly --loglevel=info

# Worker 2 (maintenance tasks)
celery -A backend.anomaly.celery_app worker -Q maintenance --loglevel=info

# Beat (single instance, schedule all)
celery -A backend.anomaly.celery_app beat --loglevel=info
```

---

## CUSTOMIZATION

### Adjust Alert Thresholds

Edit alert_thresholds table (or Python):

```bash
# Via psql
UPDATE alert_thresholds 
SET warn_pct = 20.0, critical_pct = 75.0 
WHERE category = 'aws';

# Or update in Python before scan
```

### Add New Alert Type

Edit `backend/anomaly/scanner.py`:

```python
def detect_my_alert(transaction, baseline, thresholds):
    # Your logic here
    return {
        "severity": "warning",
        "alert_type": "my_type",
        "category": "...",
        ...
    }

# In AnomalyScanner.run():
for transaction in recent_transactions:
    my_alert = self.detect_my_alert(transaction, baseline, thresholds)
    if my_alert:
        self.create_alert(conn, my_alert)
```

### Change Scan Schedule

Edit `backend/anomaly/celery_app.py`:

```python
"scan_for_anomalies": {
    "schedule": crontab(hour=3, minute=30),  # Now 3:30 AM UTC
    ...
}
```

See: https://docs.celeryproject.io/en/stable/userguide/periodic-tasks.html

---

## NEXT STEPS

With Phase 4 complete:

✓ Background anomaly detection running
✓ Alerts written to PostgreSQL
✓ LangGraph agent has real data
✓ Founder can ask "What alerts do we have?" and get context

**Phase 5 Ideas:**
- Real-time alerts via Websockets/SSE to frontend
- Slack notifications for CRITICAL alerts
- Alert causality analysis (ML model identifies root cause)
- Budget forecasting (will we hit runway?)
- Approval workflow for spending exceptions

---

## QUICK REFERENCE

```bash
# Start everything
Terminal 1: celery -A backend.anomaly.celery_app worker --loglevel=info
Terminal 2: celery -A backend.anomaly.celery_app beat --loglevel=info
Terminal 3: celery -A backend.anomaly.celery_app flower --port=5555
Terminal 4: uvicorn backend.main:app --reload --port 8000

# URLs
Flower:    http://localhost:5555
FastAPI:   http://localhost:8000
Docs:      http://localhost:8000/docs

# Test scan
python backend/anomaly/scanner.py

# View alerts
curl http://localhost:8000/alerts

# Reset alerts (careful!)
redis-cli FLUSHDB
python backend/anomaly/migrations/run_migrations.py
```

---

**End Phase 4 Documentation**
