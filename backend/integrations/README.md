# Merge.dev Accounting Integration

Production data integration for Agentic CFO using Merge.dev's unified Accounting API.

## Overview

This module provides a drop-in replacement for the ERPNext simulator, allowing real accounting data from:
- **QuickBooks Online**
- **Xero**
- **Stripe** (revenue)
- **NetSuite**
- **Sage Intacct**
- And 15+ more accounting platforms via Merge.dev

## Quick Start

### 1. Get Merge.dev API Credentials

1. Sign up at https://app.merge.dev
2. Go to **Settings > API** and copy your API key
3. Link your customer's accounting account in the Merge dashboard (e.g., their QuickBooks)
4. Copy the account token generated for that linked account

### 2. Configure Environment

Copy `.env.merge.example` to `.env` and fill in your credentials:

```bash
# Production data source
DATA_SOURCE=merge

# Merge.dev credentials
MERGE_API_KEY=sk_prod_xxxxx
MERGE_ACCOUNT_TOKEN=acc_xxxxx
```

### 3. Restart Backend

```bash
# Backend will now pull from Merge.dev instead of ERPNext simulator
python -m uvicorn backend.main:app --reload
```

That's it! No code changes needed.

## Architecture

### Data Flow

```
Real Accounting System (QB, Xero)
           ↓
    Merge.dev Unified API
           ↓
   MergeAccountingClient
           ↓
    Sync to PostgreSQL
           ↓
    CFO Dashboard & Agent
```

### Switching Between Data Sources

```python
# Environment variable controls which client is used
DATA_SOURCE = os.getenv("DATA_SOURCE", "erpnext")

if DATA_SOURCE == "merge":
    client = MergeAccountingClient()  # Real accounting data
else:
    client = ERPNextClient()  # Simulator
```

## API Methods

### `get_cash_balance()`

Returns:
```json
{
  "cash": 245000,
  "ar": 125000,
  "ap": 45000,
  "net_cash": 325000,
  "currency": "USD",
  "last_updated": "2026-03-15T10:30:00Z"
}
```

### `get_expenses(period_months=3)`

Returns:
```json
{
  "breakdown": {
    "Payroll": 125000,
    "AWS": 18750,
    "SaaS": 8500,
    "Marketing": 25000
  },
  "trend": {
    "Payroll": [120000, 125000, 125000],
    "AWS": [17500, 18750, 18750]
  },
  "movers": [
    {"category": "AWS", "pct_change": 7.1, "amount": 1250}
  ],
  "total": 177250,
  "period_months": 3,
  "last_updated": "2026-03-15T10:30:00Z"
}
```

### `get_revenue()`

Returns:
```json
{
  "mrr": 75000,
  "arr": 900000,
  "growth_pct": 12.5,
  "churn_rate": 2.1,
  "nrr": 115,
  "trend_12m": [65000, 68000, ...],
  "last_updated": "2026-03-15T10:30:00Z"
}
```

### `sync_to_postgres()`

Syncs all accounting data to PostgreSQL. Called by Celery task.

Returns:
```json
{
  "status": "success",
  "records_synced": 3,
  "duration_seconds": 12.4
}
```

## Scheduled Sync Tasks

### Celery Beat Schedule

```python
app.conf.beat_schedule = {
    # Critical data every 15 minutes
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
    # Runway calculation every hour
    "calculate-runway": {
        "task": "backend.tasks.calculate_runway",
        "schedule": crontab(minute=0),
    },
}
```

### Available Tasks

**`sync_from_merge_dev(full_sync=False)`**
- Fetches data from Merge.dev
- Upserts to PostgreSQL
- Triggers anomaly detection
- Recalculates runway

**`scan_for_anomalies()`**
- Detects unusual spending patterns
- Identifies revenue changes
- Flags cash flow anomalies

**`calculate_runway()`**
- Recalculates monthly burn rate
- Updates projected runway
- Computes zero date

## Error Handling

### Rate Limiting

