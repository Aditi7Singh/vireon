"""
Ollama local fallback setup for financial data privacy.

Provides functions to ensure Ollama is running and models are available.
This enables the Agentic CFO to run entirely on-premises for data-sensitive deployments.

SETUP:
    1. Install Ollama: https://ollama.com
    2. Run: python -c "from backend.agent.ollama_setup import ensure_model; ensure_model()"
    3. Set USE_LOCAL_LLM=true in .env
    4. Start backend: uvicorn backend.main:app --reload

Models:
    - qwen3:30b (30GB) — Primary model, best tool calling + reasoning
    - qwen3:8b (5GB) — Lightweight fallback for query classification
"""

import subprocess
import logging
from typing import Optional
import httpx
from datetime import datetime

from backend.config.settings import Settings

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = Settings.OLLAMA_BASE_URL


def check_ollama_running() -> bool:
    """
    Check if Ollama is running and accessible.
    
    Attempts to call the Ollama API at http://localhost:11434/api/tags
    
    Returns:
        True if Ollama is running and responding, False otherwise
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            is_running = response.status_code == 200
            if is_running:
                logger.info("[OLLAMA] Ollama service is running and accessible")
            else:
                logger.warning(f"[OLLAMA] Ollama returned status {response.status_code}")
            return is_running
    except Exception as e:
        logger.warning(f"[OLLAMA] Ollama not running: {e}")
        return False


def check_model_available(model_name: str) -> bool:
    """
    Check if a specific model is available in Ollama.
    
    Calls the Ollama API to list available models and checks if the model exists.
    
    Args:
        model_name: The model to check (e.g., "qwen3:30b", "qwen3:8b")
    
    Returns:
        True if the model is available, False otherwise
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            # Extract list of model names from response
            models_list = data.get("models", [])
            model_names = [m.get("name", "") for m in models_list]
            
            is_available = model_name in model_names
            
            if is_available:
                logger.info(f"[OLLAMA] Model '{model_name}' is available")
            else:
                logger.warning(f"[OLLAMA] Model '{model_name}' not found. Available: {model_names}")
            
            return is_available
    except Exception as e:
        logger.error(f"[OLLAMA] Error checking models: {e}")
        return False


