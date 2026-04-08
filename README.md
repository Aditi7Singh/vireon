--# Vireon — Your AI Financial Copilot for ERP Systems

## Overview

**Vireon** is an AI-powered financial intelligence system designed to work alongside enterprise ERP platforms. The system acts as a fractional AI CFO, capable of analyzing financial data, detecting anomalies, forecasting cash runway, and answering complex financial questions in natural language.

Instead of building a simulated financial database from scratch, this system integrates directly with **ERPNext**, an open-source enterprise resource planning system used by real companies for accounting, financial management, and operations.

### ERPNext Data Coverage & Positioning
Vireon acts as an AI Copilot that **works with ERPNext + has its own modules for what's missing**. Core metrics (cash, burn, runway, revenue, expenses, and GL anomalies) are derived directly from ERPNext data. However, specific gaps in standard ERPNext are handled natively by Vireon's own tables, including:
- **Payroll/HR data** (`Employee` and `PayrollEntry` tables)
- **Loans and custom depreciation** (`Loan` and `FixedAsset` tables)

The AI agent operates as a financial analyst and decision-support tool. It retrieves financial data from ERPNext, processes it using a deterministic analytics engine, and communicates insights through a conversational interface and interactive dashboards.

This architecture ensures that financial calculations remain deterministic and auditable while still enabling natural language interaction through a large language model.

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
2.  **AI Agent Layer (GPT-4o)**: Interprets user questions and orchestrates tool usage. The agent **never** performs calculations; it calls backend tools.
3.  **Backend API Layer (FastAPI)**: Acts as the tool layer, querying ERPNext and providing structured financial outputs.
4.  **Math Engine (Python)**: Deterministic functions for calculating startup metrics (Burn Rate, Runway, ARR, MRR, Gross Margin).
5.  **ERPNext Integration**: ERPNext stores all data (Sales Invoices, Purchase Invoices, Payment Entries, GL Entries) as the source of truth.

## Tech Stack Summary

| Layer           | Technology                    |
| :-------------- | :---------------------------- |
| **Frontend**    | Next.js, Tailwind CSS, Tremor |
| **AI Agent**    | OpenAI GPT-4o / LangGraph     |
| **Backend**     | Python, FastAPI               |
| **Math Engine** | Python (Deterministic Logic)  |
| **ERP System**  | ERPNext                       |
| **Database**    | MariaDB (ERPNext default)     |

## Key Features

### Dashboard & Analytics
- **Executive Dashboard (CEO)**: Real-time cash position, monthly burn rate, runway forecast, and key financial metrics
- **Chief Technology Officer Dashboard**: AWS infrastructure costs tracking, tech spend trends, software licensing costs with quick entry forms
- **Finance Dashboard**: General ledger review, financial transactions, and detailed expense analysis
- **Revenue Dashboard**: Sales pipeline, invoice status, ARR/MRR metrics, and revenue forecasts
- **Expense Management**: Detailed expense categorization, cost allocation, and spending analysis
- **Tax Planning**: Tax liability tracking, deduction optimization, and compliance monitoring
- **Anomaly Detection**: Automated alerts for spending anomalies, revenue dips, and operational outliers

### AI & Intelligence
- **Autonomous Financial Alerts**: SMTP-integrated email notifications for spending spikes, customer churn, and runway thresholds
- **Natural Language Financial Queries**: Chat interface to ask complex financial questions (e.g., "Why did expenses increase?" or "What's our current runway?")
- **AI Agent Layer**: GPT-4o powered agent with tool calling for orchestrated financial analysis
- **Scenario Simulation**: Interactive runway scenario planner with adjustable burn rate, hiring costs, and revenue growth
- **Benchmarking**: Compare financial metrics against industry standards

