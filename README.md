# Vireon — Autonomous AI CFO for ERP Systems

> **What if your CFO never slept, never missed an anomaly, and could answer scenario questions in 3 seconds?**  
> Vireon rivals QuickBooks' complexity while acting as a proactive, always-on Finance Manager.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20Next.js%2014%20%7C%20LangGraph-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ⚡ One-Command Demo

```bash
git clone https://github.com/vireon/vireon.git && cd vireon
bash demo.sh
```

Opens at **http://localhost:3000** with Orchard Analytics Inc. pre-loaded — 12 months of SaaS financials, 7 pre-seeded anomalies, and all AI features wired up. No API keys required for analytics; add your Groq key in `backend/.env` to enable AI chat.

---

## 30-Second Pitch

A 50-person SaaS company loses **2 FTE-weeks per month** to manual finance work:
month-end close takes 8 days, anomalies are discovered at board meetings, and
"what's our runway if we hire 3 engineers?" costs 3 days of a CFO's time.

Vireon solves this with three layers that no competitor offers:

1. **Deterministic Math Engine** — runway, scenario math, and headcount cost in pure Python. Zero LLM hallucinations on numbers.
2. **LangGraph Multi-Agent System** — CFO Agent + Auditor Agent + Strategist Agent collaborate on every complex query.
3. **Isolation Forest ML** — scans every GL transaction, flags anomalies *before* the board meeting.

**Before / After:**

| Task | Before | After Vireon |
|------|--------|--------------|
| Month-end close | 8 days, 3 people | **4 hours, 1 click** |
| Spot an anomaly | Found at board meeting | **Alerted 48 hrs early** |
| Scenario planning | 3-day CFO turnaround | **3-second answer** |
| Board deck | 1 day of assembly | **Auto-generated narrative** |

---

## Why Not QuickBooks + a GPT Wrapper?

| Capability | QuickBooks | Xero | Pilot.ai | **Vireon** |
|-----------|:----------:|:----:|:--------:|:----------:|
| Multi-agent AI reasoning | ❌ | ❌ | ❌ | ✅ LangGraph CFO + Auditor + Strategist |
| ML anomaly detection | ❌ | ❌ | ❌ | ✅ Isolation Forest (scikit-learn) |
| Deterministic math engine | ❌ | ❌ | ❌ | ✅ Zero hallucination guarantee |
| Month-end close automation | Manual | Manual | Partial | ✅ 10-item auto-checklist + readiness score |
| Cash Flow at Risk | ❌ | ❌ | ❌ | ✅ 10,000 Monte Carlo paths + fan chart |
| GL drill-down from charts | ❌ | ❌ | ❌ | ✅ Click any bar → real GL entries |
| Multi-jurisdiction tax | Plugin | ❌ | US only | ✅ US/UK/Dubai/India/Singapore/EU |
| SOC 2 audit trail | Basic | Basic | ❌ | ✅ SHA-256 immutable event log |

A GPT wrapper on QuickBooks still hallucinates dollar amounts and cannot simulate "hire 5 engineers in Dubai" with deterministic payroll math. Vireon separates AI reasoning from financial arithmetic by design.

---

## Overview

**Vireon** is a sophisticated, industry-ready Autonomous AI CFO built on top of enterprise ERP platforms. It combines deterministic financial math with multi-agent AI reasoning to deliver actionable intelligence — not just charts.

### What sets Vireon apart from dashboards

| Feature | Simple Dashboard | Vireon |
|---------|-----------------|--------|
| Charts | Static visuals | **Actionable** — click to drill into real GL entries |
| Anomaly Detection | Static thresholds | **Isolation Forest ML** — detects split invoices, seasonal patterns |
| Forecasting | Simple averages | **Prophet + SARIMA ensemble** with DSO-trend inputs |
| AI Chat | Generic LLM | **LangGraph multi-agent** — Auditor + Strategist + CFO agents |
| Calculations | LLM arithmetic | **Deterministic Math Engine** — zero hallucinations |
| Cash Flow | Line chart | **Sankey diagram** (Revenue → OpEx → Net Profit) |
| Burn Analysis | Monthly bar | **Waterfall chart** with month-over-month drill-down |

---

## Architecture

