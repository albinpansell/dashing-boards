"""Minimal demo of the Component <- Data binding sketch.

Two TextBoxes bound to the same STRING source, one TagList bound to a
STRING_LIST source, plus an Interval that mutates the scalar source so
you can see reactivity through the shared dcc.Store.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, callback, dcc, html

from dashing_boards import DataType, StaticData, TagList, TextBox

title_src = StaticData("Hello, binding!", DataType.STRING, source_id="title")
tags_src = StaticData(["alpha", "beta", "gamma"], DataType.STRING_LIST, source_id="tags")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container(
    [
        html.H4("Two TextBoxes sharing one STRING source"),
        TextBox(title_src),
        TextBox(title_src),
        html.Hr(),
        html.H4("TagList bound to a STRING_LIST source"),
        TagList(tags_src),
        html.Hr(),
        dbc.Button("Tick title", id="tick", color="primary", size="sm"),
        # Place each source's Store once in the layout.
        title_src.store(),
        tags_src.store(),
    ],
    className="p-3",
)


@callback(
    Output(title_src.store_id, "data"),
    Input("tick", "n_clicks"),
    prevent_initial_call=True,
)
def _tick(n: int | None) -> str:
    return f"Hello, binding! (clicked {n or 0})"


if __name__ == "__main__":
    app.run(debug=True)