### Financial Forecasting & Planning
- **Runway Forecasting**: Real-time cash runway calculation with sensitivity analysis
- **Scenario Planning**: Model impact of hiring, cost reduction, or revenue changes on runway
- **Hiring Impact Calculator**: Estimate payroll costs and net impact on runway for new headcount
- **Tech Cost Tracking**: Monitor AWS, software licenses, and infrastructure spending with trend analysis
- **Financial Metrics**: ARR, MRR, Gross Margin, burn rate, and cash position calculations

### Multi-Channel Alerts
- **Email Notifications**: Configurable alerts sent via SMTP (Gmail, corporate email, etc.)
- **Alert Recipients**: Multiple recipient support (CEO, Finance team, custom email addresses)
- **Alert Types**: Spending anomalies, runway threshold warnings, revenue alerts, compliance notifications

### ERPNext Integration
- **Direct ERP Sync**: Reads accounting data from ERPNext (sales, purchases, GL entries)
- **Real-time Data Binding**: Dashboard metrics update automatically with ERP data
- **Custom Modules**: Payroll, loans, and fixed assets tracking beyond standard ERPNext

## Current Limitations

While Vireon provides robust financial intelligence, here are some areas that are still in development:

- **Multi-currency support** (partially implemented: currency capture and INR normalization exist; live FX sync, revaluation workflows, and full UI controls are still in progress)
- **Advanced ML forecasting** (implemented with SARIMA and Prophet fallbacks; next step is model monitoring and automated retraining)
- **OCR/document ingestion** (backend upload/status pipeline exists; production-grade OCR extraction and workflow automation are still in progress)

## Implementation Phases

### Phase 1: ERPNext Setup

- Install ERPNext and configure accounting modules.
- Enable REST API access and generate keys.

### Phase 2: Math Engine (Current Focus)

- Implement strict Python functions for core metrics:
  - `Calculate Runway (Cash ÷ Burn Rate)`
  - `Calculate Monthly Burn`
  - `Scenario Modifiers (e.g., Hiring Simulation)`

### Phase 3: Backend API Wrapper

- Implement FastAPI endpoints that wrap ERPNext API calls.
- Examples: `get_cash_balance`, `get_expenses`, `get_revenue`.

### Phase 4: AI Agent Integration

- Implement LLM with tool calling to orchestrate backend tools.

### Phase 5: Dashboard

- Build Next.js UI for visualization and real-time interaction.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL 15
- Redis 8.6+
- ERPNext instance with API credentials

### Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone https://github.com/vireon/vireon.git
   cd vireon
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   # Required: ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET
   # Required: OPENAI_API_KEY, SMTP_* settings for email alerts
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/v1/docs
   - Mailhog (Email Testing): http://localhost:1025

### Production Deployment (AWS + Ollama)

For the consolidated deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md).

For the current project status and remaining work, see [PROJECT_STATUS.md](PROJECT_STATUS.md).

### Configuration

#### Email Alerts (SMTP)
Configure in `backend/.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=alerts@yourcompany.com
ALERT_FALLBACK_EMAIL=finance@yourcompany.com
```

#### ERPNext Integration
```
ERPNEXT_URL=https://your-erpnext-instance.com
ERPNEXT_API_KEY=your-api-key
ERPNEXT_API_SECRET=your-api-secret
COMPANY_ID=your-company-id
```

#### AI Agent
```
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
```

### Database Setup

1. **Initialize PostgreSQL schema**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. **Seed demo data (optional)**
   ```bash
   docker compose exec backend python backend/scripts/seed_demo_data.py
   ```

### Development

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

#### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Project Structure

