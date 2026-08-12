# CerberOps

**DevSecOps vulnerability orchestrator** — Nmap, Nuclei, and OWASP ZAP behind one API, with AI-powered remediation via local Ollama models.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](docker-compose.yml)

---

## Why CerberOps

Running multiple security scanners means juggling different CLIs, output formats, and report styles. CerberOps wraps three industry-standard tools into a single async pipeline:

| Problem | CerberOps Solution |
|---------|-------------------|
| Different scanner CLIs and output formats | One REST API, one normalized finding schema |
| Scanning blocks your terminal for minutes | Async Celery workers, 202 Accepted + poll or WebSocket |
| Duplicate findings across tools | SHA-256 fingerprint deduplication engine |
| Raw JSON output nobody reads | AI-generated executive summary + remediation plan |
| Cloud AI means sending your vuln data externally | Local Ollama models, your data never leaves your machine |

## Architecture

```
                    +------------------+
                    |   React UI       |
                    |   (Vite + TW)    |
                    +--------+---------+
                             |
                    +--------+---------+
    CLI (Typer) --> |   FastAPI API     |
                    |   /api/v1/*       |
                    +--------+---------+
                             |
                    +--------+---------+
                    |   Celery + Redis  |
                    |   Task Queue      |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
        +-----+----+  +-----+----+  +------+-----+
        |   Nmap   |  |  Nuclei  |  | OWASP ZAP  |
        | (subnet) |  | (vuln    |  | (web app   |
        |          |  |  detect) |  |  DAST)     |
        +----------+  +----------+  +------------+
                             |
                    +--------+---------+
                    |  Dedup Engine     |
                    |  + PostgreSQL     |
                    +--------+---------+
                             |
                    +--------+---------+
                    |  Ollama (Local)   |
                    |  AI Remediation   |
                    +------------------+
```

## Quick Start

### One-command setup (Docker)

```bash
git clone https://github.com/Mavlonbek17/CerberOps.git
cd CerberOps
./scripts/setup.sh
```

This checks dependencies, installs Ollama + a small AI model, and brings up the full stack via Docker Compose.

### Manual setup

```bash
# Prerequisites: Docker, Docker Compose, Ollama (optional)

# 1. Clone and configure
git clone https://github.com/Mavlonbek17/CerberOps.git
cd CerberOps
cp .env.example .env

# 2. Start services
docker compose up -d

# 3. (Optional) Pull an AI model
ollama pull qwen2.5-coder:1.5b
```

**Access points:**

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |

## Usage

### Web UI

Open http://localhost:3000, enter a target URL, select scanners, and click **Start Scan**. Results stream in real time with severity-coded findings and an AI-generated remediation report.

### REST API

```bash
# Start a scan
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com", "scanners": ["nmap", "nuclei"]}'

# Response: {"job_id": "abc123...", "status": "queued", "message": "..."}

# Check status
curl http://localhost:8000/api/v1/scan/abc123

# Get AI report
curl http://localhost:8000/api/v1/report/abc123
```

### CLI

```bash
# Install CLI
pip install -e .

# Run a scan (waits for completion)
cerberops scan https://example.com

# Check status
cerberops status <job_id>

# View AI report
cerberops report <job_id>

# List recent scans
cerberops list

# System health
cerberops health
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | System health and scanner availability |
| `POST` | `/api/v1/scan` | Start a new scan (returns 202 + job_id) |
| `GET` | `/api/v1/scan` | List all scans |
| `GET` | `/api/v1/scan/{job_id}` | Scan status and findings |
| `DELETE` | `/api/v1/scan/{job_id}` | Cancel a scan |
| `GET` | `/api/v1/report/{job_id}` | AI-generated remediation report |
| `POST` | `/api/v1/setup` | First-run API key generation |

Full interactive docs at `/docs` (Swagger) or `/redoc`.

## Scanners

| Scanner | Type | What It Finds |
|---------|------|--------------|
| **Nmap** | Network | Open ports, service versions, risky services (telnet, FTP, exposed databases) |
| **Nuclei** | Vulnerability | CVEs, misconfigurations, exposed panels, default credentials (10,000+ templates) |
| **OWASP ZAP** | Web App (DAST) | XSS, SQLi, CSRF, broken auth, security headers, cookie issues |

## AI Models

CerberOps uses **local AI models** via Ollama. Your scan data never leaves your machine.

| Model | RAM | Speed | Quality |
|-------|-----|-------|---------|
| `qwen2.5-coder:1.5b` | ~1 GB | Fast | Good (default) |
| `llama3.2:1b` | ~1 GB | Fast | Good |
| `llama3.1:8b` | ~5 GB | Medium | Better |
| `qwen2.5-coder:7b` | ~5 GB | Medium | Better |

```bash
# Pull a model
ollama pull qwen2.5-coder:1.5b

# Or use the helper script
./scripts/pull_models.sh
```

If Ollama is not available, CerberOps falls back to template-based reports.

## Configuration

All settings via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:1.5b` | Default AI model |
| `NMAP_TIMEOUT` | `600` | Nmap scan timeout (seconds) |
| `NUCLEI_TIMEOUT` | `900` | Nuclei scan timeout |
| `ZAP_TIMEOUT` | `1200` | ZAP scan timeout |
| `ALLOW_INTERNAL_TARGETS` | `false` | Allow scanning private IPs |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Project Structure

```
CerberOps/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py             # Pydantic settings
│   ├── database.py           # Async PostgreSQL
│   ├── models.py             # SQLModel ORM models
│   ├── schemas.py            # API request/response schemas
│   ├── api/v1/               # REST endpoints
│   ├── adapters/             # Scanner wrappers (Nmap, Nuclei, ZAP)
│   ├── services/             # Business logic (dedup, AI, orchestration)
│   ├── tasks/                # Celery task definitions
│   └── core/                 # Security, exceptions
├── cli/                      # Typer CLI application
├── frontend/                 # React + Vite + Tailwind
├── scripts/                  # Setup and utility scripts
├── tests/                    # Test suite
├── docker-compose.yml        # Full-stack orchestration
├── Dockerfile                # Backend + scanners
└── Dockerfile.frontend       # React production build
```

## Security Considerations

- **Scope Validation**: Loopback and RFC1918 addresses are blocked by default
- **API Key Auth**: All mutating endpoints require `X-API-Key` header
- **Non-root Docker**: Application runs as unprivileged user inside containers
- **JSON-only Celery**: No pickle deserialization (prevents RCE via task serialization)
- **Hard timeouts**: Every scanner has configurable hard time limits
- **No external data**: AI models run locally, scan data never leaves your network

> **Important**: Only scan targets you own or have explicit authorization to test.

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run API locally
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info -Q scans

# Run frontend dev server
cd frontend && npm run dev

# Run tests
pytest

# Lint
ruff check .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[Apache License 2.0](LICENSE)