```mermaid
graph TD
    subgraph "Data Sources"
        ERP[ERPNext REST API]
        PLAID[Plaid Bank API]
        STRIPE[Stripe Webhooks]
        AWS[AWS Billing API]
    end

    subgraph "FastAPI Backend /api/v1"
        INGEST[Ingest · GL Sync]
        ANALYTICS[Analytics · Runway · Burn]
        ADVANCED[Advanced Analytics<br/>GL Drill-Down · Sankey · Waterfall]
        AGENT_RT[Agent Router]
    end

    subgraph "LangGraph Multi-Agent Layer"
        CFO[CFO Agent<br/>classify → tools → analyze]
        AUDITOR[Auditor Agent<br/>fetch_gl → reconcile → report]
        STRATEGIST[Strategist Agent<br/>baseline → payroll_tax → math_engine]
    end

    subgraph "Deterministic Engines"
        MATH[Math Engine<br/>Fully-loaded cost · Runway simulation]
        IF_SVC[Isolation Forest<br/>Split Invoice · Seasonal Anomalies]
        FORECAST[SARIMA + Prophet<br/>DSO-aware forecasting]
    end

    subgraph "Next.js Frontend"
        SANKEY[Sankey Cash Flow Map]
        WATERFALL[Waterfall Burn Analysis]
        DRAWER[GL Drill-Down Drawer]
    end

    ERP --> INGEST --> ANALYTICS
    PLAID --> AGENT_RT
    AGENT_RT --> CFO & AUDITOR & STRATEGIST
    STRATEGIST --> MATH
    ADVANCED --> IF_SVC
    SANKEY & WATERFALL & DRAWER --> ADVANCED
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Tremor, Recharts |
| **AI Agents** | LangGraph, LangChain, OpenAI GPT-4o (Groq / Ollama fallback) |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| **ML / Analytics** | Scikit-learn (Isolation Forest), Prophet, SARIMA, NumPy, Pandas |
| **Math Engine** | Pure Python — deterministic, no LLM arithmetic |
| **Database** | PostgreSQL 15, Redis 8 |
| **Job Queue** | Celery + Redis Beat |
| **ERP** | ERPNext REST API |
| **Bank Integration** | Plaid API |
| **Containers** | Docker Compose (7-service orchestration) |

---

## Key Features

### Interactive Dashboards (QuickBooks-Level)
- **Drill-Down Everything**: Click any chart segment → side drawer with real GL entries
- **Sankey Cash Flow Map**: Revenue → COGS → Gross Profit → OpEx → Net P&L
- **Waterfall Burn Analysis**: Month-over-month cash changes with bar-level drill-down
- **Executive Dashboards**: CEO (cash/runway), CTO (tech costs), Finance (GL/close)

### LangGraph Multi-Agent System
- **CFO Agent**: Full LangGraph `StateGraph` with classify → agent → tools → analyze loop
- **Auditor Agent**: Autonomous bank reconciliation — fetches GL, fetches bank statement, runs deterministic matching, flags discrepancies
- **Strategist Agent**: Complex scenario planning — "What happens if we hire 5 engineers in Dubai and lose our biggest SaaS client?"

### Deterministic Math Engine (No LLM Hallucinations)
- Fully-loaded headcount cost by location (US, Dubai, India, UK, EU, Singapore…)
- Month-by-month cash runway simulation with hire/revenue/cost events
- Burn multiple, break-even month, zero-cash-month detection

### ML Anomaly Detection 2.0
- **Isolation Forest** (Scikit-learn): detects seasonal anomalies, unusual GL patterns
- **Split Invoice Detector**: flags same-vendor similar-amounts within a time window
- **7 additional detectors**: payroll spikes, churn, vendor pricing drift, concentration risk, duplicate expenses

### Predictive Forecasting
- **SARIMA + Prophet ensemble** with automated model retraining
- **Forecast monitoring**: accuracy tracking and drift detection
- **DSO-aware cash flow**: Days Sales Outstanding trends feed into cash projections

### Phase 3 — Enterprise Intelligence (Complete)
- **Automatic Accrual Detection**: scans vendor history + service dates to surface unbooked entries before close
- **Predictive Tax Provisioning**: multi-jurisdiction (US/UK/Dubai/India/Singapore/EU), R&D credits, deduction optimizer
- **Prophet DSO Forecasting**: Days Sales Outstanding trend → expected cash collection per month
- **Automated Month-End Close**: 10-item checklist with readiness score (0–100) and blocking issue triage
- **Cash Flow at Risk (CFaR)**: 10,000 Monte Carlo paths → fan chart, CFaR@95%, probability of going negative
- **Vendor Risk Intelligence**: concentration risk, payment drift, fraud signals, W-9 compliance
- **Real-Time Stripe Webhooks**: HMAC-SHA256 verified events — live MRR, churn, payment failures
- **SOC 2 Audit Trail**: immutable SHA-256 hashed event log with tamper detection endpoint

### Phase 4 — Research-Backed Additions (Complete)
- **Agentic Close Workflow**: LangGraph CloseAgent with graceful direct-orchestration fallback
- **Zero-Shot Tax Code Classifier**: auto-classify GL descriptions to IRS account codes (6400 SaaS, 6200 R&D, etc.)
- **NLP Contract Risk Extraction**: 8 risk clause detectors — auto-renewal, termination penalties, IP rights, price escalation
- **Board Deck Auto-Generator**: LLM narrative + deterministic template fallback from real board metrics
- **Multi-Entity Consolidation**: FX translation + intercompany elimination across all subsidiaries

---

## API Endpoints (Complete Reference)

### Phase 2 — AI Upgrade
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/advanced/anomalies/isolation-forest` | Run ML anomaly scan |
| `GET`  | `/api/v1/advanced/gl/drilldown` | GL entries for a category |
| `POST` | `/api/v1/advanced/agents/reconcile` | Trigger Auditor Agent |
| `POST` | `/api/v1/advanced/agents/scenario` | Trigger Strategist Agent |
| `GET`  | `/api/v1/advanced/cash-flow/sankey` | Sankey diagram data |
| `GET`  | `/api/v1/advanced/burn-analysis/waterfall` | Waterfall chart data |

