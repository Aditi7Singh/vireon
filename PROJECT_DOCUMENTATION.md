# Vireon — AI Financial Copilot for ERP Systems

## Overview

**Vireon** is an AI-powered financial intelligence system designed to work alongside enterprise ERP platforms. The system acts as a fractional AI CFO, capable of analyzing financial data, detecting anomalies, forecasting cash runway, and answering complex financial questions in natural language.

Instead of building a simulated financial database from scratch, this system integrates directly with **ERPNext**, an open-source enterprise resource planning system used by real companies for accounting, financial management, and operations.

### ERPNext Data Coverage & Positioning
Vireon acts as an AI Copilot that **works with ERPNext + has its own modules for what's missing**. Core metrics (cash, burn, runway, revenue, expenses, and GL anomalies) are derived directly from ERPNext data. However, specific gaps in standard ERPNext are handled natively by Vireon's own tables, including:
- **Payroll/HR data** (`Employee` and `PayrollEntry` tables)
- **Loans and custom depreciation** (`Loan` and `FixedAsset` tables)

The AI agent operates as a financial analyst and decision-support tool. It retrieves financial data from ERPNext, processes it using a deterministic analytics engine, and communicates insights through a conversational interface and interactive dashboards.

This architecture ensures that financial calculations remain deterministic and auditable while still enabling natural language interaction through a large language model.

---

## System Architecture

The project moves from a demo financial simulator to a real enterprise workflow system, where ERPNext serves as the **financial system of record**.

```mermaid
graph TD
    User([User]) --> Frontend[Next.js Frontend]
    Frontend --> Agent[AI Agent Layer - LLM + Tool Calling]
    Agent --> Backend[FastAPI Backend - Tool APIs]
    Backend --> MathEngine[Analytics / Math Engine]
    MathEngine --> ERPAPI[ERPNext REST API]
    ERPAPI --> ERPDB[(ERPNext Database)]
```

### Core System Components

1.  **Frontend (Next.js + Tremor)**: Interactive dashboards, cash runway visualization, AI chat interface, and scenario simulation.
2.  **AI Agent Layer (GPT-4o / Qwen3)**: Interprets user questions and orchestrates tool usage. The agent **never** performs calculations; it calls backend tools.
3.  **Backend API Layer (FastAPI)**: Acts as the tool layer, querying ERPNext and providing structured financial outputs.
4.  **Math Engine (Python)**: Deterministic functions for calculating startup metrics (Burn Rate, Runway, ARR, MRR, Gross Margin).
5.  **ERPNext Integration**: ERPNext stores all data (Sales Invoices, Purchase Invoices, Payment Entries, GL Entries) as the source of truth.
6.  **Anomaly Detection Engine**: Celery workers scanning for financial anomalies with statistical analysis.

---

## Tech Stack

| Layer              | Technology                                           |
| :----------------- | :--------------------------------------------------- |
| **Frontend**       | Next.js 14, Tailwind CSS, Tremor, TypeScript         |
| **AI Agent**       | LangGraph, Qwen3 via Groq, Ollama                    |
| **Backend**        | Python, FastAPI, SQLAlchemy                          |
| **Math Engine**    | Python (Deterministic Logic)                         |
| **Anomaly Engine** | Celery + Redis                                       |
| **ERP System**     | ERPNext / Merge.dev                                  |
| **Database**       | SQLite (local), PostgreSQL (Neon), MariaDB (ERPNext) |

---

## Project Structure

