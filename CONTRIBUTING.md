# Contributing to CerberOps

Thank you for your interest in contributing to CerberOps! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CerberOps.git
   cd CerberOps
   ```
3. **Set up** the development environment:
   ```bash
   pip install -e ".[dev]"
   cp .env.example .env
   docker compose up -d postgres redis
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run the linter and tests:
   ```bash
   ruff check .
   pytest
   ```
4. Commit with a descriptive message
5. Push to your fork and open a Pull Request

## Code Style

- Python: Follow PEP 8, enforced by [Ruff](https://github.com/astral-sh/ruff)
- TypeScript/React: Follow the existing patterns in `frontend/src/`
- Keep functions focused and small
- Add type hints to all Python function signatures
- Write docstrings for public functions and classes

## Adding a New Scanner

1. Create `app/adapters/your_scanner_adapter.py`
2. Extend `BaseScanner` from `app/adapters/base.py`
3. Implement `is_available()`, `run()`, and `get_version()`
4. Return `list[RawFinding]` from `run()`
5. Register in `app/services/scan_service.py` `_SCANNERS` dict
6. Add to the Docker image if it requires a binary

## Reporting Issues

- Use GitHub Issues
- Include: Python version, OS, Docker version, steps to reproduce
- For security vulnerabilities, please email privately instead of opening a public issue

## Pull Request Checklist

- [ ] Code follows the existing style
- [ ] Tests pass (`pytest`)
- [ ] Linter passes (`ruff check .`)
- [ ] New features include tests
- [ ] Documentation updated if needed

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