def ensure_model(model_name: str = "qwen3:30b") -> bool:
    """
    Ensure a model is available, pulling it if necessary.
    
    Steps:
    1. Check if Ollama is running — if not, print instructions and return False
    2. Check if model is available — if not, pull it (may take 20+ minutes)
    3. Verify pull was successful
    
    Args:
        model_name: The model to ensure (default: qwen3:30b)
    
    Returns:
        True if model is now available, False if setup failed
    """
    logger.info(f"[OLLAMA] Ensuring model '{model_name}' is available...")
    
    # Step 1: Check if Ollama is running
    if not check_ollama_running():
        logger.error("[OLLAMA] Ollama is not running!")
        print()
        print("=" * 80)
        print("OLLAMA NOT RUNNING - SETUP INSTRUCTIONS")
        print("=" * 80)
        print()
        print("Ollama service is not accessible at " + OLLAMA_BASE_URL)
        print()
        print("1. Download and install Ollama:")
        print("   - macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("   - Windows: Download from https://ollama.com/download")
        print()
        print("2. Start Ollama service:")
        print("   - macOS/Linux: ollama serve")
        print("   - Windows: Start Ollama application (or: ollama serve)")
        print()
        print("3. Verify Ollama is running:")
        print("   - curl http://localhost:11434/api/tags")
        print()
        print("4. Run model setup again:")
        print("   - python -c \"from backend.agent.ollama_setup import ensure_model; ensure_model()\"")
        print()
        print("=" * 80)
        return False
    
    # Step 2: Check if model is already available
    if check_model_available(model_name):
        logger.info(f"[OLLAMA] Model '{model_name}' is already available")
        return True
    
    # Step 3: Pull the model
    logger.info(f"[OLLAMA] Pulling model '{model_name}'... this may take 20+ minutes")
    print()
    print("=" * 80)
    print(f"PULLING MODEL: {model_name}")
    print("=" * 80)
    print()
    print("This will download the model (~20GB for qwen3:30b, ~5GB for qwen3:8b)")
    print("Time estimate: 10-30 minutes depending on internet speed")
    print()
    
    try:
        # Run: ollama pull {model_name}
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=False,  # Show output to user
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"[OLLAMA] Failed to pull model '{model_name}'")
            return False
        
        logger.info(f"[OLLAMA] Model '{model_name}' pulled successfully")
        
        # Step 4: Verify the pull was successful
        if check_model_available(model_name):
            logger.info(f"[OLLAMA] Verified: Model '{model_name}' is available")
            print()
            print("=" * 80)
            print(f"SUCCESS: Model '{model_name}' is ready to use!")
            print("=" * 80)
            print()
            print("Next steps:")
            print("  1. Set USE_LOCAL_LLM=true in your .env file")
            print("  2. Start the backend: uvicorn backend.main:app --reload")
            print("  3. The Agentic CFO will use local Ollama for all LLM calls")
            print()
            return True
        else:
            logger.error(f"[OLLAMA] Model pull succeeded but verification failed")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error(f"[OLLAMA] Model pull timed out (1 hour limit)")
        return False
    except FileNotFoundError:
        logger.error("[OLLAMA] Ollama command not found. Is Ollama installed?")
        print()
        print("Ollama CLI not found in PATH. Please ensure Ollama is installed:")
        print("  - macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("  - Windows: https://ollama.com/download")
        return False
    except Exception as e:
        logger.error(f"[OLLAMA] Unexpected error during model pull: {e}")
        return False


def get_ollama_llm(model: str = "qwen3:30b"):
    """
    Get a ChatOllama LLM instance for local execution.
    
    This is a drop-in replacement for Groq that runs entirely on-premises.
    Use this when USE_LOCAL_LLM=true.
    
    Args:
        model: The Ollama model to use (default: qwen3:30b)
    
    Returns:
        ChatOllama instance configured for financial queries
    
    Example:
        llm = get_ollama_llm()
        response = llm.invoke("What is our runway?")
    """
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        logger.error("[OLLAMA] langchain_community not installed. Run: pip install langchain-community")
        raise ImportError(
            "langchain_community is required for Ollama support. "
            "Install with: pip install langchain-community"
        )
    
    logger.info(f"[OLLAMA] Initializing ChatOllama with model '{model}'")
    
    llm = ChatOllama(
        model=model,
        temperature=0,  # Deterministic for financial data
        base_url=OLLAMA_BASE_URL,
        top_k=40,  # Nucleus sampling
        top_p=0.9,  # Diversity
    )
    
    return llm


def get_ollama_fallback_llm(think_mode: bool = False) -> Optional[object]:
    """
    Get an Ollama LLM for fallback when Groq is unavailable.
    
    Checks if Ollama is running and returns an LLM instance if available.
    Returns None if Ollama is not accessible.
    
    Args:
        think_mode: If True, use larger model for complex reasoning (not used for Ollama)
    
    Returns:
        ChatOllama instance if available, None otherwise
    """
    if not check_ollama_running():
        logger.warning("[OLLAMA] Ollama not available for fallback")
        return None
    
    # Use the default model (qwen3:30b can handle both simple and complex queries)
    try:
        return get_ollama_llm("qwen3:30b")
    except Exception as e:
        logger.error(f"[OLLAMA] Failed to initialize fallback LLM: {e}")
        return None


if __name__ == "__main__":
    """
    CLI entry point for model setup.
    
    Usage:
        python -m backend.agent.ollama_setup
    """
    import sys
    
    print()
    print("=" * 80)
    print("AGENTIC CFO - OLLAMA LOCAL SETUP")
    print("=" * 80)
    print()
    print("This script will:")
    print("  1. Check if Ollama service is running")
    print("  2. Verify the Qwen 3 model is installed")
    print("  3. Pull the model if necessary (may take 20+ minutes)")
    print()
    
    model_name = "qwen3:30b"
    
    success = ensure_model(model_name)
    
    if success:
        print()
        print("✓ Setup complete! Next step:")
        print("  - Add to .env: USE_LOCAL_LLM=true")
        print("  - Or export: export USE_LOCAL_LLM=true")
        print("  - Then run: uvicorn backend.main:app --reload")
        sys.exit(0)
    else:
        print()
        print("✗ Setup failed. Please fix the issue above and try again.")
        sys.exit(1)
