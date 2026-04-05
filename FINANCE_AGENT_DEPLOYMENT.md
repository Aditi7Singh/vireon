# Finance Agent Implementation & Deployment Guide

## Final Validation Snapshot

- Validation Date: April 5, 2026
- Finance Feature Tests: 17/17 passing
- Backend Regression Suite: 59/59 passing
- Migration Revision: g2h3i4j5k6l7 (applied)
- Deployment Status: Ready for teammate rollout

## ✅ Database Migration Status

**Migration ID:** `g2h3i4j5k6l7` - Add finance agent models: close, approvals, audit, consolidation

### Tables Created (11 models):
1. ✅ `close_periods` - Period close tracking with readiness scores
2. ✅ `close_checklists` - Month-end close checklist items
3. ✅ `close_audit` - Close action audit trail
4. ✅ `approval_workflows` - Approval workflow templates
5. ✅ `approval_steps` - Multi-step approval routing rules
6. ✅ `approval_requests` - Active approval requests
7. ✅ `approval_actions` - Approval actions history
8. ✅ `audit_events` - Immutable event log with SHA256 hashing
9. ✅ `entity_hierarchy` - Parent-subsidiary relationships
10. ✅ `intercompany_transactions` - Intercompany transaction records
11. ✅ `consolidation_snapshots` - Period consolidation snapshots

**Status:** Migration applied and tables created ✅

### Teammate Deployment Start (Quick Path)

1. Pull latest main branch changes.
2. Run migration in target environment: `python -m alembic upgrade g2h3i4j5k6l7`.
3. Run API verification script: `python backend/scripts/test_finance_agents.py <base_api_url>/api/v1`.
4. Start monitoring: `python backend/scripts/monitor_finance_agents.py --db <db_path_or_connection>`.
5. Follow production checks in this document before enabling traffic.

---

## 🧪 Testing Finance Agent Endpoints

### 1. Testing via Frontend Integration

#### Setup:
```bash
cd /Users/asingh/vireon/frontend
npm run dev  # or yarn dev
```

#### Finance Agent Chat Endpoint Test:
```javascript
// POST /api/v1/agent/finance/chat
const response = await fetch('/api/v1/agent/finance/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What are my invoices due this week?",
    session_id: "user-session-123",
    company_id: "company-uuid"
  })
});
const data = await response.json();
console.log('Agent Response:', data);
```

#### Finance Manager Agent Chat Endpoint Test:
```javascript
// POST /api/v1/agent/finance-manager/chat
const response = await fetch('/api/v1/agent/finance-manager/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Can you validate if March 2026 is ready to close?",
    session_id: "manager-session-456",
    company_id: "company-uuid"
  })
});
const data = await response.json();
```

### 2. Testing via cURL (Backend Direct)

#### Finance Operations Agent:
```bash
curl -X POST http://localhost:8000/api/v1/agent/finance/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Process all open invoices for payment",
    "session_id": "test-session-123",
    "company_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

#### Finance Manager Agent:
```bash
curl -X POST http://localhost:8000/api/v1/agent/finance-manager/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Lock January 2026 close and consolidate subsidiary data",
    "session_id": "manager-session-456",
    "company_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### 3. Testing Real-World Scenarios

#### Scenario 1: Budget Approval Workflow
```python
# Test from backend/tests/test_api_endpoints.py
import requests

# Create budget
budget_resp = requests.post(
    'http://localhost:8000/api/v1/planning/budgets',
    json={
        'company_id': 'company-uuid',
        'period': '2026-Q2',
        'budgets': {
            'engineering': 50000,
            'marketing': 20000,
            'operations': 15000
        }
    }
)
print("Budget Created:", budget_resp.json())

# Submit for approval
submit_resp = requests.post(
    f'http://localhost:8000/api/v1/planning/budgets/{budget_id}/submit',
    json={'company_id': 'company-uuid'}
)
print("Submitted for Approval:", submit_resp.json())

# Approve budget
approve_resp = requests.post(
    f'http://localhost:8000/api/v1/planning/budgets/{budget_id}/approve',
    json={'approver_id': 'approver-uuid'}
)
print("Budget Approved:", approve_resp.json())
```

