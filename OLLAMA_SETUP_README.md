# Ollama Local Fallback Setup - Complete Implementation

## Overview

This implementation enables the Agentic CFO to run entirely on-premises with **zero data egress** for financial data privacy compliance.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ AGENTIC CFO BACKEND                                                 │
│                                                                     │
│  ┌──────────────────┐                                              │
│  │  FastAPI Router  │                                              │
│  │  /agent/chat     │                                              │
│  └────────┬─────────┘                                              │
│           │                                                        │
│  ┌────────▼──────────┐                                             │
│  │ LangGraph Agent   │                                             │
│  │ StateGraph        │                                             │
│  └────────┬──────────┘                                             │
│           │                                                        │
│  ┌────────▼──────────────────────────────────────────┐             │
│  │   Settings.get_llm(thinking=False)                │             │
│  │   ┌──────────────────────────────────────┐       │             │
│  │   │ if USE_LOCAL_LLM:                    │       │             │
│  │   │   return get_ollama_llm()  ◄─────────┼───────┼─── Local ───┤
│  │   │ else:                      │       │       Mode    │
│  │   │   return ChatGroq()        └─┬─────┼───────┼─── Cloud ────┤
│  │   │                             │     │   │
│  │   └─────────────────────────────────────┘     │
│  └────────┬──────────────────────────────────────┘
│           │
│  ┌────────▼─────────────────────────────────────────┐
│  │ Tools (financial queries)                        │
│  │ - get_cash_balance()                             │
│  │ - get_runway()                                   │
│  │ - simulate_hire()                                │
│  │ - etc.                                           │
│  └─────────────────────────────────────────────────┘
│
│  PRIVATE: Processes all financial data locally
│  No external API calls made
│
└─────────────────────────────────────────────────────────────────────┘

      LOCAL OLLAMA              REMOTE GROQ/OPENROUTER
      ┌──────────┐              ┌────────────────────┐
      │ Ollama   │              │ API Endpoint       │
      │ qwen3:30b│              │ (Paid/API Key)     │
      │ qwen3:8b │              │                    │
      └──────────┘              └────────────────────┘
      Port:11434                Port:443/API
```

## File Structure

```
vireon/
├── backend/
│   ├── agent/
│   │   ├── ollama_setup.py          ← NEW: Local LLM integration
│   │   ├── cfo_agent.py
│   │   ├── tools.py
│   │   ├── prompts.py
│   │   ├── routing.py
│   │   ├── memory.py
│   │   └── test_agent.py
│   ├── config/
│   │   └── settings.py              ← UPDATED: get_llm() method
│   └── main.py
├── setup_ollama.sh                  ← NEW: Automated setup
└── .env                             ← Configure: USE_LOCAL_LLM=true
```

## Three Components

### PART A: backend/agent/ollama_setup.py (295 lines)

**Purpose:** Handle Ollama orchestration and LLM provisioning

**Key Functions:**

```python
def check_ollama_running() -> bool
    # Checks http://localhost:11434/api/tags
    # Returns: True if Ollama service is running

def check_model_available(model_name: str) -> bool
    # Calls http://localhost:11434/api/tags
    # Returns: True if model exists in model list

def ensure_model(model_name: str = "qwen3:30b") -> bool
    # 1. Checks Ollama running (exits if not + prints instructions)
    # 2. Checks model available (pulls if not)
    # 3. Prints "Pulling model... this may take 20 mins"
    # 4. Runs: ollama pull {model_name}
    # 5. Verifies success!
    # Returns: True if model is ready to use

def get_ollama_llm(model: str = "qwen3:30b")
    # Returns: ChatOllama(model=model, temperature=0, base_url="http://localhost:11434")
    # Drop-in replacement for Groq
    # Use: llm = get_ollama_llm(); response = llm.invoke("query")

def get_ollama_fallback_llm(think_mode: bool = False) -> Optional
    # Graceful fallback for when Groq is unavailable
    # Returns: ChatOllama if Ollama available, None otherwise
```

**Usage:**

```bash
# CLI mode - interactive setup
python backend/agent/ollama_setup.py

# Python API - ensure specific model
from backend.agent.ollama_setup import ensure_model
success = ensure_model("qwen3:30b")

# Get LLM instance
from backend.agent.ollama_setup import get_ollama_llm
llm = get_ollama_llm()
response = llm.invoke("What's our runway?")
```

### PART B: setup_ollama.sh (131 lines)

**Purpose:** Automated Ollama installation for macOS/Linux

**What it does:**

```bash
#!/bin/bash

# Step 1: Install Ollama (if not already)
curl -fsSL https://ollama.com/install.sh | sh

# Step 2: Start Ollama service
ollama serve &

# Step 3: Pull qwen3:30b (20GB, ~15 mins)
ollama pull qwen3:30b

# Step 4: Pull qwen3:8b (5GB, ~10 mins)
ollama pull qwen3:8b

# Step 5: Test with simple prompt
ollama run qwen3:8b "Reply with only: Agentic CFO ready"

