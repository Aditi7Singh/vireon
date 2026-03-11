# Agentic CFO — AI Financial Copilot for ERP Systems

## Overview

**Agentic CFO** is an AI-powered financial intelligence system designed to work alongside enterprise ERP platforms. The system acts as a fractional AI CFO, capable of analyzing financial data, detecting anomalies, forecasting cash runway, and answering complex financial questions in natural language.

Instead of building a simulated financial database from scratch, this system integrates directly with **ERPNext**, an open-source enterprise resource planning system used by real companies for accounting, financial management, and operations.

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

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js, Tailwind CSS, Tremor |
| **AI Agent** | OpenAI GPT-4o / LangGraph |
| **Backend** | Python, FastAPI |
| **Math Engine** | Python (Deterministic Logic) |
| **ERP System** | ERPNext |
| **Database** | MariaDB (ERPNext default) |

## Key Features

-   **Autonomous Financial Alerts**: Monitors ERPNext for spending spikes, customer churn, or runway thresholds.
-   **Natural Language Financial Queries**: Ask "Why did expenses increase last month?" and get drivers identified from GL entries.
-   **Scenario Simulation**: "What if we hire 3 engineers?" — simulate payroll increases and calculate impact on runway.
-   **Financial Forecasting**: Deterministic models for ARR, MRR, Gross Margin, and operating cash flow.

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

## Project Structure

```text
agentic-cfo/
├── frontend/               # Next.js + Tailwind + Tremor
├── backend/                # FastAPI + Math Engine
│   ├── analytics/          # Core Math Engine logic
│   ├── agent/              # LLM Tool orchestration
│   └── erpnext_client/     # ERPNext REST API client
├── erpnext_integration/    # Data import scripts
└── data_generator/         # Financial simulator for populating ERPNext
```

## Future Vision

The long-term goal is to build an AI financial copilot capable of understanding and analyzing enterprise financial systems in real time, enabling founders and operators to make better financial decisions faster. This represents a step toward **autonomous financial intelligence** for modern companies.
