#!/usr/bin/env bash
# =============================================================================
# CerberOps — Universal One-Command Installer
# Supports: macOS (Intel + Apple Silicon), Linux (Debian/Ubuntu/Fedora/Arch),
#           Windows WSL2 (Ubuntu)
#
# Usage:
#   git clone https://github.com/your-org/cerberops && cd cerberops
#   chmod +x install.sh && ./install.sh
# =============================================================================

set -euo pipefail

# ── Colors & helpers ──────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m'

info()    { echo -e "${CYAN}  ▶${NC}  $*"; }
ok()      { echo -e "${GREEN}  ✔${NC}  $*"; }
warn()    { echo -e "${YELLOW}  ⚠${NC}  $*"; }
fail()    { echo -e "${RED}  ✖${NC}  $*"; }
section() { echo -e "\n${BOLD}${MAGENTA}══ $* ══${NC}"; }
ask()     { echo -e "${YELLOW}  ?${NC}  $*"; }

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${CYAN}"
cat << 'EOF'
   ██████╗███████╗██████╗ ██████╗ ███████╗██████╗  ██████╗ ██████╗ ███████╗
  ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗██╔════╝
  ██║     █████╗  ██████╔╝██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝███████╗
  ██║     ██╔══╝  ██╔══██╗██╔══██╗██╔══╝  ██╔══██╗██║   ██║██╔═══╝ ╚════██║
  ╚██████╗███████╗██║  ██║██████╔╝███████╗██║  ██║╚██████╔╝██║     ███████║
   ╚═════╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚══════╝
EOF
echo -e "${NC}"
echo -e "  ${BOLD}DevSecOps Vulnerability Orchestrator${NC}  ${DIM}— Universal Installer${NC}"
echo -e "  ${DIM}Nmap · Nuclei · OWASP ZAP · Ollama AI · PostgreSQL · Redis${NC}"
echo ""

# ── Detect OS & Architecture ──────────────────────────────────────────────────
section "Detecting system"

OS=""
ARCH=$(uname -m)
IS_ARM=false
IS_WSL=false
PKG_MGR=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    [[ "$ARCH" == "arm64" ]] && IS_ARM=true
    info "macOS detected ($(sw_vers -productVersion)) — $ARCH"
elif grep -qi microsoft /proc/version 2>/dev/null; then
    OS="linux"
    IS_WSL=true
    info "Windows WSL2 detected"
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    OS="linux"
    info "Linux detected — $ARCH"
else
    fail "Unsupported OS: $OSTYPE"
    echo "  CerberOps supports macOS, Linux, and Windows WSL2."
    exit 1
fi

[[ "$ARCH" == "aarch64" ]] && IS_ARM=true

# Detect Linux package manager
if [[ "$OS" == "linux" ]]; then
    if command -v apt-get &>/dev/null; then
        PKG_MGR="apt"
    elif command -v dnf &>/dev/null; then
        PKG_MGR="dnf"
    elif command -v pacman &>/dev/null; then
        PKG_MGR="pacman"
    else
        PKG_MGR="unknown"
    fi
    info "Package manager: ${PKG_MGR}"
fi

# Detect RAM (for model recommendations)
RAM_GB=8
if [[ "$OS" == "macos" ]]; then
    RAM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    RAM_GB=$(( RAM_BYTES / 1024 / 1024 / 1024 ))
elif [[ "$OS" == "linux" ]]; then
    RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 0)
    RAM_GB=$(( RAM_KB / 1024 / 1024 ))
fi
ok "RAM: ${RAM_GB}GB detected"

# ── Install Docker ────────────────────────────────────────────────────────────
section "Docker"