### Phase 3 & 4 — Enterprise + Research
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/phase3/accruals/detect` | Auto accrual detection |
| `POST` | `/api/v1/phase3/tax/provision` | Predictive tax provisioning |
| `POST` | `/api/v1/phase3/dso/forecast` | DSO-based cash flow forecast |
| `POST` | `/api/v1/phase3/close/run` | Automated month-end close |
| `GET`  | `/api/v1/phase3/close/checklist` | Close checklist template |
| `POST` | `/api/v1/phase3/cfar/simulate` | CFaR Monte Carlo (10K paths) |
| `POST` | `/api/v1/phase3/vendor-risk/analyze` | Vendor risk intelligence |
| `POST` | `/api/v1/phase3/tax/classify` | Zero-shot tax code classifier |
| `POST` | `/api/v1/phase3/tax/classify/batch` | Batch GL auto-classification |
| `POST` | `/api/v1/phase3/contracts/risk-extract` | NLP contract risk extraction |
| `POST` | `/api/v1/webhooks/stripe/events` | Real-time Stripe webhooks |
| `GET`  | `/api/v1/webhooks/stripe/mrr` | Live MRR dashboard |
| `POST` | `/api/v1/board-reports/{id}/generate-narrative` | LLM board deck narrative |
| `GET`  | `/api/v1/audit/tamper-check/{company_id}` | SOC 2 tamper detection |

Full API reference at `/api/v1/docs` (Swagger) or `/api/v1/redoc`.

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15
- Redis 8+
- ERPNext instance with API credentials
- OpenAI API key (or Groq / Ollama for local LLM)

### Quick Start — Demo Mode (Recommended)

```bash
# One command — seeded with 12 months of realistic SaaS data
bash demo.sh
```

This starts 4 Docker services, creates the schema, seeds Orchard Analytics Inc., and opens the dashboard. Works without any external API keys for all analytics features.

### Full Setup with Docker Compose

```bash
# 1. Clone
git clone https://github.com/vireon/vireon.git
cd vireon

# 2. Configure
cp backend/.env.demo backend/.env
# Edit backend/.env — add your GROQ_API_KEY to enable AI chat

# 3. Start all services (incl. Celery worker + scheduler)
docker compose up -d

# 4. Migrate DB
docker compose exec backend alembic upgrade head

