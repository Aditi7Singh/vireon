# Vireon MVP Definition

## Product Name
Vireon: AI Financial Copilot for ERP-driven startups and SMBs.

## MVP Goal
Deliver a production-usable finance intelligence assistant that helps founders/CFOs monitor cash health, runway, anomalies, and operational finance decisions using ERP-linked data.

## Target User
- Primary: Founder / CEO
- Secondary: Finance lead / Fractional CFO
- Tertiary: CTO monitoring infrastructure burn and budget impact

## Core Problem Statement
Finance teams spend too much time assembling data from ERP reports and spreadsheets before taking action. Vireon should provide near-real-time financial insight and guidance with deterministic, auditable metrics.

## MVP Scope (Must-Have)
1. Data Foundation
- ERP data ingestion and normalization (invoices, expenses, ledger, metrics)
- Company-level financial snapshot (cash, burn, runway, revenue)

2. AI Copilot
- Natural-language financial Q&A
- Tool-driven responses from backend calculations (not freeform arithmetic)
- Context-aware follow-up conversation

3. Dashboard Surface
- Executive dashboard (cash, burn, runway, trends)
- Revenue and expense analytics views
- Basic scenario modeling (hiring/revenue/expense change impact)

4. Risk and Alerts
- Anomaly detection and actionable alerting
- Email/SMS notification channels

5. Deployability and Operability
- Docker-based production deployment
- Liveness/readiness health endpoints
- Startup dependency checks
- CI tests for key APIs and agent quality regression

## Out of Scope for MVP
- Full accounting replacement workflow (complete AP/AR operations suite)
- Advanced enterprise governance packages (SOX-heavy workflow automation)
- Multi-entity consolidation as a default experience
- Full no-code workflow builder

## MVP Success Criteria
- Reliability: API readiness success rate >= 99% in pilot period
- Financial fidelity: Core metrics match source reports within acceptable tolerance
- User value: users can get runway/cash/burn answers in < 30 seconds
- Alert usefulness: at least 1 actionable anomaly recommendation per active account per month

## Current Build State (as implemented)
- Production compose stack with optional in-stack Ollama
- One-command EC2 bootstrap available
- Agent quality evaluator tests integrated in CI
- Health/live and health/ready endpoints available for ops

## MVP Exit Criteria
MVP is complete when pilot users can:
1. Connect data source(s) and see trusted core metrics.
2. Ask financial questions and receive actionable answers with numeric grounding.
3. Receive and act on anomaly alerts.
4. Operate deployment with standard SRE checks.