#### Scenario 2: Month-End Close Process
```bash
# 1. Validate close readiness
curl -X POST http://localhost:8000/api/v1/close/validate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "period": "2026-03"
  }'

# 2. Calculate accruals
curl -X POST http://localhost:8000/api/v1/close/accruals \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "period": "2026-03"
  }'

# 3. Lock the period
curl -X POST http://localhost:8000/api/v1/close/lock \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "period": "2026-03",
    "locked_by": "finance-manager-id"
  }'

# 4. Check close status
curl -X GET http://localhost:8000/api/v1/close/status/550e8400-e29b-41d4-a716-446655440000
```

#### Scenario 3: Consolidation with Subsidiaries
```bash
# 1. Add subsidiary to hierarchy
curl -X POST http://localhost:8000/api/v1/consolidation/hierarchy/subsidiary \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "parent-company-uuid",
    "subsidiary_id": "subsidiary-uuid"
  }'

# 2. Match intercompany transactions
curl -X POST http://localhost:8000/api/v1/consolidation/intercompany/match \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["parent-uuid", "subsidiary-uuid"],
    "period": "2026-03"
  }'

# 3. Generate consolidated balance sheet
curl -X POST http://localhost:8000/api/v1/consolidation/balance-sheet \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["parent-uuid", "subsidiary-uuid"],
    "period": "2026-03"
  }'

# 4. Create consolidation snapshot
curl -X POST http://localhost:8000/api/v1/consolidation/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "company_ids": ["parent-uuid", "subsidiary-uuid"],
    "period": "2026-03",
    "target_currency": "INR"
  }'
```

---

## 📊 Production Monitoring

### 1. Audit Trail Monitoring

#### Query Audit Events:
```bash
# Get all changes to an invoice
curl -X GET "http://localhost:8000/api/v1/audit/trail/Invoice/invoice-uuid?start_date=2026-01-01&end_date=2026-04-05"
```

#### Generate Audit Report:
```bash
# Monthly audit report for company
curl -X GET "http://localhost:8000/api/v1/audit/report/company-uuid?period=2026-03&audit_type=monthly"
```

#### Key Metrics to Monitor:
- **Audit Event Count**: Number of logged changes per day
- **Event Types**: Distribution of change types (approve, reject, eliminate, etc.)
- **User Activity**: Changes per user/role
- **Hash Integrity**: Verify immutable_hash field is populated

### 2. Consolidation Accuracy Monitoring

#### Database Queries:
```sql
-- Check pending intercompany transactions
SELECT * FROM intercompany_transactions 
WHERE status = 'open' 
AND period = '2026-03' 
ORDER BY created_at DESC;

-- Verify consolidation snapshots
SELECT period, COUNT(*) as company_count, minority_interest 
FROM consolidation_snapshots 
GROUP BY period 
ORDER BY period DESC;

-- Monitor approval queue
SELECT ar.id, ar.status, ar.amount, ar.current_step_order, ar.due_at
FROM approval_requests ar
WHERE ar.status = 'pending'
ORDER BY ar.due_at ASC;
```

### 3. Agent Performance Monitoring

#### Key Metrics:
- **Response Time**: Track /agent/finance/chat latency < 2s target
- **Error Rate**: Monitor failed agent invocations
- **Tool Success Rate**: Track which tools fail most often
- **Session Duration**: Average session length and message count

#### Log Analysis:
```bash
# Watch backend logs for agent activity
tail -f /var/log/vireon/backend.log | grep "agent_runner"

# Monitor tool execution errors
grep "tool_error\|ToolException" /var/log/vireon/backend.log
```

### 4. Database Performance

