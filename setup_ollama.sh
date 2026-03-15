#!/bin/bash

# Agentic CFO - Ollama Local Setup Script
# Installs Ollama and recommended models for on-premises financial data privacy
# 
# Usage:
#   bash setup_ollama.sh
#   chmod +x setup_ollama.sh && ./setup_ollama.sh

set -e  # Exit on error

echo ""
echo "=================================================================================================="
echo "AGENTIC CFO — OLLAMA LOCAL SETUP (Privacy Mode)"
echo "=================================================================================================="
echo ""
echo "This script will:"
echo "  1. Install Ollama (if not already installed)"
echo "  2. Pull qwen3:30b (primary model — best for tool calling, ~20GB)"
echo "  3. Pull qwen3:8b (lightweight fallback — ~5GB)"
echo "  4. Test the installation"
echo ""
echo "Total time: 30-60 minutes depending on internet speed"
echo "Total disk space: ~25GB"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

echo ""
echo "==================================================================================================>"
echo "STEP 1: Install Ollama"
echo "==================================================================================================>"

if command -v ollama &> /dev/null; then
    echo "✓ Ollama is already installed: $(ollama --version)"
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✓ Ollama installed successfully"
fi

echo ""
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
echo "✓ Ollama PID: $OLLAMA_PID"

# Wait for Ollama to be ready
echo ""
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is ready"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "==================================================================================================>"
echo "STEP 2: Pull qwen3:30b (Primary Model)"
echo "==================================================================================================>"
echo ""
echo "Model: qwen3:30b"
echo "Size: ~20GB"
echo "Best for: Tool calling, complex reasoning, financial analysis"
echo "Time: 10-30 minutes"
echo ""
ollama pull qwen3:30b
echo "✓ qwen3:30b pulled successfully"

echo ""
echo "==================================================================================================>"
echo "STEP 3: Pull qwen3:8b (Lightweight Fallback)"
echo "==================================================================================================>"
echo ""
echo "Model: qwen3:8b"
echo "Size: ~5GB"
echo "Best for: Query classification, fast responses when full model unavailable"
echo "Time: 5-15 minutes"
echo ""
ollama pull qwen3:8b
echo "✓ qwen3:8b pulled successfully"

echo ""
echo "==================================================================================================>"
echo "STEP 4: Test Installation"
echo "==================================================================================================>"
echo ""
echo "Testing qwen3:8b with a simple prompt..."
ollama run qwen3:8b "Reply with only: Agentic CFO ready"
echo ""
echo "✓ Model test successful"

echo ""
echo "==================================================================================================>"
echo "SETUP COMPLETE!"
echo "==================================================================================================>"
echo ""
echo "Next steps:"
echo ""
echo "1. Set environment variables:"
echo "   export USE_LOCAL_LLM=true"
echo "   export OLLAMA_BASE_URL=http://localhost:11434"
echo ""
echo "2. Or add to .env:"
echo "   USE_LOCAL_LLM=true"
echo "   OLLAMA_BASE_URL=http://localhost:11434"
echo ""
echo "3. Start the Agentic CFO backend:"
echo "   uvicorn backend.main:app --reload"
echo ""
echo "4. Verify: http://localhost:8000/docs"
echo ""
echo "Models installed:"
echo "  - qwen3:30b (primary, 20GB)"
echo "  - qwen3:8b (fallback, 5GB)"
echo ""
echo "Data privacy: All LLM processing runs on-premises. No data sent to external APIs."
echo ""
echo "✓ Ollama setup complete"
echo ""

# Optional: Keep Ollama running in background
echo "Keeping Ollama running in background (PID: $OLLAMA_PID)"
wait $OLLAMA_PID
