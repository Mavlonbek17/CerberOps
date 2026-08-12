#!/usr/bin/env bash
# CerberOps — One-click setup script
# Usage: ./scripts/setup.sh

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }

echo -e "${BOLD}"
echo "  ______          __             ____            "
echo " / ____/__  _____/ /_  ___  ____/ __ \\____  ___ "
echo "/ /   / _ \\/ ___/ __ \\/ _ \\/ __/ / / / __ \\/ __|"
echo "/ /___/  __/ /  / /_/ /  __/ / / /_/ / /_/ /\\__ \\"
echo "\\____/\\___/_/  /_.___/\\___/_/  \\____/ .___/|___/"
echo "                                   /_/          "
echo -e "${NC}"
echo "DevSecOps Vulnerability Orchestrator — Setup"
echo "============================================="
echo ""

# ── Check Docker ──────────────────────────────────────────
info "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | head -1)
    ok "Docker found: $DOCKER_VERSION"
else
    fail "Docker is not installed."
    echo "  Install: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker compose &> /dev/null; then
    ok "Docker Compose found"
else
    fail "Docker Compose not found (required for orchestration)"
    exit 1
fi

# ── Check Ollama ──────────────────────────────────────────
info "Checking Ollama..."
if command -v ollama &> /dev/null; then
    ok "Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
else
    warn "Ollama not installed. AI reports will use fallback templates."
    echo ""
    read -p "  Install Ollama now? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Installing Ollama..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ollama 2>/dev/null || {
                info "Downloading Ollama installer..."
                curl -fsSL https://ollama.com/install.sh | sh
            }
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
        ok "Ollama installed"
    fi
fi

# ── Pull AI Model ─────────────────────────────────────────
if command -v ollama &> /dev/null; then
    info "Checking AI models..."

    # Start ollama if not running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        info "Starting Ollama service..."
        ollama serve &> /dev/null &
        sleep 3
    fi

    DEFAULT_MODEL="qwen2.5-coder:1.5b"
    echo ""
    echo "  Available model options:"
    echo "    1) qwen2.5-coder:1.5b  (~1GB RAM, fast, good for most systems)"
    echo "    2) llama3.2:1b          (~1GB RAM, general purpose)"
    echo "    3) llama3.1:8b          (~5GB RAM, best quality)"
    echo "    4) Skip (use fallback templates)"
    echo ""
    read -p "  Select model [1]: " MODEL_CHOICE

    case "${MODEL_CHOICE:-1}" in
        1) MODEL="qwen2.5-coder:1.5b" ;;
        2) MODEL="llama3.2:1b" ;;
        3) MODEL="llama3.1:8b" ;;
        4) MODEL="" ;;
        *) MODEL="$DEFAULT_MODEL" ;;
    esac

    if [[ -n "$MODEL" ]]; then
        info "Pulling model: $MODEL (this may take a few minutes)..."
        ollama pull "$MODEL"
        ok "Model $MODEL ready"
    fi
fi

# ── Create .env ───────────────────────────────────────────
if [[ ! -f .env ]]; then
    info "Creating .env from template..."
    cp .env.example .env

    # Set the model if we chose one
    if [[ -n "${MODEL:-}" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|OLLAMA_MODEL=.*|OLLAMA_MODEL=$MODEL|" .env
        else
            sed -i "s|OLLAMA_MODEL=.*|OLLAMA_MODEL=$MODEL|" .env
        fi
    fi

    ok ".env created"
else
    ok ".env already exists"
fi

# ── Build & Start ─────────────────────────────────────────
echo ""
info "Building and starting CerberOps..."
docker compose build --quiet
docker compose up -d

echo ""
echo -e "${GREEN}${BOLD}CerberOps is ready!${NC}"
echo ""
echo "  Dashboard:  http://localhost:3000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  API:        http://localhost:8000/api/v1/health"
echo ""
echo "  Run your first scan:"
echo "    curl -X POST http://localhost:8000/api/v1/scan \\"
echo '      -H "Content-Type: application/json" \\'
echo '      -d '"'"'{"target": "https://example.com", "scanners": ["nmap", "nuclei"]}'"'"''
echo ""
echo "  Stop:  docker compose down"
echo "  Logs:  docker compose logs -f"
echo ""
