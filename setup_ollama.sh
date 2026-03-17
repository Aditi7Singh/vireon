#!/bin/bash
# Ollama Setup Script
# ==================
# Sets up Ollama for Agentic CFO Privacy Mode
# Run: chmod +x setup_ollama.sh && ./setup_ollama.sh

echo "Setting up Ollama for Agentic CFO (Privacy Mode)"
echo "================================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi

# Pull recommended models
echo ""
echo "Pulling recommended models..."

echo "Pulling qwen3:30b (primary — best tool calling, ~20GB)"
ollama pull qwen3:30b

echo ""
echo "Pulling qwen3:8b (lightweight fallback — ~5GB)"
ollama pull qwen3:8b

# Test Ollama
echo ""
echo "Testing Ollama..."
RESPONSE=$(ollama run qwen3:8b "Reply with only: Agentic CFO ready" 2>/dev/null)

if [[ "$RESPONSE" == *"ready"* ]] || [[ "$RESPONSE" == *"Ready"* ]]; then
    echo "✅ Ollama setup complete!"
    echo ""
    echo "To use local LLM:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Set USE_LOCAL_LLM=true"
    echo "  3. Restart the backend"
else
    echo "⚠️ Ollama installed but test response unclear"
    echo "  Verify with: ollama list"
fi

echo ""
echo "Done! Set USE_LOCAL_LLM=true in .env to use."
