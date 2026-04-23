# AGENTS.md

Context for agents working inside this repo. Pair with `README.md` (user-facing)
and `CONTRIBUTING.md` (workflow).

## Repo layout

```
dashing_boards/
├── src/dashing_boards/
│   ├── app.py                  # make_app() — Dash + Bootstrap + SortableJS
│   ├── __init__.py             # public API surface (export list)
│   ├── binding/                # data sources + the DataBoundComponent base
│   │   ├── component.py        # DataBoundComponent (html.Div subclass)
│   │   ├── source.py           # DataSource, StaticData, CallableDataSource,
│   │   │                       # PollingDataSource, WritableDataSource
│   │   ├── file_source.py      # FileDataSource (CSV/JSON/… with optional watch)
│   │   ├── sql_source.py       # SqlDataSource (SQLAlchemy 2.x)
│   │   ├── http_source.py      # HttpDataSource
│   │   └── types.py            # DataType enum
│   └── components/
│       ├── _writable.py        # triggered_value(), mirror_to_backing() helpers
│       ├── button/ date_picker/ diagram/ dropdown/ graph/ kanban/
│       ├── layout/             # Page, Grid, Tabs/Tab, Modal, Toast, Loading
│       ├── table/ tag_list/ text_box/ text_field/ toggle/
│       ├── tree/ tree_table/
├── examples/                   # runnable Dash apps (one per concept)
├── tests/                      # pytest; mirrors src/ layout
├── pyproject.toml              # PEP 621 metadata, deps, ruff/pytest config
└── README.md / CONTRIBUTING.md
```

## Core pattern: DataSource + DataBoundComponent

Every non-trivial component is bound to a `DataSource`. The binding layer
puts one `dcc.Store` per source into the layout and pattern-matches
callbacks by `source_id`. Components read/write that Store; re-renders
propagate via MATCH.

```python
source = StaticData([...], DataType.DATAFRAME, source_id="sales")
app.layout = Page([BarChart(source, dimensions={...}), source.store()])
```

- `source.store()` must appear **once** in the layout. Place it near the
  end of the Page children list.
- `source.source_id` must be unique across all sources in the app.
- `source.data_type` must be in the component's `ACCEPTED_TYPES` —
  violations raise `TypeError` at construction.

### Writing a new data-bound component

Subclass `DataBoundComponent`:

```python
class MyWidget(DataBoundComponent):
    ACCEPTED_TYPES = frozenset({DataType.STRING})

    @staticmethod
    def _my_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "MyWidget", "sub": "main",
                "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        return [html.Span(id=self._my_id(self.source.source_id, self.aio_id),
                          children=str(self.source.initial()))]

    @callback(
        Output({"component": "MyWidget", "sub": "main",
                "source_id": MATCH, "aio_id": MATCH}, "children"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
    )
    def _render(data):
        return str(data)
```

- Pattern-matched id keys: `component`, `sub`, `source_id`, `aio_id`.
- `aio_id` auto-defaults to a random uuid, so multiple instances bound to
  the same source coexist.
- Export from `components/<name>/__init__.py`, then from
  `components/__init__.py`, then from top-level `__init__.py`.

### Writing a writable component (writes back to the Store)

Dash requires that `Input/State` MATCH keys be a subset of `Output` MATCH
keys. Writebacks target `{"component": "DataSource", "source_id": MATCH}`
which has no `aio_id` key, so inputs must use `aio_id: ALL` (not MATCH)
and the callback resolves which instance fired:

```python
@callback(
    Output({"component": "DataSource", "source_id": MATCH}, "data",
           allow_duplicate=True),
    Input({"component": "MyWidget", "sub": "main",
           "source_id": MATCH, "aio_id": ALL}, "value"),
    prevent_initial_call=True,
)
def _write(_values):
    from .._writable import mirror_to_backing, triggered_value
    v = triggered_value()           # value of the input that actually fired
    mirror_to_backing(v)            # persists to WritableDataSource backing
    return v
```

`triggered_value()` uses `callback_context.triggered`; `mirror_to_backing()`
looks up the source via `PollingDataSource._registry` and calls `.write()` if
it's a `WritableDataSource`.

## make_app()

`make_app(__name__, ...)` is the standard entry point. It:

1. Adds `dbc.themes.BOOTSTRAP` to `external_stylesheets` (without it,
   `dbc.*` components render unstyled).
2. Adds the SortableJS CDN to `external_scripts` (required by `KanbanBoard`).
3. Forwards any other kwargs to `dash.Dash`.

Use it in all new examples and docs. Plain `Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])` also works for apps that don't need Kanban.

## Running / developing

```bash
python3 -m pip install -e .[dev]        # local install
python3 -m pytest                        # run tests
python3 -m ruff format --check .         # formatting
python3 examples/all_components_demo.py  # all components in one page
```

When a demo is already running, port 8050 is taken; pick another:

```python
app.run(debug=True, port=8051)
```

## Pre-PR checklist (mandatory)

Always run these before `git push` or opening a PR. CI runs the same
checks, so skipping them locally just means a failed build later.

```bash
python3 -m ruff format .         # apply formatting (not --check)
python3 -m pytest                 # all tests must pass
```

`ruff format .` (without `--check`) **writes** the formatting fixes. Run
it, stage the resulting changes, and include them in the same commit as
your feature work — do not push code that `ruff format --check` would
flag.

## Gotchas

- **Pattern-matched writebacks**: See "Writing a writable component" above.
  `aio_id: MATCH` on inputs + no-`aio_id` output is a Dash wildcard error.
- **DataTable rendering during edits**: The Table `_render` callback must
  guard with `no_update` when incoming data equals current state, or
  active edits get clobbered. FileDataSource `watch=True` can also
  overwrite edits on its polling tick — default to `watch=False` when
  combining Table editing with writeback.
- **SortableJS and React**: `KanbanBoard` uses SortableJS with
  `forceFallback: true`. The floating clone is styled via `fallbackClass`,
  not `dragClass` (which only applies without `forceFallback`). In `onEnd`,
  undo Sortable's DOM mutation before triggering Dash re-render, or
  React's reconciler throws `removeChild` errors.
- **Graph / Tree layout determinism**: Both use cytoscape's `preset` layout
  with positions computed server-side by `_layered_positions` (BFS from
  roots, orphans at bottom). Do not re-introduce `klay`/`dagre`/`cose` —
  they're non-deterministic across page refreshes in dash-cytoscape.
- **Plotly hierarchical charts**: `go.Treemap/Sunburst/Icicle` use
  `labels=`, not `names=` (the `px.treemap` helper does use `names`, but
  the graph-object form does not).
- **TreeTable int preservation**: `apply_aggregation` keeps results as
  `int` when every input is `int` (so SUM of `[80, 250, 120]` shows
  `450`, not `450.0`). AVERAGE always returns float.
- **Single Store per source**: Call `source.store()` exactly once per
  layout. Duplicate stores give a Dash "duplicate component id" error.

## Testing notes

Tests mirror `src/` layout. Unit tests focus on pure helpers
(`_to_elements`, `_tree_elements`, `apply_aggregation`, `_render_board`)
rather than full component trees. When touching layout logic, also
smoke-test `examples/all_components_demo.py` — any id collision or
prop-validation error surfaces there quickly.