The client includes automatic rate limit handling with exponential backoff:

```python
@retry_on_rate_limit(max_retries=3, backoff_factor=2)
def get_expenses(self):
    # Automatically retries on 429 with backoff
    pass
```

### Health Checks

Verify API connectivity before syncing:

```python
client = MergeAccountingClient()
if client.health_check():
    print("API reachable")
else:
    print("API unreachable")
```

## Deployment

### Production Checklist

- [ ] Set `DATA_SOURCE=merge` in production `.env`
- [ ] Configure `MERGE_API_KEY` and `MERGE_ACCOUNT_TOKEN`
- [ ] Enable Redis for Celery task queue
- [ ] Start Celery Beat for scheduled syncs
- [ ] Start Celery Worker for async tasks
- [ ] Verify sync logs in `SyncLog` table
- [ ] Test anomaly detection on real data

### Monitoring

Check sync status in PostgreSQL:

```sql
-- View recent syncs
SELECT source, status, records_synced, duration_seconds, created_at
FROM sync_log
ORDER BY created_at DESC
LIMIT 10;

-- View failed syncs
SELECT source, status, error_message, created_at
FROM sync_log
WHERE status = 'failed'
ORDER BY created_at DESC;
```

## Troubleshooting

### "MERGE_API_KEY and MERGE_ACCOUNT_TOKEN environment variables required"

**Fix:** Set environment variables before starting backend:
```bash
export MERGE_API_KEY=sk_prod_xxxxx
export MERGE_ACCOUNT_TOKEN=acc_xxxxx
python -m uvicorn backend.main:app --reload
```

### "Rate limited. Retry after 60s"

**Normal:** Merge.dev has rate limits (360 req/hour for most endpoints).
The client retries automatically with exponential backoff.

Control retries in `merge_client.py`:
```python
@retry_on_rate_limit(max_retries=3, backoff_factor=2)
```

### "Merge.dev API unreachable"

**Check:**
1. API credentials are correct
2. Network connectivity to api.merge.dev
3. API key has not expired
4. Account token is still linked

Run health check:
```python
from backend.integrations.merge_client import get_merge_client

client = get_merge_client()
print(client.health_check())
```

## Data Mapping

| Merge.dev Endpoint | Mapped To | CFO Display |
|---|---|---|
| `GET /balance-sheets` | `get_cash_balance()` | Cash Runway card |
| `GET /expenses` | `get_expenses()` | Burn rate chart |
| `GET /invoices?status=paid` | `get_revenue()` | Revenue metrics |
| All above | `sync_to_postgres()` | Dashboard |

## Development

### Testing Merge.dev Locally

```python
from backend.integrations.merge_client import MergeAccountingClient

# Initialize client (reads MERGE_API_KEY, MERGE_ACCOUNT_TOKEN from .env)
client = MergeAccountingClient()

# Test each endpoint
cash = client.get_cash_balance()
expenses = client.get_expenses()
revenue = client.get_revenue()

print(f"Cash: ${cash['cash']:,.0f}")
print(f"Monthly Burn: ${expenses['total']:,.0f}")
print(f"MRR: ${revenue['mrr']:,.0f}")
```

### Extending for New Data Sources

To support additional accounting platforms:

1. Check if Merge.dev already supports them (15+ platforms)
2. If not, create new client class:
   ```python
   class CustomAccountingClient:
       def get_cash_balance(self): ...
       def get_expenses(self): ...
       def get_revenue(self): ...
       def sync_to_postgres(self): ...
   ```
3. Add to `get_data_client()` router in `main.py`

## References

- [Merge.dev Accounting API Docs](https://docs.merge.dev/accounting/overview/)
- [Supported Integrations](https://merge.dev/integrations)
- [API Rate Limits](https://docs.merge.dev/accounting/limits/)
- [Authentication](https://docs.merge.dev/authentication/overview/)

## Support

- Merge.dev: support@merge.dev
- This project: GitHub issues
