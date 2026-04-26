# Vireon — Complete Feature & Deployment Overview

---

## Live URLs

| Service | URL |
|---|---|
| Frontend (S3) | http://vireon-frontend-732772501496.s3-website.ap-south-1.amazonaws.com |
| Frontend (CloudFront HTTPS) | https://d10nqxcoyrzhqf.cloudfront.net |
| Backend API | http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com |
| API Docs (Swagger) | http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/api/v1/docs |

---

## AWS Infrastructure (Deployed)

| Resource | Name / ID | Status |
|---|---|---|
| ECS Cluster | `vireon-prod-cluster` | ✅ Running |
| ECS Backend Service | `vireon-prod-backend` (revision 7) | ✅ Running |
| ECS Worker | `vireon-prod-worker` | ✅ Running |
| ECS Beat Scheduler | `vireon-prod-beat` | ✅ Running |
| RDS PostgreSQL | `vireon-postgres` (db.t3.micro) | ✅ Available |
| ElastiCache Redis | `vireon-redis` (cache.t3.micro) | ✅ Available |
| S3 (documents) | `vireon-documents-732772501496` | ✅ Active |
| S3 (frontend) | `vireon-frontend-732772501496` | ✅ Active |
| CloudFront | `E3EE5PX8GNLDQU` | ✅ Deployed |
| ALB | `vireon-prod-alb` | ✅ Active |
| ECR Backend | `vireon-backend:latest` | ✅ Pushed |
| ECR Worker | `vireon-worker:latest` | ✅ Pushed |
| Amplify (old) | `d3pntg2sxpiro4` | ⚠️ Replaced by S3+CF |

### VPC Architecture
- RDS + Redis → **default VPC** (`vpc-047a5218129c4114b`)
- ECS + ALB → **new VPC** (`vpc-08d98ac34e0e5bed7`, 10.0.0.0/16)
- RDS port 5432 open to `0.0.0.0/0` for cross-VPC access

---

## Frontend Pages (What's in the UI)

All 18 pages are deployed and accessible. Navigation is via the left sidebar inside the app.

| Page | URL Path | Status | Notes |
|---|---|---|---|
| Landing Page | `/` | ✅ Working | Newspaper-style landing, links to dashboard |
| Dashboard (main) | `/dashboard` | ✅ Working | Overview with KPI cards |
| CEO Dashboard | `/dashboard/ceo` | ✅ Working | Executive view |
| CTO Dashboard | `/dashboard/cto` | ✅ Working | Tech/ops view |
| Finance Dashboard | `/dashboard/finance` | ✅ Working | Finance team view |
| Runway | `/runway` | ✅ Working | Cash runway forecast |
| Cash Flow | `/cash-flow` | ✅ Working | Cash flow projections |
| Budget | `/budget` | ✅ Working | Budget vs actual |
| Expenses | `/expenses` | ✅ Working | Expense breakdown |
| Revenue | `/revenue` | ✅ Working | Revenue analysis |
| Payroll | `/payroll` | ✅ Working | Employee & payroll |
| Tax | `/tax` | ✅ Working | Tax planning |
| Assets | `/assets` | ✅ Working | Fixed assets & depreciation |
| Collections | `/collections` | ✅ Working | AR/AP aging |
| Benchmarking | `/benchmarking` | ✅ Working | Industry benchmarks |
| Scenarios | `/scenarios` | ✅ Working | What-if modeling |
| Anomalies | `/anomalies` | ✅ Working | Anomaly detection alerts |
| Investor | `/investor` | ✅ Working | Investor metrics |
| Operations | `/operations` | ✅ Working | Operational KPIs |
| AI Agent | `/agent` | ✅ Working (rate limited) | Chat with AI CFO |
| Features | `/features` | ✅ Working | Feature showcase |
| Settings | `/settings` | ✅ Working | System config |

---

## Backend Features

### ✅ Fully Working in Production

| Feature | API Endpoint | Notes |
|---|---|---|
| Financial metrics | `/api/v1/scorecard`, `/api/v1/runway`, `/api/v1/burn-rate` | Core KPIs |
| Cash balance | `/api/v1/cash-balance` | Real-time cash |
| Revenue | `/api/v1/revenue` | MRR, ARR, churn |
| Expenses | `/api/v1/expenses` | Breakdown by category |
| Alerts/Anomalies | `/api/v1/alerts` | Anomaly detection |
| AI Agent chat | `/api/v1/agent/chat` | Groq-powered (rate limited on free tier) |
| Payroll | `/api/v1/payroll/*` | Employee records, payroll entries |
| Tax | `/api/v1/tax/*` | Tax rules, quarterly summaries |
| Loans | `/api/v1/loans/*` | Loan tracking |
| Depreciation | `/api/v1/depreciation/*` | Asset depreciation |
| Forecasting | `/api/v1/forecast/*` | Cash forecasts |
| Planning | `/api/v1/planning/*` | Budgets, scenarios |
| FX rates | `/api/v1/fx/*` | Multi-currency |
| Collections | `/api/v1/collections/*`, `/api/v1/invoices/*` | AR/AP management |
| Benchmarks | `/api/v1/benchmarks/*` | Industry comparisons |
| Reports (PDF) | `/api/v1/reports/*` | PDF generation |
| Cloud costs | `/api/v1/cloud-costs/*` | AWS cost tracking |
| Ledger | `/api/v1/ledger/*` | General ledger |
| Financial analysis | `/api/v1/financial/*` | Comprehensive analysis |
| Recommendations | `/api/v1/recommendations/*` | AI recommendations |
| System health | `/api/v1/system/startup-health` | Health checks |
| Notifications config | `/api/v1/notifications/*` | Contact management |
| Celery workers | Background tasks | Anomaly scanning, scheduled jobs |

