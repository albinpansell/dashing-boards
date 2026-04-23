from __future__ import annotations

from typing import Any, Sequence

import dash_bootstrap_components as dbc
from dash import html


class Page(html.Div):
    """Top-level page container. Adds a title, optional subtitle, and a body."""

    def __init__(
        self,
        children: Sequence[Any],
        title: str | None = None,
        subtitle: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        head: list[Any] = []
        if title:
            head.append(html.H3(title, className="mb-1"))
        if subtitle:
            head.append(html.Div(subtitle, className="text-muted mb-3"))
        body = dbc.Container(head + list(children), fluid=True, className="p-3")
        super().__init__(children=[body], **(container_props or {}))