```
vireon/
├── PROJECT_DOCUMENTATION.md   # This comprehensive documentation
├── README.md                 # Project overview
├── docker-compose.yml        # Docker configuration
├── setup_ollama.sh          # Ollama local LLM setup script
│
├── backend/                  # FastAPI Backend + Math Engine
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database connection configuration
│   ├── auth.py             # Authentication utilities
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Core Python dependencies
│   ├── requirements_agent.txt  # LangGraph agent dependencies
│   ├── .env.example        # Environment variables template
│   │
│   ├── agent/               # Phase 3: LangGraph AI Agent
│   │   ├── cfo_agent.py    # Main LangGraph StateGraph
│   │   ├── tools.py        # 10 LangChain tool definitions
│   │   ├── prompts.py      # System prompts + CFO persona
│   │   ├── routing.py      # Query classifier
│   │   ├── memory.py       # SqliteSaver session management
│   │   └── agent_runner.py # Simple agent runner (legacy)
│   │
│   ├── analytics/          # Math Engine components
│   │   ├── metrics.py      # Core financial calculations
│   │   └── scenarios.py    # Financial scenario simulations
│   │
│   ├── anomaly/            # Phase 4: Anomaly Detection Engine
│   │   ├── celery_app.py   # Celery + Beat configuration
│   │   ├── scanner.py      # Core anomaly detection algorithms
│   │   ├── tasks.py        # Celery tasks
│   │   ├── seed_alerts.py  # Development test data
│   │   └── migrations/
│   │       └── 001_create_alerts.sql
│   │
│   ├── api/               # REST API endpoints
│   │   └── routers/
│   │       ├── agent.py    # Agent API endpoints
│   │       ├── analytics.py # Analytics API endpoints
│   │       ├── auth.py    # Authentication endpoints
│   │       ├── erpnext.py # ERPNext integration endpoints
│   │       └── ingest.py  # Data ingestion endpoints
│   │
│   ├── config/            # Configuration
│   │   ├── settings.py    # LLM, API, environment settings
│   │   └── company_profile.py  # Company financial context
│   │
│   ├── integrations/      # Production data sources
│   │   └── merge_client.py # Merge.dev unified API client
│   │
│   ├── erpnext_client/   # ERPNext API client
│   │   └── client.py
│   │
│   ├── alembic/          # Database migrations
│   │   └── versions/
│   │
│   ├── scripts/          # Utility scripts
│   │   └── simulation/  # Financial data simulation
│   │
│   └── tests/           # Backend tests
│
├── frontend/             # Next.js Frontend
│   ├── app/             # App Router pages
│   │   ├── page.tsx    # Landing page
│   │   ├── layout.tsx  # Root layout
│   │   ├── globals.css # Global styles
│   │   └── (dashboard)/ # Dashboard routes
│   │       ├── layout.tsx       # Dashboard layout
│   │       ├── agent/          # AI Agent chat interface
│   │       ├── anomalies/     # Anomaly detection dashboard
│   │       ├── dashboard/     # Main financial dashboard
│   │       ├── scenarios/     # Scenario simulation interface
│   │       └── settings/      # Application settings
│   │
│   ├── components/     # Reusable React components
│   │   └── Sidebar.tsx # Navigation sidebar
│   │
│   ├── public/        # Static assets
│   ├── tests/         # Frontend tests
│   ├── package.json   # Node.js dependencies
│   ├── tsconfig.json # TypeScript configuration
│   ├── next.config.ts # Next.js configuration
│   └── README.md     # Frontend documentation
│
└── erpnext_integration/  # ERPNext data import
    └── import_data.py
```

---

## Phase 3: LangGraph AI Agent

### Overview

The LangGraph agent provides conversational AI CFO capabilities with tool calling.

### LLM Strategy

- **Primary**: Qwen3-32B on Groq API (free, fast mode) → routine queries
- **Thinking**: QwQ-32B on Groq API (free, think mode) → complex reasoning
- **Privacy**: qwen3:30b on Ollama (local, no internet) → sensitive data
- **Future**: DeepSeek-V3 on OpenRouter (one-line swap for production)

### Agent Tools (10 total)

1. `get_cash_balance` - Current cash position
2. `get_burn_rate` - Monthly burn calculation
3. `get_runway` - Cash runway calculation
4. `simulate_hire` - Hiring impact simulation
5. `simulate_revenue_change` - Revenue scenario simulation
6. `simulate_expense_change` - Expense change simulation
7. `get_active_alerts` - Active anomaly alerts
8. `get_expense_breakdown` - Expense analysis
9. `get_revenue_metrics` - MRR/ARR metrics
10. `get_financial_scorecard` - Full KPI overview

### Key Files

- [`vireon/backend/agent/cfo_agent.py`](vireon/backend/agent/cfo_agent.py) - Main LangGraph StateGraph
- [`vireon/backend/agent/tools.py`](vireon/backend/agent/tools.py) - Tool definitions
- [`vireon/backend/agent/prompts.py`](vireon/backend/agent/prompts.py) - CFO persona prompts
- [`vireon/backend/agent/routing.py`](vireon/backend/agent/routing.py) - Query classifier
- [`vireon/backend/agent/memory.py`](vireon/backend/agent/memory.py) - Session management
- [`vireon/backend/config/settings.py`](vireon/backend/config/settings.py) - LLM configuration

---

## Phase 4: Anomaly Detection Engine

### Overview

Background Celery worker that scans GL entries and detects financial anomalies.

### Alert Types

- **Spike**: Transaction >15% above 90-day baseline (WARNING) or >50% (CRITICAL)
- **Trend**: Category growing >5%/month for 3+ consecutive months
- **Duplicate**: Same vendor, same amount within 30-day window
- **New Vendor**: First appearance of new vendor with significant spend

### Alert Thresholds

- WARNING: actual > baseline + 1.5σ AND delta_pct > 15%
- CRITICAL: actual > baseline + 2.5σ AND delta_pct > 50%

### Celery Tasks

- `scan_for_anomalies` - Daily 2am UTC scan
- `cleanup_old_alerts` - Weekly Sunday 3am UTC cleanup
- `trigger_scan_now` - On-demand scan via API

### Key Files

- [`vireon/backend/anomaly/celery_app.py`](vireon/backend/anomaly/celery_app.py) - Celery configuration
- [`vireon/backend/anomaly/scanner.py`](vireon/backend/anomaly/scanner.py) - Detection algorithms
- [`vireon/backend/anomaly/tasks.py`](vireon/backend/anomaly/tasks.py) - Background tasks
- [`vireon/backend/anomaly/migrations/001_create_alerts.sql`](vireon/backend/anomaly/migrations/001_create_alerts.sql) - DB schema

