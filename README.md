# dashing_boards

Reusable UI components for Plotly Dash apps, distributed as a Python package.

## Goals

- Keep components Python-first and easy to integrate.
- Expose a stable API with minimal assumptions about app domain data.

## Why this layout

This repository follows standard Python packaging guidance:

- `pyproject.toml` with PEP 621 metadata
- `src/` package layout
- `tests/` for pytest
- `examples/` for runnable demos
- CI workflow for tests + build

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
from dash import html
from dashing_boards import TreeTableAIO, make_app

rows = [
    {"id": "root", "parent_id": None, "name": "Root", "cost": 0},
    {"id": "a", "parent_id": "root", "name": "Child A", "cost": 10},
    {"id": "b", "parent_id": "root", "name": "Child B", "cost": 20},
]

app = make_app(__name__)
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

`make_app` is a thin wrapper over `dash.Dash` that pre-loads the Bootstrap
stylesheet and the SortableJS library (required by `KanbanBoard`). Use it
in new apps; plain `Dash(__name__)` also works if you wire those yourself.

## Development

```bash
python3 -m ruff format --check .
python3 -m pytest
python3 -m build
```

## Examples

Each file under `examples/` is a runnable Dash app demonstrating a slice of
the library. `all_components_demo.py` mounts every component in one page —
use it to smoke-test that components coexist without callback collisions.

```bash
python3 examples/all_components_demo.py      # every component, one page
python3 examples/binding_demo.py              # StaticData + TextBox/TagList
python3 examples/file_source_demo.py          # Table bound to a writable CSV
python3 examples/sql_source_demo.py           # Table + BarChart on SQLite
python3 examples/diagram_demo.py              # all Plotly chart kinds
python3 examples/graph_demo.py                # Graph + Tree (cytoscape)
python3 examples/kanban_demo.py               # drag-and-drop Kanban
python3 examples/tree_table_demo.py           # read-only TreeTable
python3 examples/tree_table_edit_demo.py      # editable TreeTable
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

## For contributors and agents

See [AGENTS.md](AGENTS.md) for a map of the repo, component/data-source
conventions, the DataBoundComponent pattern, and common gotchas.
