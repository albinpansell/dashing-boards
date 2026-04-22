from __future__ import annotations

from typing import Any, Sequence

from dash import dcc


class Loading(dcc.Loading):
    def __init__(self, children: Sequence[Any], kind: str = "default") -> None:
        super().__init__(list(children), type=kind)
