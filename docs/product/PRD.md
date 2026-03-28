# Vireon Product Requirements Document (PRD)

## 1. Executive Summary
Vireon is an AI financial copilot that combines deterministic finance analytics with conversational decision support. It is designed to help startup operators understand runway risk, spend dynamics, and revenue trajectory without manual spreadsheet stitching.

## 2. Objectives
- Provide trusted, auditable financial intelligence from ERP-linked data.
- Reduce time to insight for founders and finance teams.
- Detect anomalies early and recommend concrete actions.
- Enable production-grade deployment and monitoring.

## 3. Personas
1. Founder/CEO
- Needs quick confidence on runway, burn, and strategic tradeoffs.

2. Finance Lead / Fractional CFO
- Needs numeric consistency, trend analysis, and operational alerting.

3. CTO / Ops Leader
- Needs infrastructure cost visibility and hiring/spend impact simulation.

## 4. User Stories
1. As a CEO, I can ask "How many months of runway do we have?" and receive a numeric, actionable answer.
2. As a finance lead, I can inspect burn, revenue, and anomalies by period and category.
3. As an operator, I can simulate hiring and cost changes before committing budgets.
4. As an admin, I can deploy and verify the system health with standard readiness probes.

## 5. Functional Requirements
### 5.1 Data and Metrics
- Ingest financial records and maintain normalized tables for metrics.
- Calculate cash position, burn rate, runway, and budget variance.
- Provide historical trend access by period.

### 5.2 AI Copilot
- Route user queries and use finance tools for data retrieval.
- Enforce deterministic metric sourcing (no model-only calculations).
- Return concise insights with numeric grounding and recommendations.

### 5.3 Alerts and Risk
- Detect anomalies in spend/revenue behavior.
- Emit alerts with severity and recommended next action.
- Support configurable notification channels.

### 5.4 Dashboards
- Executive summary cards and trend visuals.
- Revenue/expense/forecast views.
- Scenario simulation UX for strategic planning.

### 5.5 Platform and Operations
- Docker deployment topology with Postgres, Redis, backend, worker, frontend.
- Health endpoints:
  - /health/live for process liveness
  - /health/ready for dependency readiness
- Startup checks for database and optional Redis readiness requirement.

## 6. Non-Functional Requirements
- Availability target: 99.5% for pilot production.
- API p95 latency target: < 600 ms for cached/simple metric queries.
- Security: secret management outside source code, role-based access, TLS in production.
- Observability: structured logs, health checks, alerting on dependency failures.

## 7. Technical Architecture
- Frontend: Next.js
- Backend: FastAPI + SQLAlchemy
- Worker: Celery + Redis
- Database: PostgreSQL
- AI layer: LangGraph/LangChain with local or hosted LLM
- Optional local inference: Ollama models (fast + thinking profiles)

## 8. Deployment Requirements
### 8.1 Supported Ollama Modes
1. Containerized Ollama in same compose stack (default implemented mode).
2. External Ollama on separate EC2 with private network routing.

### 8.2 Bootstrap
- One-command EC2 bootstrap script installs Docker, configures env, deploys stack, pulls models, and validates readiness.

## 9. Quality and Test Requirements
- Unit tests for metric integrity.
- API tests for readiness endpoints.
- Agent response evaluator tests in CI to catch regressions in:
  - numeric grounding
  - weak-confidence phrasing
  - required keyword/actionability checks

## 10. Milestones
1. MVP (current): deployable pilot with core analytics + AI copilot + alerts.
2. V1: hardened enterprise controls, richer invoice and collections workflows.
3. V2: multi-entity governance, advanced compliance/reporting automation.

## 11. Risks and Mitigations
- Risk: LLM quality variance.
  - Mitigation: dual-model strategy, evaluator tests, deterministic tool outputs.
- Risk: Data source inconsistency.
  - Mitigation: reconciliation jobs and source-of-truth policy.
- Risk: Ops complexity in production.
  - Mitigation: bootstrap automation and readiness/health checks.

## 12. Acceptance Criteria
The release is acceptable when:
1. Core endpoints and readiness checks pass in CI.
2. Deployment bootstrap completes on a fresh EC2 host.
3. AI responses pass evaluator quality thresholds for defined benchmark prompts.
4. Pilot users can obtain accurate runway/burn insights and anomaly actions from the product UI or chat.
