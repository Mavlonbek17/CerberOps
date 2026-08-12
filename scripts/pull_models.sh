#!/usr/bin/env bash
# Pull recommended AI models for CerberOps
# Usage: ./scripts/pull_models.sh [model_name]

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Install from https://ollama.com"
    exit 1
fi

# Start ollama if not running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve &> /dev/null &
    sleep 3
fi

if [[ $# -gt 0 ]]; then
    echo -e "${BLUE}Pulling: $1${NC}"
    ollama pull "$1"
    echo -e "${GREEN}Done!${NC}"
    exit 0
fi

echo "CerberOps — AI Model Setup"
echo "=========================="
echo ""
echo "Pulling recommended models..."
echo ""

MODELS=(
    "qwen2.5-coder:1.5b"
)

for model in "${MODELS[@]}"; do
    echo -e "${BLUE}Pulling: $model${NC}"
    ollama pull "$model"
    echo -e "${GREEN}Done: $model${NC}"
    echo ""
done

echo ""
echo -e "${GREEN}All models ready!${NC}"
echo ""
echo "Optional larger models (better quality, more RAM):"
echo "  ollama pull llama3.2:1b"
echo "  ollama pull llama3.1:8b"
echo "  ollama pull qwen2.5-coder:7b"