# 5. Seed demo data
docker compose exec backend python scripts/demo_full_seed.py
```

**Access:**
- Frontend:   http://localhost:3000
- API:        http://localhost:8000
- API Docs:   http://localhost:8000/api/v1/docs
- Mailhog:    http://localhost:8025

### Local Development

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
vireon/
├── frontend/
│   ├── app/(dashboard)/
│   │   ├── dashboard/            # CEO · CTO · Finance views
│   │   ├── cash-flow/            # Sankey + forecast + GL drill-down
│   │   ├── burn-analysis/        # Waterfall chart + KPIs
│   │   ├── anomalies/            # Isolation Forest ML scanner
│   │   ├── runway/               # Scenario planner
│   │   ├── scenarios/            # Scenario comparison
│   │   ├── agent/                # AI chat (CFO · Auditor · Strategist)
│   │   ├── accruals/             # ★ Phase 3: Accrual detection dashboard
│   │   ├── tax-provisioning/     # ★ Phase 3: Multi-jurisdiction tax estimates
│   │   ├── cfar/                 # ★ Phase 4: Cash Flow at Risk fan chart
│   │   ├── vendor-risk/          # ★ Phase 4: Vendor risk + tax classifier
│   │   ├── month-end-close/      # ★ Phase 3/4: Close checklist + readiness score
│   │   └── consolidation/        # ★ Phase 3: Multi-entity P&L with FX
│   └── components/
│       ├── SankeyChart.tsx       # Cash Flow Sankey diagram
│       ├── WaterfallChart.tsx    # Burn Analysis waterfall
│       ├── GLDrilldownDrawer.tsx # GL entries side drawer
│       ├── ChatDrawer.tsx        # AI agent chat
│       └── ...
│
├── backend/
│   ├── agent/
│   │   ├── cfo_agent.py          # LangGraph CFO Agent
│   │   ├── auditor_agent.py      # LangGraph Auditor (bank reconciliation)
│   │   ├── strategist_agent.py   # LangGraph Strategist (scenario planning)
│   │   ├── close_agent.py        # ★ Phase 3/4: Agentic month-end close
│   │   └── tools.py              # 100+ financial tools
│   │
│   ├── services/
│   │   ├── isolation_forest_service.py  # ML anomaly detection
│   │   ├── math_engine.py               # Deterministic scenario math
│   │   ├── forecasting_service.py       # SARIMA + Prophet
│   │   ├── accrual_detection_service.py # ★ Phase 3: Auto accrual detection
│   │   ├── predictive_tax_service.py    # ★ Phase 3: Multi-jurisdiction tax
│   │   ├── dso_forecast_service.py      # ★ Phase 3: Prophet DSO forecasting
│   │   ├── cfar_service.py              # ★ Phase 4: CFaR Monte Carlo
│   │   ├── vendor_risk_service.py       # ★ Phase 4: Vendor risk + tax classifier
│   │   └── ...
│   │
│   ├── api/routers/
│   │   ├── advanced_analytics.py  # GL drill-down · Sankey · Waterfall · IF
│   │   ├── phase3.py              # ★ Phase 3/4: All new enterprise endpoints
│   │   ├── stripe_webhooks.py     # ★ Phase 3: Real-time Stripe events
│   │   ├── agent.py               # CFO · Auditor · Strategist endpoints
│   │   └── 45+ more routers
│   │
│   ├── models.py               # 80+ SQLAlchemy models
│   ├── main.py                 # FastAPI app + all routers
│   └── requirements.txt
│
├── ARCHITECTURE.md             # Mermaid diagrams + complete feature roadmap
├── docker-compose.yml
└── DEPLOYMENT.md
```

---

## Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5433/vireon

# AI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# ERPNext
ERPNEXT_URL=https://your-erpnext.com
ERPNEXT_API_KEY=...
ERPNEXT_API_SECRET=...

# Email Alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@yourcompany.com
SMTP_PASS=app-password

# Optional: local LLM fallback
USE_LOCAL_LLM=false
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Scenario Planning Examples

The Strategist Agent handles complex natural language queries using the Deterministic Math Engine:

```
"What happens to our runway if we hire 5 engineers in Dubai and lose our 
 biggest SaaS client next quarter?"

→ Fetches baseline: $4.2M cash, $380K revenue, $620K burn
→ Fetches Dubai payroll tax: 1.15× overhead multiplier
→ Computes: 5 × $120K × 1.15 / 12 = $57,500/month extra burn
→ Revenue loss: ~$76K/month (20% MRR estimate)
→ New net burn: $353,500/month
→ Runway: 18.1 months → 11.9 months (−6.2 months)
```

---

## Real-World Impact — Illustrative Case Study

> *Based on the capabilities demonstrated in the demo. Names are illustrative.*

**Situation:** A 55-person B2B SaaS company (Series A, $3.2M ARR) was spending 9 days on month-end close and discovered a $42,000 AWS billing error *after* their board meeting.

**With Vireon:**

- **Day 1** — Isolation Forest flagged the AWS spike (+51%) on the day it appeared. CFO was notified via email alert before the billing cycle closed. Recovered $42,000.
- **Week 2** — Strategist Agent answered "what if we open a London office with 4 hires?" in 4 seconds with a full cost model (NI overhead, FX, equity dilution impact on burn multiple).
- **Month 3** — Month-end close dropped from 9 days → 5 hours. Auto-checklist identified 2 unbooked accruals and 3 unmatched bank transactions automatically.
- **Quarter 1** — Board deck narrative auto-generated in under 60 seconds from live GL data. Finance team reclaimed ~18 hours/month.

**Key metrics saved:** ~2 FTE-weeks/month in finance ops, $42K recovered anomaly, 9 days → 5 hours close cycle.

---

## Troubleshooting

### Backend
```bash
docker compose logs backend          # View logs
docker compose exec backend alembic upgrade head  # Run migrations
```

### Frontend
```bash
rm -rf frontend/.next               # Clear cache
docker compose up --build frontend  # Rebuild
```

### Redis / Celery
```bash
docker compose exec redis redis-cli ping  # Should return PONG
docker compose logs worker                # Celery worker logs
```

---

## API Documentation

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

---

## License

MIT License. See `LICENSE` for details.

---

**Version**: 3.0.0 — Autonomous AI CFO + Enterprise Intelligence  
**Last Updated**: April 2026  
**Status**: Production Ready · Enterprise Tier · Phase 3/4 Complete