install_docker_macos() {
    warn "Docker Desktop is not installed."
    echo ""
    echo -e "  ${BOLD}Options:${NC}"
    echo "    1) Download Docker Desktop automatically (recommended)"
    echo "    2) I'll install it myself — open https://docs.docker.com/desktop/mac/install/"
    echo ""
    ask "Choose [1]:"
    read -r DOCKER_CHOICE
    case "${DOCKER_CHOICE:-1}" in
        2)
            echo "  Open https://docs.docker.com/desktop/mac/install/ and re-run this script."
            exit 1
            ;;
        *)
            info "Downloading Docker Desktop for macOS..."
            if [[ "$IS_ARM" == true ]]; then
                DMG_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
            else
                DMG_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
            fi
            TMP_DMG="/tmp/Docker.dmg"
            curl -L --progress-bar "$DMG_URL" -o "$TMP_DMG"
            info "Mounting and installing Docker Desktop..."
            hdiutil attach "$TMP_DMG" -quiet
            cp -R /Volumes/Docker/Docker.app /Applications/
            hdiutil detach /Volumes/Docker -quiet
            rm -f "$TMP_DMG"
            info "Launching Docker Desktop..."
            open -a Docker
            echo ""
            warn "Docker Desktop is launching. Waiting for it to be ready (up to 60s)..."
            for i in $(seq 1 30); do
                sleep 2
                docker info &>/dev/null && break
                echo -e "  ${DIM}Waiting... ${i}/30${NC}"
            done
            ;;
    esac
}

install_docker_linux() {
    warn "Docker not found. Installing..."
    if [[ "$PKG_MGR" == "apt" ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq ca-certificates curl gnupg lsb-release
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
            https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
            | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker "$USER" || true
        sudo systemctl enable --now docker
    elif [[ "$PKG_MGR" == "dnf" ]]; then
        sudo dnf -y install dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker "$USER" || true
        sudo systemctl enable --now docker
    elif [[ "$PKG_MGR" == "pacman" ]]; then
        sudo pacman -Sy --noconfirm docker docker-compose
        sudo usermod -aG docker "$USER" || true
        sudo systemctl enable --now docker
    else
        fail "Cannot auto-install Docker on this Linux distribution."
        echo "  Install manually: https://docs.docker.com/engine/install/"
        exit 1
    fi
    ok "Docker installed"
}

if docker info &>/dev/null 2>&1; then
    ok "Docker is running: $(docker --version)"
elif command -v docker &>/dev/null; then
    warn "Docker is installed but not running. Starting..."
    if [[ "$OS" == "macos" ]]; then
        open -a Docker
        info "Waiting for Docker Desktop to start..."
        for i in $(seq 1 30); do
            sleep 2
            docker info &>/dev/null && break
            echo -e "  ${DIM}Waiting... ${i}/30${NC}"
        done
    else
        sudo systemctl start docker
        sleep 3
    fi
    docker info &>/dev/null && ok "Docker is now running" || { fail "Docker failed to start."; exit 1; }
else
    if [[ "$OS" == "macos" ]]; then
        install_docker_macos
    else
        install_docker_linux
    fi
fi

# Final check
docker info &>/dev/null || { fail "Docker is still not running. Please start Docker and re-run."; exit 1; }
ok "Docker ready: $(docker --version)"

# ── Install Ollama ────────────────────────────────────────────────────────────
section "Ollama (Local AI)"

install_ollama() {
    info "Installing Ollama..."
    if [[ "$OS" == "macos" ]]; then
        # Try Homebrew first, fall back to official installer
        if command -v brew &>/dev/null; then
            brew install --cask ollama 2>/dev/null || curl -fsSL https://ollama.com/install.sh | sh
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
}

if command -v ollama &>/dev/null; then
    ok "Ollama found: $(ollama --version 2>/dev/null | head -1)"
else
    warn "Ollama not installed."
    install_ollama
    ok "Ollama installed"
fi

# Start Ollama daemon if not running
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    info "Starting Ollama service..."
    if [[ "$OS" == "macos" ]]; then
        # On macOS, open the app or use CLI
        (ollama serve &>/dev/null &)
    else
        # On Linux, try systemd first
        (sudo systemctl start ollama 2>/dev/null || ollama serve &>/dev/null &)
    fi
    for i in $(seq 1 15); do
        sleep 2
        curl -s http://localhost:11434/api/tags &>/dev/null && break
        echo -e "  ${DIM}Waiting for Ollama... ${i}/15${NC}"
    done
fi
curl -s http://localhost:11434/api/tags &>/dev/null && ok "Ollama service is running" || warn "Ollama may not be running — AI reports will use fallback mode"

# ── Choose AI Model ───────────────────────────────────────────────────────────
section "AI Model Selection"

echo -e "  ${DIM}System: ${RAM_GB}GB RAM · $ARCH${NC}"
echo ""

# Build recommended model list based on RAM
echo -e "  ${BOLD}Choose your AI model (used for generating remediation reports):${NC}"
echo ""

if [[ $RAM_GB -ge 16 ]]; then
    echo -e "  ${GREEN}★${NC} 1) qwen2.5-coder:7b    — Best quality  · ~4.5GB · Recommended for ${RAM_GB}GB RAM"
    echo "     2) llama3.1:8b          — Great quality · ~5GB   · General purpose"
    echo "     3) qwen2.5-coder:1.5b  — Fast & light  · ~1GB   · Any machine"
    echo "     4) llama3.2:1b          — Minimal       · ~600MB · Very fast"
    RECOMMENDED="qwen2.5-coder:7b"
    DEFAULT_CHOICE="1"
elif [[ $RAM_GB -ge 8 ]]; then
    echo -e "  ${GREEN}★${NC} 1) qwen2.5-coder:1.5b  — Best for ${RAM_GB}GB RAM · ~1GB   · Fast & accurate"
    echo "     2) llama3.2:1b          — Minimal       · ~600MB · Very fast"
    echo "     3) qwen2.5-coder:7b    — High quality  · ~4.5GB · Needs 16GB+ RAM"
    RECOMMENDED="qwen2.5-coder:1.5b"
    DEFAULT_CHOICE="1"
else
    echo -e "  ${GREEN}★${NC} 1) llama3.2:1b          — Recommended for ${RAM_GB}GB RAM · ~600MB"
    echo "     2) qwen2.5-coder:1.5b  — Good quality · ~1GB"
    RECOMMENDED="llama3.2:1b"
    DEFAULT_CHOICE="1"
fi
echo "     5) Skip (use fallback text reports)"
echo ""
ask "Select model [default: ${DEFAULT_CHOICE} — ${RECOMMENDED}]:"
read -r MODEL_CHOICE

if [[ $RAM_GB -ge 16 ]]; then
    case "${MODEL_CHOICE:-1}" in
        1) CHOSEN_MODEL="qwen2.5-coder:7b" ;;
        2) CHOSEN_MODEL="llama3.1:8b" ;;
        3) CHOSEN_MODEL="qwen2.5-coder:1.5b" ;;
        4) CHOSEN_MODEL="llama3.2:1b" ;;
        5) CHOSEN_MODEL="" ;;
        *) CHOSEN_MODEL="$RECOMMENDED" ;;
    esac
