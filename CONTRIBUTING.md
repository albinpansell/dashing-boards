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

Always run these before `git push` or opening a PR. The first command
**applies** formatting; `--check .` only reports what would change and is
for CI. Commit the formatting changes together with your feature work.

```bash
python3 -m ruff format .        # write formatting fixes
python3 -m ruff format --check . # verify no outstanding diffs
python3 -m pytest
python3 -m build
```

## Pull request checklist

- Tests pass.
- Public API changes are documented in `README.md`.
- New dependencies are justified and minimal.