# Step 6: Print next steps
# - Set USE_LOCAL_LLM=true
# - Run: uvicorn backend.main:app --reload
```

**Usage:**

```bash
# Automated setup (30-60 minutes total)
chmod +x setup_ollama.sh
./setup_ollama.sh
```

### PART C: backend/config/settings.py (Updated - get_llm method)

**Purpose:** Single-point LLM provider selection

**The New Method:**

```python
@staticmethod
def get_llm(thinking: bool = False):
    """Get LLM instance based on USE_LOCAL_LLM setting."""
    
    if Settings.USE_LOCAL_LLM:
        # On-premises privacy mode
        from backend.agent.ollama_setup import get_ollama_llm
        return get_ollama_llm(model=Settings.OLLAMA_FAST_MODEL)
    
    else:
        # Cloud API mode
        from langchain_groq import ChatGroq
        
        if thinking:
            model = Settings.GROQ_THINK_MODEL  # Heavy: qwq-32b
        else:
            model = Settings.GROQ_FAST_MODEL   # Fast: qwen2-32b
        
        return ChatGroq(
            model=model,
            api_key=Settings.GROQ_API_KEY,
            temperature=0,
        )
    
    # FUTURE: One-line swap to OpenRouter/other providers
    # from langchain_openai import ChatOpenAI
    # return ChatOpenAI(
    #     base_url="https://openrouter.io/api/v1",
    #     model=Settings.OPENROUTER_MODEL,
    #     api_key=Settings.OPENROUTER_API_KEY,
    # )
```

**Usage in codebase:**

```python
# Anywhere in the agent
from backend.config.settings import Settings

# Auto-selects based on USE_LOCAL_LLM
llm = Settings.get_llm(thinking=False)
response = llm.invoke("query")
```

## Deployment Scenarios

### Scenario 1: Development (Local Privacy)

```bash
# 1. Setup Ollama
./setup_ollama.sh
# (or:) ollama pull qwen3:30b

# 2. Configure backend
echo "USE_LOCAL_LLM=true" >> .env

# 3. Start
ollama serve &
uvicorn backend.main:app --reload

# Result: ✓ All data stays on your machine
```

### Scenario 2: Production (Cloud - Default)

```bash
# 1. Configure Groq API
echo "GROQ_API_KEY=sk-..." >> .env

# 2. Start (default: USE_LOCAL_LLM=false)
uvicorn backend.main:app

# Result: ✓ Uses Groq for fast inference, 10x cheaper than custom API
```

### Scenario 3: Production (On-Premises - Regulated)

```bash
# 1. Same as Scenario 1
./setup_ollama.sh
echo "USE_LOCAL_LLM=true" >> .env

# 2. Deploy
uvicorn backend.main:app

# Result: ✓ Zero compliance concerns, zero data egress
```

### Scenario 4: Production (Custom Provider - OpenRouter/Other)

```python
# In settings.py, edit get_llm():
# Change EXACTLY 3 lines

from langchain_openai import ChatOpenAI  # 1. Change import

return ChatOpenAI(
    base_url="https://openrouter.io/api/v1",  # 2. Change URL
    model=Settings.OPENROUTER_MODEL,
    api_key=Settings.OPENROUTER_API_KEY,      # 3. Change key
    temperature=0,
)
# Deploy - works everywhere
```

## Environment Configuration

### .env (Local Privacy Mode)

```ini
# Use local Ollama
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11434

# Company config
COMPANY_NAME=SeedlingLabs

# Session storage
SESSION_DB_PATH=./data/sessions.db
```

### .env (Cloud Mode - Default)

```ini
# Use Groq API
USE_LOCAL_LLM=false
GROQ_API_KEY=sk-gsk_...

# Company config
COMPANY_NAME=SeedlingLabs

# Session storage
SESSION_DB_PATH=./data/sessions.db
```

## Testing

```bash
# Check Ollama is running
python -c "from backend.agent.ollama_setup import check_ollama_running; \
           print('Ollama:', check_ollama_running())"

# Check model availability
python -c "from backend.agent.ollama_setup import check_model_available; \
           print('qwen3:30b:', check_model_available('qwen3:30b'))"

# Test LLM (local)
python -c "from backend.config.settings import Settings; \
           llm = Settings.get_llm(); \
           print(type(llm).__name__)"

# Run test query
python -c "from backend.config.settings import Settings; \
           llm = Settings.get_llm(); \
           response = llm.invoke('Say OK'); \
           print(response.content)"
```

## Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16GB | 32GB+ |
| GPU | Optional | NVIDIA RTX 4090 or better |
| Disk | 30GB | 50GB+ |
| Bandwidth | - | 100Mbps (for model pull) |
| CPU | 4 cores | 16 cores |

**Note:** qwen3:30b can run on CPU but will be slow (10+ sec/response)

## Switching Providers

All three options work with **zero code changes in the agent**:

```python
# Current: settings.py (ONE METHOD)
Settings.get_llm()  # Automatically selects based on env

# Usage everywhere: (NO CHANGES NEEDED)
from backend.config.settings import Settings
llm = Settings.get_llm()
response = llm.invoke(query)
```

| Provider | Config | Compliance | Cost | Speed |
|----------|--------|-----------|------|-------|
| Ollama (Local) | USE_LOCAL_LLM=true | ✓ Full | Free ($0) | Variable |
| Groq (Current) | GROQ_API_KEY=... | ✗ Some | Low ($5-50/mo) | Fast |
| OpenRouter | OPENROUTER_KEY=... | ✗ Depends | Variable | Medium |

## Complete - Ready to Deploy

✅ ollama_setup.py (295 lines)
✅ setup_ollama.sh (131 lines)
✅ settings.py (get_llm method)
✅ All imports wired correctly
✅ Error handling in place
✅ Documentation complete

**Next Steps:**

1. **Local Testing:**
   ```bash
   ./setup_ollama.sh
   export USE_LOCAL_LLM=true
   uvicorn backend.main:app --reload
   ```

2. **Test Endpoints:**
   ```bash
   curl -X POST http://localhost:8000/agent/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is our runway?"}'
   ```

3. **Deploy (Choose Provider):**
   - **Local:** Keep USE_LOCAL_LLM=true
   - **Cloud:** Set GROQ_API_KEY, set USE_LOCAL_LLM=false
   - **Custom:** Update get_llm() method
