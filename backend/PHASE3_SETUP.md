# Phase 3: LangGraph AI Agent - Quick Start Guide

## Project Structure Completed

```
backend/
├── agent/
│   ├── __init__.py              ✓ Module initialization
│   ├── cfo_agent.py             ✓ Main LangGraph graph + state management
│   ├── tools.py                 ✓ 10 @tool definitions (FastAPI wrappers)
│   ├── prompts.py               ✓ System prompt + CFO persona + routing
│   ├── routing.py               ✓ Query classifier (complex/simple/alert)
│   └── memory.py                ✓ MemorySaver checkpointer setup
├── config/
│   ├── __init__.py              ✓ Module initialization
│   ├── settings.py              ✓ Environment variables + LLM config
│   └── company_profile.py       ✓ SeedlingLabs context injected into prompts
├── requirements_agent.txt       ✓ All dependencies pinned
└── agent_runner.py              ✓ (existing; can integrate with new agent)
```

## Installation Status

✓ **All dependencies installed:**
- langgraph==0.2.55
- langgraph-checkpoint-sqlite  
- langchain-core==0.3.25
- langchain-groq==0.2.3
- langchain-ollama==0.2.1
- langchain-openai==0.2.14
- httpx==0.27.0
- python-dotenv==1.0.1

✓ **All imports verified and working**

## Environment Setup

### 1. Create `.env` from template
```bash
cp .env.example .env
```

### 2. Configure Environment Variables
```env
# Use provided Groq API key
GROQ_API_KEY=your_groq_api_key_here

# FastAPI backend must be running on this URL
BACKEND_URL=http://localhost:8000

# Set to false for Groq (fast), true for Ollama (private)
USE_LOCAL_LLM=false

# Ollama only if USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11434

# Leave as-is unless you need DeepSeek on OpenRouter
# OPENROUTER_API_KEY=sk-or-v1-...
```

## LLM Architecture (LLM-Agnostic Design)

The agent routes to the correct LLM provider via ONE environment variable:

### Primary: Groq API (Qwen 2/3, QwQ)
**When:** `USE_LOCAL_LLM=false` (default)
- Fast queries → qwen2-32b
- Complex reasoning → qwq-32b (thinking mode)
- Cost: FREE (Groq free tier)
- Speed: ~200ms typical

### Privacy: Ollama Local (qwen3:30b)
**When:** `USE_LOCAL_LLM=true`
- Qwen 3-30B running locally
- Cost: FREE (local compute)
- Use for: Sensitive data, compliance

### Production: OpenRouter (DeepSeek-V3)
**When:** Swap provider in `settings.py`
- Change: `OPENROUTER_MODEL` in settings.py
- Add: `OPENROUTER_API_KEY` to `.env`
- One-line provider swap

## 10 Financial Tools Available

All tools wrap FastAPI backend endpoints:

1. `get_cash_balance()` → {cash, ar, ap, net_cash}
2. `get_burn_rate()` → {monthly_burn, breakdown, trend}
3. `get_runway()` → {runway_months, zero_date, confidence}
4. `simulate_hire()` → {new_runway, delta}
5. `simulate_revenue_change()` → {new_runway, delta}
6. `simulate_expense_change()` → {new_runway, savings}
7. `get_alerts()` → {alerts: [{severity, category, amount}]}
8. `get_expenses()` → {breakdown, trend, movers}
9. `get_revenue()` → {mrr, arr, growth, churn, nrr}
10. `get_financial_scorecard()` → All KPIs in one payload

## Query Routing (Auto-Classification)

User query → Router → Category:
- **SIMPLE_METRICS**: "What's our cash?" → single tool
- **ANALYSIS**: "Is burn accelerating?" → multi-tool analysis
- **SCENARIO**: "What if we hired 5 engineers?" → simulate + compare
- **ALERTS**: "Show red flags" → fetch + contextualize
- **CONVERSATION**: "Tell me more" → use memory + context

## Example Usage

```python
from langchain_groq import ChatGroq
from backend.agent.cfo_agent import get_cfo_agent

# Initialize LLM (Groq in this case)
llm = ChatGroq(
    model="qwen2-32b",
    temperature=0,
    api_key="your_api_key_here"
)

# Get agent
graph, invoke = get_cfo_agent(llm)

# Ask a question
response = invoke(
    graph=graph,
    query="What's our current runway?",
    user_id="cfo@seedlinglabs.com",
    session_id="session-2025-03-15"
)

print(response)
```

## Conversation Memory

- **In-memory:** MemorySaver (current)
- **Persistent:** Upgrade to SqliteSaver with langgraph-checkpoint-sqlite
- Sessions keyed by: `{user_id}:{session_id}`
- State persists across tool calls within session

## Next Steps (Phase 3.1)

1. **Test the agent** with FastAPI backend running
2. **Create REST endpoint** `/ask` for chat queries
3. **Integrate conversation memory** into database
4. **Add authentication** (user_id validation)
5. **Swap to production LLMs** (OpenRouter when needed)

## Configuration Validation

To verify settings are correct:
```python
from backend.config.settings import Settings
Settings.validate()
```

## Important Notes

- **Agent is LLM-agnostic:** Easy provider swap via env vars
- **Never self-calculates:** Always calls FastAPI tools
- **CFO persona maintained:** Professional, data-driven responses
- **Anomaly detection:** Automatically flags threshold breaches
- **Fallback ready:** Groq → Ollama → OpenRouter routing

---

**Status:** Phase 3 environment ready ✓
**Date:** March 15, 2026
**Python:** 3.11.6
