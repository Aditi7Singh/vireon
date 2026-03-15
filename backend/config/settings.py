"""Environment configuration and settings for Agentic CFO."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized settings from environment variables."""
    
    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Backend Configuration
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Company Configuration
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "SeedlingLabs")
    
    # Session Configuration
    SESSION_DB_PATH: str = os.getenv("SESSION_DB_PATH", "./data/sessions.db")
    
    # Model Names (for LLM-agnostic switching)
    # Groq models
    GROQ_FAST_MODEL: str = "qwen2-32b"  # Routine queries
    GROQ_THINK_MODEL: str = "qwq-32b"   # Complex reasoning
    
    # Ollama models (local)
    OLLAMA_FAST_MODEL: str = "qwen3:30b"  # Local privacy mode
    
    # OpenRouter models (for production swap)
    OPENROUTER_MODEL: str = "deepseek/deepseek-v3"
    
    @staticmethod
    def get_llm_config() -> dict:
        """Get LLM configuration based on settings."""
        if Settings.USE_LOCAL_LLM:
            return {
                "provider": "ollama",
                "model": Settings.OLLAMA_FAST_MODEL,
                "base_url": Settings.OLLAMA_BASE_URL,
            }
        else:
            return {
                "provider": "groq",
                "fast_model": Settings.GROQ_FAST_MODEL,
                "think_model": Settings.GROQ_THINK_MODEL,
                "api_key": Settings.GROQ_API_KEY,
            }
    
    @staticmethod
    def validate():
        """Validate critical settings are configured."""
        if not Settings.USE_LOCAL_LLM and not Settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY must be set or USE_LOCAL_LLM=true")
        if Settings.USE_LOCAL_LLM:
            # Note: could add OLLAMA connectivity check here
            pass
    
    @staticmethod
    def get_llm(thinking: bool = False):
        """
        Get LLM instance based on configuration.
        
        This is the single point of LLM selection for the entire system.
        Swap providers by changing two lines (import + return).
        
        Args:
            thinking: If True, use heavy-weight model for complex reasoning (Groq only)
        
        Returns:
            LLM instance (ChatOllama for local, ChatGroq for cloud, etc.)
        
        PRINCIPLE: LLM-agnostic architecture. Change one method, swap everywhere.
        """
        if Settings.USE_LOCAL_LLM:
            # Local on-premises execution for data privacy
            from backend.agent.ollama_setup import get_ollama_llm
            return get_ollama_llm(model=Settings.OLLAMA_FAST_MODEL)
        
        else:
            # Cloud execution via Groq API
            from langchain_groq import ChatGroq
            
            if thinking:
                # Heavy-weight model for complex reasoning
                model = Settings.GROQ_THINK_MODEL
            else:
                # Fast model for routine queries
                model = Settings.GROQ_FAST_MODEL
            
            return ChatGroq(
                model=model,
                api_key=Settings.GROQ_API_KEY,
                temperature=0,  # Deterministic for financial data
            )
        
        # FUTURE: One-line production swap to OpenRouter
        # from langchain_openai import ChatOpenAI
        # return ChatOpenAI(
        #     base_url="https://openrouter.ai/api/v1",
        #     model=Settings.OPENROUTER_MODEL,
        #     api_key=Settings.OPENROUTER_API_KEY,
        #     temperature=0,
        # )
