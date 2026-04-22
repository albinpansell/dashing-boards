from __future__ import annotations

from typing import Any, Sequence

import dash_bootstrap_components as dbc


class Tab(dbc.Tab):
    def __init__(self, label: str, children: Sequence[Any], tab_id: str | None = None) -> None:
        super().__init__(list(children), label=label, tab_id=tab_id or label)


class Tabs(dbc.Tabs):
    def __init__(
        self, tabs: Sequence[Tab], active_tab: str | None = None, container_props: dict[str, Any] | None = None
    ) -> None:
        props = dict(container_props or {})
        if active_tab is not None:
            props["active_tab"] = active_tab
        super().__init__(children=list(tabs), **props)
