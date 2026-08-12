# CerberOps — Developer Guide

## Build & Run

```bash
# Full stack (Docker)
docker compose up -d

# API only (local dev)
uvicorn app.main:app --reload --port 8000

# Celery worker
celery -A app.tasks.celery_app worker --loglevel=info -Q scans

# Frontend dev
cd frontend && npm run dev

# CLI
pip install -e . && cerberops --help
```

## Test

```bash
pytest                     # Run all tests
pytest tests/test_dedup.py # Run a specific file
ruff check .               # Lint
```

## Key Patterns

- **Scanner adapters** in `app/adapters/` implement `BaseScanner` (abc)
- **Async tasks** use Celery with Redis broker — scans never block API
- **Findings** go through `deduplicate()` before database persistence
- **AI reports** call Ollama `/api/generate` with structured JSON output
- **Scope validation** blocks private IPs by default (security)

## Adding a Scanner

1. Create `app/adapters/new_scanner_adapter.py` extending `BaseScanner`
2. Implement `is_available()`, `run()`, `get_version()`
3. Add to `_SCANNERS` dict in `app/services/scan_service.py`
4. Add binary installation to `Dockerfile` if needed