elif [[ $RAM_GB -ge 8 ]]; then
    case "${MODEL_CHOICE:-1}" in
        1) CHOSEN_MODEL="qwen2.5-coder:1.5b" ;;
        2) CHOSEN_MODEL="llama3.2:1b" ;;
        3) CHOSEN_MODEL="qwen2.5-coder:7b" ;;
        5) CHOSEN_MODEL="" ;;
        *) CHOSEN_MODEL="$RECOMMENDED" ;;
    esac
else
    case "${MODEL_CHOICE:-1}" in
        1) CHOSEN_MODEL="llama3.2:1b" ;;
        2) CHOSEN_MODEL="qwen2.5-coder:1.5b" ;;
        5) CHOSEN_MODEL="" ;;
        *) CHOSEN_MODEL="$RECOMMENDED" ;;
    esac
fi

if [[ -n "${CHOSEN_MODEL}" ]]; then
    # Check if already pulled
    if ollama list 2>/dev/null | grep -q "^${CHOSEN_MODEL}"; then
        ok "Model '${CHOSEN_MODEL}' already downloaded"
    else
        info "Pulling model: ${CHOSEN_MODEL}"
        info "This downloads once and is stored locally. Size varies (600MB–5GB)."
        echo ""
        ollama pull "${CHOSEN_MODEL}"
        ok "Model '${CHOSEN_MODEL}' ready"
    fi
else
    warn "Skipping model download — AI reports will use text templates"
    CHOSEN_MODEL="qwen2.5-coder:1.5b"
fi

# ── Create .env ───────────────────────────────────────────────────────────────
section "Configuration"

if [[ -f .env ]]; then
    ok ".env already exists — keeping your settings"
else
    if [[ -f .env.example ]]; then
        cp .env.example .env
        ok ".env created from template"
    else
        # Create minimal .env from scratch
        cat > .env << ENVEOF