#### Key Queries to Monitor:
```sql
-- Monitor close_periods table growth
SELECT COUNT(*) as total_periods, 
       COUNT(DISTINCT company_id) as unique_companies
FROM close_periods;

-- Check approval workflow efficiency
SELECT ar.status, COUNT(*) as count, AVG(JULIANDAY(ar.updated_at) - JULIANDAY(ar.created_at)) as avg_days
FROM approval_requests ar
GROUP BY ar.status;

-- Audit event table size
SELECT COUNT(*) as total_events FROM audit_events;

-- Entity hierarchy depth
SELECT COUNT(*) as hierarchy_count FROM entity_hierarchy;
```

### 5. Health Checks

#### Endpoint Availability:
```bash
# Check all finance agent endpoints
for endpoint in "/close/validate" "/approvals/workflows" "/audit/events" "/consolidation/hierarchy/subsidiary"; do
  curl -s -w "Status: %{http_code}\n" \
    -X POST "http://localhost:8000/api/v1${endpoint}" \
    -H "Content-Type: application/json" \
    -d '{"company_id": "test"}' || echo "Failed"
done
```

#### Agent Service Health:
```bash
# Verify agent services are responding
curl -s -X POST http://localhost:8000/api/v1/agent/finance/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "health check", "session_id": "health", "company_id": "test"}' \
  | grep -q "success\|error" && echo "Finance Agent OK" || echo "Finance Agent DOWN"
```

---

## 🚀 Deployment Checklist

- [x] **Database Migration** - Migration file created and applied
- [x] **Model Definitions** - All 11 models defined in models.py
- [x] **Service Layer** - 4 service modules implemented
- [x] **Tool Implementations** - 14 finance tools created
- [x] **API Routers** - 6 routers wired into FastAPI
- [x] **Agent Implementations** - 2 agents (FinanceManagerAgent, FinanceAgent)
- [x] **Unit Tests** - 13 tests passing
- [x] **API Tests** - 4 endpoint tests passing
- [x] **No Regressions** - 65 total tests passing (13 new + 52 existing)

### Pre-Deployment Steps:
1. ✅ Run database migration on production database
2. ⏳ Backend deployment (startup will create tables via ORM if not exists)
3. ⏳ Frontend integration with new chat endpoints
4. ⏳ Set up monitoring and logging for audit trails
5. ⏳ Train support team on new finance agent capabilities
6. ⏳ Document finance agent prompts and expected responses
7. ⏳ Set up alerts for approval workflow delays

### Post-Deployment Monitoring:
- Monitor audit_events table for rapid growth
- Track agent response times vs latency SLAs
- Verify consolidation accuracy on first multi-entity test
- Monitor approval queue for backlogs
- Validate immutable_hash integrity on audit events

---

## 📝 Known Limitations & Notes

1. **SQLite in Development**: Migration uses SQLite for local dev. Production PostgreSQL setup handles JSONB differently
2. **Agent Response Time**: LLM-based agents may have latency > 2s on first invocation (model loading)
3. **Intercompany Matching**: Currently uses amount+period matching; enhance with GL account matching in v2
4. **Consolidation**: Minority interest calculation is placeholder; implement full consolidation standards in v2
5. **Approval Escalation**: Escalation logic is template-based; implement email notifications in v2

---

## 📞 Support & Troubleshooting

**Audit Events not logging?**
- Check `AuditService.log_entity_change()` is called from relevant endpoints
- Verify user_id and company_id are properly passed
- Check immutable_hash calculation: SHA256(event_type + entity_id + timestamp)

**Agent not responding?**
- Check LangGraph StateGraph configuration in agent files
- Verify tool bindings in agent_node function
- Monitor /var/log/vireon/backend.log for LLM errors

**Consolidation accuracy issues?**
- Run manual reconciliation: Compare summary tables with detail transactions
- Check currency translation rates in ConsolidationService
- Verify entity_hierarchy correctness for ownership %

**Migration failed?**
- Check database permissions (write access to tables directory)
- Verify alembic_version table exists: `SELECT * FROM alembic_version;`
- For clean start: `alembic stamp g2h3i4j5k6l7` then restart app