```text
vireon/
├── frontend/                    # Next.js React Application
│   ├── app/
│   │   ├── (dashboard)/        # Dashboard Pages
│   │   │   ├── dashboard/      # Executive, CTO, Finance dashboards
│   │   │   ├── runway/         # Scenario planning
│   │   │   ├── revenue/        # Revenue analytics
│   │   │   ├── expenses/       # Expense tracking
│   │   │   ├── tax/            # Tax planning
│   │   │   ├── anomalies/      # Anomaly detection
│   │   │   ├── benchmarking/   # Industry benchmarks
│   │   │   ├── agent/          # AI chat interface
│   │   │   └── settings/       # Configuration
│   ├── components/              # Reusable React components
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utilities and store
│   └── public/                  # Static assets
│
├── backend/                     # FastAPI Python Application
│   ├── agent/                   # AI Agent implementation
│   │   ├── agent_runner.py     # Main agent orchestration
│   │   ├── tools.py            # Tool definitions for LLM
│   │   ├── prompts.py          # System prompts and templates
│   │   └── routing.py          # Tool routing logic
│   │
│   ├── api/                     # API Route Handlers
│   │   ├── routers/
│   │   │   ├── analytics.py        # Financial metrics endpoints
│   │   │   ├── notifications.py    # Alert configuration
│   │   │   ├── financial_alerts.py # Alert management
│   │   │   ├── benchmarks.py       # Industry benchmarks
│   │   │   └── ...
│   │
│   ├── analytics/               # Math Engine & Calculations
│   │   ├── metrics.py          # Core financial metrics
│   │   └── scenarios.py        # Scenario simulation
│   │
│   ├── anomaly/                # Anomaly Detection
│   │   ├── scanner.py          # Detection algorithms
│   │   └── tasks.py            # Celery background tasks
│   │
│   ├── services/               # Business Logic
│   │   ├── tax_service.py      # Tax calculations
│   │   ├── vendor_services.py  # Vendor analytics
│   │   └── stripe_sync.py      # Payment sync
│   │
│   ├── tasks/                  # Celery Background Tasks
│   │   ├── alert_tasks.py      # Email notification tasks
│   │   └── sync_tasks.py       # Data synchronization
│   │
│   ├── erpnext_client/         # ERPNext API Client
│   │   └── client.py           # REST API wrapper
│   │
│   ├── scripts/                # Database & Data Scripts
│   │   ├── seed_demo_data.py
│   │   ├── seed_financial_data.py
│   │   └── ...
│   │
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── database.py             # Database connection & migrations
│   ├── auth.py                 # Authentication & authorization
│   ├── main.py                 # FastAPI application startup
│   └── requirements.txt        # Python dependencies
│
├── docker-compose.yml          # Container orchestration
├── README.md                   # This file
└── PROJECT_STATUS.md           # Development status & roadmap
```

---

## API Reference

All API endpoints are prefixed with `/api/v1/`. Below is a summary of available endpoints:

### Authentication
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/logout` | POST | User logout |
| `/api/v1/auth/register` | POST | Register new user |

### Data Ingestion
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/ingest/accounts` | GET/POST | Fetch and sync accounts |
| `/api/v1/ingest/contacts` | GET/POST | Fetch and sync contacts |
| `/api/v1/ingest/invoices` | GET/POST | Fetch and sync invoices |
| `/api/v1/ingest/expenses` | GET/POST | Fetch and sync expenses |
| `/api/v1/ingest/employees` | GET/POST | Fetch and sync employees |

### Analytics
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/analytics/runway` | GET | Calculate cash runway |
| `/api/v1/analytics/burn-rate` | GET | Calculate burn rate |
| `/api/v1/analytics/metrics` | GET | Get monthly metrics |
| `/api/v1/analytics/summary` | GET | Financial summary |

### AI Agent
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/agent/chat` | POST | Chat with AI agent |
| `/api/v1/agent/tools` | GET | List available tools |

### ERPNext Integration
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/erpnext/sync` | POST | Sync data from ERPNext |
| `/api/v1/erpnext/accounts` | GET | Get accounts |
| `/api/v1/erpnext/invoices` | GET | Get invoices |
| `/api/v1/erpnext/payments` | GET | Get payments |

### Alerts & Anomalies
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/alerts` | GET | List alerts |
| `/api/v1/alerts/{id}` | GET/PUT | Get or update alert |