### ⚠️ Working but Limited

| Feature | Limitation | Fix |
|---|---|---|
| AI Agent | Groq free tier: 12k tokens/min, retries after 30s | Upgrade Groq to Dev tier (~$5/mo) |
| Email notifications | No SMTP configured | Add `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` to ECS env vars |
| Document OCR (advanced) | Basic extraction only, no AWS Textract | Set `OCR_ASYNC=true` + AWS Textract credentials |

### ❌ Backend Implemented but NO Frontend UI

| Feature | API Endpoint | What it does |
|---|---|---|
| Document upload | `POST /api/v1/documents/upload` | Upload invoices/receipts, extract text |
| Document workflow | `POST /api/v1/documents/{id}/workflow` | Approve/reject/post to ledger |
| Document classify | `POST /api/v1/documents/{id}/classify` | Auto-classify document type |
| User login | `POST /api/v1/token` | JWT authentication |
| User creation | `POST /api/v1/users/` | Create users with roles |
| Sandbox data ingest | `POST /api/v1/sandbox/ingest` | Bulk import financial data |
| Banking integration | `/api/v1/banking/*` | Bank feed reconciliation |
| Merge.dev connector | `/api/v1/merge/*` | Live ERP data via Merge |
| ERPNext connector | `/api/v1/erpnext/*` | Direct ERPNext integration |
| Audit log | `/api/v1/audit/*` | Transaction audit trail |
| Approval workflows | `/api/v1/approvals/*` | Multi-step approvals |
| Period close | `/api/v1/close/*` | Financial period management |
| Consolidation | `/api/v1/consolidation/*` | Multi-entity consolidation |

All of these are accessible via Swagger UI at `/api/v1/docs`.

---

## Credentials & Integrations

### Currently Configured
| Credential | Value | Used for |
|---|---|---|
| `GROQ_API_KEY` | Set | AI agent (Groq LLM) |
| `DATABASE_URL` | PostgreSQL on RDS | All data storage |
| `REDIS_URL` | ElastiCache | Celery task queue |
| `S3_BUCKET` | `vireon-documents-732772501496` | Document storage |
| `MERGE_API_KEY` | Set | Merge.dev production access |
| `SECRET_KEY` | Set | JWT signing |
| `COMPANY_NAME` | SeedlingLabs | Default company |
| `USE_LOCAL_LLM` | false | Uses Groq, not Ollama |

### Not Configured (Optional)
| Credential | What it enables |
|---|---|
| `SMTP_HOST/USER/PASS` | Email alerts and notifications |
| `MERGE_ACCOUNT_TOKEN` | Live accounting data via Merge.dev |
| `PLAID_CLIENT_ID/SECRET` | Bank account data aggregation |
| `OPENROUTER_API_KEY` | Alternative LLM provider |
| `OCR_ASYNC=true` + AWS Textract | Advanced document OCR |

---

## Known Issues & Limitations

| Issue | Cause | Status |
|---|---|---|
| AI agent slow/timeout | Groq free tier rate limit (12k TPM) | Retries after ~30s, upgrade to fix |
| Frontend CSS missing on Amplify | Amplify doesn't serve `_next` folder | Moved to S3+CloudFront, fixed |
| `/dashboard/runway` link on landing page | Wrong path (should be `/runway`) | Fixed in latest build |
| "Production connector credentials incomplete" | MERGE_ACCOUNT_TOKEN not set | Warning only, not a blocker |
| "Insecure connection" warning | Frontend on HTTP, backend on HTTP | Use CloudFront HTTPS URL to fix |
| No login page | Frontend runs in sandbox/demo mode | Auth exists in backend, no UI |

---

## Data

The app runs with **demo/sandbox data** seeded at startup. This includes:
- Sample company: SeedlingLabs
- Historical monthly metrics (12+ months)
- Sample invoices, expenses, payroll entries
- Exchange rates
- Anomaly detection baselines

To load real data:
1. Use the Swagger UI at `/api/v1/docs` → Sandbox → `POST /sandbox/ingest`
2. Or connect Merge.dev with a real accounting system account token

---

## Redeployment Commands

### Update backend config (e.g. new API key):
```bat
scripts\aws\update_secret.bat GROQ_API_KEY your_new_key
```

### Redeploy frontend after code changes:
```bat
scripts\aws\09_deploy_frontend_s3.bat
```

### Redeploy backend after code changes:
```bat
scripts\aws\02_build_and_push.bat
scripts\aws\04_deploy_backend.bat
```

### Invalidate CloudFront cache after frontend redeploy:
```powershell
aws cloudfront create-invalidation --distribution-id E3EE5PX8GNLDQU --paths "/*" --region us-east-1
```

### Check deployment status:
```bat
scripts\aws\07_verify_deployment.bat
```

### Clean up all AWS resources:
```bat
scripts\aws\cleanup_vireon.bat
```
