# Production Migration Guide: ERPNext → Merge.dev

One-week pre-demo checklist for switching to production accounting data.

## Phase 1: Setup (Day 1-2)

### 1.1 Merge.dev Account Setup

```bash
# 1. Sign up at https://app.merge.dev
# 2. Get API key from Settings > API
# 3. Link customer's accounting account through Merge dashboard

# Example: Linking a QuickBooks account
# - Go to Merge dashboard
# - Click "Link Account"
# - Direct customer to QuickBooks authentication
# - Copy account token when linking completes
```

### 1.2 Environment Configuration

```bash
# Copy .env.merge.example to .env
cp .env.merge.example .env

# Edit .env with Merge.dev credentials
MERGE_API_KEY=sk_prod_xxxxx
MERGE_ACCOUNT_TOKEN=acc_xxxxx
DATA_SOURCE=merge
```

### 1.3 Dependencies

```bash
# Ensure Python dependencies are installed
pip install -r backend/requirements.txt

# Key dependencies for Merge.dev:
# - requests (HTTP client)
# - celery (async tasks)
# - redis (task queue)
# - sqlalchemy (ORM)
# - psycopg2 (PostgreSQL)
```

## Phase 2: Testing (Day 3-4)

### 2.1 Health Check

```python
# Run from backend directory
from integrations.merge_client import get_merge_client

client = get_merge_client()
print(f"Health check: {client.health_check()}")
```

Expected output: `Health check: True`

### 2.2 Fetch Sample Data

```python
from integrations.merge_client import get_merge_client

client = get_merge_client()

# Test cash balance fetch
cash = client.get_cash_balance()
print(f"Cash balance: ${cash['cash']:,.0f}")

# Test expenses
expenses = client.get_expenses(period_months=3)
print(f"Monthly burn: ${expenses['total']:,.0f}")

# Test revenue
revenue = client.get_revenue()
print(f"MRR: ${revenue['mrr']:,.0f}")
```

### 2.3 PostgreSQL Sync Test

```python
from integrations.merge_client import get_merge_client

client = get_merge_client()
result = client.sync_to_postgres()

print(f"Sync result: {result}")
# Expected: {"status": "success", "records_synced": 3, "duration_seconds": 12.4}
```

### 2.4 Verify Data in Database

```sql
-- Check latest synced cash balance
SELECT cash, ar, ap, net_cash, source, synced_at
FROM cash_balance
ORDER BY synced_at DESC
LIMIT 1;

-- Check expense categories
SELECT category, amount
FROM expense_breakdown
ORDER BY amount DESC;

-- Check revenue metrics
SELECT mrr, arr, growth_pct
FROM revenue_metrics
ORDER BY synced_at DESC
LIMIT 1;
```

## Phase 3: Celery Task Setup (Day 4)

### 3.1 Redis Setup

```bash
# Start Redis (required for Celery)
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3.2 Start Celery Worker

```bash
# In separate terminal from backend server
cd backend
celery -A tasks worker --loglevel=info
```

### 3.3 Start Celery Beat (Scheduler)

```bash
# In another terminal
cd backend
celery -A tasks beat --loglevel=info
```

Expected output:
```
Scheduler  : celery.beat.PersistentScheduler
Instance name (hostname)@19263
- syncing.tasks.sync-merge-critical: <freq>15.0s</freq>
- syncing.tasks.sync-merge-full: <freq>1d</freq>
- syncing.tasks.calculate-runway: <freq>1h</freq>
```

### 3.4 Verify Scheduled Tasks

Monitor task execution:
```bash
# Watch Celery logs
celery -A tasks inspect active

# Check task history
SELECT * FROM syn_log WHERE source='merge' ORDER BY created_at DESC;
```

## Phase 4: Full System Test (Day 5)

### 4.1 Dashboard Test

```bash
# Start all services
docker-compose up -d  # PostgreSQL, Redis
cd backend && python -m uvicorn main:app --reload  # Port 8000
cd frontend && npm run dev  # Port 3000
```

### 4.2 Verify Dashboard Metrics

Open http://localhost:3000/dashboard and verify:
- ✓ Cash Runway card shows data (not simulator)
- ✓ Charts render with real data
- ✓ Alerts show real anomalies
- ✓ Numbers match accounting system

### 4.3 Test Anomaly Detection

Verify anomalies are detected:
```sql
SELECT * FROM alerts WHERE severity='CRITICAL' ORDER BY created_at DESC;
```

Expected: Alerts based on real accounting data patterns

### 4.4 Test Agent Chat

Send query in ChatDrawer: _"What's our current runway?"_

Verify response uses real data (e.g., specific QuickBooks account balances)

## Phase 5: Deployment (Day 6)

### 5.1 Production Environment

```bash
# Deploy backend with environment variables
export MERGE_API_KEY=sk_prod_xxxxx
export MERGE_ACCOUNT_TOKEN=acc_xxxxx
export DATA_SOURCE=merge
export DATABASE_URL=postgresql://prod_user:pwd@prod_host:5432/vireon

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### 5.2 Verify Logs

