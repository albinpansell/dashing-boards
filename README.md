# dashing_boards

Reusable UI components for Plotly Dash apps, distributed as a normal Python package.

## Goals

- Keep components Python-first and easy to integrate.
- Expose a stable API with minimal assumptions about app domain data.
- Ship components that can be installed with `pip` and used across projects.

## Why this layout

This repository follows standard Python packaging guidance:

- `pyproject.toml` with PEP 621 metadata
- `src/` package layout
- `tests/` for pytest
- `examples/` for runnable demos
- CI workflow for tests + build

## Dash component strategy

There are two common ways to publish reusable Dash UI components:

1. Python-only composite components using Dash primitives and callbacks.
2. React/JavaScript-backed Dash components generated with `dash-component-boilerplate`.

This project starts with the Python-only strategy, aligned with Dash All-in-One conventions, which is a good fit when component behavior is server-side and implemented in Python.

## First component: `TreeTableAIO`

`TreeTableAIO` is a general tree table component that supports:

- Hierarchical rows (`id`, `parent_id`, `name`)
- Expand/collapse per node
- Expand/collapse all
- Optional inline editing
- Optional field aggregation (`sum`, `average`, `min`, `max`, `equal`)

The component is intentionally generic and does not encode domain-specific fields.

## Install

```bash
python3 -m pip install dashing-boards
```

For local development:

```bash
python3 -m pip install -e .[dev]
```

## Quick usage

```python
from dash import Dash, html
from dashing_boards import TreeTableAIO

rows = [
    {"id": "root", "parent_id": None, "name": "Root", "cost": 0},
    {"id": "a", "parent_id": "root", "name": "Child A", "cost": 10},
    {"id": "b", "parent_id": "root", "name": "Child B", "cost": 20},
]

app = Dash(__name__)
app.layout = html.Div(
    TreeTableAIO(
        rows=rows,
        editable=True,
        aggregations={"cost": "sum"},
    )
)

if __name__ == "__main__":
    app.run(debug=True)
```

## Development

```bash
python3 -m ruff format --check .
python3 -m pytest
python3 -m build
```

## Examples

```bash
python3 examples/tree_table_demo.py
python3 examples/tree_table_edit_demo.py
```

## Publish to PyPI

1. Build distributions:

```bash
python3 -m build
```

2. Verify package metadata:

```bash
python3 -m twine check dist/*
```

3. Upload to TestPyPI:

```bash
python3 -m twine upload --repository testpypi dist/*
```

4. Upload to PyPI:

```bash
python3 -m twine upload dist/*
```

## Component catalog

| Category | Components |
|---|---|
| Basics | `TextBox`, `TextField`, `Button`, `Toggle`, `Dropdown`, `DatePicker`, `TagList` |
| Tables | `Table`, `TreeTableAIO` |
| Diagrams | `Diagram`, `BarChart`, `LineChart`, `ScatterChart`, `PieChart`, `Histogram`, `BoxChart`, `Heatmap`, `Sankey`, `Treemap` |
| Graphs / Trees | `Graph`, `Tree` |
| Kanban | `KanbanBoard` |
| Layout | `Page`, `Grid`, `Tab`, `Tabs`, `Modal`, `Toast`, `Loading` |

## Data sources

- `StaticData` — hardcoded Python value.
- `CallableDataSource` — value produced by an arbitrary callable.
- `SqlDataSource` — SQLAlchemy 2.x; works with SQLite, DuckDB, Postgres, etc.
- `FileDataSource` — CSV, TSV, JSON, JSONL, YAML, Parquet, Markdown, plain text. Optional live-watch (polls mtime). Opt-in atomic writes.
- `HttpDataSource` — thin REST wrapper (httpx or urllib).

All sources share the same Store-backed architecture: each exposes a `dcc.Store` with a pattern-matchable id, and every component bound to that source auto-updates via MATCH callbacks.

## Roadmap

- Replace Kanban MVP (Python-only) with a `dnd-kit`-backed React component for native drag-and-drop.
- Parent-child data dependencies for `Grid` (awaiting concrete use cases).
- Harden accessibility and keyboard interactions across all components.
