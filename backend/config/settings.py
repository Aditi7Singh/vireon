"""
Agent Configuration Settings
===========================
Configuration for the LangGraph AI Agent with Groq/Ollama support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# LLM Configuration
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"  # Default: Groq (faster, no local install needed)
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"

# Groq Configuration (Primary)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_api")
GROQ_MODEL_FAST = "llama-3.3-70b-versatile"           # Routine queries - fast mode
GROQ_MODEL_THINK = "llama-3.3-70b-versatile"    # Complex reasoning - thinking mode

# OpenRouter Configuration (Default)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_api")
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"

# Ollama Configuration (Local/Privacy Fallback)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_FAST = os.getenv("OLLAMA_MODEL_FAST", "llama3.1:8b")
OLLAMA_MODEL_THINK = os.getenv("OLLAMA_MODEL_THINK", "qwen2.5:14b")
# Backward compatibility with older single-model env var
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL_FAST)

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Company Configuration
COMPANY_NAME = os.getenv("COMPANY_NAME", "SeedlingLabs")

# Currency Configuration
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "USD")
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.1,  # Example rates - in production, fetch from API
    "GBP": 1.3,
    "CAD": 0.8,
    "AUD": 0.7,
    "JPY": 0.009,
    "INR": 0.012,
}

# Session Database
SESSION_DB_PATH = os.getenv("SESSION_DB_PATH", str(DATA_DIR / "sessions.db"))

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# PostgreSQL Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Merge.dev Configuration (Production)
MERGE_API_KEY = os.getenv("MERGE_API_KEY", "")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN", "")
DATA_SOURCE = os.getenv("DATA_SOURCE", "erpnext")  # "erpnext" or "merge"

# OpenRouter Configuration (Future production swap)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_api")

# Auth Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "vireon-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Sandbox Configuration
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "false").lower() == "true"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)


def is_sandbox_mode() -> bool:
    """Check if the application is running in sandbox mode."""
    return SANDBOX_MODE


def get_llm(thinking: bool = False):
    """
    Factory function to get the appropriate LLM based on configuration.
    
    Args:
        thinking: If True, use the thinking model for complex queries
        
    Returns:
        LangChain chat model instance
    """
    if USE_LOCAL_LLM:
        from langchain_ollama import ChatOllama
        local_model = OLLAMA_MODEL_THINK if thinking else OLLAMA_MODEL
        return ChatOllama(
            model=local_model,
            temperature=0,
            base_url=OLLAMA_BASE_URL
        )
    elif USE_OPENROUTER:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0
        )
    elif thinking:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL_THINK,
            api_key=GROQ_API_KEY,
            temperature=0
        )
    else:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL_FAST,
            api_key=GROQ_API_KEY,
            temperature=0
        )


def get_fast_llm():
    """Get the fast LLM for simple queries."""
    return get_llm(thinking=False)


def get_thinking_llm():
    """Get the thinking LLM for complex queries."""
    return get_llm(thinking=True)


def convert_currency(amount: float, from_currency: str, to_currency: str = BASE_CURRENCY) -> float:
    """
    Convert amount from one currency to another using fixed exchange rates.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code
        to_currency: Target currency code (defaults to base currency)
        
    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount
    
    # Convert to USD first, then to target
    if from_currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {from_currency}")
    if to_currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {to_currency}")
    
    usd_amount = amount / EXCHANGE_RATES[from_currency]
    return usd_amount * EXCHANGE_RATES[to_currency]
