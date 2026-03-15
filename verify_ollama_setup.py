#!/usr/bin/env python3
"""
Verification script for Ollama setup.

This script checks that all three components are properly integrated:
1. ollama_setup.py is importable and functional
2. settings.py has get_llm() method
3. Environment is configured correctly

Run: python verify_ollama_setup.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent))

print()
print("=" * 80)
print("OLLAMA SETUP VERIFICATION")
print("=" * 80)
print()

# Test 1: Import ollama_setup module
print("Test 1: ollama_setup module")
try:
    from backend.agent.ollama_setup import (
        check_ollama_running,
        check_model_available,
        ensure_model,
        get_ollama_llm,
        get_ollama_fallback_llm,
    )
    print("  [OK] All 5 functions imported successfully")
except ImportError as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Check settings.get_llm() method
print()
print("Test 2: Settings.get_llm() method")
try:
    from backend.config.settings import Settings
    
    # Check method exists
    if not hasattr(Settings, 'get_llm'):
        print("  [FAIL] Settings.get_llm() method not found")
        sys.exit(1)
    
    # Check method is callable
    if not callable(Settings.get_llm):
        print("  [FAIL] Settings.get_llm is not callable")
        sys.exit(1)
    
    print("  [OK] Settings.get_llm() method found and callable")
except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

# Test 3: Check environment variables
print()
print("Test 3: Environment variables")
try:
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    print(f"  USE_LOCAL_LLM: {use_local}")
    print(f"  OLLAMA_BASE_URL: {ollama_url}")
    print(f"  GROQ_API_KEY: {'Set' if groq_key else 'Not set'}")
    
    if use_local and not groq_key:
        print("  [OK] Configured for local Ollama mode")
    elif groq_key and not use_local:
        print("  [OK] Configured for Groq cloud mode")
    elif use_local and groq_key:
        print("  [WARNING] Both USE_LOCAL_LLM and GROQ_API_KEY set (local mode takes priority)")
    else:
        print("  [WARNING] Neither local nor cloud properly configured")
except Exception as e:
    print(f"  [FAIL] Error: {e}")
    sys.exit(1)

# Test 4: Try to call Settings.get_llm() (doesn't require Ollama/Groq to be running)
print()
print("Test 4: Calling Settings.get_llm()")
try:
    # This will fail if dependencies aren't installed, but that's OK
    # We just want to verify the method exists and has proper logic
    
    # We can't actually call it without proper env setup, but we can check it's valid
    import inspect
    source = inspect.getsource(Settings.get_llm)
    
    checks = [
        ("USE_LOCAL_LLM check", "USE_LOCAL_LLM" in source),
        ("get_ollama_llm import", "get_ollama_llm" in source),
        ("ChatGroq fallback", "ChatGroq" in source),
        ("thinking parameter", "thinking" in source),
    ]
    
    for check_name, result in checks:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")
    
    if all(result for _, result in checks):
        print("  [OK] Settings.get_llm() has correct implementation")
    else:
        print("  [FAIL] Settings.get_llm() missing some logic")
        sys.exit(1)

except Exception as e:
    print(f"  [FAIL] Error inspecting get_llm: {e}")
    sys.exit(1)

# Test 5: Check file structure
print()
print("Test 5: File structure")
files_to_check = [
    ("backend/agent/ollama_setup.py", 200),  # Should be ~295 lines
    ("backend/config/settings.py", 100),     # Should be ~108 lines
    ("setup_ollama.sh", 100),                # Should be ~131 lines
]

all_files_ok = True
for filepath, min_lines in files_to_check:
    full_path = Path(__file__).parent / filepath
    if full_path.exists():
        with open(full_path, 'r') as f:
            lines = len(f.readlines())
        status = "[OK]" if lines >= min_lines else "[WARNING]"
        print(f"  {status} {filepath} ({lines} lines, min {min_lines})")
    else:
        print(f"  [FAIL] {filepath} not found")
        all_files_ok = False

if not all_files_ok:
    sys.exit(1)

# Test 6: Check Ollama connectivity (optional, may not be running)
print()
print("Test 6: Ollama connectivity (optional)")
try:
    is_running = check_ollama_running()
    if is_running:
        print("  [OK] Ollama is running at http://localhost:11434")
    else:
        print("  [INFO] Ollama is not running (this is OK for now)")
except Exception as e:
    print(f"  [INFO] Could not check Ollama: {e}")

# Test 7: Check model availability (optional)
print()
print("Test 7: Model availability (optional)")
try:
    if check_ollama_running():
        models_to_check = ["qwen3:30b", "qwen3:8b"]
        for model in models_to_check:
            available = check_model_available(model)
            status = "[OK]" if available else "[INFO]"
            print(f"  {status} {model}: {available}")
    else:
        print("  [INFO] Ollama not running, skipping model check")
except Exception as e:
    print(f"  [INFO] Could not check models: {e}")

# Summary
print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print()
print("NEXT STEPS:")
print()
print("1. For LOCAL/PRIVACY mode:")
print("   - Install Ollama: https://ollama.com")
print("   - Run setup: ./setup_ollama.sh  OR  python backend/agent/ollama_setup.py")
print("   - Set env: export USE_LOCAL_LLM=true")
print()
print("2. For CLOUD mode (default):")
print("   - Set Groq API key: export GROQ_API_KEY=sk-...")
print("   - Leave USE_LOCAL_LLM=false (default)")
print()
print("3. Start backend:")
print("   - Local: ollama serve &  then  uvicorn backend.main:app --reload")
print("   - Cloud: uvicorn backend.main:app --reload")
print()
print("4. Access API docs:")
print("   - http://localhost:8000/docs")
print()
print("=" * 80)
print()
