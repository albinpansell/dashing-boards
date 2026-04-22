from __future__ import annotations

from typing import Any, Sequence

import dash_bootstrap_components as dbc


class Modal(dbc.Modal):
    def __init__(self, title: str, children: Sequence[Any], is_open: bool = False, modal_id: str | None = None) -> None:
        body = [dbc.ModalHeader(dbc.ModalTitle(title)), dbc.ModalBody(list(children))]
        kwargs: dict[str, Any] = {"is_open": is_open}
        if modal_id is not None:
            kwargs["id"] = modal_id
        super().__init__(body, **kwargs)
