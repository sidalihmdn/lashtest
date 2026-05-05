# Contributing to lashtest

Thank you for your interest in contributing. This document explains how to set up a development environment, run tests, and submit changes.

---

## Development setup

**Prerequisites:** Python 3.9+, `git`

```bash
git clone https://github.com/sidalihmdn/lashtest.git
cd lashtest

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

---

## Running tests

```bash
# All unit tests
pytest tests/unit/

# With coverage report
pytest tests/unit/ --cov=src/lashtest --cov-report=term-missing

# A specific file
pytest tests/unit/test_response.py -v
```

---

## Project structure

```
src/lashtest/
├── core/          # APIClient, Request, Response, exceptions
├── http/          # Auth strategies
├── decorators/    # Test decorators
├── utils/         # fake data, SSL detection, logger
└── cli/           # Click-based CLI

tests/
├── unit/          # Unit tests (no network calls)
└── *.py           # Integration tests (require network)
```

---

## Guidelines

- **Unit tests required** — every new public method needs unit tests in `tests/unit/`
- **No network calls in unit tests** — use `unittest.mock` to mock `APIClient` and `requests`
- **Type hints** — add type annotations to all new public functions and methods
- **No pinned versions** — use `>=` specifiers in `pyproject.toml`, never `==`
- **Keep it simple** — avoid adding dependencies; prefer stdlib solutions

---

## Submitting changes

1. Fork the repository and create a branch from `main`
2. Make your changes with tests
3. Run `pytest tests/unit/` and ensure all tests pass
4. Open a pull request with a clear description of what the change does and why

---

## Reporting issues

Open an issue at https://github.com/sidalihmdn/lashtest/issues. Include:
- Python version and OS
- Minimal code that reproduces the problem
- Expected vs actual behaviour