---

## Phase 5: Production Data Integration

### Merge.dev Integration

Replace ERPNext with real accounting data from QuickBooks, Xero, NetSuite via Merge.dev.

### Data Source Routing

```python
# In config/settings.py
DATA_SOURCE = "erpnext"  # or "merge" for production

def get_data_client():
    if DATA_SOURCE == "merge":
        return MergeAccountingClient()
    else:
        return ERPNextClient()
```

### Key Files

- [`vireon/backend/integrations/merge_client.py`](vireon/backend/integrations/merge_client.py) - Merge.dev client

---

## Configuration

### Environment Variables

```bash
# LLM Configuration
GROQ_API_KEY=your_groq_key_here
USE_LOCAL_LLM=false  # Set true for Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:30b

# Backend API
BACKEND_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://user:pass@host/dbname
SESSION_DB_PATH=./data/sessions.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Merge.dev (Production)
MERGE_API_KEY=your_merge_key
MERGE_ACCOUNT_TOKEN=your_account_token
DATA_SOURCE=erpnext  # or "merge"

# Slack Notifications
SLACK_WEBHOOK_URL=your_webhook_url

# Company
COMPANY_NAME=SeedlingLabs
```

### Installation

```bash
# Backend setup
cd vireon/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements_agent.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload

# Start Celery worker (new terminal)
celery -A backend.anomaly.celery_app worker -l info

# Start Celery Beat (new terminal)
celery -A backend.anomaly.celery_app beat -l info

# Frontend setup
cd vireon/frontend
npm install
npm run dev
```

### Ollama Setup (Privacy Mode)

```bash
chmod +x vireon/setup_ollama.sh
./vireon/setup_ollama.sh

# Then set USE_LOCAL_LLM=true in .env
```

---

## Key Features

### 1. Autonomous Financial Alerts

Monitors ERPNext for spending spikes, customer churn, or runway thresholds. Automatically detects and alerts on:

- Unusual expense patterns
- Duplicate payments
- Budget variances exceeding thresholds

### 2. Natural Language Financial Queries

Ask questions like "Why did expenses increase last month?" and get AI-driven insights with drivers identified from GL entries.

### 3. Scenario Simulation

"What if we hire 3 engineers?" — Simulate payroll increases and calculate impact on runway with precise mathematical models.

### 4. Financial Forecasting

Deterministic models for ARR, MRR, Gross Margin, and operating cash flow that remain auditable and verifiable.

### 5. Conversation Memory

The agent maintains context across conversation turns using SqliteSaver checkpointer.

---

## API Endpoints

### Authentication

- `POST /api/v1/auth/token` - Get authentication token
- `GET /api/v1/auth/me` - Get current user info

### Analytics

- `GET /api/v1/metrics/financials/{company_id}` - Get financial summary
- `POST /api/v1/scenarios/simulate-hiring` - Simulate hiring impact
- `POST /api/v1/scenarios/simulate-revenue` - Simulate revenue change

### Agent

- `POST /api/v1/agent/chat` - Send query to AI agent
- `POST /api/v1/agent/chat/stream` - Streaming response (SSE)
- `GET /api/v1/agent/history/{session_id}` - Get conversation history

### Alerts

- `GET /api/v1/alerts` - Get active alerts
- `POST /api/v1/alerts/scan-now` - Trigger manual scan
- `PATCH /api/v1/alerts/{alert_id}/dismiss` - Dismiss an alert

### ERPNext

- `GET /api/v1/erpnext/accounts` - Fetch accounts from ERPNext
- `POST /api/v1/erpnext/sync` - Sync data from ERPNext

---

## Future Vision

The long-term goal is to build an AI financial copilot capable of understanding and analyzing enterprise financial systems in real time, enabling founders and operators to make better financial decisions faster. This represents a step toward **autonomous financial intelligence** for modern companies, with Vireon leading the way.

---

## License

This project is proprietary software. All rights reserved.

---

## Quick Reference

### One-Line LLM Swap

```python
# Development (free)
llm = ChatGroq(model="qwen3-32b", api_key=GROQ_API_KEY)

# Local / Privacy
llm = ChatOllama(model="qwen3:30b")

# Production scale
llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1",
                 model="deepseek/deepseek-chat-v3-5",
                 api_key=OPENROUTER_KEY)

# Best reasoning (paid)
llm = ChatAnthropic(model="claude-sonnet-4-20250514",
                    api_key=ANTHROPIC_KEY)
```

### Starting Services

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Celery Worker
celery -A backend.anomaly.celery_app worker -l info

# Celery Beat
celery -A backend.anomaly.celery_app beat -l info

# Flower (monitoring)
celery -A backend.anomaly.celery_app flower --port=5555

# Frontend
cd frontend && npm run dev
```