```bash
# Check backend startup
docker logs vireon-backend

# Expected: "Using data source: merge"
```

### 5.3 Celery Monitoring

```bash
# Monitor task execution in production
celery -A tasks inspect active_queues
celery -A tasks inspect stats

# Check sync logs
SELECT status, COUNT(*) FROM sync_log GROUP BY status;
```

## Phase 6: Demo Day (Day 7)

### 6.1 Pre-Demo Checks

```bash
# 24 hours before demo, verify:

# 1. Fresh sync completed
SELECT * FROM sync_log WHERE source='merge' AND created_at > NOW() - INTERVAL '1 hour';

# 2. Data freshness
SELECT synced_at FROM cash_balance ORDER BY synced_at DESC LIMIT 1;

# 3. No errors in last 24h
SELECT COUNT(*) FROM sync_log WHERE status='failed' AND created_at > NOW() - INTERVAL '24 hour';

# 4. Task queue healthy
celery -A tasks inspect active_queues
```

### 6.2 Demo Talking Points

```
Live Demo Flow:
1. Show dashboard - "This is real QuickBooks data, updated every 15 minutes"
2. Click Scenario Modal - "What if we hire 2 engineers?" (calculates impact on real data)
3. Open ChatDrawer - "Ask the AI any financial question" (agent has access to real books)
4. Show runway report - "Detailed financial analysis powered by real accounting"
5. Highlight anomalies - "These are real patterns detected in their accounting"

Key differentiator vs QBO:
- Real-time runway calculations (not quarterly reports)
- AI financial advisor (not just dashboards)
- Unified accounting (QB, Xero, Stripe, etc. all supported)
- Automated anomaly detection
- Scenario planning with live impact
```

## Rollback Plan

If issues occur, quickly switch back to simulator:

```bash
# In .env
DATA_SOURCE=erpnext

# Restart backend
# Dashboard automatically uses ERPNext data
```

No data loss — ERPNext data still in PostgreSQL.

## Troubleshooting

### Issue: "MERGE_API_KEY not found"

**Solution:**
```bash
# Verify .env file exists and contains:
echo $MERGE_API_KEY  # Should print your key

# Or set explicitly before starting:
export MERGE_API_KEY=sk_prod_xxxxx
```

### Issue: Rate limit errors in logs

**Normal behavior** — Merge.dev has rate limits (360 req/hour).
Client automatically retries with backoff.

**Monitor:**
```sql
SELECT source, status, COUNT(*) FROM sync_log GROUP BY source, status;
```

### Issue: Dashboard shows old data

**Verify syncs are running:**
```sql
SELECT * FROM sync_log WHERE source='merge' ORDER BY created_at DESC LIMIT 5;

-- Check if latest sync succeeded
SELECT status, COUNT(*) FROM sync_log WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY status;
```

### Issue: Celery tasks not running

**Check:**
```bash
# 1. Redis is running
redis-cli ping  # Should print PONG

# 2. Celery worker is running
ps aux | grep celery

# 3. Celery beat is running
ps aux | grep beat

# 4. Check logs
tail -f celery-worker.log
tail -f celery-beat.log
```

## Performance Benchmarks

Expected sync times (Merge.dev API latencies):

| Endpoint | Time | Frequency |
|---|---|---|
| Cash balance | 0.5s | 15min |
| Expenses | 1.0s | 15min |
| Revenue | 1.5s | 15min |
| **Total sync** | **3-4s** | **15min** |

If syncs exceed 30s, check:
- Network latency to api.merge.dev
- Merge API rate limits
- Current customer account complexity

## Timeline

```
Day 1-2: Setup & credentials ━━━━━━━━━━━━━━━
Day 3-4: Testing & verification ━━━━━━━━━━━━━
Day 4:   Celery task configuration ━━━━━━
Day 5:   Full system integration test ━━━━━━━━
Day 6:   Production deployment ━━━━━━━━━━━
Day 7:   Demo day ✓
```

## Contacts

- **Merge.dev Support:** support@merge.dev
- **Data Issues:** Check `sync_log` table in PostgreSQL
- **Agent Issues:** Check `/logs/agent.log`

---

**Status:** Production-ready for demo
**Last Updated:** 2026-03-15
