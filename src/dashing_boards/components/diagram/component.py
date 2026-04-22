from __future__ import annotations

from typing import Any, Callable, ClassVar

from dash import MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


def _to_dataframe(value: Any) -> Any:
    import pandas as pd

    if value is None:
        return pd.DataFrame()
    if isinstance(value, list) and value and isinstance(value[0], list):
        header, *rows = value
        return pd.DataFrame(rows, columns=header)
    if isinstance(value, list):
        return pd.DataFrame(value)
    if isinstance(value, dict):
        return pd.DataFrame([value])
    return pd.DataFrame()


def _apply_filter(df: Any, f: Any) -> Any:
    if f is None:
        return df
    if callable(f):
        return f(df)
    if isinstance(f, dict):
        mask = None
        for k, v in f.items():
            cond = df[k] == v
            mask = cond if mask is None else (mask & cond)
        return df[mask] if mask is not None else df
    if isinstance(f, str):
        return df.query(f)
    return df


def _make_figure(kind: str, df: Any, dimensions: dict[str, Any]) -> Any:
    import plotly.express as px

    fn: dict[str, Callable[..., Any]] = {
        "bar": px.bar,
        "line": px.line,
        "scatter": px.scatter,
        "pie": px.pie,
        "histogram": px.histogram,
        "box": px.box,
        "heatmap": px.density_heatmap,
        "treemap": px.treemap,
    }
    if kind in fn:
        return fn[kind](df, **dimensions)
    if kind == "sankey":
        import plotly.graph_objects as go

        src_col = dimensions.get("source", "source")
        tgt_col = dimensions.get("target", "target")
        val_col = dimensions.get("value", "value")
        labels = sorted(set(df[src_col]).union(df[tgt_col]))
        idx = {label: i for i, label in enumerate(labels)}
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(label=labels),
                    link=dict(
                        source=df[src_col].map(idx).tolist(),
                        target=df[tgt_col].map(idx).tolist(),
                        value=df[val_col].tolist(),
                    ),
                )
            ]
        )
        return fig
    raise ValueError(f"Unknown diagram kind '{kind}'")


class Diagram(DataBoundComponent):
    """Generic chart over a DataFrame-shaped source.

    `kind` ∈ {bar, line, scatter, pie, histogram, box, heatmap, sankey, treemap}.
    `dimensions` is a dict of plotly-express kwargs (x, y, color, size, ...).
    `filter` optionally trims the dataframe before plotting.
    """

    ACCEPTED_TYPES = frozenset({DataType.DATAFRAME, DataType.TABLE_2D, DataType.DICT})
    DEFAULT_KIND: ClassVar[str] = "bar"

    def __init__(
        self,
        source: Any,
        kind: str | None = None,
        dimensions: dict[str, Any] | None = None,
        filter: Any = None,
        height: int | None = None,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self._kind = kind or self.DEFAULT_KIND
        self._dimensions = dimensions or {}
        self._filter = filter
        self._height = height
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _graph_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Diagram", "sub": "graph", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _config_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Diagram", "sub": "config", "source_id": source_id, "aio_id": aio_id}

    def _figure(self, value: Any) -> Any:
        df = _apply_filter(_to_dataframe(value), self._filter)
        if df is None or len(df) == 0:
            import plotly.graph_objects as go

            return go.Figure()
        return _make_figure(self._kind, df, self._dimensions)

    def _build(self) -> list[Any]:
        style = {"height": f"{self._height}px"} if self._height else {}
        return [
            dcc.Store(
                id=self._config_id(self.source.source_id, self.aio_id),
                data={"kind": self._kind, "dimensions": self._dimensions, "filter_repr": repr(self._filter)},
            ),
            dcc.Graph(
                id=self._graph_id(self.source.source_id, self.aio_id),
                figure=self._figure(self.source.initial()),
                style=style,
            ),
        ]

    @callback(
        Output({"component": "Diagram", "sub": "graph", "source_id": MATCH, "aio_id": MATCH}, "figure"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Diagram", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
    )
    def _render(data: Any, config: dict[str, Any]) -> Any:
        kind = (config or {}).get("kind", "bar")
        dimensions = (config or {}).get("dimensions") or {}
        df = _to_dataframe(data)
        if df is None or len(df) == 0:
            import plotly.graph_objects as go

            return go.Figure()
        return _make_figure(kind, df, dimensions)


class BarChart(Diagram):
    DEFAULT_KIND = "bar"


class LineChart(Diagram):
    DEFAULT_KIND = "line"


class ScatterChart(Diagram):
    DEFAULT_KIND = "scatter"


class PieChart(Diagram):
    DEFAULT_KIND = "pie"


class Histogram(Diagram):
    DEFAULT_KIND = "histogram"


class BoxChart(Diagram):
    DEFAULT_KIND = "box"


class Heatmap(Diagram):
    DEFAULT_KIND = "heatmap"


class Sankey(Diagram):
    DEFAULT_KIND = "sankey"


class Treemap(Diagram):
    DEFAULT_KIND = "treemap"