### Benchmarks
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/benchmarks` | GET | Get industry benchmarks |
| `/api/v1/benchmarks/compare` | POST | Compare against benchmarks |

### Planning & Forecasting
| Endpoint | Method | Description |
| :-------- | :----- | :---------- |
| `/api/v1/planning/budgets` | GET/POST | Manage budgets |
| `/api/v1/planning/forecast` | GET/POST | Manage forecasts |
| `/api/v1/planning/scenarios` | GET/POST | Scenario planning |

## Troubleshooting

### Frontend Not Compiling
- Check browser console for errors
- Verify `frontend/.env` contains required API base URL
- Clear Next.js cache: `rm -rf frontend/.next`
- Rebuild frontend: `docker compose up --build frontend`

### Backend API Errors
- Check backend logs: `docker compose logs backend`
- Verify `backend/.env` configuration
- Ensure PostgreSQL is running: `docker compose logs postgres`
- Test database connection: `docker compose exec backend python -c "from database import engine; print(engine.execute('SELECT 1'))"`

### Email Alerts Not Sending
1. Verify SMTP credentials in `backend/.env`
2. Check backend logs: `docker compose logs backend | grep -i smtp`
3. Check test alert: `curl -X POST http://localhost:8000/api/v1/notifications/test`
4. For Gmail: Enable "Less secure app access" or use app-specific password

### ERPNext Sync Issues
1. Verify ERPNext URL is accessible
2. Check API credentials are correct
3. Review sync logs: `docker compose exec backend tail -f logs/sync.log`
4. Test connection: `curl https://your-erpnext.com/api/resource/Company`

### Redis Connection Issues
- Check Redis is running: `docker compose logs redis`
- Verify connection: `docker compose exec redis redis-cli ping`
- Expected response: `PONG`

## Deployment

### Docker Compose (Development)
```bash
docker compose up -d
```

### Production Deployment
For production deployment, consider:
1. Use managed PostgreSQL (RDS, Cloud SQL, etc.)
2. Use managed Redis (ElastiCache, Cloud Memorystore, etc.)
3. Deploy frontend to CDN (Vercel, Netlify, CloudFront)
4. Deploy backend to container service (ECS, GKE, Cloud Run)
5. Configure environment variables securely (secrets manager)
6. Enable HTTPS and proper security groups
7. Set up monitoring and alerting (DataDog, New Relic, etc.)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support & Documentation

- **Documentation**: See `PROJECT_STATUS.md` for development roadmap and current status
- **Issue Tracking**: GitHub Issues for bug reports and feature requests
- **Live Demo**: Available at https://vireon-demo.com (when deployed)
- **Community**: Join our Slack/Discord for discussions

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

## Acknowledgments

- Built with [Next.js](https://nextjs.org), [FastAPI](https://fastapi.tiangolo.com), and [ERPNext](https://erpnext.com)
- AI capabilities powered by [OpenAI GPT-4o](https://openai.com)
- Charts and visualization with [Tremor](https://www.tremor.so) and [Recharts](https://recharts.org)
- UI components with [Lucide Icons](https://lucide.dev) and [Tailwind CSS](https://tailwindcss.com)

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Status**: Stable - Production Ready

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`
- **OpenAPI Schema**: `/api/v1/openapi.json`

---

## Environment Variables

| Variable | Default | Description |
| :-------- | :------- | :---------- |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | `vireon-secret-key-change-in-production` | JWT secret key |
| `GROQ_API_KEY` | - | Groq API key for LLM |
| `USE_LOCAL_LLM` | `false` | Use local Ollama instead of Groq |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `SANDBOX_MODE` | `false` | Enable sandbox mode for testing |
| `COMPANY_NAME` | `SeedlingLabs` | Company name for display |

### Sandbox Mode

Set `SANDBOX_MODE=true` in your environment to enable sandbox mode for testing:

```bash
export SANDBOX_MODE=true
```
