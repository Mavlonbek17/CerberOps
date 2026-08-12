#!/usr/bin/env bash
# =============================================================================
# CerberOps — Universal One-Command Installer
# Supports: macOS (Intel + Apple Silicon), Linux (Debian/Ubuntu/Fedora/Arch),
#           Windows WSL2 (Ubuntu)
#
# Usage:
#   ./install.sh           # Install missing components, skip what already exists
#   ./install.sh --update  # Same + update Docker, Ollama, model, and images
# =============================================================================

set -euo pipefail

# ── Flags ─────────────────────────────────────────────────────────────────────
UPDATE_MODE=false
for arg in "$@"; do
    case "$arg" in
        --update|-u) UPDATE_MODE=true ;;
        --help|-h)
            echo "Usage: ./install.sh [--update]"
            echo ""
            echo "  (no flag)   Install missing components only. Skip anything already present."
            echo "  --update    Also update Docker, Ollama, the AI model, and Docker images."
            exit 0
            ;;
        *)
            echo "Unknown flag: $arg  (use --help for usage)"
            exit 1
            ;;
    esac
done

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
updated() { echo -e "${MAGENTA}  ↑${NC}  $*"; }

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
if [[ "$UPDATE_MODE" == true ]]; then
    echo -e "  ${MAGENTA}${BOLD}[ UPDATE MODE — will upgrade Docker, Ollama, model, and images ]${NC}"
    echo ""
fi

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

# ── Docker ────────────────────────────────────────────────────────────────────
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
            warn "Waiting for Docker Desktop to be ready (up to 60s)..."
            for i in $(seq 1 30); do
                sleep 2
                docker info &>/dev/null && break
                echo -e "  ${DIM}Waiting... ${i}/30${NC}"
            done
            ;;
    esac
}

update_docker_macos() {
    info "Checking for Docker Desktop updates..."
    # Docker Desktop on macOS updates itself — trigger via softwareupdate or
    # remind the user since Docker Desktop has its own updater built in.
    if open -a Docker 2>/dev/null; then
        # Give Docker Desktop time to check for updates (it does so on launch)
        sleep 5
        updated "Docker Desktop launched — use its menu bar icon to apply any pending update"
    fi
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

update_docker_linux() {
    info "Updating Docker Engine..."
    BEFORE=$(docker --version 2>/dev/null || echo "unknown")
    if [[ "$PKG_MGR" == "apt" ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq --only-upgrade docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ "$PKG_MGR" == "dnf" ]]; then
        sudo dnf update -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ "$PKG_MGR" == "pacman" ]]; then
        sudo pacman -Syu --noconfirm docker docker-compose
    fi
    AFTER=$(docker --version 2>/dev/null || echo "unknown")
    if [[ "$BEFORE" == "$AFTER" ]]; then
        ok "Docker already up to date: $AFTER"
    else
        updated "Docker updated: $BEFORE → $AFTER"
    fi
}

# Ensure Docker is installed and running
if docker info &>/dev/null 2>&1; then
    DOCKER_VER=$(docker --version)
    if [[ "$UPDATE_MODE" == true ]]; then
        if [[ "$OS" == "macos" ]]; then
            update_docker_macos
        else
            update_docker_linux
        fi
    else
        ok "Docker is running: $DOCKER_VER"
    fi
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
        # Also update if in update mode
        [[ "$UPDATE_MODE" == true ]] && update_docker_linux
    fi
    docker info &>/dev/null && ok "Docker is now running" || { fail "Docker failed to start."; exit 1; }
else
    # Not installed at all
    if [[ "$OS" == "macos" ]]; then
        install_docker_macos
    else
        install_docker_linux
    fi
fi

# Final guard
docker info &>/dev/null || { fail "Docker is still not running. Please start Docker and re-run."; exit 1; }
ok "Docker ready: $(docker --version)"

# ── Ollama ────────────────────────────────────────────────────────────────────
section "Ollama (Local AI)"

install_ollama() {
    info "Installing Ollama..."
    if [[ "$OS" == "macos" ]]; then
        if command -v brew &>/dev/null; then
            brew install --cask ollama 2>/dev/null || curl -fsSL https://ollama.com/install.sh | sh
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
}

update_ollama() {
    info "Updating Ollama..."
    BEFORE=$(ollama --version 2>/dev/null | head -1 || echo "unknown")
    if [[ "$OS" == "macos" ]] && command -v brew &>/dev/null; then
        # Check if installed via Homebrew cask
        if brew list --cask ollama &>/dev/null 2>&1; then
            brew upgrade --cask ollama 2>/dev/null || true
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        # Official installer is idempotent and updates in place
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    AFTER=$(ollama --version 2>/dev/null | head -1 || echo "unknown")
    if [[ "$BEFORE" == "$AFTER" ]]; then
        ok "Ollama already up to date: $AFTER"
    else
        updated "Ollama updated: $BEFORE → $AFTER"
    fi
}

if command -v ollama &>/dev/null; then
    if [[ "$UPDATE_MODE" == true ]]; then
        update_ollama
    else
        ok "Ollama found: $(ollama --version 2>/dev/null | head -1)"
    fi
else
    warn "Ollama not installed."
    install_ollama
    ok "Ollama installed: $(ollama --version 2>/dev/null | head -1)"
fi

