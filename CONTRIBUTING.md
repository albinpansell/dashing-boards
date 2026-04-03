# Contributing

## Setup

```bash
python3 -m pip install -e .[dev]
```

## Workflow

1. Open an issue for significant changes.
2. Keep changes focused and minimal.
3. Add or update tests for behavior changes.
4. Run local checks before creating a pull request.

## Local checks

```bash
python3 -m ruff format --check .
python3 -m pytest
python3 -m build
```

## Pull request checklist

- Tests pass.
- Public API changes are documented in `README.md`.
- New dependencies are justified and minimal.