DATABASE_URL=postgresql+asyncpg://cerberops:cerberops_secret@postgres:5432/cerberops
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=${CHOSEN_MODEL}
ZAP_API_URL=http://zap:8080
ZAP_API_KEY=
NMAP_TIMEOUT=600
NUCLEI_TIMEOUT=900
ZAP_TIMEOUT=1200
LOG_LEVEL=INFO
ALLOW_INTERNAL_TARGETS=false
WORKERS=2
ENVEOF
        ok ".env created"
    fi
fi

# Update OLLAMA_MODEL in .env to match what was chosen
if [[ "$OS" == "macos" ]]; then
    sed -i '' "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=${CHOSEN_MODEL}|" .env
else
    sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=${CHOSEN_MODEL}|" .env
fi

# Ensure OLLAMA_BASE_URL uses host.docker.internal (Docker → host Ollama)
if [[ "$OS" == "macos" ]]; then
    sed -i '' "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|" .env
elif [[ "$IS_WSL" == true ]]; then
    # In WSL, Docker can't use host.docker.internal reliably — use the gateway
    GATEWAY=$(ip route show default 2>/dev/null | awk '/default/ {print $3}' | head -1)
    sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://${GATEWAY}:11434|" .env
else
    sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|" .env
fi

ok "Configuration ready"

# ── Build & Launch via Docker Compose ────────────────────────────────────────
section "Building & Starting CerberOps"

info "Building Docker images (first run takes 2–5 minutes)..."
docker compose build

echo ""
info "Starting all services..."
docker compose up -d

# ── Health Check ─────────────────────────────────────────────────────────────
section "Health Check"

info "Waiting for services to be ready..."
sleep 8

MAX_WAIT=60
ELAPSED=0
until curl -s http://localhost:8000/api/v1/health &>/dev/null || [[ $ELAPSED -ge $MAX_WAIT ]]; do
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo -e "  ${DIM}Waiting for API... ${ELAPSED}s${NC}"
done

if curl -s http://localhost:8000/api/v1/health &>/dev/null; then
    HEALTH=$(curl -s http://localhost:8000/api/v1/health)
    NMAP_OK=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if d['scanners']['nmap'] else '✖')" 2>/dev/null || echo "?")
    NUCLEI_OK=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if d['scanners']['nuclei'] else '✖')" 2>/dev/null || echo "?")
    ZAP_OK=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if d['scanners']['zap'] else '✖')" 2>/dev/null || echo "?")
    AI_OK=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if d['ollama_available'] else '✖')" 2>/dev/null || echo "?")
    DB_OK=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if d['database'] else '✖')" 2>/dev/null || echo "?")

    echo ""
    echo -e "  ${BOLD}Service Status:${NC}"
    echo -e "    ${CYAN}Nmap${NC}        $NMAP_OK"
    echo -e "    ${CYAN}Nuclei${NC}      $NUCLEI_OK"
    echo -e "    ${CYAN}OWASP ZAP${NC}   $ZAP_OK"
    echo -e "    ${CYAN}Ollama AI${NC}   $AI_OK  (model: ${CHOSEN_MODEL})"
    echo -e "    ${CYAN}Database${NC}    $DB_OK"
else
    warn "API not ready yet — it may still be starting up"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║   CerberOps is ready!                   ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Dashboard${NC}    →  http://localhost:3000"
echo -e "  ${BOLD}API Docs${NC}     →  http://localhost:8000/docs"
echo -e "  ${BOLD}Health${NC}       →  http://localhost:8000/api/v1/health"
echo ""
echo -e "  ${BOLD}Quick scan:${NC}"
echo -e "  ${DIM}curl -X POST http://localhost:8000/api/v1/scan \\${NC}"
echo -e "  ${DIM}  -H \"Content-Type: application/json\" \\${NC}"
echo -e "  ${DIM}  -d '{\"target\": \"https://example.com\", \"scanners\": [\"nmap\", \"nuclei\"]}'${NC}"
echo ""
echo -e "  ${BOLD}Manage:${NC}"
echo -e "  ${DIM}docker compose logs -f       # View logs${NC}"
echo -e "  ${DIM}docker compose down          # Stop everything${NC}"
echo -e "  ${DIM}docker compose restart       # Restart${NC}"
echo ""