# Ensure Ollama daemon is running
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    info "Starting Ollama service..."
    if [[ "$OS" == "macos" ]]; then
        (ollama serve &>/dev/null &)
    else
        (sudo systemctl start ollama 2>/dev/null || ollama serve &>/dev/null &)
    fi
    for i in $(seq 1 15); do
        sleep 2
        curl -s http://localhost:11434/api/tags &>/dev/null && break
        echo -e "  ${DIM}Waiting for Ollama... ${i}/15${NC}"
    done
fi
curl -s http://localhost:11434/api/tags &>/dev/null \
    && ok "Ollama service is running" \
    || warn "Ollama daemon not responding — AI reports will use fallback mode"

# ── AI Model ──────────────────────────────────────────────────────────────────
section "AI Model"

echo -e "  ${DIM}System: ${RAM_GB}GB RAM · $ARCH${NC}"
echo ""

# Build model menu based on RAM
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
echo "     5) Skip"
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
    ALREADY_PULLED=false
    ollama list 2>/dev/null | grep -q "^${CHOSEN_MODEL}" && ALREADY_PULLED=true

    if [[ "$ALREADY_PULLED" == true && "$UPDATE_MODE" == false ]]; then
        ok "Model '${CHOSEN_MODEL}' already downloaded — skipping"
    else
        if [[ "$UPDATE_MODE" == true && "$ALREADY_PULLED" == true ]]; then
            info "Pulling latest version of '${CHOSEN_MODEL}'..."
            BEFORE_DIGEST=$(ollama show "${CHOSEN_MODEL}" 2>/dev/null | grep -i digest | awk '{print $2}' || echo "unknown")
            ollama pull "${CHOSEN_MODEL}"
            AFTER_DIGEST=$(ollama show "${CHOSEN_MODEL}" 2>/dev/null | grep -i digest | awk '{print $2}' || echo "unknown")
            if [[ "$BEFORE_DIGEST" == "$AFTER_DIGEST" ]]; then
                ok "Model '${CHOSEN_MODEL}' already at latest version"
            else
                updated "Model '${CHOSEN_MODEL}' updated to latest"
            fi
        else
            info "Pulling model: ${CHOSEN_MODEL}"
            info "This downloads once and is stored locally (600MB–5GB)."
            echo ""
            ollama pull "${CHOSEN_MODEL}"
            ok "Model '${CHOSEN_MODEL}' ready"
        fi
    fi
else
    warn "Skipping model — AI reports will use text templates"
    CHOSEN_MODEL="${RECOMMENDED}"
fi

# ── Configuration ─────────────────────────────────────────────────────────────
section "Configuration"

if [[ -f .env ]]; then
    ok ".env already exists — keeping your settings"
else
    if [[ -f .env.example ]]; then
        cp .env.example .env
        ok ".env created from template"
    else
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

# Always sync OLLAMA_MODEL in .env to the chosen model
if [[ "$OS" == "macos" ]]; then
    sed -i '' "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=${CHOSEN_MODEL}|" .env
    sed -i '' "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|" .env
elif [[ "$IS_WSL" == true ]]; then
    GATEWAY=$(ip route show default 2>/dev/null | awk '/default/ {print $3}' | head -1)
    sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=${CHOSEN_MODEL}|" .env
    sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://${GATEWAY}:11434|" .env
else
    sed -i "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=${CHOSEN_MODEL}|" .env
    sed -i "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|" .env
fi

ok "Configuration ready (model: ${CHOSEN_MODEL})"

# ── Build & Launch ────────────────────────────────────────────────────────────
section "Building & Starting CerberOps"

if [[ "$UPDATE_MODE" == true ]]; then
    info "Pulling latest base images from Docker Hub..."
    docker compose pull --quiet || true
    info "Rebuilding CerberOps images (no cache)..."
    docker compose build --no-cache
    info "Restarting all services..."
    docker compose up -d --force-recreate
    updated "All Docker images rebuilt and services restarted"
else
    info "Building Docker images (first run takes 2–5 minutes)..."
    docker compose build
    info "Starting all services..."
    docker compose up -d
fi

# ── Health Check ──────────────────────────────────────────────────────────────
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
    _check() { echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✔' if $1 else '✖')" 2>/dev/null || echo "?"; }
    NMAP_OK=$(_check   "d['scanners']['nmap']")
    NUCLEI_OK=$(_check "d['scanners']['nuclei']")
    ZAP_OK=$(_check    "d['scanners']['zap']")
    AI_OK=$(_check     "d['ollama_available']")
    DB_OK=$(_check     "d['database']")

    echo ""
    echo -e "  ${BOLD}Service Status:${NC}"
    echo -e "    ${CYAN}Nmap${NC}        $NMAP_OK"
    echo -e "    ${CYAN}Nuclei${NC}      $NUCLEI_OK"
    echo -e "    ${CYAN}OWASP ZAP${NC}   $ZAP_OK"
    echo -e "    ${CYAN}Ollama AI${NC}   $AI_OK  (model: ${CHOSEN_MODEL})"
    echo -e "    ${CYAN}Database${NC}    $DB_OK"
else
    warn "API not ready yet — it may still be starting. Check: curl http://localhost:8000/api/v1/health"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
if [[ "$UPDATE_MODE" == true ]]; then
echo -e "${BOLD}${GREEN}║   CerberOps updated & ready!            ║${NC}"
else
echo -e "${BOLD}${GREEN}║   CerberOps is ready!                   ║${NC}"
fi
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
echo -e "  ${DIM}./install.sh --update        # Update everything${NC}"
echo ""
