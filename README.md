# CerberOps

**DevSecOps Vulnerability Orchestrator** — Nmap, Nuclei, and OWASP ZAP unified behind one API, with AI-powered triage and remediation running entirely on your machine via Ollama.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](docker-compose.yml)







<img width="3454" height="1936" alt="image" src="https://github.com/user-attachments/assets/ff3edf91-cb5a-497a-bb53-dcc28d8b0c9e" />


---

## What it does

| Problem | CerberOps Solution |
|---|---|
| Three scanners, three CLIs, three output formats | One REST API, one normalized finding schema |
| Scans block your terminal for minutes | Async Celery workers — fire and poll |
| Same vulnerability reported by all three tools | SHA-256 fingerprint deduplication engine |
| Raw JSON output nobody reads | AI executive summary + remediation plan |
| Cloud AI means your vuln data leaves your network | Local Ollama — nothing ever leaves your machine |

---

## Requirements

| Requirement | Notes |
|---|---|
| [Docker Desktop](https://docs.docker.com/desktop/) | v24+ with Compose v2 |
| [Ollama](https://ollama.com) | For local AI — optional, falls back to templates |
| 8 GB RAM minimum | 16 GB recommended for better AI models |
| macOS, Linux, or Windows WSL2 | |

---

## Quick Start — One Command

```bash
git clone https://github.com/Mavlonbek17/CerberOps.git
cd CerberOps
chmod +x install.sh
./install.sh
```

The installer:
1. Detects your OS and architecture (macOS Intel/Apple Silicon, Linux, WSL2)
2. Installs Docker if missing
3. Installs Ollama if missing
4. Recommends an AI model based on your available RAM and pulls it
5. Creates `.env` from the template
6. Builds and starts all Docker services
7. Runs a health check and prints status

To update everything later:

```bash
./install.sh --update
```

---

## Manual Setup

If you prefer step-by-step control:

```bash
# 1. Clone
git clone https://github.com/Mavlonbek17/CerberOps.git
cd CerberOps

# 2. Configure
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# 3. Start all services
docker compose up -d

# 4. Pull an AI model (choose based on your RAM — see AI Models section below)
ollama pull qwen2.5-coder:1.5b
```

---

## Access Points

| Service | URL |
|---|---|
| **Dashboard (Web UI)** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/v1/health |

---

## AI Models

CerberOps uses **local Ollama models** — scan data never leaves your machine.

### Choosing a model

| Model | RAM needed | Download size | Speed | Quality | Best for |
|---|---|---|---|---|---|
| `llama3.2:1b` | 4 GB | ~600 MB | Very fast | Basic | Low-RAM machines |
| `qwen2.5-coder:1.5b` | 6 GB | ~1 GB | Fast | Good | **Default — works on most machines** |
| `llama3.1:8b` | 10 GB | ~5 GB | Medium | Great | Better summaries |
| `qwen2.5-coder:7b` | 10 GB | ~4.5 GB | Medium | **Best** | Recommended if you have 16 GB+ RAM |

> **Tip:** The installer detects your RAM automatically and recommends the right model. You can always switch by editing `OLLAMA_MODEL` in `.env` and pulling the new model.

### Pulling a model manually

```bash
# Recommended default
ollama pull qwen2.5-coder:1.5b

# Best quality (needs 16 GB RAM)
ollama pull qwen2.5-coder:7b

# List what you have
ollama list
```

### What the AI does

- **Smart Recon** — Before scanning, the AI fingerprints the target and narrows down which Nuclei templates and Nmap port ranges to use, reducing scan time and noise.
- **False Positive Filter** — After scanning, the AI reviews low and medium severity findings and tags obvious noise as filtered, so you focus on real issues.
- **Executive Summary** — Generates a human-readable report with risk overview, technical details, and a prioritized remediation plan.
- **AI Chat** — Ask follow-up questions about any completed scan directly in the dashboard.
- **PoC Generator** — For critical/high findings, generates a safe proof-of-concept verification script.

If Ollama is not running, CerberOps falls back to template-based reports — all scanning still works normally.

---

## Scanners

| Scanner | Type | What it finds |
|---|---|---|
| **Nmap** | Network | Open ports, service versions, risky services (Telnet, FTP, exposed databases) |
| **Nuclei** | Vulnerability | CVEs, misconfigurations, exposed admin panels, default credentials (10,000+ templates) |
| **OWASP ZAP** | Web App DAST | XSS, SQLi, CSRF, broken auth, missing security headers, cookie issues |

> **ZAP note:** ZAP runs as a Docker container and needs a few seconds to initialise on first start. It is included in `docker compose up -d` automatically.

---

## Usage

### Web UI

Open http://localhost:3000, enter a target URL or IP, choose your scan engines, and click **Launch Scan**. Results update in real time with severity-coded findings. Click **AI Chat** to ask questions about the scan.

### REST API

```bash
# Start a scan
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com", "scanners": ["nmap", "nuclei", "zap"]}'

# Response
# {"job_id": "abc123", "status": "queued"}

# Poll status + findings
curl http://localhost:8000/api/v1/scan/abc123

# Get AI report
curl http://localhost:8000/api/v1/report/abc123
```

### CLI

```bash
# Install
pip install -e .

# Scan and wait for results
cerberops scan https://example.com

# Check status
cerberops status <job_id>

# Read AI report
cerberops report <job_id>

# List all scans
cerberops list

# System health
cerberops health
```

---

## Configuration

All settings are in the `.env` file. Copy `.env.example` to get started.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:1.5b` | AI model to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `ZAP_API_URL` | `http://localhost:8080` | ZAP daemon URL |
| `ZAP_TIMEOUT` | `1200` | ZAP scan timeout in seconds |
| `NMAP_TIMEOUT` | `600` | Nmap timeout in seconds |
| `NUCLEI_TIMEOUT` | `900` | Nuclei timeout in seconds |
| `ALLOW_INTERNAL_TARGETS` | `false` | Allow scanning private/RFC1918 IPs |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health and scanner availability |
| `POST` | `/api/v1/scan` | Start a new scan |
| `GET` | `/api/v1/scan` | List all scans |
| `GET` | `/api/v1/scan/{job_id}` | Scan status and findings |
| `DELETE` | `/api/v1/scan/{job_id}` | Cancel a running scan |
| `GET` | `/api/v1/report/{job_id}` | AI-generated remediation report |
| `POST` | `/api/v1/chat/{job_id}` | Chat with AI about a scan |
| `GET` | `/api/v1/findings/{job_id}` | Raw findings list |

Full interactive docs at http://localhost:8000/docs

---

## Project Structure

```
CerberOps/
├── app/
│   ├── adapters/          # Scanner wrappers (Nmap, Nuclei, ZAP)
│   ├── api/v1/            # REST endpoints
│   ├── services/          # AI triage, chat, dedup, orchestration
│   ├── tasks/             # Celery task definitions
│   ├── core/              # Security, exceptions
│   ├── models.py          # SQLModel ORM models
│   ├── schemas.py         # API request/response schemas
│   └── config.py          # Pydantic settings
├── frontend/              # React + Vite + Tailwind dashboard
├── cli/                   # Typer CLI
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── install.sh             # One-command installer
├── docker-compose.yml     # Full-stack orchestration
├── Dockerfile             # Backend + scanners image
└── Dockerfile.frontend    # React production build
```

---

## Security

- Private IPs and loopback addresses are blocked by default (`ALLOW_INTERNAL_TARGETS=false`)
- API key authentication on all mutating endpoints (`X-API-Key` header)
- Docker containers run as non-root users
- No pickle serialization in Celery (prevents RCE via task queue)
- Hard timeouts on every scanner
- All AI processing is local — no data sent to external services

> **Important:** Only scan targets you own or have explicit written authorization to test. Unauthorized scanning is illegal.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run API locally (without Docker)
uvicorn app.main:app --reload --port 8000

# Run Celery worker locally
celery -A app.tasks.celery_app worker --loglevel=info -Q scans

# Run frontend dev server
cd frontend && npm run dev

# Run tests
pytest

# Lint
ruff check .
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[Apache License 2.0](LICENSE)
